"""Low-current optical bench for Adafruit 5201 + QT Py ESP32-S3.
CircuitPython; not globe firmware. Verify 5 V / 3.3 V level shifting first.
This code has not been tested on physical hardware.
"""
import json
import board
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT

matrix = Adafruit_RGBMatrixQT(board.STEMMA_I2C())
matrix.enable = False
matrix.global_current = 8  # Register code, NOT milliamps or a measured power limit.
matrix.set_led_scaling(32)
matrix.fill(0)
matrix.enable = True
AMBER = (64, 24, 0)  # Deliberately dim; tune only after current/temperature checks.

def color(weight=1.0):
    r, g, b = [round(c * weight) for c in AMBER]
    return (r << 16) | (g << 8) | b

def pattern(choice):
    matrix.fill(0)
    if choice == "1":
        matrix.pixel(6, 4, color())
    elif choice == "2":
        matrix.pixel(4, 4, color())
        matrix.pixel(7, 4, color())  # 9 mm separation on the reference board.
    elif choice == "3":
        for y in range(9):
            for x in range(13):
                if x % 2 == 0 and y % 2 == 0:
                    matrix.pixel(x, y, color())
    elif choice == "4":
        with open("/vancouver-13x9-test-pattern.json") as source:
            data = json.load(source)
        for cell in data["rows"]:
            matrix.pixel(cell["col"], cell["row"], color(cell["coverage"]))
    elif choice == "5":
        matrix.fill(color())  # Keep the low global/scaling settings.
    elif choice != "0":
        print("Unknown choice; matrix left off.")

print("0 off; 1 center pixel; 2 separated pixels; 3 sparse grid;")
print("4 Vancouver area; 5 dim all-on; q quit. Starts dark.")
try:
    while True:
        choice = input("> ").strip()
        if choice == "q":
            break
        pattern(choice)
except (KeyboardInterrupt, EOFError):
    pass
finally:
    matrix.fill(0)
    matrix.enable = False
