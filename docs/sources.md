# Data and dependency provenance

## Land outlines

- Natural Earth vector data, 1:110m land GeoJSON, downloaded 2026-10-03.
- Source: https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson
- Local file: `preview/data/land.geojson`
- SHA-256: `9e0729ee253ca7d7a5c4ae9395fb1902264c5377c52e224d13dd85010e2835d9`
- Natural Earth data is public domain: https://www.naturalearthdata.com/about/terms-of-use/
- This dataset supplies simplified land outlines only. It does not provide elevation, roads, actual travel paths, or comprehensive small islands.

The source URL follows an upstream branch; the vendored file and checksum record the actual data used. No geography requests are made when the simulator opens.

## Elevation

The bundled 1,080 × 540 grid comes from the ETOPO 20-arc-minute sample in Matplotlib Basemap at pinned revision `912b90bdf9245a84db5e523fef57b491b4b958e1`. See [the elevation record](elevation.md) for source URLs, SHA-256 checksums, resampling, physical scale, and limitations. The upstream [MIT license](elevation-data-license.md) is bundled in the HTML and prototype kit.

## Software

Three.js 0.180.0 (MIT) and esbuild 0.25.10 (MIT) are pinned in `package.json` and `package-lock.json`. Bundled license comments are retained in the standalone HTML. See their package license files for the complete notices.

No account, geocoder, API key, third-party font service, map tile service, or network connection is required by the generated simulator.

## Hardware assumptions

The prototype guide specifies a generic strip class and required dimensions. No manufacturer part has been independently confirmed or selected. Manufacturer pages attempted during design were unavailable through the environment's network policy; dimensions and current ratings must be verified with the actual supplier before purchasing.
