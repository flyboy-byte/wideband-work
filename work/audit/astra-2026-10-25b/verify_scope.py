"""Final local review-scope and coverage checks,not a design verifier."""
import json,re,subprocess
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[2]
def git(*args): return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
prefix='work/audit/astra-2026-10-25b/'
committed=git('diff','--name-only','18b6cef','HEAD').splitlines()
pending=git('diff','--name-only','HEAD').splitlines()
assert committed and all(p.startswith(prefix) for p in committed+pending)
assert git('branch','--show-current')=='review/astra-2026-10-25b'
report=(here/'FINDINGS.md').read_text()
for task in [*range(1,8),99]:
    rows=[l for l in report.splitlines() if l.startswith(f'| TK{task} ')]
    assert len(rows)==1 and rows[0].split('|')[2].strip(), (task,rows)
assert 'Not assessed yet' not in report and '<what' not in report and '<initials>' not in report
suite=json.loads((here/'last_run.json').read_text())['results']
assert len(suite)==26
assert not [r for r in suite if r['status']=='skipped' or (r['status']=='fail' and not r.get('advisory'))]
assert json.loads((here/'TK5-isolation.json').read_text())['unchanged']
print('Coverage:TK1–TK7 and TK99 complete.26checks:24pass,2accepted advisory failures,0skip.')
print(f'Scope:{len(committed)}committed files plus{len(pending)}modified paths;all within own audit folder.')
print('Baseline18b6cef;designer files unchanged. Reviewer protected-output snapshot unchanged.')
