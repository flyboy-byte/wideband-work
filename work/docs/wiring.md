# Wiring sheet: carrier J3 and the module's SWD pads

Written 2026-10-24 for the r41 layout with the B1 fix. Use **terminal numbers and the labels printed on the bottom
silkscreen**, never reference designators. Before wiring anything into a car, check this against the board in your
hand: count the pins on the real connector, and read the silkscreen.

## J3: Molex MX120G, 12-way (the only connector to the outside)

The header on the board is **Molex 36783-1201** (MX120G, right angle, sealed, -40 to +105 C). The harness plug is
**Molex 36792-1201** (MX120G 12-circuit sealed female receptacle; Newark lists it as the mate; DOCUMENTED there).
Take its terminals and seals from Molex's MX120G application spec, AS-36783-001-001 (confirm before buying).

Pins are numbered as in the board's footprint (upstream's). 7-12 is the row nearer the board edge (the connector's
mouth side) and 1-6 the inner row; both count from the GND end (DOCUMENTED, pad positions: 1-6 at y 66.0, 7-12 at
y 62.5, edge at about 54.7). Whether Molex's moulded cavity numbers match is INFERRED (upstream built carriers with this
footprint); check the housing.

| J3 | Silkscreen (bottom) | Signal | Goes to | Wire |
| --- | --- | --- | --- | --- |
| 1 | GND (lower row) | Power and heater ground | Engine block / battery negative, its own wire, ring terminal | carries the heater current: 0.75 mm2 / 18 AWG (INFERRED) |
| 2 | 1 (under LSU 4.9) | LSU Ip | Sensor plug pin 1 | in the sensor harness |
| 3 | 3 | LSU heater - | Sensor plug pin 3 | heater current |
| 4 | 4 | LSU heater + (12 V after the board's diode) | Sensor plug pin 4 | heater current |
| 5 | **OUT** | 0-5 V output (10 AFR = 0 V, 20 AFR = 5 V; 5 V while not ready) | Receiver's 0-5 V input (Speeduino O2 input, FlashPro analog input, a gauge) | shielded or twisted with J3-7's wire |
| 6 | **12V** | Supply in, switched ignition 12 V | Fused ignition-switched 12 V | heater current; fuse 5 A (INFERRED: LSU 4.9 heater draws up to about 2 A cold, FROM MEMORY) |
| 7 | **GND** (upper row) | Output reference ground | Receiver's sensor/analog ground, and nothing else (owner C3: star at the ECU) | twisted with J3-5's wire |
| 8 | 2 | LSU Vm | Sensor plug pin 2 | |
| 9 | 5 | LSU Rtrim | Sensor plug pin 5 | |
| 10 | 6 | LSU Un | Sensor plug pin 6 | |
| 11 | H (under CAN) | CAN H | rusEFI / CAN bus, optional | twisted pair with J3-12 |
| 12 | L | CAN L | | |

- **The 120R jumper** (top side, near the screw hole) terminates CAN. Bridge it only if this is the end of a bus with no
  other terminator. Unused without a CAN bus.
- **The TEST jumper** is for bench test A1 only (1.00 / 2.50 / 4.00 V steps). Leave it open in the car. It also moves
  the CAN ID (`docs/firmware.md`).
- **J3-1 and J3-7 are the same copper on the board.** If J3-1's wire ever opens, the heater current (amps) would
  return through J3-7 and the receiver's sensor-ground pin, which is not made for that (Codex C3). J3-1 must be a
  solid crimp to the block. Optional, INFERRED: a 250-500 mA fuse in the J3-7 wire. The output's own current is under
  2 mA, so the fuse adds no measurable offset, and it opens before an ECU's sensor ground carries heater current.
- Bench test A4 measures the ground offset in the car: under 20 mV between J3-7 at the controller and the receiver's
  ground pin.

## Sensor plug: Bosch LSU 4.9

Harness-side plug **Bosch 1 928 404 669** with its terminals and seals (REPORTED: rusEFI wiki and plug-kit sellers).
**Don't cut off the sensor's own plug**: it holds the laser-trimmed calibration resistor (rusEFI wiki).

| Sensor pin | Signal | Usual Bosch wire colour (REPORTED, rusEFI wiki; check your sensor) | J3 |
| --- | --- | --- | --- |
| 1 | Ip (pump current) | red | 2 |
| 2 | Vm (virtual ground) | yellow | 8 |
| 3 | H- (heater -) | white | 3 |
| 4 | H+ (heater +) | grey | 4 |
| 5 | Rtrim | green | 9 |
| 6 | Un (Nernst) | black | 10 |

The board's silkscreen numbers under and over "LSU 4.9" are these sensor pin numbers, so silkscreen "1" at J3-2 goes
to sensor pin 1.

## SWD (first flash and trim reflash)

See `renders/module/swd-pads.png` (from `gen/swd_diagram.py`, drawn from the board files and seen from below).

- J2 on the module's underside: pad 1 = 3.3 V (target sense), 2 = SWDIO, 3 = nRESET, 4 = SWCLK, 5 = GND,
  6 = SWO (not connected). DOCUMENTED, module netlist.
- The pattern looks like Tag-Connect's ARM Cortex layout. A probe with the 10-pin 0.05" Cortex connector takes the
  **TC2030-CTX-NL**; the owner's route below uses the **TC2030-IDC-NL** instead (FROM MEMORY: confirm either cable's
  pinout against J2 before buying).
- **Owner's route (2026-10-24): HiLetgo ST-Link V2 clone + TC2030-IDC-NL + 4 male-to-female jumpers.** The clone has a
  2x5 0.1" header with its own labelled pinout (no ARM 10-pin), and the IDC-NL ends in a 6-pin 0.1" socket wired 1:1 to
  the J2 pads (FROM MEMORY: check with a meter before first use).

  | J2 pad / IDC pin | Signal | Clone pin |
  | --- | --- | --- |
  | 2 | SWDIO | SWDIO |
  | 4 | SWCLK | SWCLK |
  | 5 | GND | GND |
  | 3 | nRESET | RST (optional) |
  | 1 | 3.3 V | **not connected**: the clone's 3.3 V is a supply output, not a sense input |
  | 6 | SWO | not connected |

  Flash with stlink-tools: `st-flash write work/fw-build/<commit>/wideband_image_with_bl.bin 0x08000000`, then read back
  and compare (`st-flash read`, `docs/flashing-and-test-plan.md` step 5). No mass erase, no option bytes. Clones may
  carry remarked chips and ST's CubeProgrammer may refuse them; stlink-tools / OpenOCD usually work (FROM MEMORY).
  Alternative with voltage sense: STLINK-V3MINIE; whether the TC2030-CTX-NL plugs into its 14-pin STDC14 socket without
  an adapter is UNKNOWN.
- The three locating holes are 2 on one side and 1 on the other, so the "-NL" plug only goes on one way.
- **Flash the module before soldering it to the carrier**, while J2 is fully exposed. After that J2 sits in the
  carrier's 8.0 x 5.5 mm cutout, about 1 mm clear of the pad pattern each side. Whether the plug body fits through the
  cutout (1.6 mm board plus the header standoff) is UNKNOWN until tried. You need it for the trim reflash after A1.
- Power the board from its own supply while flashing. Pad 1 only senses the target voltage.
