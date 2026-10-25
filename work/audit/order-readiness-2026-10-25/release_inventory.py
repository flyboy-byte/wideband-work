"""Independent checks of the frozen release; never modifies design/release files."""
import hashlib, json, re, subprocess, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO / 'work'
FAB = WORK / 'fab/flyboy-o2-v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def command(*args):
    p = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    if p.returncode: raise RuntimeError(p.stdout+p.stderr)
    return p.stdout
def norm(s):
    # Ignore timestamp/software comment metadata only; retain all plot/drill commands.
    return '\n'.join(l for l in s.splitlines() if not any(x in l for x in
        ('CreationDate', 'GenerationSoftware', 'G04 Created by', '; Created by', '; DRILL file')))

manifest=json.loads((FAB/'RELEASE.json').read_text())
assert len(manifest['files']) == 8
hashes={n:sha(FAB/n) for n in manifest['files']}
for n,h in hashes.items():
    assert h.startswith(manifest['files'][n]), n
    print('HASH OK', n, h)
(HERE/'release-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
bad=[r['name'] for r in manifest['checks'] if r['status']!='pass' and not r.get('advisory')]
assert not bad, bad
for row in manifest['checks']:
    for path,h in row['files'].items():
        p=WORK/path
        if not p.exists():
            equivalent=FAB/p.name
            if equivalent.exists(): p=equivalent
            else:
                print('RECORDED BUILD ARTIFACT NOT AVAILABLE in clean worktree:',path)
                continue
        assert sha(p).startswith(h), path
print('Release recorded checks:',len(manifest['checks']),'nonadvisory failures:',len(bad))
for base in (manifest['commit'], '18b6cef'):
    changed=command('git','diff','--name-only',base,'HEAD','--','hardware','firmware','work/gen')
    assert not changed.strip(), changed
    print('No hardware/firmware/generator change since',base)

with tempfile.TemporaryDirectory(prefix='wb-order-gerbers-') as td:
    pcb=REPO/'hardware/board_carrier/board_carrier.kicad_pcb'
    command('kicad-cli','pcb','export','gerbers','--layers',
        'F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','-o',td+'/',str(pcb))
    command('kicad-cli','pcb','export','drill','--format','excellon','--excellon-separate-th',
        '--excellon-units','mm','-o',td+'/',str(pcb))
    with zipfile.ZipFile(FAB/'carrier-gerbers.zip') as z:
        assert len(z.namelist())==12
        for n in z.namelist():
            if n.endswith('.gbrjob'): continue
            assert norm(z.read(n).decode())==norm((Path(td)/n).read_text()), n
            print('CARRIER LAYER/DRILL IDENTICAL',n)
upstream=REPO/'hardware/board_module/export/rev C/GERBER-wideband_controller.zip'
assert sha(upstream)==sha(FAB/'module-gerbers.zip')
print('MODULE archive byte-identical to committed upstream rev C',sha(upstream))
print('NOTE: archive identity alone does not prove all module geometry matches current PCB; checked separately.')
print('Release inventory: PASS')
