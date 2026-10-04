"""Dual-bank MB85RC256V recovery log for coordinates, radius and brightness.
The SQLite database retains names/history. A valid FRAM bank survives interrupted
writes to the other bank; a CRC and final commit marker reject incomplete records.
"""
import struct,zlib
BANK=16384;HEADER=32;MAGIC=b'GLOBEF1\0';COMMIT=b'\xa5\x5a\xc3\x3c'
class FRAM:
 def __init__(self,memory):self.memory=memory
 def bank(self,index):
  h=self.memory.read(index*BANK,HEADER)
  if h[28:32]!=COMMIT:return None
  try:
   magic,revision,count,radius,brightness,crc=struct.unpack('<8sIHffI',h[:26])
   if magic!=MAGIC or count>2000 or not 25<=radius<=350 or not 0<=brightness<=1:return None
   body=self.memory.read(index*BANK+HEADER,count*8)
   if zlib.crc32(h[:22]+body)!=crc:return None
   visits=[]
   for i in range(count):
    lat,lon=struct.unpack_from('<ii',body,i*8)
    if abs(lat)>900000000 or abs(lon)>1800000000:return None
    visits.append({'name':'Recovered visit '+str(i+1),'lat':lat/1e7,'lon':lon/1e7})
   return {'revision':revision,'version':2,'visits':visits,'radiusMiles':radius,'brightness':brightness,'bank':index}
  except (ValueError,struct.error):return None
 def latest(self):
  banks=[b for i in range(2) if (b:=self.bank(i)) is not None];return max(banks,key=lambda b:b['revision']) if banks else None
 def save(self,state):
  previous=self.latest();index=1-previous['bank'] if previous else 0;base=index*BANK
  body=b''.join(struct.pack('<ii',round(v['lat']*1e7),round(v['lon']*1e7)) for v in state['visits']);prefix=struct.pack('<8sIHff',MAGIC,state['revision'],len(state['visits']),state['radiusMiles'],state['brightness']);header=prefix+struct.pack('<I',zlib.crc32(prefix+body))+b'\0\0'
  self.memory.write(base+28,b'\0'*4);self.memory.write(base+HEADER,body);self.memory.write(base,header)
  if self.memory.read(base,28)!=header or self.memory.read(base+HEADER,len(body))!=body:raise OSError('FRAM recovery write did not verify')
  self.memory.write(base+28,COMMIT)
  if self.bank(index) is None:raise OSError('FRAM recovery commit did not verify')
class I2CMemory:
 def __init__(self,bus=1,address=0x50):
  from smbus2 import SMBus,i2c_msg
  self.bus=SMBus(bus);self.address=address;self.msg=i2c_msg
 def read(self,offset,length):
  out=bytearray()
  for i in range(0,length,128):
   p=offset+i;w=self.msg.write(self.address,bytes([p>>8,p&255]));r=self.msg.read(self.address,min(128,length-i));self.bus.i2c_rdwr(w,r);out.extend(bytes(r))
  return bytes(out)
 def write(self,offset,data):
  for i in range(0,len(data),30):
   p=offset+i;self.bus.i2c_rdwr(self.msg.write(self.address,bytes([p>>8,p&255])+data[i:i+30]))
