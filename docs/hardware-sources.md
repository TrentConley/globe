# Hardware evidence and references

> Earlier study: the current A0 geometry, parts and release holds are in [engineering-report.md](engineering-report.md). Use that report for fabrication planning.


Checked for the 25× terrain / 50-mile build design on 2026-10-03. Facts below distinguish verified references from unqualified procurement choices. CAD files are linked rather than redistributed.

## Assembled prototype matrix

- Product: [Adafruit 5201](https://www.adafruit.com/product/5201), IS31FL3741 13×9 RGB matrix.
- [Open hardware at 07d4cb6a19e65be56da4a96736c2335b714ff82b](https://github.com/adafruit/Adafruit-IS31FL3741-PCB/tree/07d4cb6a19e65be56da4a96736c2335b714ff82b).
- Checked README, Eagle schematic and board XML.
- Verified: 117 RGB pixels, 3 mm pitch, nominal 39 × 27 mm active cells, board outline 39 × 51.08 mm, 3.3–5 V stated supply, four I²C addresses.
- SDA/SCL pull-ups connect through R7 to VCC. A 5 V matrix needs level translation to ESP32 3.3 V pins.
- The RGB resistor network and multiplexing are not automatically suitable for a custom monochrome panel.
- The README has one “IS32FL3741” spelling; the schematic/library and product title identify IS31FL3741.
- Open hardware license: Creative Commons Attribution/Share-Alike as specified in its repository. No board CAD is included here.

## Matrix driver software

- [Adafruit C++ at 43fbdcf44e754df9ff432bfbbecc2dd65f69c6e2](https://github.com/adafruit/Adafruit_IS31FL3741/tree/43fbdcf44e754df9ff432bfbbecc2dd65f69c6e2).
- Checked source/header and qtmatrix-rgbswirl example.
- Verified interface: 351 channels, default address 0x30, global current, per-channel scaling/PWM and enable/reset.
- [CircuitPython driver](https://github.com/adafruit/Adafruit_CircuitPython_IS31FL3741) and Adafruit_RGBMatrixQT were checked for the bench utility. The class implements this board's non-linear RGB/row mapping.
- Upstream examples with current/scaling at 255 are demonstrations, not a qualified starting power configuration for this fixture.
- Direct manufacturer datasheet retrieval was blocked. Peak current, scan duty, compliance, external resistor, IC dissipation and LED pulse limits remain required custom-PCB release checks.

## Controller

- Product: [Adafruit 5426](https://www.adafruit.com/product/5426), QT Py ESP32-S3.
- [Board at 333b35f9c77338d69816e542e7c6aa4db271d432](https://github.com/adafruit/Adafruit-QT-Py-ESP32-S3-PCB/tree/333b35f9c77338d69816e542e7c6aa4db271d432).
- Verified from README and pinout: 8 MB flash, 512 KB SRAM, no PSRAM, native USB, Wi-Fi, separate I²C interfaces including QT.
- Do not draw the matrix's full LED current through the controller's regulator or signal connectors.

## Level shifting and bus expansion

- [Adafruit BSS138 level shifter, 757](https://www.adafruit.com/product/757); [open reference](https://github.com/adafruit/4-Channel-Level-Shifter-PCB).
- Verified: four BSS138 FETs, 10 kΩ pull-ups, I²C-compatible bidirectional design; account for its slower edges.
- [Adafruit TCA9548A, 2717](https://www.adafruit.com/product/2717); [open reference](https://github.com/adafruit/Adafruit-TCA9548A-I2C-Multiplexer-PCB).
- Verified: eight branches, address 0x70 configurable through 0x77.
- Bus capacitance, combined pull-ups and installed wiring require review and measurement.

## Persistence, local server and firmware updates

Checked in Espressif's official ESP-IDF repository:

- [NVS](https://github.com/espressif/esp-idf/blob/4d59230ddff16327812782151ef0afef202dc6d7/docs/en/api-reference/storage/nvs_flash.rst).
- [HTTP server](https://github.com/espressif/esp-idf/blob/4d59230ddff16327812782151ef0afef202dc6d7/docs/en/api-reference/protocols/esp_http_server.rst).
- [OTA/rollback](https://github.com/espressif/esp-idf/blob/4d59230ddff16327812782151ef0afef202dc6d7/docs/en/api-reference/system/ota.rst).

NVS documents power-interruption recovery, with the new key/value potentially lost if interrupted during its write. This supports committed records and a previous valid history; it does not certify a complete application's multi-record transaction.

## Not verified

No live inventory/quote, final resin/coating, measured optical spread, final amber LED/bin, reviewed custom PCB, full-globe thermal/stability result, or hardware execution of bench code.

Several manufacturer/shop and direct datasheet URLs were blocked by this environment's network policy. Official open repositories supplied the checked references above. Treat architectural part families as candidates until current datasheets and supplied revisions are reviewed.
