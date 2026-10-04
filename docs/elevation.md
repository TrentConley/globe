# Real elevation for the preview and print

The globe uses an ETOPO-derived **20-arc-minute elevation grid** distributed with Matplotlib Basemap. Major ranges are geographic features rather than procedural noise. The same sampler drives the globe's raised geometry and the curved STL shell. Oceans remain at the nominal sphere radius; below-sea-level elevations are flattened to preserve the base wall.

## Physical scale

For a 305 mm globe, one metre of Earth elevation becomes `152.5 / 6371008.8` millimetres. At literal scale, Everest's 8,849 m height would be about **0.212 mm**. The default **25× vertical exaggeration** makes the terrain more legible; the slider allows 0× (smooth sphere) through 40×.

This coarse grid's highest sample is **6,229 m**, giving about **3.728 mm** of relief at 25× or 5.964 mm at 40×. It averages away individual summits and must not be described as reproducing Everest's peak. Resolution is roughly 37 km at the equator, equivalent to 0.89 mm on the globe. It is appropriate for a first shape study of mountain ranges, not fine local topography.

The world preview samples geometry at 0.5°; the 36° printable section uses a finer 0.25° local mesh. Both interpolate the same elevation grid, so no additional detail is invented. Simplified Natural Earth land boundaries mask the elevation; small islands and coastal detail are limited. The material's color has a slight height-dependent variation, and surface lighting comes from the displaced geometry's normals. A directional light to the upper left of the camera reveals ridges and valleys, with a restrained fill light keeping the shadow side visible. The lights follow camera orientation, so zoom and orbit do not turn the key light into a flat frontal light.

The base shell is 1 mm thick radially; terrain adds to that thickness. Raised areas can transmit less light, which is one reason to test a curved sample before building the complete globe. The screen does not simulate measured resin transmission or coating behavior.

## Reproducible source

Pinned repository revision: [`matplotlib/basemap@912b90bdf9245a84db5e523fef57b491b4b958e1`](https://github.com/matplotlib/basemap/tree/912b90bdf9245a84db5e523fef57b491b4b958e1/doc/examples).

The repository's `doc/examples/plotmap.py` identifies the sample as ETOPO bathymetry/topography. Its exact original ETOPO edition is not specified there; we do not label it ETOPO1 or a current high-resolution DEM.

Source files under `doc/examples/`, with SHA-256:

| File | SHA-256 |
| --- | --- |
| `etopo20data.gz` | `bd6549bb0a675d2978d1dee1609fc4cec7e4d74b98d4fe49c0e8a2e8c8f3b8ce` |
| `etopo20lons.gz` | `95109988351bed186a886c6dd2a607455939013dfc49f7b7c61997d3389802b7` |
| `etopo20lats.gz` | `3201109f72a8371d1fee6396292618c9b05cae0a55abf8b2117bb2ef1f7e97ce` |

Run `python3 tools/prepare-elevation.py` with NumPy installed to regenerate `preview/data/elevation-grid.js`. It verifies source hashes and coordinates, removes the repeated cyclic column, sorts longitudes west to east, reverses rows north to south, and rounds samples to signed 16-bit metres (at most 0.5 m quantization error). The resulting grid is 1,080 × 540 samples at cell centers. Its decoded little-endian binary SHA-256 is `f6adfe45277d668c278dc8a4431bca6484c17565df89bd98095d694b5b37e9f3`.

Runtime sampling uses bilinear interpolation, wraps at the date line, and converges to a common elevation at each pole. Normal builds use the bundled grid and require no data downloads. The upstream [MIT notice](elevation-data-license.md) is retained in the kit and standalone HTML.

Earlier default settings of 4×, 12× and the former 24× maximum upgrade once to the chosen 25× design setting. Other saved terrain heights are retained, including an explicitly flat surface. After migration, any new height choice persists without being upgraded again. Saved destinations, radius, and brightness remain intact.
