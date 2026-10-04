# Manufacture the first globe sample

Build one interchangeable curved optical fixture at the final globe's scale. Keep the 305 mm diameter, 25× terrain and 50-mile patterns. This sample tests light transmission, unwanted glow, finish, print detail and fit. It does not establish complete-globe strength, power consumption, longevity or matrix-driver operation.

[Print-shop request ZIP](sample-print-request.zip) · [PCB-assembly request ZIP](sample-pcb-request.zip) · [Test plan PDF](sample-test-plan.pdf) · [Inspect the fixture in 3D](engineering.html)

![Exploded curved sample using the actual CAD](engineering-assets/engineering-prototype.png)

## What to order

Use two service requests: one for the printed parts and one for the assembled circuit board. Ask each service to review its files and quote before fabrication. No supplier has been selected, contacted or paid, and these files have not yet been physically qualified.

Examples of services to request quotes from are PCBWay, or JLC3DP for printing and JLCPCB for assembly. These are candidates, not qualified suppliers for these particular files. Their review must confirm the thin walls, clear resin and chosen LED before you place an order.

### Printed parts

The fixture footprint is approximately 56 × 48 mm. Everything is in millimetres at 100% scale. These are the same checked A0 manufacturing meshes; this plan increases sample quantities to preserve uncoated controls.

| File in the print request | Quantity | Requested material/process | Purpose |
|---|---:|---|---|
| `prototype-shell-vancouver-25x.stl` | 2 | Clear, untinted SLA/DLP resin; same batch | Keep one clear; tint the other |
| `prototype-shell-himalaya-25x.stl` | 2 | Same clear resin/process | Thicker-terrain comparison; one clear and one tinted |
| `baffle-type-02.stl` | 2 | Opaque black SLA/DLP resin | One working cell grid and one spare |
| `prototype-cradle-type-02.stl` | 1 | SLS/MJF PA12 preferred | Bench fixture; a rigid alternative can be quoted separately |
| `magnet-seat-M2-4mm.stl` | 3 | PA12, matched to the fit coupon | Magnetic shell seats |
| `magnet-fit-coupon.stl` | 1 | Same material/process as the seats | Check magnet-pocket fit before assembly |

Ask the printer to confirm the **0.4 mm baffle walls**, approximately 1.6 mm cell openings, 1 mm minimum shell wall and magnet pockets. Layer height alone does not establish dimensional accuracy. Request the actual resin product, print process, orientation, post-cure process and expected dimensional tolerance. Ask about optical clarity, yellowing/UV stability and compatibility with a transparent tint and matte clear coat.

Do not permit automatic scaling, thickening, hollowing or geometry repair that changes these features. Ask the service to flag a feature it cannot print. Agree support placement before printing: protect the smooth inner optical surface, shell seating faces, magnet pockets and baffle openings. Deliver washed and fully cured parts, with every cell cleaned, unpainted and undyed. Keep post-processing identical between the clear controls and finish samples; avoid sanding or polishing the optical surfaces without recording it.

Black appearance alone does not prove a 0.4 mm wall blocks amber light. That is part of this sample's test. Do not silently substitute ordinary opaque white resin for the shell or a thicker coarse grid for the baffle.

### Assembled optical PCB

Request the board service's minimum economical bare-board quantity, with **two boards assembled** if the quote is acceptable. One is the working board; the other helps distinguish an assembly fault from an optical problem. Do not buy a quantity of full-globe matrix boards.

The PCB request contains the routed `optical-bench-10` board, Gerbers, separate plated/nonplated drills, BOM, component placement CSV, project/library files and its saved-file validation. Specify **two layers, 1.0 mm FR4, nominal 35 µm copper, black soldermask preferred**. The ten 1005-metric/0402-imperial LEDs are on the front; ten 1 kohm 0603 resistors are on the back. Wire pads are not components to assemble.

