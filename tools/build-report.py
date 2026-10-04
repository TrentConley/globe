"""Render the current engineering report, figures and downloadable check records."""
from pathlib import Path
import markdown,shutil,html,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dist';ASSET=OUT/'engineering-assets';ASSET.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'docs/engineering-assets').glob('*'):shutil.copy2(p,ASSET/p.name)
for p in (ROOT/'artifacts').glob('engineering-*.png'):shutil.copy2(p,ASSET/p.name)
for p in (ROOT/'engineering/release').glob('*.png'):shutil.copy2(p,ASSET/p.name)
checks=OUT/'engineering-checks';checks.mkdir(exist_ok=True)
for p in (ROOT/'engineering/release').iterdir():
 if p.suffix in ('.csv','.json'):shutil.copy2(p,checks/p.name)
shutil.copy2(ROOT/'electronics/bench-release/board-front.svg',ASSET/'bench-board-front.svg')
text=(ROOT/'docs/engineering-report.md').read_text();text=text.replace('## What exists','[TOC]\n\n## What exists',1)
text+='''\n\n## Direct downloads and inspection records

- [Complete CAD, sources, firmware, test board and schedules](engineering-package.zip)
- [Small optical prototype only](optical-prototype-A0.zip)
- [Printable engineering report](engineering-report.pdf)
- [Machine-readable release status](engineering-checks/release-status.json)
- [Parts and processes](engineering-checks/parts-manifest.csv)
- [Electronics and hardware BOM](engineering-checks/electronics-and-hardware-bom.csv)
- [Metal cut list](engineering-checks/metal-cut-list.csv)
- [Acceptance worksheet](engineering-checks/acceptance-worksheet.csv)
- [Matrix-board routing hold](engineering-checks/matrix-routing-hold.json)
- [Assembly intersection audit](engineering-checks/assembly-intersections.json)
- [Mechanical simulation outputs](engineering-checks/structural-analysis.json)
- [Thermal simulation outputs](engineering-checks/thermal-analysis.json)
- [Download checksums](engineering-downloads.json)

Optional large faceted STEP boundaries are separate from the main package. The checked STLs and parametric source are the primary cage definition. **Octant 04 failed STEP round-trip validation and is not supplied as STEP.**

'''
for i in [1,2,3,5,6,7,8]:text+=f'- [Cage octant {i:02} — checked faceted STEP ZIP](cad-step/cage-octant-{i:02}.step.zip)\n'
rendered=markdown.markdown(text,extensions=['tables','fenced_code','toc'],extension_configs={'toc':{'toc_depth':'2-2'}}).replace('<table>','<div class="table-scroll"><table>').replace('</table>','</table></div>')
css='''*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#111719;color:#e5e6dc;font:16px/1.8 system-ui,sans-serif}header{padding:18px 28px;border-bottom:1px solid #ffffff22;display:flex;gap:25px;flex-wrap:wrap}main{max-width:1130px;padding:28px 30px 100px;margin:auto}a{color:#e8bd77;text-underline-offset:3px}h1{font:normal clamp(36px,5vw,60px)/1.15 Georgia,serif;max-width:950px;margin:20px 0 30px}h2{font:normal 30px/1.3 Georgia,serif;color:#e8bd77;margin:65px 0 20px;scroll-margin-top:20px}h3{margin-top:30px}img{display:block;max-width:100%;height:auto;margin:30px auto;border-radius:10px}.table-scroll{overflow-x:auto;border:1px solid #ffffff22;border-radius:8px;margin:25px 0}table{border-collapse:collapse;width:100%;min-width:590px;font-size:14px;line-height:1.6}th,td{text-align:left;vertical-align:top;padding:13px;border-bottom:1px solid #ffffff1a}th{background:#273133;color:#efd3a4}tr:nth-child(even){background:#ffffff03}code{font-size:.88em;background:#ffffff0b;padding:2px 4px;overflow-wrap:anywhere}pre{overflow-x:auto}.toc{background:#1b2427;border:1px solid #ffffff15;border-radius:10px;padding:10px 28px}.toc ul{padding-left:20px}.toc a{color:#c7d0c7}li{margin:8px 0}strong{color:#f3e9d8}footer{margin-top:60px;color:#acb7b1;border-top:1px solid #ffffff22;padding-top:20px;font-size:13px}@media(max-width:600px){main{padding:24px 18px 70px}h2{font-size:26px}header{gap:16px;padding:16px 18px}body{font-size:15px}}@page{size:A4;margin:15mm}@media print{html{color-scheme:light}body{background:white;color:#171717;font-size:9.5pt;line-height:1.55}main{max-width:none;padding:0}header,.toc{display:none}a,h1,h2,h3,strong{color:#171717}h1{font-size:28pt}h2{font-size:18pt;margin-top:28px;break-after:avoid}p,li{orphans:3;widows:3}img{max-height:240mm;object-fit:contain;break-inside:avoid}table{min-width:0;font-size:8pt}th,td{padding:5px;border-color:#bbb}th,tr:nth-child(even){background:#eee;color:#111}.table-scroll{overflow:visible;border-color:#bbb}tr{break-inside:avoid}footer{color:#555}a{text-decoration:none}code{background:#eee}}'''
page=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Travel Globe — Engineering prototype A0</title><style>{css}</style></head><body><header><a href="index.html">Travel simulator</a><a href="engineering.html">Actual CAD assembly</a><a href="engineering-package.zip">CAD and source package</a><a href="engineering-report.pdf">PDF</a></header><main>{rendered}<footer>A0 engineering prototype · 305 mm · 25× terrain · 50-mile footprints · No physical fabrication or testing performed.</footer></main></body></html>'
(OUT/'engineering-report.html').write_text(page)
# Earlier references remain available, with their superseded status visible before instructions.
for name in ['build-guide.html','hardware-sources.html']:
 p=OUT/name
 if p.exists():
  s=p.read_text();banner='<aside data-a0-notice style="padding:20px;background:#4b3922;color:#fff">Earlier study: counts and mechanics are superseded by <a style="color:#ffe0a6" href="engineering-report.html">Engineering prototype A0</a>. Use its actual CAD and qualification plan for the current design.</aside>'
  if 'data-a0-notice' not in s:p.write_text(s.replace('<body>','<body>'+banner,1))
print('Built illustrated engineering report and inspection downloads')
