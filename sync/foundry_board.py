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


def _panel_css(a, w, h, logo_h=118):
    return f"""@font-face{{font-family:Panel;src:url('{a}/ShareTechMono-Regular.ttf')}}
.panel{{width:{w}px;height:{h}px;background:url('{a}/beer-panel-bg.jpg') center/cover;box-sizing:border-box;padding:6px 10px 10px;
 display:flex;flex-direction:column;align-items:center;font-family:Panel,monospace;color:#161616;overflow:hidden;
 -webkit-text-stroke:1.3px #161616;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.logo{{height:{logo_h}px;margin-top:4px}}
.ontap{{font-size:{round(logo_h*.34)}px;letter-spacing:1px;line-height:1;margin-top:2px}}
.rule{{width:{round(w*.35)}px;border-top:3px solid #161616;margin:8px 0 10px}}
.ln{{white-space:nowrap;text-align:center;line-height:1.08;font-size:var(--fs);letter-spacing:.5px}}
.grp{{display:flex;flex-direction:column;align-items:center}}
.other .ln{{font-size:calc(var(--fs)*.9)}}
.sub{{font-size:calc(var(--fs)*.45);text-decoration:underline;margin:6px 0 4px;letter-spacing:1px}}
.tax{{margin-top:auto;font-size:calc(var(--fs)*.78);padding-top:6px}}"""


_FIT = """<script>/* biggest text that fits the panel; squeeze any line that is still too wide */
function fit(){var p=document.getElementById('p'),s=200;
function fits(){return p.scrollHeight<=p.clientHeight}
p.style.setProperty('--fs',s+'px');while(!fits()&&s>12){s-=1;p.style.setProperty('--fs',s+'px')}
document.querySelectorAll('.ln').forEach(function(l){var w=p.clientWidth-20;
 if(l.scrollWidth>w){l.style.transform='scaleX('+(w/l.scrollWidth)+')'}});window.scrollTo(0,0)}
document.fonts.ready.then(fit);</script>"""


def _panel(a, sections):
    house, guest, other = sections.get("house", []), sections.get("guest", []), sections.get("other", [])
    body = f"<div class='grp house'>{_lines(house)}</div>"
    if guest:
        body += f"<div class=sub>GUEST TAPS</div><div class='grp guest'>{_lines(guest)}</div>"
    if other:
        body += f"<div class=rule></div><div class='grp other'>{_lines(other)}</div>"
    return (f"<div class=panel id=p><img class=logo src='{a}/fo-logo.png'><div class=ontap>ON TAP</div><div class=rule></div>"
            f"<div style='display:flex;flex-direction:column;align-items:center;width:100%'>{body}</div>"
            f"<div class=tax>TAX INCLUDED</div></div>")


def board_html(sections, scale=1.0, page_css=""):
    """The whole 1920x1080 screen. scale/page_css let the same layout print on 11x17."""
    a = ASSETS.as_uri()
    p = PANEL
    return f"""<!doctype html><meta charset=utf-8><style>{_panel_css(a, p['width'], p['height'])}
{page_css}html,body{{margin:0;background:#fff}}
.board{{position:relative;width:1920px;height:1080px;transform:scale({scale});transform-origin:0 0}}
.bg{{position:absolute;left:0;top:0;width:1920px;height:1080px}}
.board .panel{{position:absolute;left:{p['left']}px;top:{p['top']}px}}</style>
<div style="width:{1920*scale:.0f}px;height:{1080*scale:.0f}px;overflow:hidden">
<div class=board><img class=bg src='{a}/template.jpg'>{_panel(a, sections)}</div></div>{_FIT}"""


def tent_html(sections):
    """Letter portrait table tent: just the orange ON TAP panel with a white border."""
    a = ASSETS.as_uri()
    w, h = 744, 984  # 7.75in x 10.25in at 96 px/in, inside 0.375in margins
    return f"""<!doctype html><meta charset=utf-8><style>{_panel_css(a, w, h, logo_h=190)}
@page{{size:8.5in 11in;margin:.375in}}html,body{{margin:0}}</style>{_panel(a, sections)}{_FIT}"""


def poster_html(sections):
    """11x17 landscape: the full board, scaled to the sheet (16.5in wide inside 0.25in margins)."""
    scale = 16.5 * 96 / 1920
    top = (10.5 * 96 - 1080 * scale) / 2
    return board_html(sections, scale, f"@page{{size:17in 11in;margin:.25in}}body{{padding-top:{top:.0f}px}}")


def _chrome(args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                           "--virtual-time-budget=5000"] + args, capture_output=True)


def render_prints(sections, out_dir):
    """Write foundry-tent.pdf (letter) and foundry-11x17.pdf (tabloid landscape). Returns (tent, poster) paths or None."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for name, page in (("foundry-tent", tent_html(sections)), ("foundry-11x17", poster_html(sections))):
        src, pdf = out_dir / f"{name}.html", out_dir / f"{name}.pdf"
        src.write_text(page)
        pdf.unlink(missing_ok=True)
        if Path(CHROME).exists():
            _chrome(["--no-pdf-header-footer", f"--print-to-pdf={pdf}", src.as_uri()])
        made.append(pdf if pdf.exists() else None)
    return tuple(made)


def render_board(sections, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    page, png = out_dir / "foundry-board.html", out_dir / "foundry-board.png"
    page.write_text(board_html(sections))
    png.unlink(missing_ok=True)
    if Path(CHROME).exists():
        _chrome(["--window-size=1920,1080", f"--screenshot={png}", page.as_uri()])
    return png if png.exists() else None


if __name__ == "__main__":
    sample = {"house": [("Waynesbeero", "8"), ("6th Lord IPA", "9"), ("Baby Bask", "9")],
              "guest": [("Alewerks-Brown", "8.50"), ("Falcon Smash", "10")],
              "other": [("Bold Rock", "10"), ("Potter's Cider", "10"), ("Red or White Wine", "10"), ("White Claw", "10")]}
    print(render_board(sample, HERE / "Foundry Board"))
