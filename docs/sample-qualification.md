# Sample A1: component and material review

**Status: prepared for supplier review and a physical experiment; not released for fabrication.** The LED manufacturer drawing, current stock, printer capability and finish compatibility are still open. There is also a solder-to-grid clearance hold described below. No supplier has confirmed these items. This document records the exact proposed choices and the evidence needed to close each item.

[Sample instructions](sample-plan.html) · [Printer request](sample-print-request.zip) · [PCB request](sample-pcb-request.zip)

## Proposed materials and finish

| Part | First-choice quote request | What must be confirmed |
|---|---|---|
| Four curved shells and two thickness coupons | **Formlabs Clear Resin V5**, untinted, fully washed/cured, same resin lot and post-processing | Printer actually uses this product; 1 mm minimum shell wall; support strategy; cure; dimensional tolerance; clarity and UV/yellowing information |
| Two cell grids | **Formlabs Black Resin V5**, fully washed/cured | Unsupported 0.4 mm walls and approximately 1.6 mm open cells survive printing and cleaning; optical opacity is a subsequent sample test |
| Cradle, three seats, magnet fit coupon | **PA12**, SLS or MJF; use the same process for seats and fit coupon | State powder product/process and dimensional tolerance; no paint or infiltration that changes fits |
| Transparent darkening experiment | **Tamiya X-19 Smoke** acrylic model paint | Current product instructions and supplier advice for the particular fully cured resin; physical coupon adhesion/transmission test |
| Thinner, only if needed | **Tamiya X-20A** acrylic thinner | Use only the product's stated method; record actual dilution; no improvised solvent substitution |
| Separate matte topcoat experiment | **Tamiya XF-86 Flat Clear** acrylic | Qualify over cured X-19 on the witness coupon before a terrain shell |

These are specific **experimental candidates**, not verified resin/paint combinations or claims that PCBWay/JLC3DP stock them. If the service cannot supply the named resin, request its exact alternative product and technical data sheet as a separate option. Keep control and coated parts on the same alternative resin and batch. Do not buy a litre of resin for this outsourced test.

