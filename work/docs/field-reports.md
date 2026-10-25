# Field reports from other builders

What other people hit building upstream's controller, so our first run doesn't repeat it. Source: the designer's
thread, rusEFI forum t=1856, "Wideband Controller: Fully Custom, no ASIC!", 224 posts, 2020-10-30 to 2025-02-24, read
2026-10-25 (REPORTED: forum posts, not checked by us). Rev C is never named there.

| Report (date, poster) | What it means for us | Covered by |
| --- | --- | --- |
| "NOT STANDALONE: REQUIRES VOLTAGE DATA INPUT VIA CAN" (AndreyB, 2023-11, top post) | Our firmware starts the heater without CAN: battery state Unknown -> internal supply, ramp at about 10.5 s on f0 (host tests). It assumes 13 V without CAN (`docs/firmware.md`, D11) | host test `test_heater_update.cpp`; bench H-tests. First real check is on the bench |
| Heater would not start until rusEFI's CAN broadcast was enabled (stefanst, 2021-12) | Same question, older firmware. A Speeduino on the bus sends no rusEFI frames, so we stay in standalone | as above |
| Overheat LED with and without sensor: a 62k fitted where 62R was needed, R14 on their board (diegort5, 2025-02) | Our module R10 (pump shunt, 61.9R) is substituted: C2087389 is ERA-3AEB61R9V, 61.9 ohm (checked at JLC, 2026-10-25) | `module-bom.csv` line 16 |
| Free air read about 10 AFR, butane 29: Ip and Rtrim swapped? (pkagiantas, 2023-12) | A wiring swap reads backwards. Check the LSU plug pins against `docs/wiring.md` by meter before first heat | bench W1 |
| Heater faults traced to cables and connectors (md_sanci, benassi124, 2024-03); heater wire 18 AWG | Heater current is up to about 2 A cold: crimp and pull-test the heater pins | wiring |
| Heater overshoot (mck1117, 2021-07); overheat shutdown after 3-4 min (NickZ, 2023-07, unresolved) | First heats in free air, watch the LED and the output; stop on an overheat | bench H-tests |
| Raw firmware fails "Firmware integrity check fail": the image needs the CRC (mck1117, 2022-05) | We flash the package from `checks/fw_package.py` (bootloader + app with CRC) | `fw_package.py check` |
| ST-Link clone worked with STM32CubeProgrammer, not ST-Link Utility 4.5; better with USB power (AndreyB, 2021-05); F0 held in reset while flashing (md_sanci, 2024-03, unresolved) | Use CubeProgrammer; if it won't connect, try "connect under reset" | flashing doc |
| Two hand-soldered boards had GND shorted to VCC (AndreyB, 2021-11) | Meter GND to +5V and to 3V3 before first power | bench A1 |
