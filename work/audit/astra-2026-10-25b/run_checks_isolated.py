"""Run canonical reviewer mode and verify its promised protected outputs stay unchanged."""
import hashlib,json,subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
work=here.parents[1]
def snapshot():
    files=[work/'STATE.md',work/'checks/last_run.json']
    files+=sorted((work/'checks/out').rglob('*'))
    return {str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else 'MISSING'
            for p in files if not p.is_dir()}
before=snapshot()
result=subprocess.run(['python3','checks/run_all.py','--report',str(here)],cwd=work)
after=snapshot()
out={'before':before,'after':after,'unchanged':before==after,'checks_returncode':result.returncode}
(here/'TK5-isolation.json').write_text(json.dumps(out,indent=2)+'\n')
print('Reviewer-mode protected STATE/last_run/checks-out unchanged:',before==after)
raise SystemExit(result.returncode or int(before!=after))
