#!/usr/bin/env python3
"""Inventory actual BLX sites and narrowed target sets without changing the checker."""
import subprocess,re,importlib.util,pathlib,sys
work=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('stackcheck',work/'checks/stack_estimate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=subprocess.run(['arm-none-eabi-objdump','-d','-C','--no-show-raw-insn',sys.argv[1]],capture_output=True,text=True,check=True).stdout
sites={};cur=None
for line in s.splitlines():
    q=re.match(r'^[0-9a-f]+ <(.+)>:$',line)
    if q:cur=q[1]
    if re.search(r'\bblx\s+r\d+',line):sites.setdefault(cur,[]).append(line.strip())
for caller,rows in sites.items():
    print(caller,len(rows),'site(s)', 'NARROW' if caller in m.NARROW else 'FULL SET')
    for row in rows:print(' ',row)
    if caller in m.NARROW:print(' targets:',sorted(m.NARROW[caller]))
print('TOTAL',len(sites),'callers',sum(map(len,sites.values())),'BLX sites')
