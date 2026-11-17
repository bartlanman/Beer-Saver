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
import argparse, base64, datetime, html, json, os, subprocess, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRANCH_ID = 1392
BS_API = f"https://api.usbeersaver.com/api/{BRANCH_ID}"
UT_API = "https://business.untappd.com/api/v1"
STATE = Path(os.environ.get("TAP_SYNC_STATE", Path.home() / ".beersaver-tap-state.json"))
OUT = Path(os.environ.get("TAP_SYNC_OUT", Path.home() / "Desktop" / "Tap Menu"))
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
    return m, {b["beersaver"]: b for b in m["beers"]}


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


def untappd_sync(changes, beers, meta, live):
    """Make the Untappd tap menu match Beer Saver for the Taproom taps that changed."""
    email, token = secret("UNTAPPD_EMAIL", "untappd-email"), secret("UNTAPPD_TOKEN", "untappd-token")
    sec = meta["untappd_tap_section_id"]
    items = http("GET", f"{UT_API}/sections/{sec}/items", email, token).get("items", [])
    by_tap = {str(i.get("tap_number") or "").strip(): i for i in items}
    todo = []
    for t in changes:
        if t["bar"] != "1 Taproom":
            continue  # Foundry taps are not on the Untappd menu
        cur, want = by_tap.get(t["tap"]), beers.get(t["beer"])
        if t["beer"] == "*EMPTY":
            if cur:
                todo.append(("remove", t, cur, None))
            continue
        if not want or not want.get("untappd_id"):
            todo.append(("unmapped", t, cur, None))
            continue
        if cur and cur.get("untappd_id") == want["untappd_id"]:
            continue  # same beer (retap) - nothing to change on Untappd
        todo.append(("replace" if cur else "add", t, cur, want))

    for action, t, cur, want in todo:
        print(f"  Untappd {action:8} tap {t['tap']:5} {(cur or {}).get('name', '-')!s:35} -> {t['beer']}")
        if not live or action == "unmapped":
            continue
        if cur:
            http("DELETE", f"{UT_API}/items/{cur['id']}", email, token)
        if want:
            res = http("POST", f"{UT_API}/sections/{sec}/items", email, token,
                       {"untappd_id": want["untappd_id"]})
            item = res.get("item") or (res.get("items") or [None])[0]
            body = {"tap_number": t["tap"]}
            if want.get("menu_name"):
                body["name"] = want["menu_name"]
            http("PATCH", f"{UT_API}/items/{item['id']}", email, token, {"item": body})
            sizes = meta["untappd_container_size_ids"]
            for size, price in (want.get("prices") or meta["default_prices"]).items():
                http("POST", f"{UT_API}/items/{item['id']}/containers", email, token,
                     {"container": {"container_size_id": sizes[size], "price": float(price)}})
    return [x for x in todo if x[0] == "unmapped"]


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
    logo_html = f"<img class=logo src='{esc(logo)}' alt='Basic City'>" if logo else "<div class=logo>BASIC CITY</div>"
    today = datetime.date.today().strftime("%B %-d, %Y")
    page = f"""<!doctype html><meta charset=utf-8><title>Beer on Tap</title><style>
@page{{size:letter;margin:.45in}}html,body{{margin:0}}
body{{font-family:"Fira Sans","Avenir Next","Helvetica Neue",Arial,sans-serif;color:#111;height:9.95in;display:flex;flex-direction:column}}
.box{{border:2.5px solid #111}}.hd{{display:flex;justify-content:space-between;align-items:center;padding:14pt 14pt 12pt;border-bottom:2.5px solid #111}}
h1{{margin:0;font-size:20pt;letter-spacing:.5pt}}.sub{{font-size:12pt}}.logo{{height:44pt;max-width:120pt;object-fit:contain;font-weight:bold;letter-spacing:2pt}}
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
<script>/* shrink the beer text until the box clears the footer: always one page */
var c=document.querySelector('.cols'),b=document.querySelector('.box'),f=document.querySelector('.ft'),s=10;
while(s>6&&b.getBoundingClientRect().bottom>f.getBoundingClientRect().top-12){{s-=.25;c.style.fontSize=s+'pt';}}</script>"""
    html_path = OUT / "tap-menu.html"
    html_path.write_text(page)
    pdf_path = OUT / "tap-menu.pdf"
    pdf_path.unlink(missing_ok=True)  # never print a stale menu if Chrome fails
    if Path(CHROME).exists():
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf_path}", html_path.as_uri()], capture_output=True)
    return pdf_path if pdf_path.exists() else html_path


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
        return
    for t in changes:
        print(f"  {t['bar']} {t['tap']:5} {t['beer']}  (changed {t['connect']}, {t['pct']}% left)")

    first_run = not old and not a.force
    if first_run:
        print("  First run: recording the current taps as the starting point; Untappd left as is.")
    unmapped = [] if (a.no_untappd or first_run) else untappd_sync(changes, beers, meta, a.live)
    menu = render_menu(taps, beers, meta)
    print(f"  Menu: {menu}")
    printer = os.environ.get("MENU_PRINTER")
    if a.live and printer and menu.suffix == ".pdf":
        copies = os.environ.get("MENU_COPIES", "10")
        subprocess.run(["lp", "-d", printer, "-n", copies, str(menu)], check=False)
        print(f"  Sent {copies} copies to printer {printer}")

    new_beers = sorted({t["beer"] for t in changes if t["beer"] not in beers and t["beer"] != "*EMPTY"}
                       | {t["beer"] for _, t, _, _ in unmapped})
    if new_beers:
        print("  TO DO (manual):")
        for b in new_beers:
            print(f"   - '{b}': add to sync/beer-map.json; add its draft buttons in Toast; "
                  f"link them in Beer Saver > LINKING (buttons appear there within ~90 min)")
    if a.live or not old:
        STATE.write_text(json.dumps(taps, indent=1))


if __name__ == "__main__":
    main()
