"""Render the build guide to static HTML. pip install -r tools/requirements-docs.txt."""
from pathlib import Path
import html
import shutil
import markdown

root = Path(__file__).resolve().parent.parent
out = root / "dist"
out.mkdir(exist_ok=True)
css = """
:root{color-scheme:dark;--bg:#101619;--paper:#172023;--text:#e7e7dc;--muted:#aab6b0;--gold:#e0b875}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:17px/1.75 system-ui,sans-serif}
header{border-bottom:1px solid #ffffff20;padding:18px max(22px,calc((100vw - 1120px)/2))}
header a{margin-right:24px}main{max-width:1120px;margin:auto;padding:35px 24px 100px}
h1{font:normal clamp(36px,5vw,62px)/1.13 Georgia,serif;color:#f5eedf;margin:15px 0 30px}
h2{font:normal 30px/1.3 Georgia,serif;color:var(--gold);margin:65px 0 20px;scroll-margin-top:25px}
h3{font-size:21px;margin:32px 0 12px}p,li{max-width:90ch}a{color:var(--gold);text-underline-offset:3px}
table{border-collapse:collapse;min-width:590px;width:100%;font-size:14px;line-height:1.55}
.table-scroll{overflow-x:auto;margin:25px 0;border:1px solid #ffffff20;border-radius:8px}
th,td{padding:14px;text-align:left;vertical-align:top;border-bottom:1px solid #ffffff15}
th{background:#263033;color:#f0d4a2}tr:nth-child(even){background:#ffffff04}
blockquote{margin:25px 0;border-left:3px solid var(--gold);padding:12px 24px;background:var(--paper);color:#ccd5cd}
img{max-width:100%;height:auto;display:block;margin:30px auto;border-radius:12px}
code{font-size:.85em;background:#ffffff08;padding:2px 5px}pre{overflow-x:auto}.toc{background:var(--paper);padding:20px 28px;border:1px solid #ffffff12;border-radius:12px;font-size:14px}.toc>ul{list-style:none;padding:0}.toc ul ul{display:none}
footer{border-top:1px solid #ffffff20;margin-top:60px;padding-top:20px;color:var(--muted);font-size:13px}
@media(max-width:650px){body{font-size:16px}main{padding:25px 20px 60px}h2{font-size:26px}table{min-width:530px}}
@media print{:root{color-scheme:light}body{background:white;color:#171717;font-size:10pt}main{padding:0;max-width:none}header,.toc{display:none}a,h1,h2,h3{color:#111}a{text-decoration:none}h2{break-after:avoid;margin-top:25px}table{min-width:0;font-size:8pt}th,td{padding:5px;border-color:#bbb}th,blockquote,tr:nth-child(even){background:#eee;color:#111}img{max-height:350px;object-fit:contain}.table-scroll{overflow:visible;break-inside:avoid}footer{color:#333}}
"""
for source, target, title in [
    ("build-guide.md", "build-guide.html", "Travel Globe — Physical Build Guide"),
    ("hardware-sources.md", "hardware-sources.html", "Travel Globe — Hardware References"),
]:
    text = (root / "docs" / source).read_text()
    if source == "build-guide.md":
        text = text.replace("## 1.", "[TOC]\n\n## 1.", 1)
    rendered = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"toc_depth": "2-2"}})
    rendered = rendered.replace('href="prototype-kit.zip"', 'href="https://trentconley.github.io/globe/prototype-kit.zip"')
    rendered = rendered.replace("<table>", '<div class="table-scroll"><table>').replace("</table>", "</table></div>")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#101619"><title>{html.escape(title)}</title><style>{css}</style></head><body><header><a href="index.html">← Globe simulator</a><a href="build-guide.html">Build guide</a><a href="structure.html">3D structure</a><a href="https://trentconley.github.io/globe/prototype-kit.zip">Download package</a></header><main>{rendered}<footer>Travel Globe · Engineering design and prototype package · 25× terrain / 50-mile radius · Print this page to save a PDF.</footer></main></body></html>"""
    (out / target).write_text(page)
shutil.copytree(root / "docs/build-assets", out / "build-assets", dirs_exist_ok=True)
shutil.copytree(root / "artifacts/engineering", out / "engineering", dirs_exist_ok=True)
print("Built self-contained guide pages with local diagrams and engineering downloads.")
