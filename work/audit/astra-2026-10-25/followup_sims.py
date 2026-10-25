#!/usr/bin/env python3
import pathlib,subprocess
here=pathlib.Path(__file__).resolve().parent
for label,cmd in [('TK6-extra-fixed',['python3','audit/astra-2026-10-25/analog_extra.py','TK6b']),('TK7-delayed',['python3','audit/astra-2026-10-25/stability_current.py'])]:
    subprocess.run(['python3',str(here/'capture.py'),label,*cmd],check=False)
