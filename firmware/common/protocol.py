"""Bounded RS-485 packets shared by CPython and MicroPython; no dependencies."""
try:
 import ustruct as struct
except ImportError:
 import struct
VERSION=1
BEGIN,TILE,COMMIT,ACK,NACK,STATUS,BLANK,PING=range(1,9)
MAX_PAYLOAD=512

def crc32(data):
 crc=0xffffffff
 for byte in data:
  crc^=byte
  for _ in range(8):crc=(crc>>1)^(0xedb88320 if crc&1 else 0)
 return crc^0xffffffff

def encode(sector,kind,revision,payload=b''):
 if not 0<=sector<=255 or not 0<=revision<2**32 or len(payload)>MAX_PAYLOAD:raise ValueError('packet limits')
 body=struct.pack('<BBBIH',VERSION,sector,kind,revision,len(payload))+payload
 body+=struct.pack('<I',crc32(body));out=bytearray([0x7e])
 for b in body:
  if b in (0x7e,0x7d):out.extend((0x7d,b^0x20))
  else:out.append(b)
 out.append(0x7e);return bytes(out)

def decode(body):
 if len(body)<13:raise ValueError('short packet')
 version,sector,kind,revision,n=struct.unpack('<BBBIH',body[:9])
 if version!=VERSION or n>MAX_PAYLOAD or len(body)!=13+n:raise ValueError('packet shape')
 if struct.unpack('<I',body[-4:])[0]!=crc32(body[:-4]):raise ValueError('CRC')
 return sector,kind,revision,bytes(body[9:-4])

class Decoder:
 def __init__(self):self.buf=bytearray();self.escape=False;self.dropping=False
 def feed(self,data):
  packets=[]
  for byte in data:
   if byte==0x7e:
    if self.buf and not self.dropping:
     try:packets.append(decode(self.buf))
     except ValueError:pass
    self.buf=bytearray();self.escape=False;self.dropping=False
   elif not self.dropping:
    if self.escape:self.buf.append(byte^0x20);self.escape=False
    elif byte==0x7d:self.escape=True
    else:self.buf.append(byte)
    if len(self.buf)>MAX_PAYLOAD+13:self.buf=bytearray();self.dropping=True
  return packets
