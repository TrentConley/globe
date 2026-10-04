import unittest,sys,tempfile,json,sqlite3,os,subprocess,time,threading,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for folder in ('firmware','firmware/common','firmware/sector'):sys.path.insert(0,str(ROOT/folder))
from protocol import *
from state import Sector
from is31fl3741 import IS31FL3741
from globe_host.store import Store,InvalidProject,validate_project
from globe_host.mapper import Mapper
from globe_host.transport import SimulatedTransport
from globe_host.power import PowerGuard,PowerFault
class ProtocolTests(unittest.TestCase):
 def test_crc_known_vector_and_fragmented_escape(self):
  self.assertEqual(crc32(b'123456789'),0xcbf43926);data=bytes(range(256))*2;packet=encode(19,TILE,4294967295,data);d=Decoder();out=[]
  for b in packet:out+=d.feed(bytes([b]))
  self.assertEqual(out,[(19,TILE,4294967295,data)])
 def test_corruption_truncation_oversize_and_resync(self):
  p=bytearray(encode(1,BEGIN,2,b'abc'));p[5]^=1;d=Decoder();self.assertEqual(d.feed(p),[]);self.assertEqual(d.feed(b'\x7e'+b'a'*10000+b'\x7e'),[]);self.assertLessEqual(len(d.buf),525);self.assertEqual(d.feed(encode(1,PING,3)),[(1,PING,3,b'')])
 def test_limits(self):
  for args in [(256,PING,0,b''),(0,PING,-1,b''),(0,TILE,0,b'x'*513)]:
   with self.assertRaises(ValueError):encode(*args)
class SectorTests(unittest.TestCase):
 def setUp(self):
  self.frames=[];self.blanks=[];self.s=Sector(0,[0,3],lambda f:self.frames.append(dict(f)),lambda:self.blanks.append(True),b'd'*32)
 def send(self,k,r=1,p=b''):return self.s.handle(k,r,p)[0]
 def test_atomic_complete_retry_and_stale(self):
  self.assertEqual(self.send(BEGIN,p=b'd'*32),NACK);self.s.temperature(25);self.assertEqual(self.send(BEGIN,p=b'd'*32),ACK)
  self.assertEqual(self.send(TILE,p=bytes([0])+bytes(351)),ACK);self.assertEqual(self.send(COMMIT),NACK);self.assertFalse(self.frames)
  self.send(TILE,p=bytes([3])+bytes([7])*351);self.assertEqual(self.send(COMMIT),ACK);self.assertEqual(len(self.frames),1);self.assertEqual(self.send(COMMIT),ACK);self.assertEqual(len(self.frames),1);self.assertEqual(self.send(BEGIN,0,b'd'*32),NACK)
 def test_temperature_and_bad_map_fail_off(self):
  self.s.temperature(25);self.assertEqual(self.send(BEGIN,p=b'x'*32),NACK)
  for temp in [None,float('nan'),50,85,-11]:self.s.temperature(temp);self.assertFalse(self.s.temperature_ok);self.assertFalse(self.s.visible)
 def test_i2c_failure_blanks(self):
  self.s.show=lambda f:(_ for _ in ()).throw(OSError('bus'));self.s.temperature(25);self.send(BEGIN,p=b'd'*32)
  for t in [0,3]:self.send(TILE,p=bytes([t])+bytes(351))
  self.assertEqual(self.send(COMMIT),NACK);self.assertTrue(self.blanks)
class StoreTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'db';self.s=Store(self.path)
 def tearDown(self):self.tmp.cleanup()
 def project(self):return {'visits':[{'name':'Vancouver','lat':49.2827,'lon':-123.1207}],'radiusMiles':50,'brightness':.6}
 def test_save_restart_conflict_backup(self):
  saved=self.s.replace(self.project(),0);self.assertEqual(saved['revision'],1);self.assertEqual(Store(self.path).read(),saved)
  with self.assertRaises(InvalidProject):self.s.replace(self.project(),0)
  backup=Path(self.tmp.name)/'backup';self.s.backup(backup);self.assertEqual(Store(backup).read(),saved)
 def test_abrupt_exit_retains_committed_and_discards_uncommitted(self):
  self.s.replace(self.project(),0)
  code="import sqlite3,os;c=sqlite3.connect(%r);c.execute('BEGIN IMMEDIATE');c.execute(\"INSERT INTO projects VALUES(2,0,'{}')\");os._exit(9)"%str(self.path)
  r=subprocess.run([sys.executable,'-c',code]);self.assertEqual(r.returncode,9);self.assertEqual(Store(self.path).read()['revision'],1)
  c=sqlite3.connect(self.path);self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok');c.close()
 def test_validation(self):
  for bad in [{'visits':[{'name':'x','lat':float('nan'),'lon':0}]},{'visits':[],'radiusMiles':True},{'visits':[],'brightness':2}, {'visits':[{'name':'x','lat':91,'lon':0}]}]:
   with self.assertRaises(InvalidProject):validate_project(bad)
