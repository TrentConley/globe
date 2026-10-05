"""Audit saved sample A1 meshes and export its actual geometry for the viewer.

Component bodies are assumed clearance envelopes, pending LED datasheet review.
Mating contacts are explicitly allowed; wires, glue and print error are omitted.
"""
from pathlib import Path
import hashlib
import json
import math
import sys
import numpy as np
import manifold3d as mf
import trimesh

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'cad/generated'
REPORT = ROOT / 'engineering/release'
tile = json.loads((CAD / 'layout.json').read_text())['tiles'][124]
parts = {}
files = {}


def add(name, filename=None, mesh=None, xyz=None):
    if filename:
        files[filename] = hashlib.sha256((CAD / filename).read_bytes()).hexdigest()
    m = mesh if mesh is not None else trimesh.load_mesh(CAD / filename)
    if xyz is not None:
        m.apply_translation(xyz)
    parts[name] = m


add('cradle', 'prototype-cradle-type-02.stl')
add('pcb', 'pcb-type-02.stl')
add('baffle', 'sample-baffle-type-02-clearance.stl')
for i, (x, y) in enumerate(tile['holes']):
    add('seat-' + str(i), 'magnet-seat-M2-4mm.stl', xyz=[x, y, 0])

sys.path.insert(0, str(ROOT / 'electronics'))
from audit_bench import parse
pcb = ROOT / 'electronics/bench-release/optical-bench-10.kicad_pcb'
for item in parse(pcb.read_text()):
    if not isinstance(item, list) or item[0] != 'footprint':
        continue
    ref = next(x[2] for x in item if isinstance(x, list) and x[:2] == ['property', 'Reference'])
    if ref[0] not in ('D', 'R'):
        continue
    pos = next(x[1:] for x in item if isinstance(x, list) and x[0] == 'at')
    x, y = map(float, pos[:2])
    rot = math.radians(float(pos[2]) if len(pos) > 2 else 0)
    size = [1, 0.5, 0.5] if ref[0] == 'D' else [1.6, 0.8, 0.6]
    m = trimesh.creation.box(size)
    m.apply_transform(trimesh.transformations.rotation_matrix(-rot, [0, 0, 1]))
    m.apply_translation([x - 60, 60 - y, size[2] / 2 if ref[0] == 'D' else -1 - size[2] / 2])
    add(ref, mesh=m)


def solid(mesh):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(mesh.vertices, dtype=np.float32),
                               tri_verts=np.asarray(mesh.faces, dtype=np.uint32)))


expected = {tuple(sorted((name, 'pcb'))) for name in parts if name.startswith(('D', 'R', 'seat-'))}
expected.add(('cradle', 'pcb'))
expected.update((name, 'shell') for name in parts if name.startswith('seat-'))
reports = []
for region in ['vancouver', 'himalaya']:
    add('shell', 'prototype-shell-' + region + '-25x.stl')
    manager = trimesh.collision.CollisionManager()
    for name, mesh in parts.items():
        manager.add_object(name, mesh)
    _, pairs = manager.in_collision_internal(return_names=True)
    unexpected = set(pairs) - expected
    assert not unexpected, unexpected
    # Boolean volume checks also detect containment, which surface tests can miss.
    grid = solid(parts['baffle'])
    overlap = {name: abs(float((grid ^ solid(mesh)).volume()))
               for name, mesh in parts.items() if name != 'baffle'}
    assert max(overlap.values()) < 0.001, overlap
    grid_collision = trimesh.collision.CollisionManager()
    grid_collision.add_object('baffle', parts['baffle'])
    gaps = {name: float(grid_collision.min_distance_single(parts[name]))
            for name in ['shell', 'cradle'] + ['D' + str(i) for i in range(1, 11)]}
    assert gaps['shell'] >= 0.3
    assert min(gaps['D' + str(i)] for i in range(1, 11)) > 0.15
    reports.append({'shell': region, 'unexpectedSurfaceIntersections': [],
                    'matingSurfaceContacts': sorted(pairs),
                    'baffleIntersectionVolumesMM3': overlap, 'baffleMinimumGapsMM': gaps})

record = {'revision': 'sample-A1', 'physicalTested': False,
          'scope': 'Nominal saved meshes; assumed component envelopes; no print variation, wires or adhesives',
          'ledEnvelopeMM': [1, 0.5, 0.5], 'resistorEnvelopeMM': [1.6, 0.8, 0.6],
          'pcbSHA256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
          'meshSHA256': files, 'checks': reports}
(REPORT / 'sample-fit-checks.json').write_text(json.dumps(record, indent=2) + '\n')

parts['shell'] = trimesh.load_mesh(CAD / 'prototype-shell-vancouver-25x.stl')
scene = trimesh.Scene()
for name, mesh in parts.items():
    color = ([58, 60, 60, 255] if name == 'shell' else
             [64, 69, 73, 255] if name == 'baffle' else
             [41, 103, 82, 255] if name == 'pcb' else
             [205, 158, 66, 255] if name.startswith('D') else [178, 187, 186, 255])
    mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        baseColorFactor=color, metallicFactor=0.1, roughnessFactor=0.85))
    label = 'sample-A1-' + name
    if name.startswith(('D', 'R')):
        label += '-assumed-body-envelope'
    scene.add_geometry(mesh, node_name=label)
scene.export(ROOT / 'artifacts/assembly/prototype.glb')
print(json.dumps({'checks': len(reports), 'unexpectedIntersections': 0,
                  'shellGapsMM': [r['baffleMinimumGapsMM']['shell'] for r in reports],
                  'minLEDtoGridMM': min(reports[0]['baffleMinimumGapsMM']['D' + str(i)] for i in range(1, 11))}, indent=2))
