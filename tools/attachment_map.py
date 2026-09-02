#!/opt/homebrew/bin/python3.11
"""Current-constriction diagnostic from out/phase2_state.csv.

The program's question is whether the arc constricts onto the cathode tip.
The electrode-surface attachment split is still PRESCRIBED (mp_bt_presc,
pbt_phi = 0.2 at the tip), so what is actually predicted is the INTERIOR
current channel. This tool measures it.

Exact relations used (axisymmetric, B = B_theta(r,z) e_theta):
  I(r,z) = r B_theta / (mu0/2pi)      enclosed poloidal current, exact
  j_z    = (1 / 2 pi r) dI/dr
  j_r    = -(1 / 2 pi r) dI/dz
Resistivity mirrors mv_eta_calc in rail/mpd_solver.rail exactly; T and
alpha come from the same Saha inversion as tools/alpha_map.py.

Reports: total Ohmic power (the number the uniform-capped eta got wrong by
~60x), eta dynamic range and cap/floor occupancy, the current-channel
radius r50/r90 versus z, and where the Ohmic dissipation actually sits.

Usage: attachment_map.py [J_amps] [tag]  -> out/img/phase2_<tag>_current.png
"""
import csv, math, os, sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = float(sys.argv[1]) if len(sys.argv) > 1 else 8000.0
TAG = sys.argv[2] if len(sys.argv) > 2 else "pion"

MU0_2PI = 2.0e-7
K_B = 1.380649e-23
M_AR = 6.633e-26
CHI_K = 182882.69143808
SAHA_C = 2.8976196474863585e22
ETA_CAP, ETA_FLOOR = 1.0e-3, 1.0e-7
R_C, L_C = 0.0095, 0.10           # cathode radius, length (m)
NR, NZ = 130, 106
DR, DZ = 0.0005, 0.00125

# ── read state ────────────────────────────────────────────────────────
F = {k: np.zeros((NR, NZ)) for k in ["r", "z", "rho", "p", "bt"]}
mask = np.zeros((NR, NZ), int)
with open(os.path.join(ROOT, "out", "phase2_state.csv")) as f:
    for row in csv.DictReader(f):
        j, i = int(row["j"]), int(row["i"])
        F["r"][j, i] = float(row["r_m"])
        F["z"][j, i] = float(row["z_m"])
        F["rho"][j, i] = float(row["rho"])
        F["p"][j, i] = float(row["p_Pa"])
        F["bt"][j, i] = float(row["bt_T"])
        mask[j, i] = int(row["mask"])

sj, si = slice(1, NR - 1), slice(1, NZ - 1)
r2 = F["r"][sj, si]
z2 = F["z"][sj, si]
rho = F["rho"][sj, si]
p = F["p"][sj, si]
bt = F["bt"][sj, si]
mk = mask[sj, si]
fluid = mk == 0
solid = (mk == 1) | (mk == 2)
r_cm, z_cm = r2[:, 0] * 100, z2[0, :] * 100


# ── Saha inversion (mirrors alpha_map.py / eos_* in mpd_solver.rail) ──
def alpha_of(n, t):
    if t < 2500.0:
        return 0.0
    s = SAHA_C * t * math.sqrt(t) * math.exp(-CHI_K / t)
    return 2.0 / (1.0 + math.sqrt(1.0 + 4.0 * n / s))


def alpha_from_p(rho_c, p_c):
    n = max(rho_c, 1e-8) / M_AR
    t_lo, t_hi = 50.0, p_c / (n * K_B)
    if t_hi < 2500.0:
        return 0.0, t_hi
    for _ in range(60):
        t = 0.5 * (t_lo + t_hi)
        if (1.0 + alpha_of(n, t)) * n * K_B * t < p_c:
            t_lo = t
        else:
            t_hi = t
    t = 0.5 * (t_lo + t_hi)
    return alpha_of(n, t), t


al = np.zeros_like(rho)
tt = np.zeros_like(rho)
for j, i in zip(*np.where(fluid)):
    al[j, i], tt[j, i] = alpha_from_p(rho[j, i], p[j, i])

# eta exactly as mv_eta_calc: Spitzer + electron-neutral, caps numeric-only
a_f = np.maximum(al, 1e-8)
t_eV = np.maximum(tt / 11604.518, 0.1)
eta_ei = 5.0e-5 / (t_eV * np.sqrt(t_eV))
eta_en = 2.2046e-8 * np.sqrt(np.maximum(tt, 0.0)) * (1.0 - a_f) / a_f
eta = np.clip(eta_ei + eta_en, ETA_FLOOR, ETA_CAP)