For an automatic PCB quote, upload the enclosed `fabrication-gerbers.zip`. Upload `bom.csv` and `placement.csv` separately for assembly, and send `START-HERE-RFQ.txt` with the order-review request. For printing, upload each STL under its specified material and quantity from `print-order.csv`.

The BOM's Kingbright APHHS1005SYCK LED is a **candidate**, not a qualified final choice. Require the assembler to check the current manufacturer datasheet against the footprint, cathode/pad-1 assignment, package size, placement rotation and amber/yellow color. Ask them to identify any substitute for review before fitting it. Require continuity/short inspection and an individual LED test through the fitted resistors; an automated optical inspection alone does not prove correct light output. Keep the datasheet and inspection result with the sample.

The tiny LED/resistor assembly is outsourced. Your soldering is the eleven accessible wires between the finished board and a Pico.

### Other items

Buy one Raspberry Pi Pico **with headers**, a data-capable USB cable, fine insulated wire and ordinary soldering supplies. Use a small screw-terminal/header adapter if it makes Pico wiring easier. Also obtain:

- Twenty 4 mm diameter × 2 mm magnets: fifteen are used for the three seats and four shells, leaving five spare.
- Three M2 × 22 countersunk screws, three M2 nuts, and four adhesive rubber feet at least 2 mm thick. Confirm the screw-head fit and engagement on the printed parts.
- A removable magnet-retention material compatible with the chosen resin; qualify it on the fit coupon. Keep the seat screws serviceable.
- A caliper, basic multimeter and contact thermometer if available.
- A small amount of **transparent smoke/charcoal tint**, compatible with the cured resin, plus a compatible matte clear finish for a separate comparison. Follow the product's application/curing instructions. Ordinary opaque black paint is not the starting finish.

Use **$250 as the first-round target**, and a **$500 stop-and-review ceiling** within the overall globe budget. These are suggested spending limits, not supplier prices. Quote printing, assembly, materials and shipping separately; manufacturing minimums may dominate the cost.

## Assembly and first power

1. Photograph and label every part: Vancouver clear/tint, Himalaya clear/tint, baffle A/B. Record resin and batch. Measure the magnet coupon and inspect all optical cells under a light. Do not force a magnet or a warped shell into place.
2. With the circuit unpowered, inspect polarity, solder joints and shorts. Confirm each numbered wire pad reaches one LED anode through its 1 kohm resistor and that the cathodes share ground.
3. Solder board pads **0–9 to Pico GP0–GP9**, respectively, and board GND to Pico GND. GPIO names are not physical header-pin numbers; `firmware/wiring.csv` gives the exact header-pin mapping. Add wire strain relief at the cradle. This is a USB-powered logic-level circuit: **never apply the full globe's 12 V supply**.
4. Install RP2040 MicroPython with Thonny. Copy `firmware/main.py` and `firmware/patterns.json` from the PCB request to the Pico's root. These are the existing ten-cell bench firmware files. On the first boot the LEDs are off; after a pattern is saved, it returns on restart.
5. In Thonny's Shell run `import main`, then `main.show('walk-0', 0.1)`. Repeat through `walk-9`. Confirm ten separate emitters before adding optical parts. The resistors stay fitted for every test.
6. Install the nuts, board and three magnet seats in the cradle using the M2 × 22 screws. Fit the rubber feet. Fit the baffle without stressing the board or blocking cells; small removable retention dots at the outer edge are acceptable. Keep adhesive out of the light paths.
7. Pair and mark magnet polarities. Each shell uses three magnets and shares the fixture's three mating magnets. The seating rim at local Z=5.0 mm sets shell position; the fixture magnet face is recessed at Z=4.8 mm. The baffle must not support or push the shell outward. Test retention and removability gently.
8. Test **both clear shells before applying any finish**. If the clear shell is already too dim or creates a broad haze, investigate that before adding tint.

## A controlled finish experiment

