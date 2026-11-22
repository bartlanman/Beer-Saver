#!/usr/bin/env python3
"""
Beer Saver -> Untappd + printed menu sync for Basic City.

Run every few minutes (see README.md in this folder). Each run:
  1. Reads the current tap list from the Beer Saver API (/Inventory).
  2. Compares it with the last run (state file). A tap "changed" when its
     beverage or its ConnectTime (keg change time) differs.
  3. If anything changed:
       - updates the Untappd "Beer on Tap!" menu for Taproom taps,
       - writes a fresh menu (HTML + PDF) and sends it to the printer,
       - prints a checklist of manual steps (Toast button, Beer Saver linking).

Safety: DRY RUN is the default. Nothing is written to Untappd and nothing is
printed unless you pass --live. Credentials come from environment variables
(or the macOS Keychain); they never live in this repo.

Environment:
  BEERSAVER_USER    e.g. "<ClientID>-<username>"
  BEERSAVER_PASS
  UNTAPPD_EMAIL     Untappd for Business login email
  UNTAPPD_TOKEN     Untappd for Business read/write API token (Account > API)
  MENU_PRINTER      CUPS printer name (see `lpstat -p`); optional
  MENU_COPIES       copies printed per menu change; default 10
  CHROME            path to Chrome for HTML->PDF; optional (macOS default used)

UNTESTED against the live Untappd API; run without --live first and check output.
"""
import argparse, base64, datetime, difflib, html, json, os, re, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRANCH_ID = 1392
BS_API = f"https://api.usbeersaver.com/api/{BRANCH_ID}"
UT_API = "https://business.untappd.com/api/v1"
STATE = Path(os.environ.get("TAP_SYNC_STATE", Path.home() / ".beersaver-tap-state.json"))
OUT = Path(os.environ.get("TAP_SYNC_OUT", HERE / "Tap Menu"))  # not ~/Desktop: macOS blocks background jobs there
LEARNED = Path(os.environ.get("TAP_SYNC_LEARNED", HERE / "learned-beers.json"))  # beers found automatically
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def secret(name, keychain_service):
    v = os.environ.get(name)
    if v:
        return v
    try:  # macOS Keychain: security add-generic-password -s <service> -a "$USER" -w
        return subprocess.run(["security", "find-generic-password", "-s", keychain_service, "-w"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        sys.exit(f"Missing credential {name} (env var or Keychain service '{keychain_service}')")


def http(method, url, user, pw, body=None):
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Authorization", "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode())
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw.strip() else None


def tap_label(description):
    """'1 Taproom - 01' -> ('1 Taproom', '1');  '1 Taproom - DB 2' -> ('1 Taproom', 'DB 2')."""
    bar, _, tap = description.partition(" - ")
    tap = tap.strip()
    return bar.strip(), (str(int(tap)) if tap.isdigit() else tap)


def load_map():
    m = json.loads((HERE / "beer-map.json").read_text())
    beers = {}
    if LEARNED.exists():  # found automatically on earlier runs; beer-map.json wins
        beers.update({b["beersaver"]: b for b in json.loads(LEARNED.read_text())})
    beers.update({b["beersaver"]: b for b in m["beers"]})
    return m, beers


def _norm(text):
    text = re.sub(r"[^a-z0-9 ]", " ", (text or "").lower().replace("\u2019", "'").replace("'", ""))
    return " ".join(w for w in text.split() if w not in {"the", "beer", "co", "company"})


def _short_brewery(name):
    drop = {"brewing", "brewery", "company", "co", "co.", "beer", "brewers", "ales", "craft", "llc"}
    return " ".join(w for w in (name or "").split() if w.lower().strip(",.") not in drop) or name


def price_for(abv, meta):
    """Price a new beer by ABV using meta['price_tiers'] (first tier whose max_abv it's under)."""
    try:
        abv = float(abv)
    except (TypeError, ValueError):
        abv = 0.0
    for tier in meta.get("price_tiers", []):
        if abv < tier.get("max_abv", 999):
            return dict(tier["prices"])
    return dict(meta["default_prices"])


def _beer_from_untappd(name, item, meta, prices=None):
    house = "basic city" in (item.get("brewery") or "").lower()
    menu_name = item.get("name") if house or (item.get("name") or "").startswith("Guest Tap!") \
        else f"Guest Tap! - {_short_brewery(item.get('brewery'))} {item.get('name')}"
    return {"beersaver": name, "untappd_id": item["untappd_id"], "menu_name": menu_name,
            "brewery": item.get("brewery") or "", "abv": item.get("abv") or "",
            "style": item.get("short_style") or item.get("style") or "",
            "location": item.get("brewery_location") or "",
            "description": " ".join((item.get("description") or "").split()),
            "prices": prices or price_for(item.get("abv"), meta),
            "status": "auto", "found": datetime.date.today().isoformat()}


def _match(query, item):
    """(acceptable, score). Acceptable only if every word of the Beer Saver name is in the
    Untappd name (with or without brewery), or the names are nearly identical."""
    q = _norm(query)
    names = [_norm(item.get("name")), _norm(f"{item.get('brewery')} {item.get('name')}"),
             _norm(f"{_short_brewery(item.get('brewery'))} {item.get('name')}")]
    ratio = max(difflib.SequenceMatcher(None, q, n).ratio() for n in names)
    contains = set(q.split()) <= set(" ".join(names).split())
    house = "basic city" in (item.get("brewery") or "").lower()
    score = ratio + (0.2 if contains else 0) + ((0.35 if contains else 0.1) if house else 0)
    return (contains or ratio >= 0.9), score


def lookup_new_beers(taps, beers, meta, live=True):
    """Give every beer on a Taproom or Foundry tap full menu details before anything prints.

    Beers missing from beer-map.json / learned-beers.json are looked up on Untappd:
    first on our own Untappd tap menu (keeps its prices), then in the Untappd beer
    database (priced by ABV). Results are saved to learned-beers.json."""
    new = sorted({t["beer"] for t in taps if t["bar"] in ("1 Taproom", "2 Foundry") and t["beer"] != "*EMPTY"
                  and not (beers.get(t["beer"]) or {}).get("untappd_id")})
    if not new:
        return []
    try:
        email, token = secret("UNTAPPD_EMAIL", "untappd-email"), secret("UNTAPPD_TOKEN", "untappd-token")
        menu = http("GET", f"{UT_API}/sections/{meta['untappd_tap_section_id']}/items", email, token).get("items", [])
    except Exception as e:
        print(f"  Lookup skipped (Untappd unreachable: {e})")
        return new
    learned = json.loads(LEARNED.read_text()) if LEARNED.exists() else []
    missing = []
    for name in new:
        found = None
        on_menu = max((i for i in menu if _match(name, i)[0]), key=lambda i: _match(name, i)[1], default=None)
        if on_menu:
            prices = {c["container_size"]["name"]: c["price"] for c in on_menu.get("containers") or []
                      if c.get("container_size", {}).get("name") in ("16oz", "8oz", "4oz")}
            if not prices:
                prices = {c["container_size"]["name"]: c["price"] for c in
                          http("GET", f"{UT_API}/items/{on_menu['id']}/containers", email, token).get("containers", [])
                          if c.get("container_size", {}).get("name") in ("16oz", "8oz", "4oz")}
            found, how = _beer_from_untappd(name, on_menu, meta, prices or None), "from the Untappd menu"
        else:
            results = []
            for q in (f"Basic City {name}", name):
                try:
                    results += http("GET", f"{UT_API}/items/search?q={urllib.parse.quote(q)}", email, token).get("items", [])
                except Exception:
                    pass
            pool = [r for r in {r["untappd_id"]: r for r in results if r.get("untappd_id")}.values()
                    if _match(name, r)[0]]
            house = [r for r in pool if "basic city" in (r.get("brewery") or "").lower()]
            if len(house) > 1:  # e.g. plain "Tart Up": several of our releases fit - take the newest
                pick, how = max(house, key=lambda r: r["untappd_id"]), \
                    f"from an Untappd search, priced by ABV - CHECK: {len(house)} Basic City beers fit, took the newest"
            elif pool:
                pick = max(pool, key=lambda r: (_match(name, r)[1], r.get("rating_count") or 0))
                how = "from an Untappd search, priced by ABV"
            else:
                pick = None
            if pick:
                found = _beer_from_untappd(name, pick, meta)
        if found:
            beers[name] = found
            learned = [b for b in learned if b["beersaver"] != name] + [found]
            p = found["prices"]
            print(f"  NEW BEER '{name}' -> {found['menu_name']} ({found['abv']}%, "
                  f"${p.get('16oz')}/${p.get('8oz')}/${p.get('4oz')}) {how}")
        else:
            missing.append(name)
            print(f"  NEW BEER '{name}': no Untappd match - prints with its Beer Saver name only")
    if live:
        LEARNED.write_text(json.dumps(learned, indent=1, ensure_ascii=False))
    return missing


def read_taps():
    user, pw = secret("BEERSAVER_USER", "beersaver-api-user"), secret("BEERSAVER_PASS", "beersaver-api-pass")
    taps = []
    for row in http("GET", f"{BS_API}/Inventory", user, pw):
        bar, tap = tap_label(row["Description"])
        taps.append({"meter": int(row["MeterID"]), "bar": bar, "tap": tap,
                     "beer": row["BeverageName"], "connect": row["ConnectTime"],
                     "pct": round(100 * (row.get("CurrentKegPctRemaining") or 0))})
    return taps


def diff(old, new):
    """Taps whose BEER changed (or that are new). A retap of the same beer only moves
    ConnectTime; it changes nothing on the menu, so it is not reported."""
    prev = {t["meter"]: t for t in old}
    return [t for t in new if t["meter"] not in prev or prev[t["meter"]]["beer"] != t["beer"]]


def untappd_sync(taps, beers, meta, live):
    """Make the Untappd tap menu hold exactly the beers on the Taproom taps.

    Matches by Untappd beer id, not tap number (our Untappd items have no tap
    numbers). Adds mapped beers that are missing; removes menu beers that are in
    beer-map.json but no longer on any Taproom tap. Never touches a menu item
    whose beer isn't in beer-map.json."""
    email, token = secret("UNTAPPD_EMAIL", "untappd-email"), secret("UNTAPPD_TOKEN", "untappd-token")
    sec = meta["untappd_tap_section_id"]
    items = http("GET", f"{UT_API}/sections/{sec}/items", email, token).get("items", [])
    on_menu = {i.get("untappd_id"): i for i in items}
    known = {b["untappd_id"] for b in beers.values() if b.get("untappd_id")}

    want, unmapped = {}, []
    for t in taps:
        if t["bar"] != "1 Taproom" or t["beer"] == "*EMPTY":
            continue  # Foundry taps are not on the Untappd menu
        b = beers.get(t["beer"])
        if not b or not b.get("untappd_id"):
            unmapped.append(("unmapped", t, None, None))
            print(f"  Untappd unmapped tap {t['tap']:5} {t['beer']} (not in beer-map.json; left alone)")
            continue
        want.setdefault(b["untappd_id"], (t, b))

    adds = [(t, b) for uid, (t, b) in want.items() if uid not in on_menu]
    removes = [i for uid, i in on_menu.items() if uid in known and uid not in want]
    for i in removes:
        print(f"  Untappd remove   {i.get('name')}  (no longer on a Taproom tap)")
    for t, b in adds:
        print(f"  Untappd add      {b.get('menu_name') or t['beer']}  (tap {t['tap']})")
    if not adds and not removes:
        print("  Untappd: already matches the Taproom taps")
    if not live:
        return unmapped

    for i in removes:
        http("DELETE", f"{UT_API}/items/{i['id']}", email, token)
    sizes = meta["untappd_container_size_ids"]
    for t, b in adds:
        res = http("POST", f"{UT_API}/sections/{sec}/items", email, token, {"untappd_id": b["untappd_id"]})
        item = res.get("item") or (res.get("items") or [None])[0]
        if b.get("menu_name"):
            http("PATCH", f"{UT_API}/items/{item['id']}", email, token, {"item": {"name": b["menu_name"]}})
        for size, price in (b.get("prices") or meta["default_prices"]).items():
            http("POST", f"{UT_API}/items/{item['id']}/containers", email, token,
                 {"container": {"container_size_id": sizes[size], "price": float(price)}})
    if removes or adds:  # edits stay a draft until published; screens and the app show the published menu
        http("POST", f"{UT_API}/menus/{meta['untappd_tap_menu_id']}/publish", email, token)
        print("  Untappd menu published")
    return unmapped


def render_menu(taps, beers, meta=None):
    """One letter page in the style of the Untappd 'Beer on Tap!' print menu:
    Taproom taps only, in tap order, split into two boxed columns."""
    OUT.mkdir(parents=True, exist_ok=True)
    meta = meta or {}
    foot = meta.get("print_footer", {})
    esc = html.escape
    order = lambda x: (x["tap"].startswith("DB"), x["tap"].zfill(5))
    cards = []
    for t in sorted((t for t in taps if t["bar"] == "1 Taproom" and t["beer"] != "*EMPTY"), key=order):
        b = beers.get(t["beer"], {})
        line = " \u2022 ".join(x for x in (b.get("style"), (b["abv"].rstrip("0").rstrip(".") + "% ABV") if b.get("abv") else "",
                                           b.get("location")) if x)
        prices = b.get("prices") or {}
        price = " \u00b7 ".join(f"{size} ${prices[size]}" for size in ("16oz", "8oz", "4oz") if prices.get(size))
        cards.append(f"<div class=beer><div class=nm>{esc(b.get('menu_name') or t['beer'])}</div>"
                     + (f"<div class=st>{esc(line)}</div>" if line else "")
                     + (f"<div class=ds>{esc(b['description'])}</div>" if b.get("description") else "")
                     + (f"<div class=pr>{esc(price)}</div>" if price else "") + "</div>")
    half = (len(cards) + 1) // 2
    cols = "".join(f"<div class=col><h2>_DRAFT</h2>{''.join(c)}</div>" for c in (cards[:half], cards[half:]))
    logo = foot.get("logo_url")
    logo_html = (f"<img class=logo id=logo crossorigin=anonymous src='{esc(logo)}' alt='Basic City'>"
                 if logo else "<div class=logo>BASIC CITY</div>")
    today = datetime.date.today().strftime("%B %-d, %Y")
    page = f"""<!doctype html><meta charset=utf-8><title>Beer on Tap</title><style>
@page{{size:letter;margin:.45in}}html,body{{margin:0}}
body{{font-family:"Fira Sans","Avenir Next","Helvetica Neue",Arial,sans-serif;color:#111;height:9.95in;display:flex;flex-direction:column}}
.box{{border:2.5px solid #111}}.hd{{display:flex;justify-content:space-between;align-items:center;padding:14pt 14pt 12pt;border-bottom:2.5px solid #111}}
h1{{margin:0;font-size:20pt;letter-spacing:.5pt}}.sub{{font-size:12pt}}.logo{{height:44pt;max-width:120pt;object-fit:contain;font-weight:bold;letter-spacing:2pt;filter:grayscale(1) brightness(1.25) contrast(1.8)}}
.cols{{display:grid;grid-template-columns:1fr 1fr;font-size:10pt}}.col{{padding:10pt 14pt 6pt}}.col+.col{{border-left:2.5px solid #111}}
h2{{font-size:1.6em;margin:0 0 .5em}}.beer{{margin:0 0 .8em;break-inside:avoid}}.nm{{font-weight:600;font-size:1.25em}}
.st{{font-size:1.05em}}.ds{{font-size:.9em;line-height:1.3;margin-top:.1em;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.pr{{font-weight:700;font-style:italic;font-size:1.05em;margin-top:.2em}}
.ft{{margin-top:auto;display:grid;grid-template-columns:1fr 1.3fr 1fr;align-items:end;font-size:10pt}}
.ft .c{{text-align:center;padding:0 10pt}}.ft .c .tax{{display:inline-block;border-bottom:2.5px solid #111;padding-bottom:6pt;margin-bottom:6pt}}.ft .r{{text-align:right}}
</style>
<div class=box><div class=hd><div><h1>{esc(meta.get("menu_title", "BEER ON TAP!"))}</h1><div class=sub>{esc(meta.get("menu_subtitle", "Draft"))}</div></div>{logo_html}</div>
<div class=cols>{cols}</div></div>
<div class=ft><div>{esc(foot.get("phone", ""))} \u2022 {esc(foot.get("website", ""))}</div>
<div class=c><div class=tax>{esc(foot.get("note", ""))}</div><br>{today} \u2022 Subscribe to us on Untappd</div>
<div class=r>{esc(foot.get("address", ""))}</div></div>
<script>/* logo: Untappd's file has a beige box and a faint reflection - keep only the dark ink */
(function(){{var im=document.getElementById('logo');if(!im)return;
function clean(){{try{{var c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;
var x=c.getContext('2d');x.drawImage(im,0,0);var d=x.getImageData(0,0,c.width,c.height),p=d.data;
for(var i=0;i<p.length;i+=4){{var l=.3*p[i]+.59*p[i+1]+.11*p[i+2];
if(p[i+3]<20||l>140){{p[i+3]=0}}else{{p[i]=p[i+1]=p[i+2]=Math.max(0,l-40);p[i+3]=255}}}}
x.putImageData(d,0,0);var W=c.width,H=c.height,a=W,b=H,e=-1,f=-1;
for(var y=0;y<H;y++)for(var q=0;q<W;q++)if(p[(y*W+q)*4+3]){{if(q<a)a=q;if(q>e)e=q;if(y<b)b=y;if(y>f)f=y}}
if(e>=a){{var t=document.createElement('canvas');t.width=e-a+1;t.height=f-b+1;t.getContext('2d').drawImage(c,a,b,t.width,t.height,0,0,t.width,t.height);c=t}}
c.className='logo';c.style.filter='none';c.style.height='44pt';c.style.width='auto';im.replaceWith(c)}}catch(e){{}}}}
if(im.complete&&im.naturalWidth)clean();else{{im.addEventListener('load',clean);
im.addEventListener('error',function(){{var o=new Image();o.className='logo';o.alt='Basic City';o.src=im.src;im.replaceWith(o)}})}}}})();
/* shrink the beer text until the box clears the footer: always one page */
var c=document.querySelector('.cols'),b=document.querySelector('.box'),f=document.querySelector('.ft'),s=10;
while(s>6&&b.getBoundingClientRect().bottom>f.getBoundingClientRect().top-12){{s-=.25;c.style.fontSize=s+'pt';}}</script>"""
    html_path = OUT / "tap-menu.html"
    html_path.write_text(page)
    pdf_path = OUT / "tap-menu.pdf"
    pdf_path.unlink(missing_ok=True)  # never print a stale menu if Chrome fails
    if Path(CHROME).exists():
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=10000",
                        f"--print-to-pdf={pdf_path}", html_path.as_uri()], capture_output=True)
    return pdf_path if pdf_path.exists() else html_path


