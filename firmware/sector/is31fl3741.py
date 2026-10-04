"""MicroPython-compatible monochrome driver. Register behavior cross-checked
against the Adafruit MIT driver and the published QMK register constants.
Physical current, bus timing and channel polarity still need a bench test.
"""
class IS31FL3741:
 def __init__(self,i2c,address,current=16):
  if address not in (0x30,0x31,0x32,0x33) or not 0<=current<=32:raise ValueError('driver configuration')
  self.i2c=i2c;self.address=address;self.page=None
  if self.i2c.readfrom_mem(address,0xfc,1)[0]!=address*2:raise OSError('LED driver ID mismatch')
  self.select(4);self.write(0x3f,b'\xae');self.page=None
  self.select(4);self.write(0,b'\x00');self.write(1,bytes([current]))
  self.select(2);self.write(0,bytes([255])*180)
  self.select(3);self.write(0,bytes([255])*171)
  self.show(bytes(351));self.select(4);self.write(0,b'\x01')
 def write(self,register,data):self.i2c.writeto_mem(self.address,register,data)
 def select(self,page):
  if self.page!=page:self.write(0xfe,b'\xc5');self.write(0xfd,bytes([page]));self.page=page
 def show(self,pixels):
  if len(pixels)!=351:raise ValueError('A driver frame has 351 channels')
  self.select(0);self.write(0,pixels[:180]);self.select(1);self.write(0,pixels[180:])
