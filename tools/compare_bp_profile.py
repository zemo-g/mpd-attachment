#!/opt/homebrew/bin/python3.11
"""Compare the solver's backplate pressure profile against the Cory-based
parabola (program.md eq set): p(r, z0) = b - a r^2 with p(r_ch) from Cory's
fit and p(r_c) from the phase-1b inference (ln_ch variant).

Usage: compare_bp_profile.py [J_amps]  (default 8000)
Reads out/phase2_bp_profile.csv, prints a comparison table + rms.
"""
import csv, math, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = float(sys.argv[1]) if len(sys.argv) > 1 else 8000.0

r_c, r_ch = 0.0095, 0.064
p_rch = 6.5e-4 * J ** 1.5

# phase-1b inferred p(r_c, z0), lnch variant, from the fig1 measured points
# (interpolate the semi_decomposition output if present)
p_rc = None
semi = os.path.join(ROOT, "out", "semi_decomposition.csv")
if os.path.exists(semi):
    pts = []
    with open(semi) as f:
        for row in csv.DictReader(f):
            pts.append((float(row["J_A"]), float(row["p_rc_lnch"])))
    pts.sort()
    for (j0, p0), (j1, p1) in zip(pts, pts[1:]):
        if j0 <= J <= j1:
            p_rc = p0 + (p1 - p0) * (J - j0) / (j1 - j0)
            break
if p_rc is None:
    p_rc = 1600.0  # fig-4 scale fallback
a = (p_rc - p_rch) / (r_ch ** 2 - r_c ** 2)
b = p_rc + a * r_c ** 2

rows = []
with open(os.path.join(ROOT, "out", "phase2_bp_profile.csv")) as f:
    for row in csv.DictReader(f):
        rows.append((float(row["r_m"]), float(row["p_Pa"])))

print(f"J = {J:.0f} A   Cory p(r_ch) = {p_rch:.0f}   inferred p(r_c) = {p_rc:.0f}")
print(f"parabola: p = {b:.0f} - {a:.3e} r^2")
print(f"{'r (cm)':>8} {'solver':>10} {'parabola':>10} {'ratio':>7}")
ss, n = 0.0, 0
for r, p in rows:
    ref = b - a * r * r
    if r < 0.012 or abs(r - 0.032) < 0.002 or r > 0.055:
        print(f"{100*r:8.2f} {p:10.1f} {ref:10.1f} {p/ref:7.2f}")
    ss += (p / ref - 1.0) ** 2
    n += 1
print(f"rms relative deviation over {n} radii: {math.sqrt(ss/n):.3f}")
