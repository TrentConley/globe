"""MicroPython Pico, ten-cell optical bench. Use Thonny's Shell to call show().
Each GPIO MUST reach its LED through the board's 1 kohm series resistor.
USB-powered bench only: never connect this passive board to the globe's 12 V rail.
"""
from machine import Pin,PWM
import json,os
with open('patterns.json') as f:patterns=json.load(f)
outputs=[PWM(Pin(i),freq=2000,duty_u16=0) for i in range(10)]
def show(name='vancouver',brightness=.1,save=True):
 if name not in patterns or not 0<=brightness<=1:raise ValueError('Choose a listed pattern and brightness 0..1')
 for output,value in zip(outputs,patterns[name]):output.duty_u16(round(value/255*brightness*65535))
 if save:
  with open('bench-state.tmp','w') as f:json.dump({'name':name,'brightness':brightness},f)
  os.rename('bench-state.tmp','bench-state.json')
 print('Pattern:',name,'PWM scale:',brightness)
try:
 with open('bench-state.json') as f:state=json.load(f)
 show(state['name'],state['brightness'],False)
except (OSError,ValueError,KeyError):show('off',0,False)
print("Ready. In Thonny: import main; main.show('vancouver', 0.1)")
