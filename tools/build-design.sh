#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/globe-cache}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-/tmp/globe-config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-/tmp/globe-data}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/globe-mpl}"
GLOBE_PYTHON="${GLOBE_PYTHON:-python3}"
node tools/design-layout.mjs
"$GLOBE_PYTHON" tools/refine-layout.py
"$GLOBE_PYTHON" cad/build.py --only base
"$GLOBE_PYTHON" cad/build.py --only spine
"$GLOBE_PYTHON" cad/build.py --only tiles
"$GLOBE_PYTHON" cad/frame_mesh.py
"$GLOBE_PYTHON" cad/surfaces.py
"$GLOBE_PYTHON" cad/controllers.py
"$GLOBE_PYTHON" cad/prototype.py
if [[ "${1:-}" == --step ]]; then "$GLOBE_PYTHON" cad/mesh_step.py; fi
/usr/bin/python3 electronics/generate.py
/usr/bin/python3 electronics/prewire.py
/usr/bin/python3 electronics/envelopes.py
"$GLOBE_PYTHON" tools/pixel-map.py
"$GLOBE_PYTHON" tools/simulate-structure.py
"$GLOBE_PYTHON" tools/simulate-thermal.py
"$GLOBE_PYTHON" tools/simulate-optics.py
"$GLOBE_PYTHON" tools/assembly-audit.py
"$GLOBE_PYTHON" tools/release-tables.py
"$GLOBE_PYTHON" tools/release-documents.py
npm run build
mkdir -p dist/assembly
cp artifacts/assembly/* dist/assembly/
