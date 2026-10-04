"""Measured 12 V branch interlock. Relay is normally open and fails off.
INA260 reads are independent of rendering and serial timeouts. Faults latch until
service restart; they are never cleared by repeatedly retrying a display update.
"""
import threading,time,math
class PowerFault(OSError):pass
class PowerGuard:
 def __init__(self,sensor,relay,limit_watts=12.0):
  self.sensor=sensor;self.relay=relay;self.limit=limit_watts;self.fault=None;self.enabled=False;self.last=None;self.stop=threading.Event();self.lock=threading.RLock();self.relay.off();self.thread=None
 def sample(self):
  with self.lock:
   if self.fault:raise PowerFault(self.fault)
   try:
    v,a,w=self.sensor.read()
    if not all(math.isfinite(x) for x in (v,a,w)) or not 10.8<=v<=13.2 or not -.01<=a<=1.2 or not 0<=w<=self.limit:raise PowerFault('12 V branch outside commissioned power limits')
    self.last={'volts':v,'amps':a,'watts':w,'monotonic':time.monotonic()};return self.last
   except Exception as error:
    self.relay.off();self.enabled=False;self.fault='Power interlock: '+str(error);raise PowerFault(self.fault)
 def enable(self):
  with self.lock:self.sample();self.relay.on();self.enabled=True
 def run(self):
  while not self.stop.wait(.1):
   try:self.sample()
   except PowerFault:break
 def start(self):
  self.enable();self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def check(self):
  if self.fault:raise PowerFault(self.fault)
  if not self.enabled or not self.last or time.monotonic()-self.last['monotonic']>.5:
   self.relay.off();self.enabled=False;self.fault='Power interlock sampling stopped';raise PowerFault(self.fault)
 def close(self):
  self.stop.set();self.relay.off();self.enabled=False
  if self.thread:self.thread.join(timeout=1)
  if hasattr(self.sensor,'close'):self.sensor.close()
class INA260:
 def __init__(self,bus=1,address=0x40):
  from smbus2 import SMBus
  self.bus=SMBus(bus);self.address=address
  if self.reg(0xfe)!=0x5449 or self.reg(0xff)&0xfff0!=0x2270:raise PowerFault('INA260 identity check failed')
 def reg(self,register):
  value=self.bus.read_word_data(self.address,register);return ((value&255)<<8)|(value>>8)
 def read(self):
  current=self.reg(1);current=current if current<32768 else current-65536
  return self.reg(2)*.00125,current*.00125,self.reg(3)*.01
 def close(self):self.bus.close()
def hardware_guard():
 from gpiozero import OutputDevice
 relay=OutputDevice(17,active_high=True,initial_value=False)
 try:return PowerGuard(INA260(),relay)
 except Exception:relay.off();raise
