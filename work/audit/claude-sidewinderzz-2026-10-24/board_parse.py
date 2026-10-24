# Minimal KiCad .kicad_pcb reader (no pcbnew): footprints, pads with board coordinates and nets.
# Used by this review to read the netlist and distances from board_carrier.kicad_pcb at the reviewed commit.
import re,sys,math
def parse(s):
    tok=re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')
    st=[[]]
    for m in tok.finditer(s):
        t=m.group()
        if t=='(':st.append([])
        elif t==')':x=st.pop();st[-1].append(x)
        else:st[-1].append(t[1:-1] if t[0]=='"' else t)
    return st[0][0]
def kids(n,name):return [c for c in n if isinstance(c,list) and c and c[0]==name]
def kid(n,name):
    k=kids(n,name);return k[0] if k else None
def load(p):return parse(open(p).read())
def footprints(b):
    out=[]
    for fp in kids(b,'footprint'):
        at=kid(fp,'at');x,y=float(at[1]),float(at[2]);r=float(at[3]) if len(at)>3 else 0
        layer=kid(fp,'layer')[1]
        ref=None;val=None;props={}
        for p in kids(fp,'property'):props[p[1]]=p[2]
        ref=props.get('Reference');val=props.get('Value')
        pads=[]
        for pd in kids(fp,'pad'):
            pa=kid(pd,'at');px,py=float(pa[1]),float(pa[2])
            a=math.radians(r);gx=x+px*math.cos(a)+py*math.sin(a);gy=y-px*math.sin(a)+py*math.cos(a)
            n=kid(pd,'net');pf=kid(pd,'pinfunction')
            sz=kid(pd,'size')
            pads.append(dict(num=pd[1],net=(n[2] if n and len(n)>2 else (n[1] if n else '')),x=gx,y=gy,fn=pf[1] if pf else '',size=(float(sz[1]),float(sz[2])) if sz else None,type=pd[2]))
        out.append(dict(ref=ref,val=val,x=x,y=y,rot=r,layer=layer,pads=pads,props=props,lib=fp[1]))
    return out