Keep one shell of each terrain uncoated throughout. On the other pair, test a thin transparent tint first; photograph and record it after full cure. Add another coat only if necessary, recording the change. Apply matte clear only after evaluating the tint itself, then repeat the comparison. This separates the effects of resin thickness, pigment and surface finish.

Use the same PCB, baffle, LED pattern, viewing distance, room lighting and PWM setting for paired comparisons. Do not change the 50-mile pattern or enlarge the illuminated patch to make a poor material result look better. If you decide to enlarge footprints, record it as a deliberate design tradeoff.

Try these commands:

```python
main.show('walk-0', 0.1)  # one emitter; repeat walk-1 through walk-9
main.show('vancouver', 0.1)
main.show('seattle', 0.1)
main.show('both', 0.1)
main.show('all', 0.1)
main.show('off', 0)
```

Repeat the comparisons at PWM scales 0.1, 0.3 and 1.0 as needed; **1.0 means full PWM, not 1 amp or a calibrated brightness**. Keep the 1 kohm resistors in place. For an individual LED at full PWM, measuring voltage across its resistor gives current approximately as `I = V / 1000 ohms`. Record the result rather than assuming the bench matches the eventual scanned matrix driver.

Photograph unlit and lit samples in normal room lighting, then in dim conditions. Check the object by eye at approximately 25 cm and 1 m. Lock camera exposure, focus and white balance; turn off HDR/night-mode processing and avoid saturated highlights. An ordinary phone JPEG is useful for visual comparison but **not a calibrated light measurement**. Use RAW/linear image data or suitable optical instrumentation for quantitative brightness ratios, and subtract the LEDs-off background.

## What would constitute a useful pass?

These are proposed acceptance targets, not measured results or guarantees.

| Test | Evidence to record | Starting decision rule |
|---|---|---|
| Finish when off | Clear/tinted pair under normal room light | Tinted shell looks acceptably charcoal while preserving visible terrain |
| Local light | One-cell walk and the 50-mile city patterns | Warm, localized patches; no broad glow through the whole shell |
| Neighbor leakage | Single commanded cell with off-frame background removed | Target brightest adjacent uncommanded cell below 15% of the lit cell, using a linear measurement |
| Thick terrain | Swap Vancouver/Himalaya shells on the same board, comparing the same emitter at unchanged settings | Target at least 40% of the reference-region light; investigate dim ridges before considering compensation |
| Two destinations | Vancouver, Seattle, then both | Their relative positions and separation remain understandable; use a geographic reference for context |
| Fit and service | Photograph seated gaps; remove/refit at least 20 times | No flexing, sticking, cracked walls or migrating magnets; shell seats consistently |
| Stability of the sample | Run selected pattern for one hour; record current and contact temperature | No visible finish change, loosening or unexpected heating; this does not qualify the full globe's thermal limits |

The small triangular sample and its ten selected emitters cannot establish whole-globe geographic recognizability. Assess the size of the local marks now, then use a larger populated panel for that decision. The high-relief coupon samples thicker terrain; it does not necessarily put the globe's maximum 4.73 mm thickness over every tested emitter.

If the optical result only works in a dark room at the bench board's highest output, treat it as marginal until a final-driver test establishes sufficient light within the power budget. If tint blocks mountains or clear resin spreads too much light, change the material/finish or shell construction and repeat this inexpensive sample before ordering a full globe.

## The next sample after this passes

The next release should combine **one completed final-driver LED tile** with the winning shell/baffle material, plus **one full-size terrain panel and representative cage/spoke joints**. The matrix tile still needs completed routing and electrical review before it can be manufactured. That stage checks real scanned-drive brightness, current and shutdown; panel warpage and seams; retention; and joint fit/load behavior. A later populated sector checks geographic recognition, cabling and heat.

Keep the successful material/process recipe, uncoated controls, photographs, current readings and test log. Passing the small optical fixture is a decision to proceed to those tests, not approval to order all 226 matrix boards or all twenty terrain panels.
