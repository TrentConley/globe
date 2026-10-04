"""Local globe service. Run with --simulate for software validation without hardware."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import argparse,hmac,json,secrets,threading,time,os,sqlite3
from .store import Store,InvalidProject
from .mapper import Mapper
from .transport import SerialTransport,SimulatedTransport
from .power import hardware_guard
from .fram import FRAM,I2CMemory

class Application:
 def __init__(self,db,pixel_map,manifest,token,simulate,serial_port=None):
  self.fram=None if simulate else FRAM(I2CMemory());recovery=self.fram.latest() if self.fram else None
  try:self.store=Store(db)
  except sqlite3.DatabaseError:
   if recovery is None:raise
   for suffix in ('','-wal','-shm'):
    old=Path(str(db)+suffix)
    if old.exists():old.rename(Path(str(old)+'.corrupt-'+str(time.time_ns())))
   self.store=Store(db)
  if recovery and recovery['revision']>self.store.read()['revision']:self.store.restore(recovery)
  self.save_lock=threading.RLock();self.mapper=Mapper(pixel_map);self.token=token;self.simulate=simulate;self.stop=threading.Event()
  data=json.loads(Path(manifest).read_text());sectors={int(k):v for k,v in data['sectors'].items()}
  self.transport=SimulatedTransport(sectors,data['sha256']) if simulate else SerialTransport(serial_port,sectors,data['sha256'])
  self.power=None if simulate else hardware_guard()
  if self.power:self.power.start()
  self.display={'state':'starting','appliedRevision':None,'mode':'simulation' if simulate else 'device'}
  self.thread=threading.Thread(target=self.worker,daemon=True);self.thread.start()
 def worker(self):
  applied=None;last_ping=0
  while not self.stop.wait(.2):
   state=self.store.read()
   try:
    if self.power:self.power.check();self.display['power']=dict(self.power.last)
    if applied!=state['revision']:
     self.display.update(state='updating',savedRevision=state['revision'])
     frames,metrics=self.mapper.render(state);self.transport.update(state['revision'],frames)
     applied=state['revision'];self.display.update(state='showing',appliedRevision=applied,metrics=metrics,error=None)
    if time.monotonic()-last_ping>10:
     last_ping=time.monotonic()
     if not self.transport.health(state['revision']):applied=None
   except (OSError,ValueError,TimeoutError) as error:
    self.display.update(state='fault',error=str(error));applied=None;self.stop.wait(2)
 def save_project(self,project,expected):
  with self.save_lock:
   state=self.store.replace(project,expected)
   if self.fram:
    try:self.fram.save(state)
    except OSError:
     if self.power:self.power.close()
     raise
   return state
 def snapshot(self):return {**self.store.read(),'display':dict(self.display)}
 def close(self):
  self.stop.set()
  if self.power:self.power.close()
  self.thread.join(timeout=5)

def make_server(app,host='127.0.0.1',port=8081):
 web=Path(__file__).resolve().parents[1]/'web'
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def send(self,code,data,kind='application/json'):
   if kind=='application/json':data=json.dumps(data,allow_nan=False,separators=(',',':')).encode()
   self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(data)
  def authorized(self):return hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+app.token)
  def do_GET(self):
   if self.path=='/':return self.send(200,(web/'index.html').read_bytes(),'text/html; charset=utf-8')
   if self.path not in ('/api/state','/api/export'):return self.send(404,{'error':'Not found'})
   if not self.authorized():return self.send(401,{'error':'Enter the device key'})
   state=app.snapshot()
   if self.path=='/api/export':state={k:state[k] for k in ('version','visits','radiusMiles','brightness')}
   self.send(200,state)
  def do_PUT(self):
   if self.path!='/api/state':return self.send(404,{'error':'Not found'})
   if not self.authorized():return self.send(401,{'error':'Enter the device key'})
   # Browser writes use a custom Authorization header; no cross-origin permission is granted.
   try:
    size=int(self.headers.get('Content-Length','0'))
    if not 0<size<=512000:return self.send(413,{'error':'Project too large'})
    if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'Use JSON'})
    body=json.loads(self.rfile.read(size));expected=body.get('expectedRevision')
    if isinstance(expected,bool) or not isinstance(expected,int):raise InvalidProject('A current revision is required')
    app.save_project(body.get('project'),expected);self.send(200,app.snapshot())
   except OSError:self.send(503,{'error':'Recovery storage did not verify. Reload; service the FRAM before further use.'})
   except InvalidProject as e:self.send(409 if 'another window' in str(e) else 400,{'error':str(e)})
   except (ValueError,TypeError,AttributeError):self.send(400,{'error':'Invalid request'})
  def do_OPTIONS(self):self.send(403,{'error':'Cross-origin access disabled'})
 return ThreadingHTTPServer((host,port),Handler)

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',default='/var/lib/travel-globe');p.add_argument('--pixel-map',required=True);p.add_argument('--manifest',required=True);p.add_argument('--simulate',action='store_true');p.add_argument('--serial');p.add_argument('--host',default='0.0.0.0');p.add_argument('--port',type=int,default=8081);a=p.parse_args()
 if not a.simulate and not a.serial:p.error('Specify the USB RS-485 port or explicitly select --simulate')
 folder=Path(a.data);folder.mkdir(parents=True,exist_ok=True);key=folder/'device-key.txt'
 if not key.exists():
  fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(24)+'\n')
 token=key.read_text().strip();app=Application(folder/'travels.sqlite3',a.pixel_map,a.manifest,token,a.simulate,a.serial);server=make_server(app,a.host,a.port)
 print('Globe service listening on port',server.server_port,'Mode:',app.display['mode'],flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close();app.close()
if __name__=='__main__':main()
