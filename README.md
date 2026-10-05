# Travel Globe — Places, remembered.

A visual prototype for a **305 mm (12-inch) programmable travel globe**: charcoal raised terrain, warm gold **visited areas**, and dark places still to explore.

Each saved place contributes an approximate footprint, initially **50 miles in radius**. Nearby footprints merge. No connecting travel lines are drawn, and visiting a city never selects its entire country. The opening example highlights Vancouver while leaving distant Canada and South Dakota dark.

## Engineering prototype A0

Open the [actual CAD assembly](https://trentconley.github.io/globe/engineering.html), [engineering report](https://trentconley.github.io/globe/engineering-report.html), and [downloadable CAD/source package](https://trentconley.github.io/globe/engineering-package.zip).

This release adds a bolted cage, spine, spokes, shell panels, optical baffles, fitted prototype cradle, machining references, wiring/BOM schedules, persistent device software and engineering simulations. The ten-cell optical PCB is routed and reports zero DRC violations/unconnected items; its candidate LED still needs supplier and physical qualification.

**The full globe is not fabrication-ready.** Its six dense matrix board types remain incompletely routed, the south-polar coverage needs revision, and real optics, joint strength, temperatures, supplier fit and hardware operation have not been tested. The 3D assembly uses actual checked meshes; its materials do not predict measured light output. The $4,500 allocation is an unquoted budget ceiling.

Start with the [sample manufacturing plan](https://trentconley.github.io/globe/sample-plan.html), with separate printer/PCB quote packs and clear-versus-tinted controls. The previous [structural concept](https://trentconley.github.io/globe/structure.html) and [early test guide](https://trentconley.github.io/globe/build-guide.html) remain available as historical studies; their counts and mechanics are superseded by A0.

The current **sample A1** adds grid mounting clearance, 1–4.75 mm finish coupons and hardened bench firmware. Its [component/material review](https://trentconley.github.io/globe/sample-qualification.html) lists specific proposed resin/finish products and the unresolved LED/printer approvals. These are review packs, not confirmed supplier orders. The older full-globe A0 package is unchanged.

## Open and use

Open [the public simulator](https://trentconley.github.io/globe/) in a modern browser, or use `dist/globe.html` locally. The renderer, coastline, and elevation data are bundled into this self-contained file. Some phone file viewers block HTML; the local-server option below is an alternative.

- Add a place by latitude/longitude, or pick its coordinates with **Add on globe**.
- Adjust **Approximate visit radius** to balance recognition and physical display resolution.
- Try **Overlapping Bay Area visits** to see nearby footprints merge, or **Scattered western visits** to see gaps remain dark. These are illustrative examples, not claims about your travel history.
- **Keep highlights on land** clips the visual footprints to the simplified coastline. Turn it off to see the full footprint. This does not promise that the hardware can resolve every coastal edge.
- Use **Print section** to inspect a curved section of the full-size globe and export a shell STL in millimetres. The geography is fixed; changing your visited places changes the light, not the print.
- Compare the ideal coverage with **Show coarse 72-LED approximation** before buying hardware. The cheap test layout can enlarge, shift, or merge small areas.
- Export travel JSON as a backup. Browser storage retains visits locally; it is not the future controller's nonvolatile storage.

On a 305 mm globe, a 50-mile radius is **1.93 mm**, making one footprint about **3.85 mm across**. Zoom in to inspect small areas; the simulator does not artificially enlarge them in the ideal view.

## Build and run

With Node 20+:

```sh
cd /workspace/globe
npm ci
npm run build
npm test
```

Optional local server: `npm start` serves `dist` on port 4173. A phone on the same local network can use the computer's LAN address and port. This development server has no authentication; stop it when finished.

## Saved history

New exports use `{ "version": 2, "radiusMiles": 50, "visits": [{ "name": "Vancouver", "lat": 49.2827, "lon": -123.1207 }] }`.

The simulator accepts earlier version 1 travel files and retains their place coordinates, ignoring old connection flags. Existing personal browser history is migrated to a new storage key, while the original version 1 entry is preserved. The earlier illustrative route demo is replaced by the Vancouver example.

## What the preview and print represent

- Real simplified coastlines and **ETOPO-derived elevation**, showing major ranges with adjustable vertical exaggeration. The preview and STL use the same elevation field.
- Nominal diameter 305 mm before relief. Default 25× exaggeration raises the highest sampled terrain about 3.73 mm; the 40× setting reaches about 5.96 mm. Individual peaks are averaged by the coarse grid.
- Exported curved section: 36° × 36°, about 95 mm across, with at least a 1 mm radial base wall.
- Terrain stays fixed. There are no visit-specific grooves or engraved paths in the print.
- STL contains shape only, without color, lighting, tint, support structures, or printer settings. The simulator’s stand is illustrative; use the separate A0 CAD assembly for the engineered stand.

See [terrain data and scale](docs/elevation.md), [the physical prototype guide](docs/prototype.md), [design decisions](docs/design.md), and [validation record](docs/validation.md). The physical finish, lighting, electronics, and physical phone-to-controller operation remain to be tested.

Coastlines are public-domain [Natural Earth land data](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson); see [provenance](docs/sources.md). Rendering uses Three.js (MIT).


## Reproduce engineering work

Read [cloud/local setup](docs/cloud-setup.md). `tools/build-design.sh` regenerates mechanical geometry, geographic mappings, simulations and assembly assets. `--step` adds slow faceted cage STEP checks. Run `python3 tools/build-report.py` after generating screenshots to render the illustrated report. `tools/package-engineering.py` produces the release archives and checksum manifest.

`npm test` covers the appearance/terrain geometry. `python3 -m unittest discover -s tests -p 'test_firmware.py' -v` covers persistence, protocols and simulated controllers. [Pi installation](firmware/install/README.md) includes a desktop simulation and the proposed hardware provisioning flow.

Generated large CAD/build outputs are excluded from source Git; the public package contains the checked release artifacts. Full matrix candidates are explicitly held, and full-globe Gerbers are not supplied. Hardware/data license notices are in [third-party notices](docs/third-party/hardware-and-data.md).

To reproduce sample A1 after the saved A0 CAD is available: run `python3 cad/sample-readiness.py`, then `python3 tools/check-sample-fit.py`. The latter exports the revised sample viewer mesh and checks both shells against the actual passive-board placement. Run `python3 tools/check-bench-runtime.py --micropython /path/to/micropython` using MicroPython v1.26.0 Unix; the GPIO/timing are mocked. See `engineering/release/sample-*-checks.json` for hashes, assumptions and results. Generate the review packs with `python3 tools/prepare-sample-order.py`, render their combined PDF with `node tools/render-sample-plan.cjs`, then run the pack script again to include the current PDF. Copy `artifacts/assembly/prototype.glb` into `dist/assembly/` after a general A0 assembly build, which otherwise restores the old prototype viewer mesh.
