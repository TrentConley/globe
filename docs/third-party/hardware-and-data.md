# Hardware and geographic references

The reference Eagle schematic in `electronics/reference/adafruit-matrix.sch` is from Adafruit's IS31FL3741 PCB repository, commit `07d4cb6a19e65be56da4a96736c2335b714ff82b`: https://github.com/adafruit/Adafruit-IS31FL3741-PCB . The complete supplied README attribution and CC BY-SA 3.0 license are included beside it. The generated driver footprint and pin mapping use that reference. The globe board layout is independently generated and is not a copy of the reference PCB routing.

Standard footprints come from KiCad's footprint libraries. The installed distribution's copyright/license notices, including the board-use exception, are included as `kicad-footprints-copyright.txt`.

Natural Earth land geometry is public domain. The detailed input was retrieved from https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson on 2026-10-04; SHA-256: `1ac90796408bc6ad6911d69448485d3c4dbf2190370080368a09976e1c9f7416`. Source: https://www.naturalearthdata.com/about/terms-of-use/ . The input file is included to make the version reproducible.

Elevation uses the project's existing 20-arcminute ETOPO sample distributed with Basemap. Its source and redistribution notice are in the existing elevation-data documents. Resampling does not add higher-resolution geographic information.

IS31FL3741 register behavior was checked against Adafruit's MIT-licensed CircuitPython implementation and QMK's public register constants. The QMK source is not included or copied into the firmware. Manufacturer datasheet/current behavior, chosen LED polarity and purchased module dimensions remain physical/electrical qualification items.

Freerouting 2.4.1 was used locally for the optical bench board; binary SHA-256 `251101c3eeac22d7e7dfcf6796603279e5d1000283eb82d8f093780f7afc6aa9`. Its binary is not redistributed in the design package. https://github.com/freerouting/freerouting . The checked routed KiCad board and SES are retained, so reproducing the released prototype does not depend on rerunning the router.
