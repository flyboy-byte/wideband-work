"""Reject simulator failures even if ngspice returns finite zero measurements."""
import re
def reached_window(output,stop_seconds):
    if re.search(r'run simulation\(s\) aborted|doAnalyses:.*Timestep too small|fatal error',output,re.I):return False
    m=re.search(r'^vout\s*=\s*\S+\s+from=\s*\S+\s+to=\s*(\S+)',output,re.M)
    return bool(m and float(m.group(1))>=stop_seconds*(1-1e-6))