Product identities, supplier availability and current application instructions still need primary-source review. The websites to use are [Formlabs](https://formlabs.com/), [Formlabs support](https://support.formlabs.com/), and [Tamiya USA](https://www.tamiyausa.com/). They are reference destinations, not evidence of a completed review.

### Finish trial before coating terrain

The new 32 × 24 mm coupon has four 8 mm strips, **1, 2, 3 and 4.75 mm thick**, with a flat underside. Order two in the same clear resin batch as the shells. Keep coupon C0 completely uncoated. On coupon C1, divide its 24 mm length into three 8 mm lanes running across all four thicknesses; label only its edge or a separate card.

1. Photograph both coupons unlit and backlit before coating. Reject oily, tacky, cracked or visibly under-cured surfaces to the printer. Use the coating maker's preparation and curing instructions; do not invent an abrasive or solvent treatment.
2. Brush one thin, even X-19 coat on C1, leaving its underside clear. Record brush, dilution, coat count, temperature and cure time. After the stated cure, photograph it at the same LED setting and exposure as C0.
3. Add one further thin X-19 coat to lanes B and C only; cure and compare. Then apply one thin XF-86 coat to lane C only, following its instructions. The three lanes now compare one smoke coat, two smoke coats, and two smoke coats plus matte clear.
4. Place the same coupon strip over the same light source at unchanged distance for each comparison. Use an opaque card mask to isolate one strip at a time; this is a material transmission comparison, not the curved fixture's leakage test.
5. After the stated cure and again after seven days, inspect for tack, clouding, cracks, delamination and handling marks. On the coupon edge only, try a gentle thumbnail rub and a repeatable low-tack tape lift. Record tape and method. This is a practical screening test, not an ASTM adhesion certification or a longevity prediction.
6. Choose the least coating that looks acceptably charcoal when off while leaving the thick strip visibly lit. Transfer that recorded recipe to one Vancouver and one Himalaya shell, exterior only. Keep the two other shells clear. Repeat the curved fixture tests before accepting the recipe.

If no lane passes both appearance and transmission, stop and change the resin/finish; a thicker opaque paint coat cannot solve that tradeoff. The witness coupon checks the worst nominal wall thickness independently of where the ten sample LEDs happen to sit under mountains.

## LED and resistor review

The first candidate remains **Kingbright APHHS1005SYCK**, ten front-side LEDs per board. Request its current manufacturer PDF from [Kingbright USA](https://www.kingbrightusa.com/), plus distributor stock/lead time from [DigiKey](https://www.digikey.com/) or [Mouser](https://www.mouser.com/). A catalog description saying “0402” is insufficient.

The saved board is electrically routed, but its LED footprint is a **generic KiCad 1005-metric LED footprint**, not proof of fit to that Kingbright part. These facts can be checked from the supplied board:

| Board fact | Value to compare against the manufacturer drawing |
|---|---|
| Fabrication body rectangle | 1.0 × 0.5 mm |
| Fit-audit body allowance | 1.0 × 0.5 × 0.5 mm; assumed, not a verified package maximum |
| Copper pad size | 0.59 × 0.64 mm each |
| Pad centers | X = −0.485 and +0.485 mm in footprint coordinates |
| Copper inner gap / total span | 0.38 / 1.56 mm |
| Electrical convention | Pad 1 = cathode/common GND; pad 2 = anode through its channel resistor |
| Placement | D1–D10 on front, rotations in `placement.csv`; manufacturer cathode mark and tape orientation must be reconciled with these rotations |

The assembler must return the package maximum dimensions, recommended land pattern, cathode marking/drawing, emission direction, wavelength/color bin, current rating, forward-voltage range, reflow profile and an in-stock sourcing option. Record PDF revision and distributor/date in `supplier-review.csv`. Do not populate an unreviewed substitute. If the land pattern differs, revise and recheck the board before ordering.

**Solder clearance hold:** the grid starts 0.10 mm above the nominal PCB face. An additional check extruded each entire LED copper pad to an **assumed 0.20 mm solder height**; the smallest side clearance to the grid was just **0.0127 mm**. That allowance is not a measured solder fillet, but it shows why the much larger LED-body clearance cannot establish manufacturability. Obtain the actual package underside/terminal drawing, assembled height, paste/fillet envelope and board/grid positioning tolerances. If solder occupies this allowance, add local underside relief to the grid and recheck the geometry and optical leakage before printing. Do not rely on a printer holding a 0.013 mm side gap or force the grid down onto solder joints. **The current sample grid remains on hold for this review/redesign.**

The resistor candidate is **Yageo RC0603FR-071KL**, 1 kohm, 1%, 0603 imperial, ten rear-side parts. Confirm its current data sheet and minimum 0.063 W rating or approve an equivalent. At an **assumed** maximum logic output of 3.465 V and minimum 990 ohms, even a shorted LED would draw at most about **3.50 mA per channel**, 35 mA for ten, and dissipate about **12.2 mW in each resistor**. This conservative resistor calculation does not verify Pico per-pin/aggregate output ratings, actual LED current, brightness, or the final matrix driver's operating point. Check the original RP2040 Pico documentation as part of the electrical review.

## Printer reply needed

Use [PCBWay 3D printing](https://www.pcbway.com/rapid-prototyping/3d-printing/) or [JLC3DP](https://jlc3dp.com/) for a capability/quote request. Use [PCBWay assembly](https://www.pcbway.com/pcb-assembly.html) or [JLCPCB](https://jlcpcb.com/) for the passive board. These are candidate services; no account submission, quote, availability check or order has occurred.

Ask for a written reply to all rows of `supplier-review.csv`, including exact material products, support placement, cleaning, cure and dimensional tolerances. **Request ±0.10 mm or better on the mating optical faces as a proposed target, not an established process capability.** The revised grid's nominal minimum shell gap is 0.349 mm. Two surfaces each displaced 0.10 mm toward each other would leave about 0.149 mm; warpage, accumulated mounting errors and resin swelling are additional. If the service cannot meet the target, return its tolerance estimate for a clearance redesign instead of forcing the fit.

Boss apertures are now 7.6 mm around nominal 6.6 mm bosses. Verify they remain open after support removal. Preserve all 0.4 mm walls and clean every cell. Magnet fit must still be checked against the supplied pocket coupon and actual magnets; nominal magnet diameter is not a press-fit specification.

## Evidence already obtained

- New baffle and stepped coupon: saved STLs each form one closed, consistently oriented solid with positive volume.
- Both curved shells: no unexpected surface intersections with the nominal assembly; independent solid intersections show no baffle overlap with other parts. Minimum modeled shell/grid gap is **0.349 mm**; the ten assumed LED bodies have at least **0.270 mm** to the grid.
- Added solder-envelope check: minimum **0.0127 mm** side gap for an assumed 0.20 mm-high envelope over each full LED copper pad. This is a **fabrication hold**, not a passed tolerance check; actual assembled dimensions are required.
- Existing passive PCB: zero saved DRC violations and zero unconnected nets; routing unchanged.
- Revised firmware: **11 behavioral cases passed in CPython and MicroPython v1.26.0 Unix**, including all ten channels, invalid pattern rejection, damaged saved settings, interrupted writes, GPIO/storage errors and an interrupted walk. GPIO and timing were mocked; the filesystem was the host's. This is not a Pico execution or flash power-cut test.

The JSON evidence is supplied in both request packs. Pending items are deliberately left blank in the supplier review sheet. A written printer reply, approved LED data sheet and material coupon results are required before describing the corresponding choices as qualified.
