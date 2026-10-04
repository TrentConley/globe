"""Copy with protocol.py, state.py, is31fl3741.py and sector.json to a Pico.
MicroPython hardware integration; requires bench qualification before use.
"""
import machine,time,json,binascii
from protocol import Decoder,encode
from state import Sector
from is31fl3741 import IS31FL3741
import onewire,ds18x20

with open('sector.json') as f:config=json.load(f)
sector_id=config['sector'];tiles=config['tiles'];digest=binascii.unhexlify(config['map_sha256'])
sdb=[machine.Pin(p,machine.Pin.OUT,value=0) for p in (10,11,12,13)]
de=machine.Pin(6,machine.Pin.OUT,value=0)
uart=machine.UART(1,115200,tx=machine.Pin(4),rx=machine.Pin(5),rxbuf=2048)
i2c=machine.I2C(0,sda=machine.Pin(0),scl=machine.Pin(1),freq=100000)
reset=machine.Pin(14,machine.Pin.OUT,value=1)
sensor=ds18x20.DS18X20(onewire.OneWire(machine.Pin(15)))
watchdog=machine.WDT(timeout=8000);drivers={};decoder=Decoder();last_contact=time.ticks_ms();last_temp=0;converting=False;rom=None

def blank():
 for pin in sdb:pin.value(0)

def mux(channel):i2c.writeto(0x70,bytes([1<<channel]))
def initialize():
 blank();drivers.clear()
 # I2C stays operational in software shutdown; SDB is raised for initialization only
 # after a valid local temperature, with all PWM registers reset before enabling output.
 for tile in tiles:
  bus=tile//4;sdb[bus].value(1);mux(bus);drivers[tile]=IS31FL3741(i2c,0x30+tile%4,current=min(32,max(0,int(config.get('current_code',4)))))
 blank()
def show(frames):
 blank()
 if len(drivers)!=len(tiles):initialize()
 for tile,pixels in frames.items():mux(tile//4);drivers[tile].show(pixels)
 for bus in {tile//4 for tile in tiles}:sdb[bus].value(1)

state=Sector(sector_id,tiles,show,blank,digest)
while True:
 watchdog.feed();now=time.ticks_ms()
 if not converting and time.ticks_diff(now,last_temp)>1500:
  try:
   roms=sensor.scan()
   if len(roms)!=1:raise OSError('one local temperature sensor required')
   rom=roms[0];sensor.convert_temp();converting=True;last_temp=now
  except OSError:state.temperature(None);last_temp=now
 elif converting and time.ticks_diff(now,last_temp)>=800:
  try:state.temperature(sensor.read_temp(rom))
  except OSError:state.temperature(None)
  converting=False
 if time.ticks_diff(now,last_contact)>60000:blank();state.visible=False
 if uart.any():
  for address,kind,revision,payload in decoder.feed(uart.read()):
   if address!=sector_id:continue
   last_contact=now;reply,data=state.handle(kind,revision,payload);de.value(1);uart.write(encode(sector_id,reply,revision,data));uart.flush();time.sleep_us(250);de.value(0)
 time.sleep_ms(2)
