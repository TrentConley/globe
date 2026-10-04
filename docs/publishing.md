# Public simulator

- Simulator: https://trentconley.github.io/globe/
- Prototype kit: https://trentconley.github.io/globe/prototype-kit.zip
- Published files: https://github.com/TrentConley/globe/tree/gh-pages
- Initial successful deployment: https://github.com/TrentConley/globe/actions/runs/37145966955
- Initial published commit: dea5dc6 (gh-pages)
- Real-elevation update: cee0d24 (gh-pages)
- Terrain update deployment: https://github.com/TrentConley/globe/actions/runs/37147437199 (completed successfully)

GitHub Pages automatically published the initial gh-pages branch. The successful deployment and site URL were confirmed from GitHub's workflow run. The public raw index.html was fetched and matched dist/index.html byte for byte. Direct access to the github.io domain was blocked by this workspace's network policy, so a post-deployment browser smoke test against the live domain was not completed here.

The static public site contains the simulator, design viewers, engineering reports and downloadable packages. Travel edits remain in each visitor's browser; there is no server-side history synchronization or hardware connection. Browser storage on the public site's origin is separate from any earlier local-file or development-server history; JSON export/import can transfer visits.

## Updating the public site

Rebuild the simulator and regenerate the kit after the relevant tests. Fetch the current gh-pages branch from the repository before updating it. Replace index.html with dist/index.html and prototype-kit.zip with artifacts/globe-prototype-kit.zip. Retain .nojekyll, commit, and push normally without force. Check the Pages deployment result before announcing an update. The gh-pages branch contains built distribution files; source development is preserved separately from the built site.

The real-elevation update passed 16 geometry/data tests and 38 browser checks locally. The public raw index at cee0d24 exactly matched the validated build (SHA-256 `59011df15b8e6a07f3fb5fec0dad177c4ce3eacf006dbd4c9ae7c9696044eadb`). GitHub confirmed successful deployment and the expected site URL; the live github.io domain remains untested from this restricted workspace.

The terrain visibility revision `5fea8a9` uses a 12× default, a 24× slider limit, camera-relative side lighting, and clearer charcoal shading. Its local validation passed 16 geometry/data tests and 41 browser checks; the bundled prototype measurements and screenshots use the new default.

Terrain visibility deployment completed successfully: https://github.com/TrentConley/globe/actions/runs/37152397728. The published HTML matched the validated build byte-for-byte, SHA-256 `181e359f9f54de38e70f504dfe6b32efe21d1cf04dc76bac5286499eb61163f1`.


The physical-build design release adds a 25× default (40× adjustable limit), the detailed build-guide web page, an 18-page PDF, hardware references, seven small optical test prints, BOM/test-log CSVs, a reference matrix pattern and a bench utility. The kit preserves project source for maintenance. Validation for the release: 16 geometry/data tests, 41 simulator browser checks, 26 guide/link/layout checks, and independent geometry inspection of the nine supplied STL files. No hardware execution is implied.

The physical-build release was published at commit ca9a9cc. Its full Pages workflow completed with Status Success (build 43 s, deploy 13 s): https://github.com/TrentConley/globe/actions/runs/37156657901. The public raw simulator, HTML guide, PDF and source-reference page matched the locally checked files byte-for-byte. Direct live-domain browser testing remains unavailable in this workspace; desktop/phone browser validation used the same local build.


The structural study adds https://trentconley.github.io/globe/structure.html, linked from the simulator and guide, plus static cutaway/prototype images and an updated source-inclusive kit. Commit 5667aa3 contains five interactive views, component visibility/inspection and image export. The public raw structure page matched the locally checked build byte-for-byte, SHA-256 34d293a357fd5b5bb77ac5b2d9df1a2794471393767f7ace915edd8ce6153895. Local validation passed 19 structural browser checks, 27 guide checks and 16 existing geometry/data tests. The complete assembly remains a concept, with no physical fabrication or production-CAD release implied.

GitHub confirmed the complete Pages workflow succeeded for 5667aa3: https://github.com/TrentConley/globe/actions/runs/37163390246 (26 s total, successful deployment to the expected site URL). Live-domain browser access remains restricted here; the identical build was checked locally.


## Engineering A0 publication

The current engineering build adds `engineering.html`, `engineering-report.html` / PDF, `engineering-package.zip`, `optical-prototype-A0.zip`, `assembly/`, `engineering-assets/`, `engineering-checks/`, and optional compressed cage STEP downloads under `cad-step/`. `engineering-downloads.json` records SHA-256 hashes and byte sizes. Copy the complete checked `dist` output to the existing gh-pages checkout after fetching/fast-forwarding; retain `.nojekyll` and historical links.

Validation before this release: 87 saved STL files independently checked as closed, outward, single solids; nine selected assembly collision-group checks with zero unintended intersections; matching pixel-map hash and twenty sector configurations; 16 geometry tests, 14 device tests, 11 CAD browser checks, report image/link/mobile/PDF checks, and the portable ten-cell board at zero DRC violations/unconnected items. Full matrix routing and physical qualification remain held. Read the current report, not historical concept counts, for the manufacturing state.

Check the complete Pages workflow status after pushing, then compare the public raw viewer/report/manifest against the tested local bytes. A successful local build alone is not evidence of a successful deployment. Direct github.io browser access may remain unavailable under this environment policy.
