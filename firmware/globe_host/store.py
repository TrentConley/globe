"""Durable travel history. Acknowledgement follows a committed SQLite transaction."""
import json,math,sqlite3,threading,time
from contextlib import contextmanager
from pathlib import Path

class InvalidProject(ValueError):pass

def validate_project(project):
 if not isinstance(project,dict):raise InvalidProject('Project must be an object')
 visits=project.get('visits');radius=project.get('radiusMiles',50)
 if not isinstance(visits,list) or len(visits)>2000:raise InvalidProject('Use at most 2,000 places')
 if isinstance(radius,bool) or not isinstance(radius,(float,int)) or not math.isfinite(radius) or not 25<=radius<=350:raise InvalidProject('Radius must be 25–350 miles')
 clean=[]
 for item in visits:
  if not isinstance(item,dict):raise InvalidProject('Invalid place')
  name=item.get('name');lat=item.get('lat');lon=item.get('lon')
  if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise InvalidProject('A place needs a name of 1–100 characters')
  if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) for x in (lat,lon)) or abs(lat)>90 or abs(lon)>180:raise InvalidProject('Invalid coordinates')
  clean.append({'name':name.strip(),'lat':float(lat),'lon':float(lon)})
 brightness=project.get('brightness',.6)
 if isinstance(brightness,bool) or not isinstance(brightness,(int,float)) or not math.isfinite(brightness) or not 0<=brightness<=1:raise InvalidProject('Brightness must be 0–1')
 return {'version':2,'radiusMiles':float(radius),'brightness':float(brightness),'visits':clean}

class Store:
 def __init__(self,path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock()
  with self.connection() as c:
   c.execute('CREATE TABLE IF NOT EXISTS projects(revision INTEGER PRIMARY KEY, created REAL NOT NULL, document TEXT NOT NULL)')
   if not c.execute('SELECT 1 FROM projects LIMIT 1').fetchone():c.execute('INSERT INTO projects VALUES(0,?,?)',(time.time(),json.dumps(validate_project({'visits':[]}))))
 @contextmanager
 def connection(self):
  c=sqlite3.connect(self.path,timeout=10)
  try:
   c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA synchronous=FULL');c.execute('PRAGMA busy_timeout=10000')
   with c:yield c
  finally:c.close()
 def read(self):
  with self.lock,self.connection() as c:
   revision,created,document=c.execute('SELECT revision,created,document FROM projects ORDER BY revision DESC LIMIT 1').fetchone()
  return {'revision':revision,'savedAt':created,**json.loads(document)}
 def replace(self,project,expected_revision):
  clean=validate_project(project)
  with self.lock,self.connection() as c:
   c.execute('BEGIN IMMEDIATE');current=c.execute('SELECT MAX(revision) FROM projects').fetchone()[0]
   if expected_revision!=current:raise InvalidProject('This globe changed in another window. Reload before saving.')
   if current>=2**32-1:raise InvalidProject('Revision counter requires maintenance')
   c.execute('INSERT INTO projects VALUES(?,?,?)',(current+1,time.time(),json.dumps(clean,separators=(',',':'),allow_nan=False)))
   # Retain a rolling recovery history; a downloaded export remains the independent backup.
   c.execute('DELETE FROM projects WHERE revision < ?',(max(0,current+1-100),));c.commit()
  return self.read()
 def restore(self,state):
  clean=validate_project(state)
  with self.lock,self.connection() as c:
   c.execute('BEGIN IMMEDIATE');current=c.execute('SELECT MAX(revision) FROM projects').fetchone()[0]
   if state['revision']>current:c.execute('INSERT INTO projects VALUES(?,?,?)',(state['revision'],time.time(),json.dumps(clean)))
 def backup(self,path):
  with self.lock,self.connection() as source,sqlite3.connect(path) as target:source.backup(target)
