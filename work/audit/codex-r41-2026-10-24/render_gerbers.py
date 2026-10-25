"""Render actual fab ZIP using Gerbonara (independent of pcbnew).
Run with uv run --with gerbonara python .../render_gerbers.py
"""
import hashlib
import json
import subprocess
from pathlib import Path
from gerbonara import LayerStack

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
source=WORK/'out/carrier/carrier-gerbers.zip'
stack=LayerStack.open(source)
summary={'zip_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'layers':{str(k):len(v.objects) for k,v in stack.graphic_layers.items()}}
for side in ('top','bottom'):
    path=HERE/('gerber-'+side+'.svg')
    path.write_text(str(stack.to_pretty_svg(side=side,margin=1)))
    subprocess.run(['rsvg-convert','-w','1000','-o',str(path.with_suffix('.png')),str(path)],check=True)
(HERE/'gerber-render.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
