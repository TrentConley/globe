# Ten-cell optical qualification PCB — A0

This is the routed, DRC-clean passive board for the type-02 curved prototype. It is **not** one of the full-globe matrix boards. Supplier review of the candidate LED datasheet, pad-1 cathode orientation, package dimensions and placement rotation remains required before assembly. No hardware has been tested.

Fabrication: 2 layers, 1.0 mm FR4, 35 µm nominal copper, ordinary lead-free finish, black soldermask preferred, no impedance control. Minimum design track 0.15 mm, copper clearance 0.25 mm, via drill 0.30 mm. Outline and three nonplated 2.2 mm mounting holes are in the Gerber/drill set. Use the actual placement CSV and embedded board footprints as the source of component centers/orientations; front and back assembly are required. D1–D10 are LEDs on the front, R1–R10 are 1 kohm resistors on the rear. P0–P9 and GND are wire pads, not placed parts.

`gerbers/` includes copper, soldermask, paste, silkscreen, board edge, and separate plated/nonplated drill files. The PDF drill maps are inspection aids. `optical-bench-10.kicad_pcb` is the checked source board; `placement.csv`, `bom.csv`, `validation.json` and the DRC JSON support assembler review. Footprints are embedded in the board. The small custom library and fp-lib-table are supplied for editing.

Each GPIO pad drives exactly one series 1 kohm resistor and one LED anode; all cathodes connect to GND. Connect pad N to Pico GPN for N=0–9 and connect common ground. Never apply 12 V. Use firmware/ten-cell-bench and the physical assembly sequence in docs/engineering-report.md. Start at low PWM; qualify finish transmission, optical leakage and mechanical fit before scaling the design.
