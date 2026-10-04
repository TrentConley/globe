"""Linear 3-D beam analysis with explicit assumptions and an analytical benchmark.
N, mm, MPa. Contact, socket slip, creep, buckling imperfections and drop impact
are outside this solver; results are a screening model, not proof of a build.
"""
from pathlib import Path
import json,math
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'engineering/release';OUT.mkdir(exist_ok=True)
D=json.loads((ROOT/'cad/generated/layout.json').read_text());R=D['requirements']

def stiffness(a,b,E,G,area,I,J):
 d=b-a;L=np.linalg.norm(d);x=d/L;ref=np.array([0.,0.,1.])
 if abs(x@ref)>.95:ref=np.array([0.,1.,0.])
 y=np.cross(ref,x);y/=np.linalg.norm(y);z=np.cross(x,y);rot=np.array([x,y,z]);T=np.zeros((12,12))
 for i in range(4):T[3*i:3*i+3,3*i:3*i+3]=rot
 k=np.zeros((12,12))
 for ids,m in [([0,6],E*area/L*np.array([[1,-1],[-1,1]])),([3,9],G*J/L*np.array([[1,-1],[-1,1]])),
 ([1,5,7,11],E*I/L**3*np.array([[12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],[-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])),
 ([2,4,8,10],E*I/L**3*np.array([[12,-6*L,-12,-6*L],[-6*L,4*L*L,6*L,2*L*L],[-12,6*L,12,6*L],[-6*L,2*L*L,6*L,4*L*L]]))]:
  k[np.ix_(ids,ids)]+=m
 return T.T@k@T,k,T,L

def section(ro,ri=0):return math.pi*(ro*ro-ri*ri),math.pi/4*(ro**4-ri**4),math.pi/2*(ro**4-ri**4)
def benchmark():
 A,I,J=section(3,2);k,_,_,_=stiffness(np.zeros(3),np.array([100.,0,0]),69000,26538,A,I,J)
 f=np.zeros(6);f[2]=-1;u=np.linalg.solve(k[6:,6:],f);expected=-100**3/(3*69000*I)
 err=abs(u[2]-expected)/abs(expected);assert err<1e-10
 return {'case':'100 mm aluminum tube cantilever, 1 N tip load','analytical_mm':expected,'solver_mm':u[2],'relative_error':err}

def model():
 nodes=list(np.array(D['nodes'])*R['frame_vertex_radius_mm']);edges=[]
 for a,b in D['edges']:edges.append((a,b,'nylon',1.8,0))
 degree=np.bincount(np.array(D['edges']).ravel(),minlength=len(nodes))
 major=[i for i,n in enumerate(D['nodes']) if degree[i]==5 and abs(n[2])<.9]
 hubs=[]
 for sign in [-1,1]:
  ids=[i for i in major if nodes[i][2]*sign>0];z=float(np.mean([nodes[i][2] for i in ids]));idx=len(nodes);nodes.append(np.array([0.,0.,z]));hubs.append(idx)
  for i in ids:edges.append((idx,i,'aluminum',4,2))
 root=len(nodes);nodes.append(np.array([0.,0.,-186.]));edges.extend([(root,hubs[0],'aluminum',6,4),(hubs[0],hubs[1],'aluminum',6,4)])
 return np.array(nodes),edges,root

def solve(nodes,edges,root,loads,modulus_factor=1):
 nd=len(nodes)*6;K=lil_matrix((nd,nd));elements=[]
 for a,b,mat,ro,ri in edges:
  E=R['nylon_E_MPa_lower_bound']*modulus_factor if mat=='nylon' else R['aluminum_E_MPa'];G=E/(2*(1+.35 if mat=='nylon' else 1+.33));A,I,J=section(ro,ri)
  k,local,T,L=stiffness(nodes[a],nodes[b],E,G,A,I,J);ids=np.r_[np.arange(a*6,a*6+6),np.arange(b*6,b*6+6)];K[np.ix_(ids,ids)]+=k
  elements.append((ids,local,T,A,I,J,ro,mat,L))
 K=K.tocsr();free=np.setdiff1d(np.arange(nd),np.arange(root*6,root*6+6));u=np.zeros(nd);u[free]=spsolve(K[free][:,free],loads[free]);res=K@u-loads
 stresses=[]
 for ids,k,T,A,I,J,r,mat,L in elements:
  f=k@T@u[ids];axial=max(abs(f[0]),abs(f[6]))/A;bending=max(math.hypot(f[4],f[5]),math.hypot(f[10],f[11]))*r/I;torsion=max(abs(f[3]),abs(f[9]))*r/J
  stresses.append(math.sqrt((axial+bending)**2+3*torsion**2))
 residual=float(np.linalg.norm(res[free])/max(np.linalg.norm(loads[free]),1e-12));assert residual<1e-7
 return u.reshape(-1,6),np.array(stresses),residual

def main():
 bench=benchmark();nodes,edges,root=model();N=len(D['nodes'])
 # Use a 3.5 kg screening supported globe mass until the weighed assembly supersedes it.
 # Loads include shell, baffles, frame, boards, controllers and wiring; base is assessed separately.
 supported_kg=3.5;gravity=R['gravity_m_s2'];F=np.zeros(len(nodes)*6);F[np.arange(N)*6+2]=-supported_kg*gravity/N
 cases=[]
 for name,f,scale in [('gravity',F,1),('3g handling',F*3,1),('gravity, half nylon stiffness',F,.5)]:
  u,s,res=solve(nodes,edges,root,f,scale);ny=max(v for v,e in zip(s,edges) if e[2]=='nylon');al=max(v for v,e in zip(s,edges) if e[2]=='aluminum')
  cases.append({'case':name,'max_displacement_mm':float(np.linalg.norm(u[:N,:3],axis=1).max()),'nylon_max_nominal_beam_stress_MPa':float(ny),'aluminum_max_nominal_beam_stress_MPa':float(al),'nylon_yield_factor':25/ny,'aluminum_yield_factor':145/al,'spine_nominal_stress_MPa':float(max(v for v,e in zip(s,edges) if e[3]==6)),'equilibrium_relative_residual':res})
  if name=='gravity':gravity_u=u;gravity_s=s
 # Lateral load at the north cage node, in addition to gravity.
 f=F.copy();top=int(np.argmax(nodes[:N,2]));f[top*6]+=5;u,s,res=solve(nodes,edges,root,f)
 cases.append({'case':'gravity plus 5 N lateral at north pole','max_displacement_mm':float(np.linalg.norm(u[:N,:3],axis=1).max()),'nylon_max_nominal_beam_stress_MPa':float(max(v for v,e in zip(s,edges) if e[2]=='nylon')),'aluminum_max_nominal_beam_stress_MPa':float(max(v for v,e in zip(s,edges) if e[2]=='aluminum')),'equilibrium_relative_residual':res})
 steel_volume=json.loads((ROOT/'cad/generated/cad-audit-base.json').read_text())[2]['volume_mm3'];ballast_kg=steel_volume*7.85e-6;base_kg=ballast_kg+.40
 total=supported_kg+base_kg;cg_height=(supported_kg*224+base_kg*18)/total;foot_radius=94
 tipping=total*gravity*(foot_radius/1000)/(.3765)
 report={'model':'3-D linear Euler-Bernoulli beam screening; joints assumed rigid','supported_mass_kg':supported_kg,'benchmark':bench,'cases':cases,'stability':{'base_mass_assumption_kg':base_kg,'ballast_mass_kg':ballast_kg,'total_mass_kg':total,'center_of_gravity_above_table_mm':cg_height,'support_foot_radius_mm':foot_radius,'ideal_tipping_angle_deg':math.degrees(math.atan(foot_radius/cg_height)),'ideal_horizontal_force_at_top_to_tip_N':tipping,'sliding_coefficient_needed_at_5N':5/(total*gravity)},'limits':['No local stress concentration at bolt holes or molded joints','No bolt preload/contact/slip solution; socket torque and pull tests required','No nonlinear drop/impact or long-term creep prediction','Rigid base attachment assumed; actual base/collar must be checked','PA12 properties are conservative assumptions, not certified print-process values']}
 (OUT/'structural-analysis.json').write_text(json.dumps(report,indent=2))
 fig=plt.figure(figsize=(10,9),facecolor='#101619');ax=fig.add_subplot(projection='3d',facecolor='#101619');segments=[nodes[[a,b]] for a,b,*_ in edges];deformed=nodes+gravity_u[:,:3]*150
 ax.add_collection3d(Line3DCollection(segments,colors='#63716e',linewidths=.45,alpha=.4));lines=Line3DCollection([deformed[[a,b]] for a,b,*_ in edges],cmap='magma',linewidths=1.3);lines.set_array(gravity_s);ax.add_collection3d(lines)
 ax.set(xlim=(-150,150),ylim=(-150,150),zlim=(-200,150));ax.set_box_aspect((1,1,1.15));ax.set_axis_off();ax.view_init(19,32)
 ax.set_title('Gravity load: 3.5 kg supported mass\nDeformation shown at 150×; color = nominal beam stress',color='#e9e6d9',pad=15)
 cb=fig.colorbar(lines,ax=ax,shrink=.55,pad=.01);cb.set_label('MPa',color='white');cb.ax.tick_params(colors='white');fig.savefig(OUT/'structural-gravity.png',dpi=180,bbox_inches='tight');plt.close(fig)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
