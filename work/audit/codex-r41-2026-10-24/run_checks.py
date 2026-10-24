"""Run the configured checks without replacing the designer's STATE/last_run files."""
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
results = []
for item in json.loads((WORK / 'checks/checks.json').read_text()):
    start = time.monotonic()
    try:
        p = subprocess.run(item['cmd'], cwd=WORK, capture_output=True, text=True, timeout=240)
        code, output = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        code, output = 124, 'TIMEOUT after 240 seconds; not a pass'
    results.append(dict(name=item['name'], command=item['cmd'], returncode=code,
                        advisory=item.get('advisory'), seconds=round(time.monotonic()-start, 2), output=output))
    (HERE / 'checks.json').write_text(json.dumps(results, indent=2) + '\n')
    print(item['name'], code, flush=True)
