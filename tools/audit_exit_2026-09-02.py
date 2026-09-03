#!/usr/bin/env python3.11
"""Independent audit of the mv_ghost_exit pressure-outlet fix (2026-09-02).

Reads three state CSVs (nosink old-outlet plateau, fromfill old-outlet
plateau, and 400 steps of the new pressure outlet from the nosink state)
and computes exit-plane geometry, mass-flux-weighted exit Mach, the
choked-flow chamber-pressure prediction, and cross-checks mv_ghost_exit
and mv_exit_probe by hand against the raw fields.

Grid: 130 x 106, dr = 0.0005 m, dz = 0.00125 m, r = (j-0.5) dr.
Masks: 0 fluid, 1 cathode, 2 anode, 3 axis, 4 wall, 5 backplate,
6 inlet, 7 outflow. Exit fluid column is i = 104 (mp_nzm2); ghost is
i = 105.

No repo/state files are written; this script only reads CSVs.
"""
import csv
import math

import numpy as np

GAMMA = 5.0 / 3.0
M_ION_AR = 6.633e-26   # kg, mpd_solver.rail line 41
K_BOLTZ = 1.380649e-23  # J/K, mpd_solver.rail line 137
MDOT_NOMINAL = 6.0e-3   # kg/s, 6 g/s
AMB_P = 1.0             # Pa, amb_p
AMB_RHO = 3.0e-5        # kg/m^3, amb_rho
RHO_FLOOR = 1.0e-8
DR = 0.0005
DZ = 0.00125
I_EXIT = 104            # mp_nzm2, last fluid column at the exit
J_MAX_FLUID = 128       # mp_nrm2

STATES = {
    "nosink (old outlet, seg8, 2.2 kPa floor)":
        "/Users/user/projects/mpd-attachment/out/phase2_state_A_nosink_seg8.csv",
    "fromfill (old outlet, seg4, 23 kPa floor)":
        "/tmp/run_kT_fromfill/out/state_seg4.csv",
    "smoke (new pressure outlet, +400 steps from nosink)":
        "/tmp/smoke_exit/out/phase2_state.csv",
}


def load(path):
    rows = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    n = len(rows)
    j = np.zeros(n, dtype=int)
    i = np.zeros(n, dtype=int)
    r_m = np.zeros(n)
    mask = np.zeros(n, dtype=int)
    rho = np.zeros(n)
    vr = np.zeros(n)
    vz = np.zeros(n)
    p = np.zeros(n)
    bt = np.zeros(n)
    for k, row in enumerate(rows):
        j[k] = int(row["j"])
        i[k] = int(row["i"])
        r_m[k] = float(row["r_m"])
        mask[k] = int(row["mask"])
        rho[k] = float(row["rho"])
        vr[k] = float(row["vr"])
        vz[k] = float(row["vz"])
        p[k] = float(row["p_Pa"])
        bt[k] = float(row["bt_T"])
    nz = i.max() + 1
    nr = j.max() + 1
    idx = j * nz + i
    order = np.argsort(idx)
    return dict(j=j[order], i=i[order], r_m=r_m[order], mask=mask[order],
                rho=rho[order], vr=vr[order], vz=vz[order], p=p[order],
                bt=bt[order], nz=nz, nr=nr)


def exit_rows(st):
    """Return boolean mask over the full array selecting exit-column
    (i == I_EXIT) cells that are FLUID (mask == 0)."""
    return (st["i"] == I_EXIT) & (st["mask"] == 0)


