#!/usr/bin/env python3
"""Ionization-fraction map from out/phase2_state.csv (rho, p_Pa columns).

Inverts p = (1+alpha) n k T with Saha alpha(n, T) for T by bisection
(monotone in T), then reports alpha statistics and renders a map.
Constants mirror the eos_* block in rail/mpd_solver.rail exactly.

Usage: alpha_map.py <tag>   -> out/img/phase2_<tag>_alpha.png
"""
import csv, math, os, sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K_B = 1.380649e-23
M_AR = 6.633e-26
CHI_K = 182882.69143808
SAHA_C = 2.8976196474863585e22


def alpha_of(n, t):
    if t < 2500.0:
        return 0.0
    s = SAHA_C * t * math.sqrt(t) * math.exp(-CHI_K / t)
    return 2.0 / (1.0 + math.sqrt(1.0 + 4.0 * n / s))


def alpha_from_p(rho, p):
    n = max(rho, 1e-8) / M_AR
    t_lo, t_hi = 50.0, p / (n * K_B)  # (1+alpha) >= 1 so T <= p/nk
    if t_hi < 2500.0:
        return 0.0, t_hi
    for _ in range(60):
        t = 0.5 * (t_lo + t_hi)
        a = alpha_of(n, t)
        if (1.0 + a) * n * K_B * t < p:
            t_lo = t
        else:
            t_hi = t
    t = 0.5 * (t_lo + t_hi)
    return alpha_of(n, t), t


tag = sys.argv[1] if len(sys.argv) > 1 else "saha"
nr, nz = 130, 106
rho = np.zeros((nr, nz))
p = np.zeros((nr, nz))
mask = np.zeros((nr, nz), int)
rr = np.zeros((nr, nz))
zz = np.zeros((nr, nz))
with open(os.path.join(ROOT, "out", "phase2_state.csv")) as f:
    for row in csv.DictReader(f):
        j, i = int(row["j"]), int(row["i"])
        rho[j, i] = float(row["rho"])
        p[j, i] = float(row["p_Pa"])
        mask[j, i] = int(row["mask"])
        rr[j, i] = float(row["r_m"])
        zz[j, i] = float(row["z_m"])

al = np.zeros((nr, nz))
tt = np.zeros((nr, nz))
fluid = mask == 0
for j, i in zip(*np.where(fluid)):
    al[j, i], tt[j, i] = alpha_from_p(rho[j, i], p[j, i])

af = al[fluid]
print(f"fluid cells: {af.size}")
print(f"alpha mean {af.mean():.4f}  max {af.max():.4f}  "
      f"frac(alpha>0.5) {(af > 0.5).mean():.3f}  frac(alpha>0.01) {(af > 0.01).mean():.3f}")
tf = tt[fluid]
print(f"T mean {tf.mean():.0f} K  max {tf.max():.0f} K")

sl_j, sl_i = slice(1, nr - 1), slice(1, nz - 1)
r_cm = rr[sl_j, 1] * 100
z_cm = zz[1, sl_i] * 100
Zg, Rg = np.meshgrid(z_cm, r_cm)
am = np.where(fluid[sl_j, sl_i], al[sl_j, sl_i], np.nan)

fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
pc = ax.pcolormesh(Zg, Rg, am, cmap="viridis", shading="auto", vmin=0, vmax=1)
fig.colorbar(pc, ax=ax, label="ionization fraction alpha")
ax.set_xlabel("z (cm)")
ax.set_ylabel("r (cm)")
ax.set_title("Saha ionization fraction (steady state)")
out = os.path.join(ROOT, "out", "img", f"phase2_{tag}_alpha.png")
fig.tight_layout()
fig.savefig(out)
print("wrote", out)
