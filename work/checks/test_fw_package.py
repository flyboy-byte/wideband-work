#!/usr/bin/env python3
"""F2 (docs/flashing-and-test-plan.md): the package checker must accept good images and reject each kind of bad one.

  python3 checks/test_fw_package.py

Fixtures: upstream's shipped `for_rusefi/wideband_image.h` (a release that rusEFI flashes), and the newest staged build in
`work/fw-build/` for the bootloader + app image (skipped, and said so, if none has been built). Vector faults get a fresh
CRC so only the vector check can catch them. Exit 1 on any wrong verdict.
"""
import struct, sys, tempfile, zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fw_package as fw

REPO = fw.REPO


def recrc(img):
    return img[:-4] + zlib.crc32(img[:-4]).to_bytes(4, 'big')


def set_word(img, index, value):
    return img[:index * 4] + struct.pack('<I', value) + img[index * 4 + 4:]


def verdict(data, suffix='.bin'):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / ('image' + suffix)
        (p.write_text if suffix == '.h' else p.write_bytes)(data)
        return fw.check_file(p)


def main():
    app, problems = fw.parse_header((REPO / 'for_rusefi/wideband_image.h').read_text())
    assert not problems and len(app) == fw.APP_SIZE, problems
    cases = [('upstream image as shipped (.h)', (REPO / 'for_rusefi/wideband_image.h').read_text(), '.h', True),
             ('upstream image as .bin', app, '.bin', True),
             ('one app byte flipped', app[:1000] + bytes([app[1000] ^ 0x01]) + app[1001:], '.bin', False),
             ('one padding byte changed', app[:-10] + b'\x00' + app[-9:], '.bin', False),
             ('CRC bytes in little-endian order', app[:-4] + app[-4:][::-1], '.bin', False),
             ('truncated by 4 bytes', app[:-4], '.bin', False),
             ('extended by 4 bytes', app + b'\xff' * 4, '.bin', False),
             ('linked for 0x08000000 (no bootloader offset), CRC redone',
              recrc(set_word(app, 1, (struct.unpack_from('<I', app, 4)[0] - fw.BL_SIZE))), '.bin', False),
             ('reset vector with the Thumb bit cleared, CRC redone',
              recrc(set_word(app, 1, struct.unpack_from('<I', app, 4)[0] & ~1)), '.bin', False),
             ('HardFault vector into the config page, CRC redone', recrc(set_word(app, 3, fw.CONFIG_START + 1)), '.bin', False),
             ('stack pointer outside RAM, CRC redone', recrc(set_word(app, 0, 0x20002000)), '.bin', False),
             ('header array renamed', fw.header_text(app).replace('build_wideband_image_bin', 'image'), '.h', False),
             ('header _len wrong', fw.header_text(app).replace('_len = 25600', '_len = 25596'), '.h', False)]

    staged = sorted((REPO / 'work/fw-build').glob('*/wideband_image_with_bl.bin'), key=lambda p: p.stat().st_mtime)
    if staged:
        full = staged[-1].read_bytes()
        bl = full[:fw.BL_SIZE]
        cases += [(f'staged bootloader + app ({staged[-1].parent.name})', full, '.bin', True),
                  ('bootloader + app + a config page', full + b'\xff' * fw.CONFIG_SIZE, '.bin', False),
                  ('bootloader + upstream app (both valid parts)', bl + app, '.bin', True),
                  ('bootloader padded short by 4 (app shifted)', bl[:-4] + app + b'\xff' * 4, '.bin', False),
                  ('bootloader reset vector pointing into the app', set_word(bl, 1, fw.APP_START + 0x101) + app, '.bin', False)]
    else:
        print('SKIP bootloader + app cases: no staged build (run checks/fw_package.py build)')

    wrong = 0
    # The bootloader's own isAppValid() (host-compiled), on its own: zlib catches CRC faults first in the cases above
    for name, data, good in [('isAppValid() alone: upstream image', app, True),
                             ('isAppValid() alone: CRC bytes swapped', app[:-4] + app[-4:][::-1], False),
                             ('isAppValid() alone: one byte flipped', app[:1000] + bytes([app[1000] ^ 1]) + app[1001:], False)]:
        accepted, msg = fw.bootloader_accepts(data)
        ok = accepted == good
        wrong += not ok
        print(f'{"ok  " if ok else "WRONG"} {"accept" if good else "reject"}: {name}  ({msg})')
    for name, data, suffix, good in cases:
        found = verdict(data, suffix)
        ok = (not found) == good
        wrong += not ok
        print(f'{"ok  " if ok else "WRONG"} {"accept" if good else "reject"}: {name}' +
              ('' if good or not found else f'  ({found[0]})') + ('' if ok else f'  -> {found or "accepted"}'))
    print(f'{len(cases) + 3} package cases, {wrong} wrong verdict(s)')
    return 1 if wrong else 0


if __name__ == '__main__':
    raise SystemExit(main())
