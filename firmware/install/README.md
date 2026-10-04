# Pi installation and commissioning — A0, hardware qualification pending

Start with the ten-cell USB Pico test. The full sector firmware and host have been tested with mocks and simulated serial sectors, not physical matrix boards. Do not energize the unfinished matrix candidates.

## Desktop software simulation

From the source/package root, install `firmware/requirements-host.txt` in a virtual environment, then run:

```sh
PYTHONPATH=firmware python3 -m globe_host.server --simulate --data /tmp/globe-demo --pixel-map engineering/release/pixel-map.npz --manifest engineering/release/pixel-map.json --host 127.0.0.1 --port 8081
```

Open http://127.0.0.1:8081. Read the key locally from `/tmp/globe-demo/device-key.txt` and enter it in the page. Add a named latitude/longitude, save, and export a backup. Restart with the same data path to check persistence. Simulation sends the real packet format through twenty software sector models; it does not operate hardware. Do not use a temporary data path on the finished device.

## Raspberry Pi Zero 2 W

Use current Raspberry Pi OS Lite 64-bit, configure Wi-Fi and hostname `travel-globe`, and install an endurance SD card. Copy the package to `/opt/travel-globe`, retaining its directory structure. These are provisioning instructions to run on the Pi, not commands run in the cloud:

```sh
sudo apt update
sudo apt install python3-venv python3-lgpio python3-gpiozero i2c-tools
sudo raspi-config nonint do_i2c 0
sudo useradd --system --create-home --user-group --groups i2c,gpio,dialout globe
sudo install -d -o globe -g globe -m 0700 /var/lib/travel-globe
sudo python3 -m venv --system-site-packages /opt/travel-globe/.venv
sudo /opt/travel-globe/.venv/bin/pip install -r /opt/travel-globe/firmware/requirements-host.txt
```

Aarch64 wheels for NumPy/SciPy and OS GPIO packages are required; installation on this Pi model is not yet verified. Use a named USB RS-485 device from `/dev/serial/by-id/`; do not assume `/dev/ttyUSB0` remains stable. Make `/etc/travel-globe.env` contain one line with the actual path:

```
GLOBE_SERIAL=/dev/serial/by-id/REPLACE_WITH_YOUR_ADAPTER
```

Keep the relay open and disconnect the sector power outputs during first bring-up. Pi I²C uses GPIO2/SDA and GPIO3/SCL (header pins 3/5). FRAM is 0x50, INA260 is 0x40; both use 3.3 V logic and common ground. Confirm the exact breakout supply/pull-up wiring. The INA260 senses **before the normally-open relay**, so voltage can be checked while the load is disconnected. GPIO17 is header pin 11 and drives only the relay transistor, never the coil directly. See the wiring drawing.

Test sensor identity, relay off/on behavior and fault shutdown on a current-limited supply before connecting one qualified sector. The relay uses a 100 kohm external transistor-base pull-down; sector shutdown and RS-485 DE also need external pull-downs. A process death or OS hang is not a certified hardware watchdog: prove physical behavior, and add an independent watchdog if commissioning finds that the relay can stay on. Branch fuses and local PTCs do not depend on Python.

After hardware qualification, install the unit:

```sh
sudo install -m 0644 /opt/travel-globe/firmware/install/globe.service /etc/systemd/system/globe.service
sudo systemctl daemon-reload
sudo systemctl enable --now globe.service
sudo systemctl status globe.service
```

Use `journalctl -u globe.service` for faults. The service does not automatically restart after a failed startup or an interlock trip. Inspect and correct the cause, then `sudo systemctl restart globe.service`. Read the device key locally with sudo from `/var/lib/travel-globe/device-key.txt`. Do not paste it into public issues or the GitHub viewer.

Open `http://travel-globe.local:8081` on the same trusted home network, or use the Pi's LAN IP. The A0 service uses HTTP and a device key; it is not an Internet-facing service. No port forwarding is required. Export the travel JSON after changes. The public GitHub Pages site visualizes the design and does not synchronize with the Pi automatically.

## Sector Pico deployment

Install a current RP2040 MicroPython release. Keep tile harnesses disconnected during USB flashing. Copy these files onto each Pico with Thonny:

- `firmware/common/protocol.py` → `/protocol.py`
- `firmware/sector/state.py`, `is31fl3741.py`, `main.py` → files at the device root
- The matching `firmware/config/sector-NN/sector.json` → `/sector.json`

Label the physical Pico S00 through S19 and verify its map SHA against `engineering/release/pixel-map.json`. The local `tiles` values are 0–15 within that sector, not global 0–319 tile IDs. Start with current code 4. Do not increase it by interpreting the code as milliamps.

Wire GP0/1 to mux SDA/SCL, GP14 to reset, GP10–13 to downstream shutdown, GP4/5 to transceiver DI/RO, GP6 to joined DE and /RE, GP15 to the single local DS18B20. Ground TCA A0/A1/A2. Add 10 kohm reset pull-up, 10 kohm shutdown/DE pull-downs, one upstream I²C pull-up pair and one 2.2 kohm pair per populated downstream branch; account for existing breakout resistors. DS18B20 uses three-wire powered mode and a 4.7 kohm data pull-up. See the schedules for tile addresses and cabling.

The watchdog, local temperature interlock and 60-second host timeout must be tested on real hardware. At startup, valid temperature is required before accepting a frame. Check the matrix IC's behavior when SDB is low and whether I²C remains accessible; revise/qualify the driver sequence against the current datasheet before connecting all tiles.

## Backups and updates

Use the phone UI's JSON export, saved separately from the Pi. SQLite is the named travel history; FRAM is a compact coordinate/radius/brightness recovery copy. Names are lost if recovery relies only on FRAM. Before software or map updates, export, stop the service, preserve the entire data directory, and update the host map and all sector configurations together. Changing the map is a coordinated maintenance operation, not a routine new-destination update.
