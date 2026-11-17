#!/usr/bin/env python3
"""
Foundry bar screen: the blank Foundry template with the orange "ON TAP" beer panel
in the center, rendered to a 1920x1080 PNG for OptiSigns.

    render_board(sections, out_dir) -> Path to foundry-board.png

sections = {"house": [(name, price)], "guest": [...], "other": [...]}
Prices are strings like "9.00" (Foundry prices include tax).

Run on its own for a sample:  python3 foundry_board.py
"""
import html, os, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "foundry"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# Center panel position on the 1920x1080 template (matches the old static image).
PANEL = {"left": 648, "top": 208, "width": 570, "height": 787}


def _price(p):
    try:
        return f"${float(p):.2f}"
    except (TypeError, ValueError):
        return ""


def _lines(items):
    return "".join(f"<div class=ln><span>{html.escape(n.upper())}</span> <span>{_price(p)}</span></div>"
                   for n, p in items)


def board_html(sections):
    a = ASSETS.as_uri()
    house, guest, other = sections.get("house", []), sections.get("guest", []), sections.get("other", [])
    body = f"<div class='grp house'>{_lines(house)}</div>"
    if guest:
        body += f"<div class=sub>GUEST TAPS</div><div class='grp guest'>{_lines(guest)}</div>"
    if other:
        body += f"<div class=rule></div><div class='grp other'>{_lines(other)}</div>"
    p = PANEL
    return f"""<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:Panel;src:url('{a}/ShareTechMono-Regular.ttf')}}
html,body{{margin:0;width:1920px;height:1080px;background:#fff}}.bg{{position:absolute;left:0;top:0;width:1920px;height:1080px}}
.panel{{position:absolute;left:{p['left']}px;top:{p['top']}px;width:{p['width']}px;height:{p['height']}px;
 background:url('{a}/beer-panel-bg.jpg') center/cover;box-sizing:border-box;padding:6px 10px 10px;
 display:flex;flex-direction:column;align-items:center;font-family:Panel,monospace;color:#161616;overflow:hidden;-webkit-text-stroke:1.3px #161616}}
.logo{{height:118px;margin-top:4px}}
.ontap{{font-size:40px;letter-spacing:1px;line-height:1;margin-top:2px}}
.rule{{width:200px;border-top:3px solid #161616;margin:8px 0 10px}}
.ln{{white-space:nowrap;text-align:center;line-height:1.08;font-size:var(--fs);letter-spacing:.5px}}
.grp{{display:flex;flex-direction:column;align-items:center}}
.house .ln{{font-size:var(--fs)}}.other .ln{{font-size:calc(var(--fs)*.9)}}
.sub{{font-size:calc(var(--fs)*.45);text-decoration:underline;margin:6px 0 4px;letter-spacing:1px}}
.tax{{margin-top:auto;font-size:calc(var(--fs)*.78);padding-top:6px}}
</style>
<img class=bg src='{a}/template.jpg'><div class=panel id=p><img class=logo src='{a}/fo-logo.png'><div class=ontap>ON TAP</div><div class=rule></div>
<div id=c style="display:flex;flex-direction:column;align-items:center;width:100%">{body}</div><div class=tax>TAX INCLUDED</div></div>
<script>/* biggest text that fits the panel; squeeze any line that is still too wide */
function fit(){{var p=document.getElementById('p'),s=58;
function fits(){{return p.scrollHeight<=p.clientHeight}}
p.style.setProperty('--fs',s+'px');while(!fits()&&s>18){{s-=1;p.style.setProperty('--fs',s+'px')}}
document.querySelectorAll('.ln').forEach(function(l){{var w=p.clientWidth-20;
 if(l.scrollWidth>w){{l.style.transform='scaleX('+(w/l.scrollWidth)+')'}}}});
p.scrollTop=0;document.documentElement.scrollTop=0;window.scrollTo(0,0)}}
document.fonts.ready.then(fit);</script>"""


def render_board(sections, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    page, png = out_dir / "foundry-board.html", out_dir / "foundry-board.png"
    page.write_text(board_html(sections))
    png.unlink(missing_ok=True)
    if Path(CHROME).exists():
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--window-size=1920,1080", "--virtual-time-budget=5000", f"--screenshot={png}",
                        page.as_uri()], capture_output=True)
    return png if png.exists() else None


if __name__ == "__main__":
    sample = {"house": [("Waynesbeero", "8"), ("6th Lord IPA", "9"), ("Baby Bask", "9")],
              "guest": [("Alewerks-Brown", "8.50"), ("Falcon Smash", "10")],
              "other": [("Bold Rock", "10"), ("Potter's Cider", "10"), ("Red or White Wine", "10"), ("White Claw", "10")]}
    print(render_board(sample, HERE / "Foundry Board"))