def _is_house(b):
    return "basic city" in (b.get("brewery") or "").lower()


def foundry_sync(taps, beers, meta, live):
    """Make the Untappd 'Foundry On Tap' Draft / Guest Taps sections match Beer Saver's Foundry taps.

    Every item in those two sections is managed here; More Drinks is never touched.
    Prices come from foundry_price in beer-map.json (Toast prices, tax included); a beer
    without one gets meta['foundry']['default_prices'] and the log says CHECK PRICE."""
    f = meta["foundry"]
    email, token = secret("UNTAPPD_EMAIL", "untappd-email"), secret("UNTAPPD_TOKEN", "untappd-token")
    want = {}
    for t in taps:
        if t["bar"] != "2 Foundry" or t["beer"] == "*EMPTY":
            continue
        b = beers.get(t["beer"]) or {}
        if not b.get("untappd_id"):
            print(f"  Foundry: '{t['beer']}' has no Untappd match - not on the screen")
            continue
        want.setdefault(b["untappd_id"], b)
    have = {}
    for kind in ("house", "guest"):
        for i in http("GET", f"{UT_API}/sections/{f['sections'][kind]}/items", email, token).get("items", []):
            have[i.get("untappd_id")] = (kind, i)
    removes = [i for uid, (k, i) in have.items() if uid not in want or k != ("house" if _is_house(want[uid]) else "guest")]
    adds = [b for uid, b in want.items() if uid not in have or have[uid][1] in removes]
    for i in removes:
        print(f"  Foundry remove   {i.get('name')}")
    for b in adds:
        kind = "house" if _is_house(b) else "guest"
        name = b.get("foundry_name") or re.sub(r"^Guest Tap! - ", "", b.get("menu_name") or b["beersaver"])
        price = b.get("foundry_price")
        note = "" if price else "  CHECK PRICE: no Toast price saved, used the default"
        price = price or f["default_prices"][kind]
        b["_foundry"] = (kind, name, price)
        print(f"  Foundry add      {name} ${price} ({'Draft' if kind == 'house' else 'Guest Taps'}){note}")
    if not live:
        return
    for i in removes:
        http("DELETE", f"{UT_API}/items/{i['id']}", email, token)
    for b in adds:
        kind, name, price = b.pop("_foundry")
        res = http("POST", f"{UT_API}/sections/{f['sections'][kind]}/items", email, token, {"untappd_id": b["untappd_id"]})
        item = res.get("item") or (res.get("items") or [None])[0]
        http("PATCH", f"{UT_API}/items/{item['id']}", email, token, {"item": {"name": name}})
        http("POST", f"{UT_API}/items/{item['id']}/containers", email, token,
             {"container": {"container_size_id": f["container_size_id"], "price": float(price)}})
    if adds or removes:  # Untappd puts new items first; put both sections back in tap order
        order = list(want)
        for kind in ("house", "guest"):
            items = http("GET", f"{UT_API}/sections/{f['sections'][kind]}/items", email, token).get("items", [])
            items.sort(key=lambda i: order.index(i["untappd_id"]) if i.get("untappd_id") in order else 99)
            for pos, i in enumerate(items):
                if i.get("position") != pos:
                    http("PATCH", f"{UT_API}/items/{i['id']}", email, token, {"item": {"position": pos}})


