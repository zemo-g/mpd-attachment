#!/opt/homebrew/bin/python3.11
"""Compare two phase2 run logs at MATCHED PHYSICAL TIME.

Different cfl_c (or any dt-affecting change) makes step counts
incomparable; the honest comparison is trajectories in t. Interpolates
run B onto run A's print times over their overlapping window and prints
side-by-side vmax/mass/ptip/mdot_out with ratios.

Usage: compare_runs_t.py <logA> <logB> [labelA labelB]
"""
import re, sys
import numpy as np

def parse(f):
    rows = []
    for ln in open(f):
        m = re.search(r"step (\d+)\s+t=([\d.e+-]+)\s+dt=([\d.e+-]+)\s+mass=([\d.e+-]+)\s+vmax=([\d.e+-]+)\s+ptip=([\d.e+-]+)\s+pwall=([\d.e+-]+).*mdot_out=([\d.e+-]+)", ln)
        if m:
            rows.append([float(m.group(i)) for i in range(1, 9)])
    a = np.array(rows)
    if a.size == 0:
        sys.exit(f"no periodic prints parsed from {f}")
    return a  # cols: step t dt mass vmax ptip pwall mdot_out

A = parse(sys.argv[1]); B = parse(sys.argv[2])
la = sys.argv[3] if len(sys.argv) > 3 else sys.argv[1]
lb = sys.argv[4] if len(sys.argv) > 4 else sys.argv[2]
t_hi = min(A[-1, 1], B[-1, 1])
Aw = A[A[:, 1] <= t_hi + 1e-12]
names = {3: "mass", 4: "vmax", 5: "ptip", 7: "mdot_out"}
print(f"A = {la}   B = {lb}   overlap t <= {t_hi:.4e} s")
print(f"{'t (s)':>11} | " + " | ".join(f"{n+'_A':>10} {n+'_B':>10} {'B/A':>6}" for n in names.values()))
for row in Aw:
    t = row[1]
    line = f"{t:11.4e} | "
    parts = []
    for c, n in names.items():
        vb = np.interp(t, B[:, 1], B[:, c])
        parts.append(f"{row[c]:10.4g} {vb:10.4g} {vb/row[c]:6.3f}")
    print(line + " | ".join(parts))
# growth-rate comparison on vmax: fit d(ln vmax)/dt on the overlap
def rate(X):
    Xw = X[X[:, 1] <= t_hi + 1e-12]
    return np.polyfit(Xw[:, 1], np.log(Xw[:, 4]), 1)[0]
ra, rb = rate(A), rate(B)
print(f"\nvmax e-folding rate: A {ra:.4g} /s   B {rb:.4g} /s   ratio B/A = {rb/ra:.3f}")
print("ratio ~1.0 => runaway independent of numerical dissipation (PHYSICAL)")
print("ratio far from 1 => diffusion-sensitive solution (NUMERICS first)")
