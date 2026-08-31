#!/opt/homebrew/bin/python3.11
"""Render tier-1 field images from out/phase2_state.csv.

Produces (in out/img/):
  phase2_<tag>_hero.png    pressure + current streamlines, mirrored section
  phase2_<tag>_fields.png  2x2 panel: log10 rho, p, |v|, B_theta

The current streamlines are exact: contours of r*B_theta are the poloidal
current stream function; each line is a fixed fraction of the total J.
Usage: render_fields.py [J_amps] [tag]
"""
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = float(sys.argv[1]) if len(sys.argv) > 1 else 8000.0
TAG = sys.argv[2] if len(sys.argv) > 2 else "8ka"
MU0_2PI = 2.0e-7

NR, NZ = 130, 106
fields = {k: np.zeros((NR, NZ)) for k in ["r", "z", "mask", "rho", "vr", "vz", "p", "bt"]}
with open(os.path.join(ROOT, "out", "phase2_state.csv")) as f:
    for row in csv.DictReader(f):
        j, i = int(row["j"]), int(row["i"])
        fields["r"][j, i] = float(row["r_m"])
        fields["z"][j, i] = float(row["z_m"])
        fields["mask"][j, i] = int(row["mask"])
        fields["rho"][j, i] = float(row["rho"])
        fields["vr"][j, i] = float(row["vr"])
        fields["vz"][j, i] = float(row["vz"])
        fields["p"][j, i] = float(row["p_Pa"])
        fields["bt"][j, i] = float(row["bt_T"])

# physical cells only (drop ghost rows); j=1..128, i=1..104
sl_j, sl_i = slice(1, 129), slice(1, 105)
r = fields["r"][sl_j, 1] * 100  # cm, per-row radius
z = fields["z"][1, sl_i] * 100
mask = fields["mask"][sl_j, sl_i]
rho = fields["rho"][sl_j, sl_i]
p = fields["p"][sl_j, sl_i]
bt = fields["bt"][sl_j, sl_i]
vmag = np.sqrt(fields["vr"][sl_j, sl_i] ** 2 + fields["vz"][sl_j, sl_i] ** 2)
solid = (mask == 1) | (mask == 2)

# current stream function: fraction of total current enclosed
psi = (fields["r"][sl_j, sl_i] * bt) / (MU0_2PI * J)
psi = np.clip(psi, 0, 1.05)

os.makedirs(os.path.join(ROOT, "out", "img"), exist_ok=True)
INK, MUT = "#1a1a24", "#8a8a96"
ELEC = "#b8bcc4"


def mirror(a):
    return np.vstack([a[::-1], a])


def setup_ax(ax):
    ax.set_xlabel("z (cm)")
    ax.set_ylabel("r (cm)")
    ax.tick_params(colors=MUT, labelsize=8)
    for s in ax.spines.values():
        s.set_color(MUT)
        s.set_linewidth(0.6)


def draw_electrodes(ax, both=True):
    # cathode: r <= 0.95 cm, z 0..10; anode: r 5.1..6.4, z 10.25..11.25
    for sgn in ([1, -1] if both else [1]):
        ax.add_patch(Rectangle((0, 0 if sgn > 0 else -0.95), 10.0, 0.95,
                               facecolor=ELEC, edgecolor=INK, linewidth=0.7, zorder=5))
        ax.add_patch(Rectangle((10.25, sgn * 5.1 if sgn > 0 else -6.4), 1.0, 1.3,
                               facecolor=ELEC, edgecolor=INK, linewidth=0.7, zorder=5))
    ax.text(5.0, 0.0, "cathode", ha="center", va="center", fontsize=8,
            color=INK, zorder=6)
    ax.text(10.75, 5.75 if both else 5.75, "anode", ha="center", va="center",
            fontsize=7, color=INK, zorder=6, rotation=90)
    if both:
        ax.text(10.75, -5.75, "anode", ha="center", va="center", fontsize=7,
                color=INK, zorder=6, rotation=90)


rm = np.concatenate([-r[::-1], r])
Zg, Rg = np.meshgrid(z, rm)

# ── hero: pressure + current streamlines, mirrored ──
fig, ax = plt.subplots(figsize=(10, 6.2), dpi=170)
pm = mirror(np.where(solid, np.nan, p))
pc = ax.pcolormesh(Zg, Rg, pm, cmap="magma", shading="auto",
                   vmin=0, vmax=np.nanpercentile(pm, 99))
psim = mirror(np.where(solid, np.nan, psi))
cs = ax.contour(Zg, Rg, psim, levels=np.arange(0.1, 1.0, 0.1),
                colors="#e8f0ff", linewidths=0.8, alpha=0.85)
draw_electrodes(ax)
setup_ax(ax)
ax.set_title(f"PBT self-field arc, argon 6 g/s, J = {J/1000:.0f} kA  -  "
             "pressure field with current streamlines (each line = 10% of J)",
             fontsize=10, color=INK)
cb = fig.colorbar(pc, ax=ax, shrink=0.85, pad=0.02)
cb.set_label("p (Pa)", fontsize=8, color=MUT)
cb.ax.tick_params(labelsize=7, colors=MUT)
fig.tight_layout()
fig.savefig(os.path.join(ROOT, "out", "img", f"phase2_{TAG}_hero.png"),
            facecolor="white")
plt.close(fig)

# ── 2x2 field panel (upper half only, more detail) ──
panels = [
    ("log10 density (kg/m^3)", np.log10(np.maximum(rho, 1e-9)), "viridis", None),
    ("pressure (Pa)", p, "magma", np.nanpercentile(p[~solid], 99)),
    ("|v| (km/s)", vmag / 1000.0, "cividis", None),
    ("B_theta (T)", bt, "inferno", None),
]
fig, axes = plt.subplots(2, 2, figsize=(12, 7), dpi=150)
Zh, Rh = np.meshgrid(z, r)
for ax, (title, data, cmap, vmax) in zip(axes.flat, panels):
    d = np.where(solid, np.nan, data)
    pc = ax.pcolormesh(Zh, Rh, d, cmap=cmap, shading="auto",
                       vmax=vmax if vmax is not None else np.nanmax(d))
    draw_electrodes(ax, both=False)
    setup_ax(ax)
    ax.set_title(title, fontsize=9, color=INK)
    cb = fig.colorbar(pc, ax=ax, shrink=0.9, pad=0.02)
    cb.ax.tick_params(labelsize=7, colors=MUT)
fig.suptitle(f"Phase 2 solver state, J = {J/1000:.0f} kA argon 6 g/s "
             "(resistive, attachment prescribed)", fontsize=11, color=INK)
fig.tight_layout()
fig.savefig(os.path.join(ROOT, "out", "img", f"phase2_{TAG}_fields.png"),
            facecolor="white")
plt.close(fig)
print("wrote out/img/phase2_%s_hero.png, out/img/phase2_%s_fields.png" % (TAG, TAG))
