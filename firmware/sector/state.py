"""Testable sector transaction logic. Nothing is shown until a complete frame commits."""
from protocol import BEGIN,TILE,COMMIT,PING,BLANK,ACK,NACK
class Sector:
 def __init__(self,sector,tiles,show,blank,map_digest=None):
  self.sector=sector;self.tiles=set(tiles);self.show=show;self.blank=blank;self.pending=None;self.frames={};self.applied=None;self.temperature_ok=False;self.fault='temperature not yet verified';self.visible=False;self.map_digest=map_digest
 def temperature(self,celsius):
  self.temperature_ok=isinstance(celsius,(int,float)) and -10<=celsius<50
  if not self.temperature_ok:self.blank();self.visible=False;self.fault='temperature missing or outside operating range'
  else:self.fault=None
 def handle(self,kind,revision,payload):
  try:
   if kind==PING:return ACK,bytes([1 if self.temperature_ok else 0,1 if self.visible else 0])
   if kind==BLANK:self.blank();self.visible=False;self.pending=None;self.frames={};return ACK,b''
   if not self.temperature_ok:raise ValueError('thermal interlock')
   if kind==BEGIN:
    if self.map_digest is not None and payload!=self.map_digest:raise ValueError('pixel map mismatch')
    if self.applied is not None and revision<self.applied:raise ValueError('stale revision')
    self.pending=revision;self.frames={};return ACK,b''
   if kind==TILE:
    if revision!=self.pending or len(payload)!=352 or payload[0] not in self.tiles:raise ValueError('unexpected tile')
    self.frames[payload[0]]=bytes(payload[1:]);return ACK,b''
   if kind==COMMIT:
    if revision==self.applied and self.pending is None:return ACK,b''
    if revision!=self.pending or set(self.frames)!=self.tiles:raise ValueError('incomplete frame')
    self.show(self.frames);self.visible=True;self.applied=revision;self.pending=None;self.frames={};return ACK,b''
   raise ValueError('unknown command')
  except (ValueError,OSError) as error:
   if isinstance(error,OSError):self.blank();self.visible=False;self.fault='I2C failure'
   return NACK,str(error).encode()[:100]