def foundry_screen(meta, live, force=False):
    """Rebuild the Foundry bar screen image from the Untappd 'Foundry On Tap' menu when it changed
    (beer changes from Beer Saver, or hand edits to More Drinks in Untappd)."""
    import hashlib
    import foundry_board
    f = meta["foundry"]
    email, token = secret("UNTAPPD_EMAIL", "untappd-email"), secret("UNTAPPD_TOKEN", "untappd-token")
    sections = {}
    for kind in ("house", "guest", "other"):
        rows = []
        for i in sorted(http("GET", f"{UT_API}/sections/{f['sections'][kind]}/items", email, token).get("items", []),
                        key=lambda i: i.get("position") or 0):
            cs = i.get("containers") or http("GET", f"{UT_API}/items/{i['id']}/containers", email, token).get("containers", [])
            rows.append((i.get("name"), cs[0]["price"] if cs else ""))
        sections[kind] = rows
    digest = hashlib.sha1(json.dumps(sections, sort_keys=True).encode()).hexdigest()
    out = OUT.parent / "Foundry Board" if OUT.name == "Tap Menu" else OUT / "Foundry Board"
    stamp = out / "last.sha1"
    if not force and stamp.exists() and stamp.read_text() == digest:
        return None
    lines = " / ".join(f"{n} ${p}" for k in ("house", "guest", "other") for n, p in sections[k])
    print(f"  Foundry screen: {lines}")
    if not live:
        return None
    png = foundry_board.render_board(sections, out)
    if png:
        stamp.write_text(digest)
        print(f"  Foundry screen image: {png}")
    # Paper menus for the Foundry: letter table tents + 11x17 landscape boards
    printer = os.environ.get("MENU_PRINTER")
    if printer:
        tent, poster = foundry_board.render_prints(sections, out)
        # The Mac mini's "Kyocera" queue (Generic PostScript) has no 11x17 size, so 11x17s go to a second
        # queue on the same printer whose PPD adds Tabloid (see INSTALL-Mac-mini.md, "11x17 printer").
        tabloid = os.environ.get("FOUNDRY_POSTER_PRINTER", "Kyocera_11x17")
        if subprocess.run(["lpstat", "-p", tabloid], capture_output=True).returncode != 0:
            print(f"  WARNING: printer {tabloid} not found - 11x17s would print on letter; skipped")
            tabloid = None
        jobs = ((tent, printer, os.environ.get("FOUNDRY_TENT_COPIES", "12"), ["-o", "media=Letter"], "letter table tents"),
                (poster, tabloid, os.environ.get("FOUNDRY_POSTER_COPIES", "10"),
                 ["-o", "PageSize=Tabloid", "-o", "fit-to-page"], "11x17 menus"))
        for pdf, queue, n, opts, what in jobs:
            if pdf and queue and int(n) > 0:
                subprocess.run(["lp", "-d", queue, "-n", n, *opts, str(pdf)], check=False)
                print(f"  Sent {n} Foundry {what} to {queue}")
    return png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="actually update Untappd and print")
    ap.add_argument("--force", action="store_true", help="treat every tap as changed")
    ap.add_argument("--no-untappd", action="store_true")
    a = ap.parse_args()

    meta, beers = load_map()
    taps = read_taps()
    old = json.loads(STATE.read_text()) if STATE.exists() else []
    changes = taps if a.force or not old else diff(old, taps)
    print(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {len(taps)} taps, {len(changes)} changed"
          f"{'' if a.live else ' (DRY RUN)'}")
    if not changes:
        if a.live:
            STATE.write_text(json.dumps(taps, indent=1))  # keep keg levels/retap times current
        _foundry(meta, a)
        return
    for t in changes:
        print(f"  {t['bar']} {t['tap']:5} {t['beer']}  (changed {t['connect']}, {t['pct']}% left)")

    missing = lookup_new_beers(taps, beers, meta, a.live)  # before anything prints or goes to Untappd

    first_run = not old and not a.force
    if first_run:
        print("  First run: recording the current taps as the starting point; Untappd left as is.")
    taproom = [t for t in changes if t["bar"] == "1 Taproom"]
    unmapped = [] if (a.no_untappd or first_run or not taproom) else untappd_sync(taps, beers, meta, a.live)
    if "foundry" in meta and not a.no_untappd and (first_run or any(t["bar"] == "2 Foundry" for t in changes)):
        try:
            foundry_sync(taps, beers, meta, a.live)
        except Exception as e:
            print(f"  Foundry sync failed: {e}")
    menu = render_menu(taps, beers, meta)
    print(f"  Menu: {menu}")
    printer = os.environ.get("MENU_PRINTER")
    if a.live and printer and menu.suffix == ".pdf" and (taproom or a.force):
        copies = os.environ.get("MENU_COPIES", "10")
        subprocess.run(["lp", "-d", printer, "-n", copies, str(menu)], check=False)
        print(f"  Sent {copies} copies to printer {printer}")

    fresh = sorted({t["beer"] for t in changes if (beers.get(t["beer"]) or {}).get("status") == "auto"
                    and beers[t["beer"]].get("found") == datetime.date.today().isoformat()} | set(missing))
    if fresh:
        print("  TO DO (manual): add draft buttons in Toast, then link them in Beer Saver > LINKING "
              "(buttons appear there within ~90 min) for: " + ", ".join(fresh))
    if a.live or not old:
        STATE.write_text(json.dumps(taps, indent=1))
    _foundry(meta, a)


def _foundry(meta, a):
    if "foundry" not in meta or a.no_untappd:
        return
    try:
        foundry_screen(meta, a.live, a.force)
    except Exception as e:  # never let the screen stop the menu sync
        print(f"  Foundry screen failed: {e}")


if __name__ == "__main__":
    main()
