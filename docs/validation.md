# Validation record — 2026-10-03

## Executed for the 25× physical-build design revision

- `npm run build`: generated a self-contained simulator with embedded land and elevation data, plus renderer and elevation-distribution licenses.
- `npm test`: **16 tests passed**, none skipped. They cover scale, spherical footprints, Vancouver versus distant Canada and South Dakota, unvisited gaps, overlap without added brightness, order independence, date-line/pole behavior, soft edges, old-history migration, valid/invalid imports, closed printable geometry, and minimum wall thickness. Additional terrain checks compare eight independently sampled source locations, date-line/pole continuity, real elevation-to-millimetre scale, linear exaggeration, smooth oceans, and the exported shell height.
- `node tools/browser-smoke.cjs`: **41 checks passed** in Chromium. The rendered Vancouver example lights Vancouver while Montreal, Edmonton, and South Dakota remain unlit. Tests also exercise land clipping, merged Bay Area visits, separated western visits, globe picking, saved history and radius after reload, older JSON imports, browser-history migration without deleting the original entry, the 390 px phone layout, and exports. Terrain checks cover actual data, default physical height, persistence of a flat setting, and migration from the old texture control. Returning visitors receive the stronger default once, while custom heights and their travel history remain intact. No runtime errors or external service requests were observed.
- Desktop and phone screenshots were visually inspected for visible mountain relief under the new side lighting.
- The actual downloaded shell was byte-for-byte identical after adding a distant visit and after increasing footprint radius. Visited history changes lighting, not printable geography.
- Both current example STLs were independently parsed. Every geometric edge belongs to exactly two faces with opposite direction. Both volumes are positive; each file contains 84,096 triangles.

## Current example export measurements

The example shell uses the Vancouver section centered at **49.2827° N, 123.1207° W**, real ETOPO-derived elevations with 25× vertical exaggeration, and a nominal 305 mm globe. The example travel JSON stores Vancouver with a 50-mile radius. Measurements below are bounding-box extents, not surface arc lengths.

| Download | Width × height × depth, mm | Closed volume, mm³ |
| --- | --- | ---: |
| Light-only shell | 94.345 × 94.800 × 16.570 | 11,970.781 |
| LED carrier | 89.368 × 89.368 × 15.255 | 12,847.867 |

The carrier has smaller physical bounds because it follows an inner concentric sphere with the same angular span. Do not scale it to match the shell's bounding box. The current kit includes these two prints; it does not include the superseded engraved-route example.

## Repeating the browser checks

The cloud runtime supplied Playwright 1.62.1 and Chromium. The optional test script requires Playwright to be resolvable by Node and a compatible Chromium binary. If using another machine, install Playwright in your development environment and set `GLOBE_CHROMIUM` to its browser executable if it differs from `/usr/bin/chromium`.

Serve the generated `dist` directory, then run:

```sh
node tools/browser-smoke.cjs
```

It defaults to `http://127.0.0.1:4173/globe.html`; override `GLOBE_TEST_URL` when needed. Screenshots and downloaded test files go under `artifacts/` and contain demonstration data only.

The managed Chromium installation blocks `file://` navigation, so browser automation used a local HTTP server. The standalone file is bundled to open directly in ordinary browsers, but direct file opening was not validated in this managed browser. Phone file viewers may need the local-server option described in the README.

## Not yet established

No physical part has been printed, no LED hardware has been assembled or flashed, and no finish has been tested. Mesh closure and radial wall calculations do not certify a printer, support orientation, minimum wall for a specific material, mechanical strength, heat behavior, or optical transmission. The coarse LED display is illustrative, not measured diffusion. The device's power-loss retention and phone-to-controller updates await the electronics prototype.


## Physical-design package checks

- Seven new optical test STLs were generated: four thickness slabs, a smooth curved shell, a Vancouver shell and a Himalayan shell. Their geometry has positive volume and closed, consistently oriented edges. Curved samples use 21,312 triangles each; the slabs use 12 each.
- The independent scale calculations give a 3.852215 mm footprint diameter and 3.727520 mm maximum grid relief at 25×. The JSON contains dimensions, volumes, pitch estimates and power scenarios with their assumptions.
- The area-sampled reference-board pattern has exactly 117 distinct valid cells with finite coverage values in [0, 1].
- The guide passed 26 browser checks covering all 13 sections, navigation targets, local downloads including the 18-page PDF, diagram loading and phone layout. Its desktop/phone screenshots were inspected.
- The optical-bench Python utility passed syntax compilation only. It has not run on a controller; no hardware or optical claims follow from that check.
- The prototype board schematic was inspected for signal pull-up voltage and its PCB for actual matrix pitch and board outline. Current datasheet limits and supplied hardware revisions remain release checks.

The complete globe does not yet have released production CAD, PCB layouts or device firmware. The guide specifies the prototype stages required to establish them.


## Structural viewer checks

The structural concept adds cutaway, assembled, exploded, frame and prototype views. Nineteen Chromium checks passed for geometry settings, view/layer controls, spacing, image export, phone layout, runtime errors and preserving existing travel storage. Desktop cutaway/assembled/exploded/prototype images and the phone cutaway were visually inspected. The existing sixteen geography/print-geometry tests also passed. Six south-pole carrier facets are omitted for the support spine. These checks establish visualization behavior, not physical assembly fit, optical performance or strength.
