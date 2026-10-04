"""Sew the checked STL boundary into a valid, faceted STEP solid. No remeshing."""
from pathlib import Path
import json,argparse
import numpy as np
import cadquery as cq
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'cad/generated'
def convert(path):
 data=np.load(path);v=data['vertices'];f=data['faces'];sew=BRepBuilderAPI_Sewing(.00001)
 for ids in f:
  face=cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*v[i]) for i in ids],close=True));sew.Add(face.wrapped)
 sew.Perform();shape=cq.Shape.cast(sew.SewedShape());shells=shape.Shells()
 if len(shells)!=1:raise ValueError('Expected one sewn shell')
 solid=cq.Solid.makeSolid(shells[0]);volume=float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
 if not solid.isValid():solid=solid.fix()
 if not solid.isValid() or abs(solid.Volume()-volume)>max(.001,volume*1e-6):raise ValueError('STEP boundary invalid or changed volume')
 target=path.with_suffix('.step');cq.exporters.export(solid,str(target),opt={'write_pcurves':False});reimport=cq.importers.importStep(str(target)).val()
 if not reimport.isValid() or len(reimport.Solids())!=1 or abs(reimport.Volume()-volume)>max(.001,volume*1e-6):raise ValueError(f'STEP round trip failed: valid={reimport.isValid()}, solids={len(reimport.Solids())}, volume={reimport.Volume()}, expected={volume}')
 print(target.name,'valid STEP round trip',round(volume,3),flush=True)
 return {'part':path.stem,'valid':True,'solids':1,'volume_mm3':volume,'faceted':True,'reimport_checked':True,'triangles':len(f)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--part');a=p.parse_args();paths=[OUT/(a.part+'.npz')] if a.part else sorted(OUT.glob('cage-octant-*.npz'))
 report=[]
 for path in paths:
  path.with_suffix('.step').unlink(missing_ok=True)
  try:report.append(convert(path))
  except ValueError as error:path.with_suffix('.step').unlink(missing_ok=True);report.append({'part':path.stem,'valid':False,'reason':str(error),'manufacturingFormat':'checked STL remains available'});print(path.stem,str(error),flush=True)
  (OUT/('cad-audit-frame-step.json' if not a.part else 'cad-audit-step-'+a.part+'.json')).write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
