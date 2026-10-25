#!/usr/bin/env python3
"""Run only as-built topology E from the reviewed wrapper, retaining source hash."""
import pathlib,subprocess,hashlib
p=pathlib.Path(__file__).resolve().parents[2]/'sim/stability.sh'
s=p.read_text();prefix=s.split('for c in 1p 1n 10n 47n; do run A')[0]
assert prefix!=s
print('SOURCE SHA256',hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)
script=prefix.replace('cd "$(dirname "$0")"','cd '+str(p.parent))
script=script.replace('400u','3m').replace('300u','2.8m').replace('395u','2.99m').replace('1.0m','5m').replace('1.2m','6m').replace('400e-6','3e-3')
script+='\nfor c in 1p 1n 10n 47n 100n; do run E $c 1n 470; done\n[ "$FAILED" -eq 0 ]\n'
raise SystemExit(subprocess.run(['bash','-s'],input=script,text=True).returncode)
