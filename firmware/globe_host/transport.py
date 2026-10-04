"""Single-master RS-485 transport; USB adapter must handle transmit direction."""
import time,threading,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'common'))
from protocol import Decoder,encode,BEGIN,TILE,COMMIT,ACK,NACK,PING,BLANK

class SerialTransport:
 def __init__(self,port,sectors,map_digest):
  import serial
  self.serial=serial.Serial(port,115200,timeout=.05,write_timeout=1);self.decoder=Decoder();self.sectors=sectors;self.map_digest=bytes.fromhex(map_digest);self.lock=threading.RLock()
 def request(self,sector,kind,revision,payload=b''):
  packet=encode(sector,kind,revision,payload)
  with self.lock:
   for attempt in range(3):
    self.serial.write(packet);self.serial.flush();deadline=time.monotonic()+2
    while time.monotonic()<deadline:
     for address,reply,rev,data in self.decoder.feed(self.serial.read(512)):
      if address==sector and rev==revision:
       if reply==ACK:return data
       if reply==NACK:raise OSError('Sector '+str(sector)+': '+data.decode(errors='replace'))
   raise TimeoutError('Sector '+str(sector)+' did not acknowledge')
 def update(self,revision,frames):
  with self.lock:
   for sector,tiles in self.sectors.items():
    self.request(sector,BEGIN,revision,self.map_digest)
    for tile in tiles:self.request(sector,TILE,revision,bytes([tile%16])+frames[tile])
   # All sectors received complete buffers before any are asked to display the revision.
   for sector in self.sectors:self.request(sector,COMMIT,revision)
 def blank(self,revision):
  for sector in self.sectors:
   try:self.request(sector,BLANK,revision)
   except (OSError,TimeoutError):pass
 def health(self,revision):
  replies=[self.request(s,PING,revision) for s in self.sectors]
  return all(len(r)>=2 and r[0] and r[1] for r in replies)

class SimulatedTransport:
 def __init__(self,sectors,map_digest):
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'sector'))
  from state import Sector
  self.sectors=sectors;self.map_digest=bytes.fromhex(map_digest);self.display={};self.devices={}
  for sector,tiles in sectors.items():
   def show(frames,s=sector):self.display[s]={k:bytes(v) for k,v in frames.items()}
   def blank(s=sector):self.display[s]={}
   device=Sector(sector,[t%16 for t in tiles],show,blank,self.map_digest);device.temperature(25);self.devices[sector]=device
  self.decoder=Decoder();self.lock=threading.RLock()
 def request(self,sector,kind,revision,payload=b''):
  # Exercise the same packet codec and transaction state machine as the real wire path.
  packet=self.decoder.feed(encode(sector,kind,revision,payload))[0]
  reply,data=self.devices[sector].handle(packet[1],packet[2],packet[3])
  if reply!=ACK:raise OSError(data.decode())
  return data
 update=SerialTransport.update
 blank=SerialTransport.blank
 health=SerialTransport.health
