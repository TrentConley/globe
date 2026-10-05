"""MicroPython RP2040 Pico: USB-powered ten-cell optical bench.

Each GPIO reaches one LED THROUGH its fitted 1 kohm resistor. Never use 12 V.
Runtime tests mock GPIO; current, polarity and real flash behavior need hardware.
"""
from machine import Pin, PWM
import json
import os
import time

outputs = [PWM(Pin(i), freq=2000, duty_u16=0) for i in range(10)]


def blank():
    # Try every channel even if one peripheral reports an error.
    for output in outputs:
        try:
            output.duty_u16(0)
        except OSError:
            pass


def frame_values(frame):
    if not isinstance(frame, list) or len(frame) != 10:
        raise ValueError('A pattern must contain exactly ten values')
    if any(type(value) is not int or not 0 <= value <= 255 for value in frame):
        raise ValueError('Pattern values must be integers from 0 to 255')
    return frame


def brightness_value(value):
    if type(value) not in (int, float) or not 0 <= value <= 1:
        raise ValueError('Brightness must be a number from 0 to 1')
    return value


with open('patterns.json') as f:
    patterns = json.load(f)
if not isinstance(patterns, dict):
    raise ValueError('patterns.json must contain a pattern dictionary')
for frame in patterns.values():
    frame_values(frame)
if patterns.get('off') != [0] * 10:
    raise ValueError('The off pattern must blank all ten channels')


def show(name='vancouver', brightness=0.1, save=True):
    if type(name) is not str or name not in patterns:
        raise ValueError('Choose a listed pattern')
    brightness_value(brightness)
    # Validate and calculate the entire frame before changing any output.
    duties = [round(value / 255 * brightness * 65535)
              for value in frame_values(patterns[name])]
    try:
        for output, duty in zip(outputs, duties):
            output.duty_u16(duty)
        if save:
            with open('bench-state.tmp', 'w') as f:
                json.dump({'name': name, 'brightness': brightness}, f)
            os.rename('bench-state.tmp', 'bench-state.json')
            if hasattr(os, 'sync'):
                os.sync()
    except (OSError, ValueError):
        blank()
        raise
    print('Pattern:', name, 'PWM scale:', brightness)


def walk(brightness=0.1, hold_ms=1000):
    """Walk GP0..GP9 without flash writes; finish dark, saved state unchanged."""
    brightness_value(brightness)
    if type(hold_ms) is not int or not 1 <= hold_ms <= 10000:
        raise ValueError('Hold time must be 1..10000 milliseconds')
    for i in range(10):
        expected = [0] * 10
        expected[i] = 255
        if patterns.get('walk-' + str(i)) != expected:
            raise ValueError('Walk patterns must select exactly their numbered LED')
    try:
        for i in range(10):
            show('walk-' + str(i), brightness, False)
            time.sleep(hold_ms / 1000)
    finally:
        blank()


try:
    with open('bench-state.json') as f:
        state = json.load(f)
    if not isinstance(state, dict):
        raise ValueError('Saved state must be a dictionary')
    show(state['name'], state['brightness'], False)
except (OSError, ValueError, KeyError, TypeError):
    blank()
    print('No valid saved pattern; outputs are off.')
print("Ready. import main; main.walk(); main.show('vancouver', 0.1)")
