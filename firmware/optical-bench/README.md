# Optical bench utility

This manually selected pattern utility targets Adafruit 5201 and QT Py ESP32-S3 5426. It is not the final Wi-Fi firmware and has not been tested on hardware.

1. Verify the build guide wiring, including the bidirectional I²C level shifter for a 5 V matrix. USB controller and external matrix power positives remain separate, with a common ground.
2. Install a stable CircuitPython release matching the exact controller. Install the matching Adafruit bundle's adafruit_is31fl3741, adafruit_bus_device, and adafruit_register libraries into CIRCUITPY/lib.
3. Copy code.py and vancouver-13x9-test-pattern.json to the root of CIRCUITPY.
4. Open its USB serial console. The program starts dark and waits for a numbered choice.
5. Record supply current, gaps, finish and temperature for each low-current pattern.

Startup current/scaling values are register codes, not calibrated milliamps or a hardware safety limit. They may be too dim through a thick coating. Increase only after electrical/thermal checks. Do not start with an upstream rainbow example that sets every current control to maximum.

The JSON pattern averages the land-clipped 50-mile footprint over each 3 mm cell. It is not simulated diffusion. Verify row direction and rotation against the physical board before aligning geography. Pattern 2 has 9 mm source separation; the guide's 8 mm footprint separation is a separate test for a finer tile.

Python syntax and data bounds can be checked without a board. Optical appearance, current, GPIO/I²C operation, startup behavior and fault handling require hardware tests.
