"""Reproducible illustrative bounds, NOT a nonlinear damaged-device model."""
import pcbnew
from pathlib import Path
root=Path(__file__).resolve().parents[3]
for name,path in [('carrier','hardware/board_carrier/board_carrier.kicad_pcb'),('module','hardware/board_module/wideband_controller.kicad_pcb')]:
    b=pcbnew.LoadBoard(str(root/path))
    print(name,'rail-connected active parts:')
    for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
        if f.GetReference().startswith('U'):
            pins=[(p.GetNumber(),p.GetNetname()) for p in f.Pads() if p.GetNetname() in ('+5V','+3V3','/VOP12')]
            if pins: print(f.GetReference(),f.GetValue(),pins)
print('Assume diode0.6V. Rail voltage below is constant-load illustration only:')
for load_ma in (0,5,10,13.6):
    rail=12-0.6-470*load_ma/1000
    print(f'load{load_ma:g}mA -> rail{rail:.3f}V (not valid after device limits exceeded)')
base=5+.4+.75+2*.042+.001
print(f'Typical illustrative subtotal excluding MCU/IO/LED/ADC/buffer:{base:.3f}mA')
print(f'With ST illustrative3.4..20.7mA MCU states:{base+3.4:.3f}..{base+20.7:.3f}mA, NOT bounds')
for r in (470,2200):
    print(f'R11={r}: 12V injection at held5V={(12-5-.6)/r*1000:.3f}mA;')
    print(f'  5V into4.7k requires OA={5+(330+r)*5/4700:.3f}V before supply headroom')