# ── current density from the exact stream function ────────────────────
# Differentiate on the FULL array (ghosts included), THEN slice. Slicing
# first makes np.gradient use one-sided differences on every domain edge,
# which is wrong at the axis: the ghost carries r < 0 and B antisymmetric,
# so I[0] == I[1] and the centered form is the correct one. The one-sided
# edge value comes out exactly 2x the analytic on-axis j_z = c/pi (where
# I -> c r^2 near r = 0), so this is a factor-of-two error on the peak,
# not a rounding detail.
I_full = F["r"] * F["bt"] / MU0_2PI             # amps enclosed
dIdr = np.gradient(I_full, DR, axis=0)[sj, si]
dIdz = np.gradient(I_full, DZ, axis=1)[sj, si]
I_enc = I_full[sj, si]
two_pi_r = 2.0 * np.pi * np.maximum(r2, 0.5 * DR)
j_z = dIdr / two_pi_r
j_r = -dIdz / two_pi_r
jmag = np.hypot(j_r, j_z)

# ── Ohmic dissipation ─────────────────────────────────────────────────
q = np.where(fluid, eta * jmag ** 2, 0.0)       # W/m^3
dV = 2.0 * np.pi * r2 * DR * DZ
P_tot = float((q * dV).sum())

print(f"=== attachment diagnostic, J = {J/1000:.1f} kA, tag {TAG} ===")
print(f"fluid cells {int(fluid.sum())}")
ef = eta[fluid]
print(f"eta  min {ef.min():.3e}  med {np.median(ef):.3e}  max {ef.max():.3e}  "
      f"dynamic range {ef.max()/ef.min():.1f}x")
print(f"eta  at cap {(ef >= ETA_CAP*0.999).mean()*100:.1f}%   "
      f"at floor {(ef <= ETA_FLOOR*1.001).mean()*100:.1f}%")
af, tf = al[fluid], tt[fluid]
print(f"alpha mean {af.mean():.4f} max {af.max():.4f} "
      f"frac>0.5 {(af>0.5).mean():.3f} | T mean {tf.mean():.0f} K max {tf.max():.0f} K")
# NOTE: eta here is recomputed from (rho, p) with the CURRENT formula in
# mpd_solver.rail, not whatever the run that wrote state.csv used. On a
# state from an older eta model this is "what the current model would
# dissipate here", not that run's Ohmic power. Arc scale ~400 kW; the
# implied arc voltage below is the honest cross-check.
print(f"TOTAL OHMIC POWER  {P_tot/1000.0:.1f} kW"
      f"   => R_arc {P_tot/(J*J)*1000.0:.2f} mOhm, V_arc {P_tot/J:.1f} V")

# where the dissipation sits
Pw = q * dV
near_axis = r2 < 2.0 * R_C
tip_ball = (r2 < 2.0 * R_C) & (np.abs(z2 - L_C) < 0.01)
downstream = z2 > L_C
if P_tot > 0:
    print(f"  frac of Ohmic power at r < 2 r_c ({2*R_C*100:.1f} cm): "
          f"{Pw[near_axis].sum()/P_tot*100:.1f}%")
    print(f"  frac within 1 cm of the cathode tip:            "
          f"{Pw[tip_ball].sum()/P_tot*100:.1f}%")
    print(f"  frac downstream of the tip plane (z > 10 cm):   "
          f"{Pw[downstream].sum()/P_tot*100:.1f}%")

# ── concentration: how peaked is the dissipation (this is FREE) ───────
pw = Pw[fluid]
vw = dV[fluid]
order = np.argsort(pw / np.maximum(vw, 1e-30))[::-1]   # by power density
pw_s, vw_s = pw[order], vw[order]
vcum = np.cumsum(vw_s) / vw_s.sum()
pcum = np.cumsum(pw_s) / max(pw_s.sum(), 1e-30)
print("\n dissipation concentration (free, not prescribed):")
for f in (0.01, 0.05, 0.10, 0.25):
    k = int(np.searchsorted(vcum, f))
    k = min(k, pcum.size - 1)
    print(f"   hottest {f*100:5.1f}% of plasma VOLUME carries "
          f"{pcum[k]*100:5.1f}% of the Ohmic power")
qf = q[fluid]
print(f"   peak power density {qf.max():.3e} W/m^3, "
      f"volume-mean {(Pw.sum()/dV[fluid].sum()):.3e} => peak/mean "
      f"{qf.max()/max(Pw.sum()/dV[fluid].sum(),1e-30):.0f}x")
print(f"   peak |j| {jmag[fluid].max():.3e} A/m^2 at "
      f"r={r2[fluid][np.argmax(jmag[fluid])]*100:.2f} cm, "
      f"z={z2[fluid][np.argmax(jmag[fluid])]*100:.2f} cm")

