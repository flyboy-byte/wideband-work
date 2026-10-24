#!/usr/bin/env python3
"""Read-only regression probe: geometry metrics must not depend on track-list order.

Exit 1 means the existing layout checker is order-dependent, not that the PCB failed.
Does not save or modify the PCB. Runs the checker source in memory.
"""
import contextlib
import io
from pathlib import Path


def main():
    path = Path(__file__).resolve().with_name('layout_review.py')
    source = path.read_text()
    marker = 'by_net = {}'
    if source.count(marker) != 1:
        raise SystemExit('Checker changed; update this probe explicitly.')
    results = {}
    for name, insertion in [('original', ''), ('reverse', 'tracks.reverse()'),
                            ('sorted', 'tracks.sort(key=lambda t: (t.GetStart().x, t.GetStart().y))')]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                exec(compile(source.replace(marker, insertion + '\n' + marker), str(path), 'exec'),
                     {'__file__': str(path), '__name__': '__main__'})
            except SystemExit as exc:
                if exc.code not in (None, 0, 1):
                    raise
        results[name] = [line for line in output.getvalue().splitlines() if '% over GND' in line]
        if not results[name]:
            raise SystemExit('No return-path measurements; probe is inconclusive.')
        print(name + '\n' + '\n'.join(results[name]))
    differs = any(value != results['original'] for value in results.values())
    print('FAIL: track-order-dependent metrics' if differs else 'PASS: tested orders agree')
    return int(differs)


if __name__ == '__main__':
    raise SystemExit(main())
