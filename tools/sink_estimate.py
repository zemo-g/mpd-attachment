#!/opt/homebrew/bin/python3.11
"""Magnitude estimate for candidate energy sinks, BEFORE implementing any.

Computed per-cell on a saved phase2 state (same Saha inversion as
alpha_map/attachment_map), against that state's own Ohmic power:

1. RADIATION. Bremsstrahlung is exact closed-form:
     P_br = 1.69e-38 n_e n_i sqrt(T_eV)  W/m^3   (NRL formulary, Z=1)
   Recombination (free-bound) runs ~ (chi/kT) x brems, and argon line
   radiation at ~1 eV is larger still but geometry/trapping dependent.
   We report brems exactly and a GENEROUS x100 band for total radiation.
   If even x100 is small vs Ohmic, radiation cannot brake the runaway
   and option C's radiation half is falsified without a solver session.

2. WALL CONDUCTION. Scale estimate: q = kappa (T_cell - 300) / (dx/2)
   over every fluid face adjacent to a solid (electrodes, backplate,
   chamber wall), kappa in a [0.3, 3] W/m/K band (argon plasma ~1 eV
   literature range, neutral + electron). This is what a conducting-wall
   BC would remove; the boundary layer is barely resolved at 0.5 mm so
   treat as scale, not prediction.

Usage: sink_estimate.py <state.csv> [tag]
"""
import csv, math, sys
import numpy as np

K_B = 1.380649e-23; M_AR = 6.633e-26
CHI_K = 182882.69143808; SAHA_C = 2.8976196474863585e22
ETA_CAP, ETA_FLOOR = 1.0e-3, 1.0e-7
NR, NZ = 130, 106; DR, DZ = 0.0005, 0.00125

def alpha_of(n, t):
    if t < 2500.0: return 0.0
    s = SAHA_C * t * math.sqrt(t) * math.exp(-CHI_K / t)
    return 2.0 / (1.0 + math.sqrt(1.0 + 4.0 * n / s))

def alpha_from_p(rho, p):
    n = max(rho, 1e-8) / M_AR
    t_lo, t_hi = 50.0, p / (n * K_B)
    if t_hi < 2500.0: return 0.0, t_hi
    for _ in range(60):
        t = 0.5 * (t_lo + t_hi)
        if (1.0 + alpha_of(n, t)) * n * K_B * t < p: t_lo = t
        else: t_hi = t
    t = 0.5 * (t_lo + t_hi)
    return alpha_of(n, t), t

F = {k: np.zeros((NR, NZ)) for k in ["r", "rho", "p", "bt"]}
mk = np.zeros((NR, NZ), int)
for row in csv.DictReader(open(sys.argv[1])):
    j, i = int(row["j"]), int(row["i"])
    F["r"][j, i] = float(row["r_m"]); F["rho"][j, i] = float(row["rho"])
    F["p"][j, i] = float(row["p_Pa"]); F["bt"][j, i] = float(row["bt_T"])
    mk[j, i] = int(row["mask"])
fluid = mk == 0

al = np.zeros((NR, NZ)); tt = np.zeros((NR, NZ))
for j, i in zip(*np.where(fluid)):
    al[j, i], tt[j, i] = alpha_from_p(F["rho"][j, i], F["p"][j, i])

n = np.maximum(F["rho"], 1e-8) / M_AR
ne = al * n
dV = 2.0 * np.pi * F["r"] * DR * DZ

# Ohmic reference (same forms as attachment_map)
a_f = np.maximum(al, 1e-8); t_eV = np.maximum(tt / 11604.518, 0.1)
eta = np.clip(5.0e-5/(t_eV*np.sqrt(t_eV)) + 2.2046e-8*np.sqrt(np.maximum(tt,0))*(1-a_f)/a_f, ETA_FLOOR, ETA_CAP)
I_full = F["r"] * F["bt"] / 2.0e-7
jz = np.gradient(I_full, DR, axis=0) / (2*np.pi*np.maximum(F["r"], 0.5*DR))
jr = -np.gradient(I_full, DZ, axis=1) / (2*np.pi*np.maximum(F["r"], 0.5*DR))
P_ohm = float((np.where(fluid, eta*(jr**2+jz**2), 0.0) * dV).sum())

# 1. bremsstrahlung, exact
q_br = 1.69e-38 * ne * ne * np.sqrt(np.maximum(t_eV, 1e-3))
P_br = float((np.where(fluid, q_br, 0.0) * dV).sum())

# 2. wall conduction: every fluid face whose neighbor is solid (mask 1/2/4/5)
solidish = np.isin(mk, [1, 2, 4, 5])
P_wall_unit = 0.0   # at kappa = 1 W/m/K
for dj, di, dx, kind in [(1,0,DR,"r"),(-1,0,DR,"r"),(0,1,DZ,"z"),(0,-1,DZ,"z")]:
    nb = np.roll(np.roll(solidish, -dj, 0), -di, 1)
    face = fluid & nb & (tt > 300.0)
    if kind == "r":
        area = 2*np.pi*(F["r"] + dj*0.5*DR) * DZ
    else:
        area = 2*np.pi*F["r"] * DR
    P_wall_unit += float((np.where(face, (tt-300.0)/(dx*0.5), 0.0) * area).sum())

tag = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
print(f"=== sink magnitude estimate on {tag} ===")
print(f"Ohmic power (reference):        {P_ohm/1e3:9.2f} kW")
print(f"bremsstrahlung (exact):         {P_br/1e3:9.4f} kW   = {P_br/P_ohm*100:6.2f}% of Ohmic")
print(f"total radiation, x100 band:     {P_br*100/1e3:9.2f} kW   = {P_br*100/P_ohm*100:6.1f}% of Ohmic")
print(f"wall conduction @ kappa=0.3:    {P_wall_unit*0.3/1e3:9.2f} kW   = {P_wall_unit*0.3/P_ohm*100:6.1f}% of Ohmic")
print(f"wall conduction @ kappa=1.0:    {P_wall_unit*1.0/1e3:9.2f} kW   = {P_wall_unit*1.0/P_ohm*100:6.1f}% of Ohmic")
print(f"wall conduction @ kappa=3.0:    {P_wall_unit*3.0/1e3:9.2f} kW   = {P_wall_unit*3.0/P_ohm*100:6.1f}% of Ohmic")
