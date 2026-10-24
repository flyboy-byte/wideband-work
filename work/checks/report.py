#!/usr/bin/env python3
"""Build report/index.html: one self-contained page (checks, renders, open-item tests) for the owner's phone.

    python3 checks/report.py                 reads checks/last_run.json, report/tests.json, renders/<REV>/*.png

Run after checks/run_all.py. The page is then published (or republished to the same URL) with the Artifact tool;
the URL goes in STATE.md under "Review pages". Images are downscaled to JPEG and embedded, so the page needs no hosting.
"""
import base64, html, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '..')
REV = os.environ.get('REV', 'carrier-f')


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
           .replace('{{TOP}}', fig('top.png', 'Top view, 3D render (KiCad 10), r41: upstream carrier grown 15 mm (40.0 x 51.5 mm, 1.57 x 2.03 in); the analog stage, both jumpers and the M3 holes in the new strip.', 1000))
           .replace('{{BOTTOM}}', fig('bottom.png', 'Bottom view (mirrored), r41: tracks only in the strip, copper-free rings around the holes.', 1000))
           .replace('{{ISO}}', fig('iso-front.png', 'Angled, perspective (r41): the new strip in front, the sensor connector behind.', 1000)
                    + fig('iso-back.png', 'From the connector end: the stage and the module footprint.', 1000)
                    + fig('iso-bottom.png', 'Underneath: the pad labels (AOUT, GND, CAN, LSU pins) and the copper-free rings around the M3 holes.', 1000))
           .replace('{{ZOOM_CUR}}', fig('../carrier-e/bottom.png', 'Before (r36): the stage on the bottom of the strip.', 800))
           .replace('{{ZOOM_WHATIF}}', fig('top.png', 'After (r41): the stage on the top, one-sided assembly.', 800)))
    os.makedirs(os.path.join(WORK, 'report'), exist_ok=True)
    open(os.path.join(WORK, 'report', 'index.html'), 'w').write(out)
    print('report/index.html', len(out) // 1024, 'KB')


if __name__ == '__main__':
    main()
