#!/usr/bin/env python3
"""Stage and check the f0_module firmware package (docs/flashing-and-test-plan.md, F2). Never flashes anything.

  python3 checks/fw_package.py build [OUT]   build bootloader + app into OUT (default work/fw-build/<commit>), package, check
  python3 checks/fw_package.py check FILE    check a wideband_image.bin, wideband_image_with_bl.bin or wideband_image.h

The package format is upstream's (`firmware/boards/f0_module/build_wideband.sh`), reproduced here into a fresh directory:
that script deletes `firmware/build` and overwrites the tracked `for_rusefi/` files, so it is not run.
  wideband_image.bin          app only, for rusEFI's CAN updater: app padded with 0xFF to 25596 bytes + CRC32 (4 bytes,
                              big-endian, as `crc32 | xxd -r -p` writes it) = 25600 bytes, linked at 0x08001800
  wideband_image_with_bl.bin  bootloader padded to 6144 bytes + the image above = 31744 bytes from 0x08000000, for SWD;
                              stops before the 1 KiB config page at 0x08007C00
  wideband_image.h            the app image as a C array (xxd -i format), what rusEFI compiles in

Checks: exact sizes; the CRC through the bootloader's own isAppValid() (extracted from bootloader.cpp, compiled on the host
with the project's crc.cpp) and independently through zlib; vector tables (stack pointer in RAM, reset and handler vectors
odd and inside their own partition); nothing in the config page. Exit 1 if any check fails.
"""
import datetime, hashlib, json, os, re, struct, subprocess, sys, tempfile, zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FW = REPO / 'firmware'
LAYOUT = FW / 'boards/f0_module/wideband_layout.ld'
BOOTLOADER_SRC = FW / 'boards/f0_module/bootloader/bootloader.cpp'

FLASH = 0x08000000
BL_SIZE = 6 * 1024
CONFIG_SIZE = 1024
APP_START = FLASH + BL_SIZE                        # 0x08001800
APP_SIZE = 32 * 1024 - BL_SIZE - CONFIG_SIZE       # 25600, CRC in the last 4 bytes
CONFIG_START = FLASH + 32 * 1024 - CONFIG_SIZE     # 0x08007C00
RAM = (0x20000000, 0x20000000 + 6 * 1024)
VECTORS = 16 + 32                                  # Cortex-M0 core + STM32F042 interrupts
# Core slots a Cortex-M0 fetches: reset, NMI, HardFault, SVCall, PendSV, SysTick. The rest (4-10, 12, 13) are reserved on
# ARMv6-M (stm32f042x6.h IRQn_Type lists only these core exceptions); ChibiOS fills them anyway, and upstream's
# BusFault_Handler label lands there as an even address (main_hardfault_asm.S has no .type for it), harmless on the M0
USED_CORE_SLOTS = {1, 2, 3, 11, 14, 15}


def layout_matches():
    """The constants above, checked against the linker script so a layout change can't leave them stale."""
    t = LAYOUT.read_text()
    want = ['blsize = DEFINED(USE_BOOTLOADER) ? 6k : 0;',
            'appflash (rx) : org = 0x08000000 + blsize, len = 32k - blsize - 1k',
            'configflash (rx) : org = 0x08000000 + 32k - 1k, len = 1k',
            'ram0   (wx) : org = 0x20000100, len = 6k - 0x100']
    return [f'{LAYOUT.name} no longer contains "{w}": update fw_package.py' for w in want if w not in t]


def vector_problems(seg, base, size, what):
    """Vector table at the start of seg, linked at base, code allowed in [base, base + size)."""
    if len(seg) < VECTORS * 4:
        return [f'{what}: too short for a vector table']
    v = struct.unpack(f'<{VECTORS}I', seg[:VECTORS * 4])
    out = []
    if not (RAM[0] < v[0] <= RAM[1]) or v[0] % 4:
        out.append(f'{what}: initial stack pointer 0x{v[0]:08x} not a word address in RAM')
    for i, a in enumerate(v[1:], 1):
        if i < 16 and i not in USED_CORE_SLOTS:
            continue                                  # reserved on Cortex-M0
        if a == 0 and i != 1:
            continue                                  # interrupt with no handler
        if not a & 1 or not base <= a - 1 < base + size:
            out.append(f'{what}: vector {i} = 0x{a:08x} is not a Thumb address inside 0x{base:08x}-0x{base + size:08x}')
    return out


