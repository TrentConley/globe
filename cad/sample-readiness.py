"""Sample revision A1 only: mount clearance and a finish/thickness witness.

Run after the A0 CAD generation. Does not release or change full-globe geometry.
The baffle boolean uses the checked A0 source; all dimensions are millimetres.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import manifold3d as mf
import trimesh

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'cad/generated'
REPORT = ROOT / 'engineering/release'
source = CAD / 'baffle-type-02.stl'
baseline = json.loads((REPORT / 'manufacturing-mesh-checks.json').read_text())
sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert next(r['sha256'] for r in baseline if r['file'] == source.name) == sha
tile = json.loads((CAD / 'layout.json').read_text())['tiles'][124]
mesh = trimesh.load_mesh(source)
shape = mf.Manifold(mf.Mesh(vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
                            tri_verts=np.asarray(mesh.faces, dtype=np.uint32)))
for x, y in tile['holes']:
    shape -= mf.Manifold.cylinder(25, 3.8, circular_segments=96).translate([x, y, -1])


def write(name, solid):
    m = solid.to_mesh()
    mesh = trimesh.Trimesh(vertices=np.asarray(m.vert_properties)[:, :3],
                           faces=np.asarray(m.tri_verts), process=True)
    mesh.export(CAD / name)
    # Re-open the actual deliverable, rather than auditing the in-memory solid.
    saved = trimesh.load_mesh(CAD / name)
    count = len(saved.split(only_watertight=False))
    assert saved.is_watertight and saved.is_winding_consistent
    assert saved.volume > 0 and count == 1, (name, count)
    return {'file': name, 'sha256': hashlib.sha256((CAD / name).read_bytes()).hexdigest(),
            'watertight': True, 'windingConsistent': True, 'connectedSolids': count,
            'volumeMM3': float(saved.volume), 'boundsMM': saved.bounds.tolist()}


checks = [write('sample-baffle-type-02-clearance.stl', shape)]
# Flat underside; four 8 mm strips, ascending 1 / 2 / 3 / 4.75 mm.
coupon = mf.Manifold()
for i, thickness in enumerate([1, 2, 3, 4.75]):
    coupon += mf.Manifold.cube([8, 24, thickness]).translate([8 * i, 0, 0])
checks.append(write('sample-finish-thickness-coupon.stl', coupon))
record = {'revision': 'sample-A1', 'physicalTested': False,
          'sourceBaffleSHA256': sha, 'mountApertureDiameterMM': 7.6,
          'bossDiameterMM': 6.6, 'nominalBossRadialClearanceMM': 0.5,
          'couponStripThicknessMM': [1, 2, 3, 4.75], 'meshChecks': checks}
(REPORT / 'sample-geometry-checks.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
