#!/usr/bin/env python3
"""Build report/index.html: one self-contained page (checks, renders, open-item tests) for the owner's phone.

    python3 checks/report.py                 reads checks/last_run.json, report/tests.json, renders/<REV>/*.png

Run after checks/run_all.py. The page is then published (or republished to the same URL) with the Artifact tool;
the URL goes in STATE.md under "Review pages". Images are downscaled to JPEG and embedded, so the page needs no hosting.
"""
import base64, html, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '..')
REV = os.environ.get('REV', 'carrier-d')


def img(name, width=1100):
    p = os.path.join(WORK, 'renders', REV, name)
    if not os.path.exists(p):
        return ''
    jpg = subprocess.run(['magick', p, '-resize', f'{width}x', '-quality', '82', 'jpg:-'], capture_output=True, check=True).stdout
    return 'data:image/jpeg;base64,' + base64.b64encode(jpg).decode()


def fig(name, cap, width=1100):
    src = img(name, width)
    return f'<figure><img src="{src}" alt="{html.escape(cap)}" loading="lazy"><figcaption>{html.escape(cap)}</figcaption></figure>' if src else ''


def main():
    run = json.load(open(os.path.join(WORK, 'checks', 'last_run.json')))
    tests = json.load(open(os.path.join(WORK, 'report', 'tests.json')))
    rows = ''.join(
        f'<tr><td><span class="pill {r["status"]}">{r["status"].upper()}</span></td><td>{html.escape(r["name"])}</td>'
        f'<td class="sum">{html.escape(r["summary"].split(" (report")[0])}</td></tr>' for r in run['results'])
    trows = ''.join(
        f'<tr><td class="id">{t["id"]}</td><td>{html.escape(t["what"])}</td><td><span class="pill {t["state"]}">{t["state"].upper()}</span></td>'
        f'<td class="sum">{html.escape(t["result"])}</td></tr>' for t in tests['tests'])
    tpl = open(os.path.join(HERE, 'report_template.html')).read()
    out = (tpl.replace('{{DATE}}', run['date']).replace('{{HEAD}}', run['git_head']).replace('{{CHECKS}}', rows)
           .replace('{{TESTS}}', trows).replace('{{HEADLINE}}', html.escape(tests['headline']))
           .replace('{{TOP}}', fig('top.png', 'Top view, 3D render (KiCad 10). Upstream carrier plus our parts on the bottom.', 1000))
           .replace('{{BOTTOM}}', fig('bottom.png', 'Bottom view: the analog output stage (U6 op-amp, D3/D4 clamps, R8 output resistor).', 1000))
           .replace('{{ZOOM_CUR}}', fig('zoom-top-before.png', 'Before: D3 pin 1 reaches only a +5V via (blue). Nothing links it to the +5V net 4.2 mm away.', 800))
           .replace('{{ZOOM_WHATIF}}', fig('zoom-top-fixed.png', 'After: a 0.25 mm track to U2 pin 3, a ground via for C1 pin 2 (lower right), C2 pin 2 solid in the pour.', 800)))
    os.makedirs(os.path.join(WORK, 'report'), exist_ok=True)
    open(os.path.join(WORK, 'report', 'index.html'), 'w').write(out)
    print('report/index.html', len(out) // 1024, 'KB')


if __name__ == '__main__':
    main()