def bootloader_accepts(image):
    """Run the bootloader's own isAppValid() on the host against the image. Returns (ok, message)."""
    src = BOOTLOADER_SRC.read_text()
    a = src.index('#define SWAP_UINT32')
    b = src.index('__attribute__((noreturn))')
    body = src[a:b]
    if 'bool isAppValid()' not in body:
        return False, 'bootloader.cpp changed shape: isAppValid() not found between SWAP_UINT32 and boot_app()'
    code = ('#include <cstdint>\n#include <cstdio>\n#include <cstring>\n#include <rusefi/crc.h>\n'
            f'static uint32_t __appflash_start__[{APP_SIZE // 4}];\n' + body +
            'int main(int argc, char** argv) {\n'
            f'  FILE* f = fopen(argv[1], "rb"); if (!f) return 2;\n'
            f'  if (fread(__appflash_start__, 1, {APP_SIZE}, f) != {APP_SIZE}) return 2;\n'
            '  fclose(f); return isAppValid() ? 0 : 1;\n}\n')
    with tempfile.TemporaryDirectory(prefix='wideband-crc-') as tmp:
        cpp, exe, img = Path(tmp) / 'v.cpp', Path(tmp) / 'v', Path(tmp) / 'img.bin'
        cpp.write_text(code)
        img.write_bytes(image)
        r = subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++17', '-O1', '-w',
                            '-I', str(FW / 'libfirmware/util/include'), str(cpp),
                            str(FW / 'libfirmware/util/src/crc.cpp'), '-o', str(exe)], capture_output=True, text=True)
        if r.returncode:
            return False, 'could not compile isAppValid(): ' + r.stderr.strip().splitlines()[-1]
        rc = subprocess.run([str(exe), str(img)]).returncode
    return rc == 0, 'bootloader isAppValid() ' + ('accepts the image' if rc == 0 else 'REJECTS the image')


def app_problems(image, what='app image'):
    out = []
    if len(image) != APP_SIZE:
        return [f'{what}: {len(image)} bytes, expected {APP_SIZE}']
    stored = image[-4:]
    want = zlib.crc32(image[:-4]).to_bytes(4, 'big')
    if stored != want:
        out.append(f'{what}: CRC bytes {stored.hex()} != zlib CRC32 {want.hex()} (big-endian)')
    ok, msg = bootloader_accepts(image)
    if not ok:
        out.append(f'{what}: {msg}')
    out += vector_problems(image, APP_START, APP_SIZE - 4, what)
    return out


def with_bl_problems(data):
    if len(data) != BL_SIZE + APP_SIZE:
        extra = ' (reaches the config page)' if len(data) > BL_SIZE + APP_SIZE else ''
        return [f'combined image: {len(data)} bytes, expected {BL_SIZE + APP_SIZE}{extra}']
    bl = data[:BL_SIZE]
    out = vector_problems(bl, FLASH, BL_SIZE, 'bootloader')
    return out + app_problems(data[BL_SIZE:])


def parse_header(text):
    m = re.search(r'static const unsigned char (\w+)\[\] = \{(.*?)\};\s*unsigned int (\w+)_len = (\d+);', text, re.S)
    if not m:
        return None, ['header: not in the "static const unsigned char X[] = {...}; unsigned int X_len = N;" shape']
    name, body, lname, n = m.group(1), m.group(2), m.group(3), int(m.group(4))
    data = bytes(int(x, 16) for x in re.findall(r'0x([0-9a-fA-F]{2})', body))
    out = []
    if name != 'build_wideband_image_bin' or lname != name:
        out.append(f'header: array is named {name} / {lname}_len; rusEFI expects build_wideband_image_bin')
    if len(data) != n:
        out.append(f'header: {len(data)} bytes in the array but _len = {n}')
    return data, out


def header_text(image):
    """Same text as upstream's `xxd -i build/wideband_image.bin` with "static const " in front."""
    lines = []
    for i in range(0, len(image), 12):
        lines.append('  ' + ', '.join(f'0x{b:02x}' for b in image[i:i + 12]))
    return ('static const unsigned char build_wideband_image_bin[] = {\n' + ',\n'.join(lines) +
            f'\n}};\nunsigned int build_wideband_image_bin_len = {len(image)};\n')


def check_file(path):
    p = Path(path)
    if p.suffix == '.h':
        data, out = parse_header(p.read_text())
        return out + (app_problems(data) if data is not None else [])
    data = p.read_bytes()
    if len(data) == APP_SIZE:
        return app_problems(data)
    if len(data) >= BL_SIZE + APP_SIZE:
        return with_bl_problems(data)
    return [f'{p.name}: {len(data)} bytes is neither the app image ({APP_SIZE}) nor bootloader + app ({BL_SIZE + APP_SIZE})']


def sh(cmd, log, **kw):
    log.write(f'$ {" ".join(map(str, cmd))}\n')
    log.flush()
    r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, **kw)
    if r.returncode:
        sys.exit(f'failed: {" ".join(map(str, cmd))} (log: {log.name})')


