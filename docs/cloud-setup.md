# Cloud and local setup

The web app uses Node, the package lockfile, Three.js and esbuild. The checked cloud session used Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, CadQuery 2.7.0, KiCad 9.0.2 and Chromium. KiCad's `pcbnew` module belongs to `/usr/bin/python3` (Python 3.13 in this image); do not import it from the CadQuery virtual environment.

```
npm ci
python3 -m venv /workspace/globe-engineering-venv
/workspace/globe-engineering-venv/bin/pip install -r tools/requirements-engineering.txt
npm test
npm run build
python3 -m http.server 4173 --bind 0.0.0.0 --directory dist
```

For engineering commands, activate that venv or set `GLOBE_PYTHON` to its Python executable. Set writable tool caches; this cloud image's home directories are read-only:

```
export XDG_CACHE_HOME=/tmp/globe-cache
export XDG_CONFIG_HOME=/tmp/globe-config
export XDG_DATA_HOME=/tmp/globe-data
export MPLCONFIGDIR=/tmp/globe-mpl
```

Run `tools/build-design.sh` for CAD, mappings, simulations and static assembly assets. `--step` additionally sews and checks the cage's large faceted STEP files; this can take tens of minutes. Every mesh is checked before release. A STEP that fails round-trip validation must not be shipped; the closed STL and parametric source remain the primary cage definition.

The session validated the current checkout and generated artifacts. A fresh cloud snapshot restore has not been tested. System KiCad/Chromium are image capabilities, not npm or pip dependencies. If they are missing, install them in a supported system environment; do not silently skip their checks and claim the electronics/browser release passed.

The six matrix candidates are generated with `/usr/bin/python3 electronics/generate.py`; `prewire.py` adds collision-checked regular row/column segments. These remain unfinished. The checked ten-cell routed board is preserved in `electronics/bench-release/`. Its saved-file audit is `python3 electronics/audit_bench.py` after placing the board under `electronics/generated/`.

For optional rerouting, Freerouting 2.4.1 requires Java 25. The checked session used Temurin JRE 25.0.4.1+1 and a locally downloaded router. Run only the local CLI with analytics and the API server disabled. Do not upload the design to a routing service. The release package does not require Java just to inspect or fabricate the checked ten-cell board.

Device tests:

```
python3 -m unittest discover -s tests -p 'test_firmware.py' -v
```

They start a loopback HTTP server, so the cloud sandbox may require a network-capable command execution. `node tools/check-engineering.cjs` uses Playwright and `/usr/bin/chromium`, with the local server already running. The CAD viewer also needs `artifacts/assembly/*` copied into `dist/assembly/`.

The physical Pi should use Raspberry Pi OS Lite **64-bit**, an endurance SD card, and the host requirements in `firmware/requirements-host.txt`. Install GPIO/I²C support from Raspberry Pi OS, enable I²C, and use the service example in `firmware/install/`. The cloud tests mocked hardware; installing packages does not constitute a Pi hardware test.

## Sample A1 runtime checks

The optical bench has its own behavioral tests. To build the tested MicroPython Unix interpreter with GCC and Make, use the official v1.26.0 source (commit `4ce2dd2cdab6e57f3982fc899f15a2103d71b0be`):

```sh
git clone --depth 1 --branch v1.26.0 https://github.com/micropython/micropython.git /tmp/globe-micropython-v1.26.0
make -C /tmp/globe-micropython-v1.26.0/ports/unix -j4 MICROPY_PY_SSL=0 MICROPY_PY_BTREE=0 MICROPY_PY_FFI=0 MICROPY_VFS_FAT=0 MICROPY_VFS_LFS1=0 MICROPY_VFS_LFS2=0 FROZEN_MANIFEST=
python3 tools/check-bench-runtime.py --micropython /tmp/globe-micropython-v1.26.0/ports/unix/build-standard/micropython
```

This runs the same 11 cases under CPython and MicroPython. GPIO, delays and sync are mocked; ordinary file reads/writes/rename use temporary host directories. It does not emulate RP2040 electrical behavior or flash power-loss semantics. Test those on the physical sample using the saved worksheet.

The component/material review needs manufacturer and printer sites outside this environment's current package-manager allowlist. A network configuration draft has been saved for the needed destinations; a draft does not change runtime access. Apply it through Environment settings and recheck the actual sources before marking LED/material selections verified. No manufacturer data sheet or supplier acceptance was obtained through the currently blocked destinations.
