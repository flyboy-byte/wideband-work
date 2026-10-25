#!/usr/bin/env python3
"""Exact piecewise state transition for two unbuffered equal RCs; no op-amp model."""
import math
R,C,F=3300.,100e-9,46875.
def matrix(t):
    z=t/(R*C); q=math.sqrt(5)/2; k=math.exp(-1.5*z)
    a=math.cosh(q*z); b=math.sinh(q*z)/q
    return [[k*(a-.5*b),k*b],[k*b,k*(a+.5*b)]]
def mv(m,x):return [sum(a*b for a,b in zip(row,x)) for row in m]
def advance(x,u,t):return [v+u for v in mv(matrix(t),[a-u for a in x])]
def solve(m,b):
    d=m[0][0]*m[1][1]-m[0][1]*m[1][0]
    return [(b[0]*m[1][1]-m[0][1]*b[1])/d,(m[0][0]*b[1]-b[0]*m[1][0])/d]
for duty in [.5,.8]:
    h=duty/F; low=(1-duty)/F; period=matrix(1/F)
    force=mv(matrix(low),advance([0,0],3,h))
    x0=solve([[1-period[0][0],-period[0][1]],[-period[1][0],1-period[1][1]]],force)
    xh=advance(x0,3,h)
    vals=[1.68*advance(x0,3,h*i/2000)[1] for i in range(2001)]
    vals += [1.68*advance(xh,0,low*i/2000)[1] for i in range(2001)]
    error=max(abs(a-b) for a,b in zip(x0,advance(xh,0,low)))
    assert error<1e-10
    print(f'duty={duty}: mean={3*duty*1.68:.9f} V, p-p={1000*(max(vals)-min(vals)):.9f} mV, periodic residual={error:.3g} V')
