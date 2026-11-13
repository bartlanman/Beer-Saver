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
    prev = {t["meter"]: t for t in old}
    return [t for t in new if t["meter"] not in prev
            or (prev[t["meter"]]["beer"], prev[t["meter"]]["connect"]) != (t["beer"], t["connect"])]


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
            item = http("POST", f"{UT_API}/sections/{sec}/items", email, token,
                        {"untappd_id": want["untappd_id"]})["item"]
            http("PUT", f"{UT_API}/items/{item['id']}", email, token,
                 {"tap_number": t["tap"], "name": want.get("menu_name") or item.get("name")})
            for size, price in (want.get("prices") or meta["default_prices"]).items():
                http("POST", f"{UT_API}/items/{item['id']}/containers", email, token,
                     {"container_size_name": size, "price": price})
    return [x for x in todo if x[0] == "unmapped"]


def render_menu(taps, beers):
    OUT.mkdir(parents=True, exist_ok=True)
    rows_by_bar = {}
    for t in sorted(taps, key=lambda x: (x["bar"], x["tap"].startswith("DB"), x["tap"].zfill(5))):
        if t["beer"] == "*EMPTY":
            continue
        b = beers.get(t["beer"], {})
        p = (b.get("prices") or {}).get("16oz", "")
        rows_by_bar.setdefault(t["bar"], []).append(
            f"<tr><td class=n>{html.escape(t['tap'])}</td><td><b>{html.escape(b.get('menu_name') or t['beer'])}</b>"
            f"<div class=s>{html.escape(b.get('brewery', ''))}{' · ' + b['abv'] + '%' if b.get('abv') else ''}</div></td>"
            f"<td class=p>{'$' + p if p else ''}</td></tr>")
    stamp = datetime.datetime.now().strftime("%a %b %-d, %-I:%M %p")
    body = "".join(f"<h2>{html.escape(bar.split(' ', 1)[-1])}</h2><table>{''.join(r)}</table>"
                   for bar, r in rows_by_bar.items())
    page = f"""<!doctype html><meta charset=utf-8><title>On Tap</title><style>
@page{{size:letter;margin:.5in}}body{{font-family:Georgia,serif;color:#111}}h1{{text-align:center;margin:0}}
.d{{text-align:center;font-size:10pt;color:#555;margin-bottom:12pt}}h2{{border-bottom:2px solid #111;font-size:15pt;margin:14pt 0 4pt}}
table{{width:100%;border-collapse:collapse}}td{{padding:5pt 4pt;border-bottom:1px solid #ddd;font-size:13pt;vertical-align:top}}
.n{{width:42pt;color:#555}}.p{{text-align:right;width:60pt}}.s{{font-size:10pt;color:#555}}</style>
<h1>Basic City Beer Co. · On Tap</h1><div class=d>Updated {stamp}</div>{body}"""
    html_path = OUT / "tap-menu.html"
    html_path.write_text(page)
    pdf_path = OUT / "tap-menu.pdf"
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
        return
    for t in changes:
        print(f"  {t['bar']} {t['tap']:5} {t['beer']}  (changed {t['connect']}, {t['pct']}% left)")

    unmapped = [] if a.no_untappd else untappd_sync(changes, beers, meta, a.live)
    menu = render_menu(taps, beers)
    print(f"  Menu: {menu}")
    printer = os.environ.get("MENU_PRINTER")
    if a.live and printer and menu.suffix == ".pdf":
        subprocess.run(["lp", "-d", printer, str(menu)], check=False)
        print(f"  Sent to printer {printer}")

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