class DriverTests(unittest.TestCase):
 def test_register_boundaries(self):
  class Bus:
   def __init__(self):self.calls=[]
   def readfrom_mem(self,a,r,n):return bytes([a*2])
   def writeto_mem(self,a,r,d):self.calls.append((a,r,bytes(d)))
  bus=Bus();driver=IS31FL3741(bus,.0.__int__()+0x30);bus.calls.clear();pixels=bytes(i%256 for i in range(351));driver.show(pixels)
  self.assertEqual([d for a,r,d in bus.calls if r==0],[pixels[:180],pixels[180:]])
  self.assertEqual([d[0] for a,r,d in bus.calls if r==0xfd],[0,1])
class PowerTests(unittest.TestCase):
 def test_overpower_fault_latches_and_sensor_loss_fails_off(self):
  class Relay:
   def off(self):self.on_state=False
   def on(self):self.on_state=True
  class Sensor:
   value=(12,.5,6)
   def read(self):return self.value
  sensor=Sensor();relay=Relay();guard=PowerGuard(sensor,relay);guard.enable();self.assertTrue(relay.on_state);sensor.value=(12,1.1,13.2)
  with self.assertRaises(PowerFault):guard.sample()
  self.assertFalse(relay.on_state);sensor.value=(12,0,0)
  with self.assertRaises(PowerFault):guard.enable()
  guard=PowerGuard(sensor,relay);guard.enable();sensor.read=lambda:(_ for _ in ()).throw(OSError('disconnected'))
  with self.assertRaises(PowerFault):guard.sample()
  self.assertFalse(relay.on_state)
class EndToEndTests(unittest.TestCase):
 def test_mapper_and_twenty_sector_transaction(self):
  m=Mapper(ROOT/'engineering/release/pixel-map.npz');p={'visits':[{'lat':49.2827,'lon':-123.1207}],'radiusMiles':50,'brightness':.6};frames,metrics=m.render(p);self.assertGreater(metrics['litChannels'],0);duplicate,_=m.render({**p,'visits':p['visits']*2});self.assertEqual(frames,duplicate)
  manifest=json.loads((ROOT/'engineering/release/pixel-map.json').read_text());sectors={int(k):v for k,v in manifest['sectors'].items()};transport=SimulatedTransport(sectors,manifest['sha256']);transport.update(1,frames);self.assertTrue(transport.health(1));self.assertEqual(len(transport.display),20);transport.blank(1);self.assertFalse(transport.health(1));transport.update(1,frames);self.assertTrue(transport.health(1))
 def test_http_auth_save_conflict_restart(self):
  from globe_host.server import Application,make_server
  with tempfile.TemporaryDirectory() as tmp:
   app=Application(Path(tmp)/'db',ROOT/'engineering/release/pixel-map.npz',ROOT/'engineering/release/pixel-map.json','test-key',True);server=make_server(app,'127.0.0.1',0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}/api/state'
   try:
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(url)
    self.assertEqual(e.exception.code,401);data=json.dumps({'expectedRevision':0,'project':{'visits':[{'name':'Vancouver','lat':49.2827,'lon':-123.1207}]}}).encode();req=urllib.request.Request(url,data=data,method='PUT',headers={'Authorization':'Bearer test-key','Content-Type':'application/json'});saved=json.load(urllib.request.urlopen(req));self.assertEqual(saved['revision'],1)
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(req)
    self.assertEqual(e.exception.code,409)
    for _ in range(50):
     if app.display['appliedRevision']==1:break
     time.sleep(.1)
    self.assertEqual(app.display['appliedRevision'],1)
   finally:server.shutdown();server.server_close();app.close();thread.join()
   self.assertEqual(Store(Path(tmp)/'db').read()['visits'][0]['name'],'Vancouver')
if __name__=='__main__':unittest.main(verbosity=2)

class FRAMTests(unittest.TestCase):
 def test_every_interrupted_write_preserves_a_complete_bank(self):
  from globe_host.fram import FRAM
  class Memory:
   def __init__(self):self.data=bytearray(32768);self.remaining=None
   def read(self,a,n):return bytes(self.data[a:a+n])
   def write(self,a,b):
    for i,v in enumerate(b):
     if self.remaining==0:raise OSError('power cut')
     self.data[a+i]=v
     if self.remaining is not None:self.remaining-=1
  memory=Memory();fram=FRAM(memory);state={'revision':1,'visits':[{'lat':49.2827,'lon':-123.1207}],'radiusMiles':50,'brightness':.6};fram.save(state);baseline=bytes(memory.data);next_state={**state,'revision':2,'visits':state['visits']+[{'lat':40.7128,'lon':-74.006}]}
  for cut in range(53):
   memory.data[:]=baseline;memory.remaining=cut
   try:fram.save(next_state)
   except OSError:pass
   recovered=fram.latest();self.assertIn(recovered['revision'],[1,2]);self.assertEqual(len(recovered['visits']),recovered['revision'])
  memory.remaining=None;fram.save(next_state);self.assertEqual(fram.latest()['revision'],2)