# ── current channel in the PLASMA only ────────────────────────────────
# I_enc on the cathode surface is prescribed, so the free quantity is
# where the current that is already in the plasma crosses radially.
# For each axial station: I_lo = I at the innermost fluid cell (what the
# cathode has already delivered), I_hi = I at the outermost fluid cell.
# r_half is the radius where I reaches the midpoint of that rise.
print("\n current channel in the plasma (r_c = 0.95 cm, r_anode = 5.10 cm)")
print("   z(cm)  I_in/J  I_out/J  r_half(cm)  r_q(cm)=power centroid")


def col_stats(i):
    fl = np.where(fluid[:, i])[0]
    if fl.size < 3:
        return None
    Ic = np.maximum.accumulate(I_enc[fl, i])
    lo, hi = Ic[0], Ic[-1]
    rr = r_cm[fl]
    if hi - lo < 1e-6:
        rh = float("nan")
    else:
        tgt = 0.5 * (lo + hi)
        k = int(np.searchsorted(Ic, tgt))
        k = min(max(k, 1), Ic.size - 1)
        d = Ic[k] - Ic[k - 1]
        rh = rr[k - 1] + (rr[k] - rr[k - 1]) * ((tgt - Ic[k - 1]) / d if d > 0 else 0.0)
    w = Pw[fl, i]
    rq = float((w * rr).sum() / w.sum()) if w.sum() > 0 else float("nan")
    return lo / J, hi / J, rh, rq


for i in range(I_enc.shape[1]):
    zc = z_cm[i]
    if not (abs(zc % 1.0) < 0.07 or abs(zc % 1.0) > 0.93):
        continue
    st = col_stats(i)
    if st is None:
        continue
    print(f"  {zc:6.2f}  {st[0]:6.3f}  {st[1]:7.3f}  {st[2]:10.2f}  {st[3]:10.2f}")

# ── figure ────────────────────────────────────────────────────────────
INK, MUT, ELEC = "#1a1a24", "#8a8a96", "#b8bcc4"


def electrodes(ax):
    ax.add_patch(Rectangle((0, 0), 10.0, 0.95, facecolor=ELEC,
                           edgecolor=INK, linewidth=0.7, zorder=5))
    ax.add_patch(Rectangle((10.25, 5.1), 1.0, 1.3, facecolor=ELEC,
                           edgecolor=INK, linewidth=0.7, zorder=5))


def panel(ax, data, title, cmap, log=False):
    d = np.where(fluid, data, np.nan)
    if log:
        d = np.log10(np.maximum(d, 1e-30))
    Zg, Rg = np.meshgrid(z_cm, r_cm)
    pc = ax.pcolormesh(Zg, Rg, d, cmap=cmap, shading="auto",
                       vmin=np.nanpercentile(d, 1), vmax=np.nanpercentile(d, 99.5))
    psi = np.clip(np.where(solid, np.nan, I_enc / J), 0, 1.05)
    ax.contour(Zg, Rg, psi, levels=np.arange(0.1, 1.0, 0.1),
               colors="#e8f0ff", linewidths=0.6, alpha=0.8)
    electrodes(ax)
    ax.set_xlabel("z (cm)", fontsize=8)
    ax.set_ylabel("r (cm)", fontsize=8)
    ax.tick_params(colors=MUT, labelsize=7)
    ax.set_title(title, fontsize=9, color=INK)
    cb = fig.colorbar(pc, ax=ax, shrink=0.9, pad=0.02)
    cb.ax.tick_params(labelsize=7, colors=MUT)


fig, axes = plt.subplots(2, 2, figsize=(12, 7), dpi=150)
panel(axes[0, 0], jmag, "log10 |j| (A/m^2), lines = 10% of J each", "inferno", log=True)
panel(axes[0, 1], eta, "log10 eta (Ohm m)", "plasma", log=True)
panel(axes[1, 0], q, "log10 Ohmic power density (W/m^3)", "magma", log=True)
panel(axes[1, 1], al, "ionization fraction alpha", "viridis")
fig.suptitle(f"Current attachment diagnostic, J = {J/1000:.0f} kA argon 6 g/s  -  "
             f"total Ohmic {P_tot/1000:.0f} kW", fontsize=11, color=INK)
fig.tight_layout()
os.makedirs(os.path.join(ROOT, "out", "img"), exist_ok=True)
out = os.path.join(ROOT, "out", "img", f"phase2_{TAG}_current.png")
fig.savefig(out, facecolor="white")
print("\nwrote", out)