def analyze(name, path):
    st = load(path)
    sel = exit_rows(st)
    j_fluid = np.sort(st["j"][sel])
    rho = st["rho"][sel]
    vz = st["vz"][sel]
    p = st["p"][sel]
    r = st["r_m"][sel]
    j = st["j"][sel]

    rho_safe = np.maximum(rho, RHO_FLOOR)
    cs = np.sqrt(GAMMA * p / rho_safe)
    mach = vz / cs

    da = 2.0 * math.pi * r * DR  # mv_tau * mp_r_of j * mp_dr
    mdot_cell = rho * vz * da    # kg/s through each exit cell (signed)

    out_mask = vz > 0.0
    back_mask = vz < 0.0

    mdot_out_total = mdot_cell[out_mask].sum()
    mdot_back_total = mdot_cell[back_mask].sum()  # negative
    mdot_net = mdot_cell.sum()

    # mass-flux-weighted exit Mach, mirroring mv_exit_probe's ex[0]/ex[1]
    # (weight is mz * da for outflowing cells only)
    if mdot_out_total > 0:
        mach_w = (mdot_cell[out_mask] * mach[out_mask]).sum() / mdot_out_total
    else:
        mach_w = float("nan")

    supersonic_mask = out_mask & (mach >= 1.0)
    frac_supersonic_massflux = (mdot_cell[supersonic_mask].sum() / mdot_out_total
                                 if mdot_out_total > 0 else float("nan"))

    n_fluid = sel.sum()
    n_back = int(back_mask.sum())
    p_min = p.min() if n_fluid else float("nan")
    p_max = p.max() if n_fluid else float("nan")
    p_mean_massflux = ((p[out_mask] * mdot_cell[out_mask]).sum() / mdot_out_total
                        if mdot_out_total > 0 else float("nan"))

    # mass flux by radial band (thirds of the fluid j-range)
    j_lo, j_hi = j_fluid.min(), j_fluid.max()
    thirds = np.linspace(j_lo, j_hi + 1, 4)
    bands = []
    for b in range(3):
        bm = (j >= thirds[b]) & (j < thirds[b + 1])
        bands.append((thirds[b], thirds[b + 1], mdot_cell[bm].sum()))

    exit_area = da.sum()

    print(f"=== {name} ===")
    print(f"file: {path}")
    print(f"exit fluid j-rows: {j_fluid.min()}..{j_fluid.max()} "
          f"({n_fluid} cells, {n_fluid} of {J_MAX_FLUID} possible fluid rows)")
    print(f"exit area (sum 2*pi*r*dr over fluid rows): {exit_area:.6e} m^2")
    print(f"mdot_out (vz>0 cells): {mdot_out_total*1e3:.4f} g/s")
    print(f"mdot_back (vz<0 cells, signed): {mdot_back_total*1e3:.4f} g/s "
          f"({n_back} backflowing cells)")
    print(f"mdot_net (all exit cells): {mdot_net*1e3:.4f} g/s")
    for lo, hi, m in bands:
        print(f"  band j=[{lo:.1f},{hi:.1f}): mdot = {m*1e3:.4f} g/s")
    print(f"mass-flux-weighted exit Mach: {mach_w:.4f}")
    print(f"fraction of outflow mass flux with M>=1: {frac_supersonic_massflux:.4f}")
    print(f"exit p: min={p_min:.4f} Pa max={p_max:.4f} Pa "
          f"mass-flux-weighted mean={p_mean_massflux:.4f} Pa")
    print(f"per-cell Mach range: {mach[out_mask].min() if out_mask.any() else float('nan'):.4f} "
          f"to {mach[out_mask].max() if out_mask.any() else float('nan'):.4f}")
    print()
    return dict(name=name, mdot_out=mdot_out_total, mdot_net=mdot_net,
                mach_w=mach_w, frac_super=frac_supersonic_massflux,
                p_massflux=p_mean_massflux, exit_area=exit_area,
                n_fluid=n_fluid, n_back=n_back, p_min=p_min,
                j_lo=j_fluid.min(), j_hi=j_fluid.max())


def choked_prediction(results_smoke):
    """For 6 g/s at M=1 through the smoke exit-plane's own area/T
    profile, what chamber pressure (stagnation-ish, here just static p
    at the throat since M=1 means static = stagnation-adjacent for a
    simple 1-D estimate) does that imply, ideal gamma=5/3 argon."""
    print("=== Choked-flow chamber-floor estimate (ideal gamma=5/3) ===")
    area = results_smoke["exit_area"]
    mdot = MDOT_NOMINAL
    gamma = GAMMA
    R_specific = K_BOLTZ / M_ION_AR  # J/(kg K), un-ionized argon
    print(f"exit area used: {area:.6e} m^2, R_specific (neutral Ar) = {R_specific:.2f} J/kg/K")

    # mdot = rho * A * cs (M=1, cs = sqrt(gamma p/rho) = sqrt(gamma R T))
    # rho*cs = mdot/A ; p = rho R T = rho cs^2/gamma => p = (mdot/A) * cs/gamma
    # need T (or cs) independently: use smoke exit temperature range measured below.
    return R_specific


def temperature_from_p_rho(p, rho, alpha=0.0):
    n = rho / M_ION_AR
    # ideal gas p = (1+alpha) n k T  =>  T = p / ((1+alpha) n k)
    return p / ((1.0 + alpha) * n * K_BOLTZ)


def main():
    results = {}
    for name, path in STATES.items():
        results[name] = analyze(name, path)

    smoke_key = [k for k in STATES if k.startswith("smoke")][0]
    smoke = results[smoke_key]

    R_specific = choked_prediction(smoke)

    # Use the smoke state's own exit temperature (mass-flux-weighted) to
    # predict the M=1 chamber floor at 6 g/s, ideal neutral-argon EOS.
    st = load(STATES[smoke_key])
    sel = exit_rows(st)
    rho = st["rho"][sel]
    p = st["p"][sel]
    vz = st["vz"][sel]
    r = st["r_m"][sel]
    da = 2.0 * math.pi * r * DR
    mdot_cell = rho * vz * da
    out = vz > 0.0
    T = temperature_from_p_rho(p, rho)
    T_w = (T[out] * mdot_cell[out]).sum() / mdot_cell[out].sum()
    cs_w = math.sqrt(GAMMA * R_specific * T_w)
    area = da.sum()
    rho_choke = MDOT_NOMINAL / (area * cs_w)
    p_choke = rho_choke * R_specific * T_w
    print(f"mass-flux-weighted exit T (ideal, alpha=0): {T_w:.1f} K")
    print(f"implied c_s at that T (neutral Ar, gamma=5/3): {cs_w:.1f} m/s")
    print(f"choked rho at M=1, mdot=6g/s over this area: {rho_choke:.4e} kg/m^3")
    print(f"IMPLIED CHAMBER-FLOOR PRESSURE (ideal, neutral Ar, ignoring "
          f"ionization): {p_choke:.1f} Pa")
    print()

    print("=== Comparison ===")
    print(f"Cory measured backplate wall pressure: 465 Pa")
    print(f"old nosink floor: 2155 Pa (2155/465 = {2155/465:.2f}x)")
    print(f"old fromfill floor: 23000 Pa (23000/465 = {23000/465:.2f}x)")
    print(f"choked-flow prediction (this script): {p_choke:.1f} Pa "
          f"({p_choke/465:.2f}x Cory)")


if __name__ == "__main__":
    main()