def first_line(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()[0]
    except (OSError, IndexError):
        return 'not found'


def build(out):
    commit = subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(['git', '-C', str(REPO), 'status', '--porcelain', '--untracked-files=no', '--', 'firmware'],
                                capture_output=True, text=True).stdout.strip())
    out = Path(out) if out else REPO / 'work/fw-build' / (commit + ('-dirty' if dirty else ''))
    if out.exists() and any(out.iterdir()):
        sys.exit(f'{out} exists and is not empty: pick another directory (nothing is deleted here)')
    out.mkdir(parents=True, exist_ok=True)
    bl_dir, app_dir = (out / 'bl').resolve(), (out / 'app').resolve()
    with open(out / 'build.log', 'w') as log:
        # 1. Bootloader, padded to 6 KiB and wrapped as an object with a .bl section (build_bootloader.sh, into bl_dir)
        sh(['make', '-C', str(FW / 'boards/f0_module/bootloader'), '-j12', f'BUILDDIR={bl_dir}'], log)
        sh(['arm-none-eabi-objcopy', '-I', 'binary', '-O', 'binary', '--gap-fill', '0xFF', '--pad-to', hex(BL_SIZE),
            str(bl_dir / 'wideband_bootloader.bin'), str(bl_dir / 'wideband_bootloader.padded.bin')], log)
        sh(['arm-none-eabi-objcopy', '-I', 'binary', '-O', 'elf32-littlearm', '-B', 'arm', '--rename-section', '.data=.bl',
            'wideband_bootloader.padded.bin', 'wideband_bootloader.o'], log, cwd=bl_dir)
        # 2. App, linking that bootloader object (board.mk sets USE_BOOTLOADER = yes; ULIBS points it at our copy)
        sh(['make', '-C', str(FW), '-j12', 'BOARD=f0_module', f'BUILDDIR={app_dir}', f'ULIBS={bl_dir / "wideband_bootloader.o"}'], log)
    full = (app_dir / 'wideband.bin').read_bytes()
    bl = (bl_dir / 'wideband_bootloader.padded.bin').read_bytes()
    problems = layout_matches()
    if full[:BL_SIZE] != bl:
        problems.append('the app build does not start with the bootloader it was linked with')
    app = full[BL_SIZE:]
    if len(app) > APP_SIZE - 4:
        problems.append(f'app is {len(app)} bytes, more than the {APP_SIZE - 4} available')
    image = app + b'\xff' * (APP_SIZE - 4 - len(app))
    image += zlib.crc32(image).to_bytes(4, 'big')
    (out / 'wideband_image.bin').write_bytes(image)
    (out / 'wideband_image_with_bl.bin').write_bytes(bl + image)
    (out / 'wideband_image.h').write_text(header_text(image))
    for name in ('wideband_image.bin', 'wideband_image_with_bl.bin', 'wideband_image.h'):
        problems += [f'{name}: {p}' for p in check_file(out / name)]
    manifest = {
        'built': datetime.datetime.now().isoformat(timespec='seconds'),
        'board': 'f0_module', 'commit': commit, 'firmware_tree_dirty': dirty,
        'tools': {'gcc': first_line(['arm-none-eabi-gcc', '--version']), 'objcopy': first_line(['arm-none-eabi-objcopy', '--version']),
                  'make': first_line(['make', '--version']), 'host_cxx': first_line([os.environ.get('CXX', 'g++'), '--version'])},
        'flash_map': {'bootloader': f'0x{FLASH:08x}-0x{APP_START - 1:08x}', 'app': f'0x{APP_START:08x}-0x{APP_START + APP_SIZE - 5:08x}',
                      'crc': f'0x{APP_START + APP_SIZE - 4:08x}-0x{APP_START + APP_SIZE - 1:08x}',
                      'config (never in a package)': f'0x{CONFIG_START:08x}-0x{FLASH + 32 * 1024 - 1:08x}'},
        'app_bytes_used': len(app), 'app_bytes_free': APP_SIZE - 4 - len(app),
        'crc32_big_endian': image[-4:].hex(),
        'files': {n: {'bytes': (out / n).stat().st_size, 'sha256': hashlib.sha256((out / n).read_bytes()).hexdigest()}
                  for n in ('wideband_image.bin', 'wideband_image_with_bl.bin', 'wideband_image.h')},
        'checks': problems or 'all passed',
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(f'package in {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: app {len(app)} B used, '
          f'{APP_SIZE - 4 - len(app)} B free, CRC {image[-4:].hex()}')
    return problems


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('build', 'check'):
        sys.exit(__doc__)
    if sys.argv[1] == 'build':
        problems = build(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        if len(sys.argv) < 3:
            sys.exit(__doc__)
        problems = layout_matches() + check_file(sys.argv[2])
    for p in problems:
        print('FAIL', p)
    print('package check: ' + ('passed' if not problems else f'{len(problems)} problem(s)'))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
