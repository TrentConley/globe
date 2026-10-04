"""Package the current simulator and explicitly selected example outputs."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parent.parent
quick_start = """# Travel Globe — physical build design

Open build-guide.html for the complete design, prototype wiring, material tests, fabrication request, costs and acceptance criteria. Open index.html (or globe.html) for the simulator. Open structure.html for the interactive structural design study: cutaway, assembled, exploded, frame and small-prototype views. The design target is 25× terrain and a 50-mile visited-area radius.

Start with the small engineering/ print samples and the identified dense matrix. Read the guide before purchasing or requesting a print. The older coarse strip carrier under examples/ is retained only as a legacy geometry study; it is not the dense-matrix mounting design.

engineering/ contains flat thickness coupons, smooth/Vancouver/Himalayan curved shells, a prototype BOM, optical test log, geographic test pattern and reproducible scale calculations. STL units are millimetres. Samples require print-service material/support review.

firmware/optical-bench/ contains an untested low-current CircuitPython pattern utility and setup instructions. It does not implement the finished globe's Wi-Fi/persistence firmware.

project-source/ preserves the simulator, generators, tests, guide source and pinned dependencies for future maintenance.\n\nThe full approximately 95 mm example shell uses Vancouver at 25× with a 1 mm radial base wall. Adding visited places changes light, not the printed geography. Export your travel JSON to keep a backup.

Geometry and browser software have been checked. Physical printing, finish, optics, custom circuits, firmware, wiring and thermal behavior still require the staged validation in the guide. This package is not a released full-globe manufacturing design.
"""
outputs = [
    (root / "dist/globe.html", "globe.html"),
    (root / "dist/index.html", "index.html"),
    (root / "dist/structure.html", "structure.html"),
    (root / "dist/build-guide.html", "build-guide.html"),
    (root / "dist/build-guide.pdf", "build-guide.pdf"),
    (root / "dist/hardware-sources.html", "hardware-sources.html"),
    *((p, "build-assets/" + p.name) for p in sorted((root / "docs/build-assets").glob("*")) if p.is_file()),
    *((p, "engineering/" + p.name) for p in sorted((root / "artifacts/engineering").glob("*")) if p.is_file()),
    *((p, "firmware/optical-bench/" + p.name) for p in sorted((root / "firmware/optical-bench").glob("*")) if p.is_file()),
    (root / "artifacts/engineering/vancouver-13x9-test-pattern.json", "firmware/optical-bench/vancouver-13x9-test-pattern.json"),
    *((p, "docs/" + p.name) for p in sorted((root / "docs").glob("*.md"))),
    *((root / "artifacts" / name, "examples/" + name) for name in (
        "example-light-only-shell-mm.stl", "example-led-carrier-mm.stl", "example-travels.json")),
    *((root / "artifacts" / name, "previews/" + name) for name in (
        "globe-desktop.png", "curved-section.png", "scattered-visits.png", "globe-mobile.png",
        "structure-cutaway.png", "structure-exploded.png", "structure-prototype.png")),
]
# Explicit source allowlist: excludes credentials, worktree metadata, local histories and dependencies.
outputs.extend((root / name, "project-source/" + name) for name in ("README.md", "package.json", "package-lock.json"))
for folder, suffixes in (
    ("preview", {".js", ".html", ".css", ".geojson"}),
    ("tools", {".py", ".mjs", ".cjs", ".txt"}),
    ("tests", {".mjs"}),
    ("docs", {".md", ".svg", ".png"}),
    ("engineering", {".csv"}),
    ("firmware", {".py", ".md"}),
):
    outputs.extend((p, "project-source/" + str(p.relative_to(root))) for p in sorted((root / folder).rglob("*")) if p.is_file() and p.suffix in suffixes)
for source, _ in outputs:
    if not source.is_file():
        raise SystemExit(f"Missing current example output: {source}")
target = root / "artifacts/globe-prototype-kit.zip"
with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
    archive.writestr("QUICK_START.md", quick_start)
    for source, destination in outputs:
        archive.write(source, destination)
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    print(f"Verified {len(archive.namelist())} files in {target.name}, {target.stat().st_size / 1024**2:.2f} MiB")
