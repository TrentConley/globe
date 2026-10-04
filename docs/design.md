# Design direction: visited areas

The references establish the finish: a dark, tactile terrain globe with warm gold areas. The illumination should represent places actually visited at a regional scale. Vancouver should create a local highlight, not fill Canada. A place such as South Dakota remains dark until a nearby visit is added.

The phrase “carved through the world” describes the visual impression of accumulating explored areas. It does not require drawn routes, country fills, or physical travel-shaped engravings.

## Coverage rule

Store individual visited places. Each contributes a soft spherical footprint with an adjustable radius, initially 50 miles. Take the union of the footprints: overlap does not add brightness, list order does not affect coverage, and adding a distant destination never creates a connecting line.

A footprint is an approximate visual memory of a visited area, not a precise claim about every point within the circle. Add several places for a region explored more extensively. Close visits can merge naturally. Country borders do not participate in the coverage calculation.

The default preview clips footprints to land. The coastlines are simplified, and physical light diffusion will not reproduce every edge. The simulator also lets the user view the whole footprint, including water.

## What is permanent

Print the geography and raised terrain once. Lighted areas grow independently as the saved history changes. The shell export therefore stays identical when only the visits, footprint radius, or brightness change. There are no travel-specific recesses to become obsolete after the next trip.

The surface uses a real ETOPO-derived elevation grid, with 25× vertical exaggeration by default. Major ranges are represented in both the preview and exported shell; individual peaks are simplified by the coarse grid. See [elevation data and scale](elevation.md). At literal scale Mount Everest would be about 0.21 mm tall, so some vertical exaggeration is reasonable for a tactile object. Extra relief also changes light transmission through the shell.

## Scale and resolution

Using mean Earth radius 6,371.0088 km and globe radius 152.5 mm:

| Quantity | At globe scale |
| --- | ---: |
| 50-mile footprint radius | 1.926 mm |
| 50-mile footprint diameter | 3.852 mm |
| 200-mile footprint diameter | 15.409 mm |
| Whole-sphere area | 292,247 mm² |
| Approximate elements at 10 × 10 mm spacing | 2,922 |
| Approximate elements at 5 × 5 mm spacing | 11,690 |
| Approximate elements at 2 × 2 mm spacing | 73,062 |

The counts are area estimates, before seams and polar packing. They explain why a cheap large-LED arrangement cannot independently resolve every small footprint. The intended picture should remain satisfying when nearby visits merge, but distant unvisited regions should stay dark.

## Hardware direction

The [detailed build guide](build-guide.md) supersedes the earlier strip prototype. The 50-mile footprint is only 3.85 mm across, so the first optical test now uses a verified 3 mm-pitch preassembled matrix. The preferred full-globe investigation is a segmented translucent shell, controlled optical cells and custom preassembled amber tiles with 2–2.5 mm effective surface pitch.

The 25× terrain can add 3.73 mm of thickness above a smooth inner wall. Small smooth, Vancouver and Himalayan samples test this before production CAD. A terrain-following inner wall, tile segmentation, full wiring and power limits remain engineering work, informed by those measurements.

## Durable updates for the eventual device

An ESP32-class controller could provide a local web interface for phone/computer updates. Store canonical places and footprint preferences on its nonvolatile flash, separate from the LED layout. Export/import the history for backups and future hardware changes.

Validate uploads and retain a last-known-good file when replacing history. Write flash on edits rather than every display frame. On boot, load the history and recompute the coverage. A later bench milestone must demonstrate that adding a place and then physically disconnecting power preserves the same picture.

The current browser simulator has local storage and JSON import/export. It does not communicate with a controller or establish hardware power-loss retention.

## Gates before the full globe

1. Approve the area coverage and width in the simulator using familiar places.
2. Approve a curved material sample: dark when off, warm gold when on, recognizable regions, acceptable bleed, and a pleasing raised finish.
3. Demonstrate phone/computer updates and history recovery after disconnecting power.
4. Join several sections to test seams, mapping, wiring access, and heat.
5. Engineer the complete shell, support, power system, and repair access.
