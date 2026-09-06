#!/opt/homebrew/bin/python3.11
"""Exact scheme-flux closure on a phase2 state (mirrors mv_ghost_cell and the
first-order face flux Fhat = 0.5(F_c+F_g) - (dx/4dt)(U_g-U_c) at every
boundary face). Mass / z-momentum / energy INTO the domain, by family, split
into physical and LxF-diffusive parts. Also the resistive Poynting inflow
through Dirichlet faces, the central-difference eta j^2 dissipation and
the wall sink, all from the state.

Usage: audit_closure_2026-09-05.py <state.csv> <dt> <V_arc> <P_wall_log>
  e.g. ... /tmp/run_free_fromA/out/state_seg16.csv 1.0866e-8 21.2205 62508
Written for the 2026-09-05 cold audit (notes/audit_2026-09-05.md).
"""
import csv, math, sys
import numpy as np

STATE, DT, VARC, PWALL_LOG = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
J = 8000.0
NR, NZ, DR, DZ = 130, 106, 0.0005, 0.00125
MU0 = 1.2566370614359173e-6; INV_MU0 = 1.0 / MU0; MU0_2PI = 2.0e-7
K_B = 1.380649e-23; M_AR = 6.633e-26; CHI = 2.5249680505129372e-18
CHI_K = 182882.69143808; SAHA_C = 2.8976196474863585e22; GM1 = 2.0 / 3.0
TAU = 2 * math.pi
R_C, R_A, R_CH = 0.0095, 0.051, 0.064
J_CATH, J_FLUID0, I_TIP, I_TIP1 = 19, 20, 80, 81
J_ANODE, I_AN0, I_AN1, I_AIF, I_AOF = 103, 83, 90, 82, 91
J_IN1B = 36
IN_V, IN_RHO_ANN, IN_RHO_RING, KT_M = 300.0, 0.014707, 0.0064220, 62444.0
AMB_RHO, AMB_P, RHO_FLOOR = 3e-5, 1.0, 1e-8
T_WALL = 300.0

rho = np.zeros((NR, NZ)); vr = np.zeros((NR, NZ)); vz = np.zeros((NR, NZ))
p = np.zeros((NR, NZ)); bt = np.zeros((NR, NZ)); mask = np.zeros((NR, NZ), int)
with open(STATE) as f:
    for row in csv.DictReader(f):
        j, i = int(row["j"]), int(row["i"])
        rho[j, i] = float(row["rho"]); vr[j, i] = float(row["vr"]); vz[j, i] = float(row["vz"])
        p[j, i] = float(row["p_Pa"]); bt[j, i] = float(row["bt_T"]); mask[j, i] = int(row["mask"])
r_of = lambda j: (j - 0.5) * DR
z_of = lambda i: (i - 0.5) * DZ
fluid = mask == 0

def alpha_of(n, t):
    if t < 2500.0: return 0.0
    s = SAHA_C * t * math.sqrt(t) * math.exp(-CHI_K / t)
    return 2.0 / (1.0 + math.sqrt(1.0 + 4.0 * n / s))
def T_of(n, pp):
    t0 = pp / (n * K_B)
    if t0 < 2500.0: return t0, 0.0
    lo, hi = 0.3 * t0, t0
    for _ in range(60):
        tm = 0.5 * (lo + hi); a = alpha_of(n, tm)
        if (1.0 + a) * n * K_B * tm < pp: lo = tm
        else: hi = tm
    tm = 0.5 * (lo + hi); return tm, alpha_of(n, tm)

# conserved state arrays incl. ghosts
RHO = np.zeros((NR, NZ)); MR = np.zeros((NR, NZ)); MZ = np.zeros((NR, NZ))
EN = np.zeros((NR, NZ)); BT = np.zeros((NR, NZ)); EI = np.zeros((NR, NZ))
T = np.zeros((NR, NZ)); AL = np.zeros((NR, NZ))
for j in range(NR):
    for i in range(NZ):
        if not fluid[j, i]: continue
        n = max(rho[j, i], RHO_FLOOR) / M_AR
        t, a = T_of(n, p[j, i]); T[j, i] = t; AL[j, i] = a
        ei = 1.5 * p[j, i] + a * n * CHI
        EI[j, i] = max(ei, 1.5e-6)
        RHO[j, i] = rho[j, i]; MR[j, i] = rho[j, i] * vr[j, i]; MZ[j, i] = rho[j, i] * vz[j, i]
        BT[j, i] = bt[j, i]
        EN[j, i] = EI[j, i] + 0.5 * (MR[j, i]**2 + MZ[j, i]**2) / max(rho[j, i], RHO_FLOOR) + 0.5 * bt[j, i]**2 * INV_MU0

# prescribed face B (mp_bt_presc)
PBT_J_T1, PBT_J_T2 = 3700.0, 14000.0
S_INNER = math.pi * (R_CH**2 - R_A**2)
def j_lip(jt): return 0.0 if jt <= PBT_J_T1 else (jt - PBT_J_T1 if jt <= PBT_J_T2 else PBT_J_T2 - PBT_J_T1)
def ienc_aif(jt, r):
    v = j_lip(jt) + (min(jt, PBT_J_T1) / S_INNER) * math.pi * (r * r - R_A * R_A)
    return min(max(v, 0.0), jt)
def ienc_lip(jt, d): return j_lip(jt) * (1.0 - min(max(d / 0.01, 0.0), 1.0))
def bt_of(ienc, r): return MU0_2PI * ienc / max(r, 1e-6)
def bt_presc(j, i):
    m = mask[j, i]
    if m == 4: return bt_of(J, R_CH) if z_of(i) < 0.1025 else 0.0
    if m == 5: return bt_of(J, R_C) if j <= J_CATH else bt_of(J, r_of(j))
    if m == 6: return bt_of(J, r_of(j))
    if m == 2:
        if j == J_ANODE: return bt_of(ienc_lip(J, z_of(i) - 0.1025), R_A)
        if i == I_AN0: return bt_of(ienc_aif(J, r_of(j)), r_of(j))
        return 0.0
    return 0.0

# ── ghost fill (mv_ghost_cell, free cathode) ─────────────────────────
def ghost_gas(jg, ig, jf, fi, sr, sz, btg):
    RHO[jg, ig] = rho[jf, fi]; MR[jg, ig] = MR[jf, fi] * sr; MZ[jg, ig] = MZ[jf, fi] * sz
    ke = 0.5 * (MR[jg, ig]**2 + MZ[jg, ig]**2) / max(rho[jf, fi], RHO_FLOOR)
    EN[jg, ig] = EI[jf, fi] + ke + 0.5 * btg**2 * INV_MU0; BT[jg, ig] = btg; EI[jg, ig] = EI[jf, fi]
def ghost_solid(jg, ig, btg):
    RHO[jg, ig] = AMB_RHO; MR[jg, ig] = 0.0; MZ[jg, ig] = 0.0
    EN[jg, ig] = AMB_P / GM1 + 0.5 * btg**2 * INV_MU0; BT[jg, ig] = btg; EI[jg, ig] = AMB_P / GM1
subsonic_exit = np.zeros((NR, NZ), bool)
for j in range(NR):
    for i in range(NZ):
        mk = mask[j, i]
        if mk == 0: continue
        if mk == 3: ghost_gas(j, i, 1, i, -1.0, 1.0, -bt[1, i])
        elif mk == 4: ghost_gas(j, i, NR - 2, i, -1.0, 1.0, 2.0 * bt_presc(j, i) - bt[NR - 2, i])
        elif mk == 5: ghost_gas(j, i, j, 1, 1.0, -1.0, 2.0 * bt_presc(j, i) - bt[j, 1])
        elif mk == 6:
            rin = IN_RHO_ANN if j <= J_IN1B else IN_RHO_RING
            btg = 2.0 * bt_presc(j, i) - bt[j, 1]
            RHO[j, i] = rin; MR[j, i] = 0.0; MZ[j, i] = rin * IN_V
            EN[j, i] = rin * KT_M / GM1 + 0.5 * rin * IN_V**2 + 0.5 * btg**2 * INV_MU0; BT[j, i] = btg
        elif mk == 7:
            jf, fi = j, NZ - 2
            rs = max(rho[jf, fi], RHO_FLOOR); vzc = MZ[jf, fi] / rs
            cs = math.sqrt(5.0 / 3.0 * p[jf, fi] / rs); btg = -bt[jf, fi]
            if vzc >= cs: ghost_gas(j, i, jf, fi, 1.0, 1.0, btg)
            elif vzc > 0.0:
                subsonic_exit[jf, fi] = True
                eig = AMB_P / GM1 if p[jf, fi] > AMB_P else EI[jf, fi]
                RHO[j, i] = rho[jf, fi]; MR[j, i] = MR[jf, fi]; MZ[j, i] = MZ[jf, fi]
                EN[j, i] = eig + 0.5 * (MR[jf, fi]**2 + MZ[jf, fi]**2) / rs + 0.5 * btg**2 * INV_MU0; BT[j, i] = btg
            else:
                RHO[j, i] = AMB_RHO; MR[j, i] = 0.0; MZ[j, i] = 0.0
                EN[j, i] = AMB_P / GM1 + 0.5 * btg**2 * INV_MU0; BT[j, i] = btg
        elif mk == 1:
            if i == I_TIP: ghost_gas(j, i, j, I_TIP1, 1.0, -1.0, bt[j, I_TIP1])
            elif j == J_CATH: ghost_gas(j, i, J_FLUID0, i, -1.0, 1.0, bt[J_FLUID0, i] * (J_FLUID0 - 0.5) / (J_CATH - 0.5))
            else: ghost_solid(j, i, 0.0)
        else:  # anode
            if j == J_ANODE: ghost_gas(j, i, J_ANODE - 1, i, -1.0, 1.0, 2.0 * bt_presc(j, i) - bt[J_ANODE - 1, i])
            elif i == I_AN0: ghost_gas(j, i, j, I_AIF, 1.0, -1.0, 2.0 * bt_presc(j, i) - bt[j, I_AIF])
            elif i == I_AN1: ghost_gas(j, i, j, I_AOF, 1.0, -1.0, 2.0 * bt_presc(j, i) - bt[j, I_AOF])
            else: ghost_solid(j, i, bt_presc(j, i))

# pressure of any cell as the solver's p-cache (ghosts: from their own e_int)
def p_of(j, i):
    if fluid[j, i]: return p[j, i]
    # ghost: same e_int as the fluid mirror -> same p; solid/exit cases
    m = mask[j, i]
    if m == 6: return (IN_RHO_ANN if j <= J_IN1B else IN_RHO_RING) * KT_M
    if m == 7:
        jf, fi = j, NZ - 2
        if subsonic_exit[jf, fi]: return AMB_P if p[jf, fi] > AMB_P else p[jf, fi]
        if MZ[jf, fi] <= 0.0: return AMB_P
        return p[jf, fi]
    if RHO[j, i] == AMB_RHO and MR[j, i] == 0.0 and MZ[j, i] == 0.0 and EI[j, i] == AMB_P / GM1: return AMB_P
    # mirror ghost: p equals the mirrored fluid cell's p; find it
    if m == 3: return p[1, i]
    if m == 4: return p[NR - 2, i]
    if m == 5: return p[j, 1]
    if m == 1: return p[j, I_TIP1] if i == I_TIP else p[J_FLUID0, i]
    if m == 2:
        if j == J_ANODE: return p[J_ANODE - 1, i]
        if i == I_AN0: return p[j, I_AIF]
        return p[j, I_AOF]
    return AMB_P

def F_r(j, i):
    rs = max(RHO[j, i], RHO_FLOOR); v = MR[j, i] / rs; pt = p_of(j, i) + 0.5 * BT[j, i]**2 * INV_MU0
    return np.array([MR[j, i], MR[j, i] * v + pt, MZ[j, i] * v, (EN[j, i] + pt) * v])
def F_z(j, i):
    rs = max(RHO[j, i], RHO_FLOOR); v = MZ[j, i] / rs; pt = p_of(j, i) + 0.5 * BT[j, i]**2 * INV_MU0
    return np.array([MZ[j, i], MR[j, i] * v, MZ[j, i] * v + pt, (EN[j, i] + pt) * v])
def U(j, i): return np.array([RHO[j, i], MR[j, i], MZ[j, i], EN[j, i]])

fam_phys = {}; fam_diff = {}
def add(d, k, v): d[k] = d.get(k, np.zeros(4)) + v
NAME = {1: "cathode", 2: "anode", 3: "axis", 4: "wall", 5: "backplate", 6: "inlet", 7: "exit"}
for j in range(1, NR - 1):
    for i in range(1, NZ - 1):
        if not fluid[j, i]: continue
        r = r_of(j)
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jn, iN = j + dj, i + di
            mk = mask[jn, iN]
            if mk == 0: continue
            corner = (mk == 1 and jn == J_CATH and iN == I_TIP) or (mk == 2 and jn == J_ANODE and iN in (I_AN0, I_AN1))
            name = NAME[mk] + (" CORNER" if corner else "")
            if dj != 0:
                rf = r + dj * 0.5 * DR; area = TAU * rf * DZ
                fh = 0.5 * (F_r(j, i) + F_r(jn, iN)); dif = -(DR / (4 * DT)) * dj * (U(jn, iN) - U(j, i))
                sgn = -dj   # inflow into the cell
            else:
                area = TAU * r * DR
                if mk == 6:
                    rin = IN_RHO_ANN if j <= J_IN1B else IN_RHO_RING
                    pin = rin * KT_M; ein = rin * KT_M / GM1 + 0.5 * rin * IN_V**2
                    pm2 = 0.5 * INV_MU0 * (BT[j, i]**2 + BT[jn, iN]**2)
                    # S/2 for gas parts + magnetic parts kept from the pair
                    fz1 = 0.5 * (F_z(j, i) + F_z(jn, iN))
                    fh = np.array([rin * IN_V, 0.0, rin * IN_V**2 + pin + 0.5 * pm2, (ein + pin) * IN_V + pm2 * IN_V])
                    dif = np.zeros(4)
                else:
                    fh = 0.5 * (F_z(j, i) + F_z(jn, iN)); dif = -(DZ / (4 * DT)) * di * (U(jn, iN) - U(j, i))
                sgn = -di
            add(fam_phys, name, sgn * fh * area); add(fam_diff, name, sgn * dif * area)

print("=== scheme boundary fluxes INTO the domain (mass kg/s | m_z N | energy kW), physical part / LxF diffusive part")
tot_p = np.zeros(4); tot_d = np.zeros(4)
for k in sorted(fam_phys):
    a, b = fam_phys[k], fam_diff[k]; tot_p += a; tot_d += b
    print(f"  {k:16s} mass {a[0]:+.3e} {b[0]:+.3e} | mz {a[2]:+8.3f} {b[2]:+8.3f} | en {a[3]/1e3:+8.2f} {b[3]/1e3:+8.2f}")
print(f"  {'TOTAL':16s} mass {tot_p[0]:+.3e} {tot_d[0]:+.3e} | mz {tot_p[2]:+8.3f} {tot_d[2]:+8.3f} | en {tot_p[3]/1e3:+8.2f} {tot_d[3]/1e3:+8.2f}")
print(f"  net mass {tot_p[0]+tot_d[0]:+.3e} kg/s   net mz {tot_p[2]+tot_d[2]:+.3f} N   net hyperbolic energy {(tot_p[3]+tot_d[3])/1e3:+.2f} kW")

# ── resistive Poynting inflow through Dirichlet faces; eta j^2; wall sink ──
def eos_lnl(n, a, t):
    t_eV = max(t / 11604.518, 0.1); ne = max(a * n * 1e-6, 1.0)
    return min(max(23.0 - 0.5 * math.log(ne) + 1.5 * math.log(t_eV), 2.0), 20.0)
def eta_of(j, i):
    n = max(rho[j, i], RHO_FLOOR) / M_AR; t = T[j, i]; a = max(AL[j, i], 1e-8)
    t_c = max(t / 11604.518, 0.1); lnl = eos_lnl(n, a, t)
    e = 5.2e-5 * lnl / (t_c * math.sqrt(t_c)) + 2.2046e-8 * math.sqrt(t) * (1.0 - a) / a
    return min(max(e, 1e-7), 1e-3)
def wall_kappa(n, a, t):
    kn = 0.0177 * math.exp(0.7 * math.log(t / 300.0))
    if a <= 0.0: return kn
    lnl = eos_lnl(n, a, t); t_eV = t / 11604.518
    return (1.0 - a) * kn + a * 0.000230348819 * t * t_eV * math.sqrt(t_eV) / lnl
ETA = np.zeros((NR, NZ))
for j in range(NR):
    for i in range(NZ):
        if fluid[j, i]: ETA[j, i] = eta_of(j, i)
P_res = {}; P_diss = 0.0; P_wall = 0.0; P_diss_hot = []
for j in range(1, NR - 1):
    for i in range(1, NZ - 1):
        if not fluid[j, i]: continue
        r = r_of(j); vol = TAU * r * DR * DZ
        jr = -INV_MU0 * (BT[j, i + 1] - BT[j, i - 1]) / (2 * DZ)
        rs = max(r, 1e-4)
        jz = INV_MU0 * ((r + DR) * BT[j + 1, i] - (r - DR) * BT[j - 1, i]) / (2 * DR * rs)
        P_diss += ETA[j, i] * (jr * jr + jz * jz) * vol
        D = ETA[j, i] * INV_MU0
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jn, iN = j + dj, i + di; mk = mask[jn, iN]
            if mk == 0: continue
            if mk == 1: continue   # free cathode: zero flux by construction
            bf = 0.5 * (BT[j, i] + BT[jn, iN])
            if dj != 0:
                rf = r + dj * 0.5 * DR; area = TAU * rf * DZ
                if rf <= 0.0: continue
                dn = dj * (r_of(jn) * BT[jn, iN] - r * BT[j, i]) / (rf * DR)   # (1/r) d(rB)/dn
            else:
                area = TAU * r * DR; dn = di * (BT[jn, iN] - BT[j, i]) / DZ
            P_res[NAME[mk]] = P_res.get(NAME[mk], 0.0) + D * bf * dn * INV_MU0 * area
        # wall sink
        nbrs = [mask[j + 1, i], mask[j - 1, i], mask[j, i + 1], mask[j, i - 1]]
        w = [1 if m in (1, 2, 4, 5) else 0 for m in nbrs]
        if sum(w) and EI[j, i] >= 1e-9 and T[j, i] > T_WALL:
            n = max(rho[j, i], RHO_FLOOR) / M_AR
            gr = 2.0 / (r * DR * DR); gz = 2.0 / (DZ * DZ)
            g = w[0] * gr * (r + 0.5 * DR) + w[1] * gr * (r - 0.5 * DR) + (w[2] + w[3]) * gz
            kap = wall_kappa(n, AL[j, i], T[j, i])
            de = min(kap * (T[j, i] - T_WALL) * DT * g, 0.5 * EI[j, i])
            P_wall += de * vol / DT
print(f"\n  sum eta j^2 dV {P_diss/1e3:.2f} kW ({P_diss/J:.2f} V; counter {VARC:.2f} V -> {VARC*J/1e3:.1f} kW); P_wall from state {P_wall/1e3:.2f} kW (log {PWALL_LOG/1e3:.1f})")
print("\n=== total energy closure at steady state (kW): hyperbolic boundary + counter - P_wall (LxF cathode/exit terms included)")
hyp = tot_p[3] + tot_d[3]
print(f"  hyperbolic boundary net {hyp/1e3:+8.2f}")
print(f"  - P_wall                {-P_wall/1e3:+8.2f}")
print(f"  hyperbolic + counter - P_wall = {(hyp + VARC*J - P_wall)/1e3:+8.2f}  (physical-only exit/inlet terms close to -3.9 kW; the gap is the gross LxF cathode +60.7 that the implicit step returns unbooked)")
print(f"\n  subsonic exit cells (frozen c_s): {int(subsonic_exit.sum())}")

# ── follow-ups ─────────────────────────────────────────────────────────
print("\n=== follow-ups")
# corrected Poynting (inflow = D B_f dB/dn_outward, same sign both sides)
P_res2 = {}
for j in range(1, NR - 1):
    for i in range(1, NZ - 1):
        if not fluid[j, i]: continue
        r = r_of(j); D = ETA[j, i] * INV_MU0
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            jn, iN = j + dj, i + di; mk = mask[jn, iN]
            if mk == 0 or mk == 1: continue
            bf = 0.5 * (BT[j, i] + BT[jn, iN])
            if dj != 0:
                rf = r + dj * 0.5 * DR
                if rf <= 0.0: continue
                area = TAU * rf * DZ; dn = (r_of(jn) * BT[jn, iN] - r * BT[j, i]) / (rf * DR)
            else:
                area = TAU * r * DR; dn = (BT[jn, iN] - BT[j, i]) / DZ
            P_res2[NAME[mk]] = P_res2.get(NAME[mk], 0.0) + D * bf * dn * INV_MU0 * area
print("  Poynting inflow (sign-corrected):", {k: round(v / 1e3, 1) for k, v in P_res2.items()}, " total", round(sum(P_res2.values()) / 1e3, 1), "kW")
# dissipation by region
diss = {"total": 0.0, "outer annulus r>5.1cm z<10.25": 0.0, "capped eta": 0.0, "r>5.1cm all z": 0.0, "T<5000K": 0.0}
for j in range(1, NR - 1):
    for i in range(1, NZ - 1):
        if not fluid[j, i]: continue
        r = r_of(j); vol = TAU * r * DR * DZ
        jr = -INV_MU0 * (BT[j, i + 1] - BT[j, i - 1]) / (2 * DZ)
        jz = INV_MU0 * ((r + DR) * BT[j + 1, i] - (r - DR) * BT[j - 1, i]) / (2 * DR * max(r, 1e-4))
        q = ETA[j, i] * (jr * jr + jz * jz) * vol
        diss["total"] += q
        if r > R_A and z_of(i) < 0.1025: diss["outer annulus r>5.1cm z<10.25"] += q
        if r > R_A: diss["r>5.1cm all z"] += q
        if ETA[j, i] >= 0.99e-3: diss["capped eta"] += q
        if T[j, i] < 5000.0: diss["T<5000K"] += q
for k, v in diss.items(): print(f"  eta j^2 in {k:32s} {v/1e3:7.1f} kW  ({100*v/diss['total']:.0f}%)")
# I_enc(r) profiles
print("  I_enc(r) kA at z = 2, 5, 8, 10 cm (r = 1.0, 2.0, 3.0, 4.0, 5.0, 5.5, 6.0, 6.375 cm):")
for zc in (2.0, 5.0, 8.0, 10.0):
    i = int(round(zc / 100 / DZ + 0.5))
    print(f"    z={100*z_of(i):5.2f}: " + " ".join(f"{r_of(j)*BT[j,i]/MU0_2PI/1e3:5.2f}" for j in (20, 40, 60, 80, 100, 110, 120, 128)))
# per-face LxF momentum at the anode
for name, cells in (("anode inner (i=82, above)", [(j, 82, +1) for j in range(J_ANODE, NR - 1)]),
                    ("anode outer (i=91, below)", [(j, 91, -1) for j in range(J_ANODE, NR - 1)]),
                    ("backplate (i=1, below, mask5)", [(j, 1, -1) for j in range(1, NR - 1) if mask[j, 0] == 5 and fluid[j, 1]]),
                    ("cathode tip (i=81, below)", [(j, 81, -1) for j in range(1, J_FLUID0)])):
    s = sum(-(DZ / (2 * DT)) * MZ[j, i] * TAU * r_of(j) * DR for j, i, di in cells if fluid[j, i])
    vmean = sum(vz[j, i] for j, i, di in cells if fluid[j, i]) / max(1, sum(1 for j, i, di in cells if fluid[j, i]))
    print(f"  LxF wall term {name:32s} {s:+7.3f} N   mean v_n {vmean:+7.1f} m/s")
# exit: mass fraction in numerically cooled cells
i = NZ - 2
mtot = sum(MZ[j, i] * TAU * r_of(j) * DR for j in range(1, NR - 1) if fluid[j, i])
mcold = sum(MZ[j, i] * TAU * r_of(j) * DR for j in range(1, NR - 1) if fluid[j, i] and T[j, i] < 300.0)
print(f"  exit mass fraction in cells with T < 300 K: {mcold/mtot:.3f}; cells: {sum(1 for j in range(1,NR-1) if fluid[j,i] and T[j,i] < 300)}")
print(f"  exit T at i=103 vs 104 for j=110..128: " + " ".join(f"{T[j,103]:.0f}/{T[j,104]:.0f}" for j in range(110, 129, 3)))

# ── Hall parameter and wall-sink split ────────────────────────────────
print("\n=== Hall parameter x = omega_ce tau_e (NRL tau_e) and where the dissipation sits")
E_CH, M_E = 1.602176634e-19, 9.1093837e-31
d_x1 = d_x02 = 0.0; vol_x1 = 0.0; xs = []
sink = {}
for j in range(1, NR - 1):
    for i in range(1, NZ - 1):
        if not fluid[j, i]: continue
        r = r_of(j); vol = TAU * r * DR * DZ
        jr = -INV_MU0 * (BT[j, i + 1] - BT[j, i - 1]) / (2 * DZ)
        jz = INV_MU0 * ((r + DR) * BT[j + 1, i] - (r - DR) * BT[j - 1, i]) / (2 * DR * max(r, 1e-4))
        q = ETA[j, i] * (jr * jr + jz * jz) * vol
        n = max(rho[j, i], RHO_FLOOR) / M_AR; a = max(AL[j, i], 1e-8); t_eV = max(T[j, i] / 11604.518, 0.1)
        ne_cm3 = max(a * n * 1e-6, 1.0); lnl = eos_lnl(n, a, T[j, i])
        tau_e = 3.44e5 * t_eV**1.5 / (ne_cm3 * lnl)
        # electron-neutral collisions shorten tau_e too (same sigma_en as eta_en)
        nu_en = (1.0 - a) * n * 1e-19 * math.sqrt(8 * K_B * T[j, i] / (math.pi * M_E))
        tau = 1.0 / (1.0 / tau_e + nu_en)
        x = E_CH * abs(BT[j, i]) * tau / M_E
        if q > 0: xs.append((q, x))
        if x > 1.0: d_x1 += q; vol_x1 += vol
        if x > 0.2: d_x02 += q
        # wall sink by neighbour family
        nb = [(mask[j + 1, i], "chamber wall" if z_of(i) < 0.1025 else "FICTITIOUS wall z>10.25"), (mask[j - 1, i], "cathode barrel"),
              (mask[j, i + 1], "anode inner face"), (mask[j, i - 1], "backplate/tip/anode outer")]
        w = [(m in (1, 2, 4, 5)) for m, _ in nb]
        if any(w) and EI[j, i] >= 1e-9 and T[j, i] > T_WALL:
            gr = 2.0 / (r * DR * DR); gz = 2.0 / (DZ * DZ)
            gs = [w[0] * gr * (r + 0.5 * DR), w[1] * gr * (r - 0.5 * DR), w[2] * gz, w[3] * gz]
            kap = wall_kappa(n, AL[j, i], T[j, i]); g = sum(gs)
            de = min(kap * (T[j, i] - T_WALL) * DT * g, 0.5 * EI[j, i])
            for gk, (m, nm) in zip(gs, nb):
                if gk > 0:
                    key = nm
                    if m == 1 and nm == "backplate/tip/anode outer": key = "cathode tip"
                    if m == 2 and nm == "backplate/tip/anode outer": key = "anode outer face"
                    if m == 5: key = "backplate"
                    if m == 4 and nm == "cathode barrel": key = "wall(r-)"
                    sink[key] = sink.get(key, 0.0) + de * (gk / g) * vol / DT
tot = sum(q for q, _ in xs)
print(f"  Ohmic dissipation in cells with x > 1: {100*d_x1/tot:.0f}%   x > 0.2: {100*d_x02/tot:.0f}%   (fluid volume with x>1: {100*vol_x1/sum(TAU*r_of(j)*DR*DZ for j in range(1,NR-1) for i in range(1,NZ-1) if fluid[j,i]):.0f}%)")
xs.sort(key=lambda t: -t[0])
print("  x in the 20 hottest-dissipation cells:", " ".join(f"{x:.2f}" for _, x in xs[:20]))
print("  wall sink by surface (kW):", {k: round(v / 1e3, 1) for k, v in sorted(sink.items())}, " total", round(sum(sink.values()) / 1e3, 1))

# ── exit column profile ───────────────────────────────────────────────
CS = np.sqrt(np.where(fluid, 5.0 / 3.0 * p / np.maximum(rho, 1e-8), 0.0))
print("\n=== exit column (i = 98..104), mass-flux-weighted over fluid rows")
print(f"{'i':>4} {'z cm':>6} {'<p>':>8} {'<T>':>8} {'<vz>':>8} {'<M>':>6} {'min p':>7} {'n M<1':>5}")
for i in range(98, NZ - 1):
    js = [j for j in range(1, NR - 1) if fluid[j, i]]
    mf = np.array([rho[j, i] * vz[j, i] * TAU * r_of(j) * DR for j in js]); w = mf / mf.sum()
    M = np.array([vz[j, i] / CS[j, i] for j in js])
    print(f"{i:4d} {100*z_of(i):6.2f} {sum(w*p[js,i]):8.1f} {sum(w*T[js,i]):8.0f} {sum(w*vz[js,i]):8.0f} {sum(w*M):6.2f} {min(p[js,i]):7.1f} {sum(M<1):5d}")
print("  per-radius, last three cells (p / T / vz / M):")
for j in (5, 20, 40, 60, 80, 100, 110, 120, 126, 128):
    s = f"  r={100*r_of(j):5.2f}cm "
    for i in (102, 103, 104):
        s += f"| {p[j,i]:7.1f} {T[j,i]:6.0f} {vz[j,i]:6.0f} {vz[j,i]/CS[j,i]:5.2f} "
    print(s)
print("  axis (j=1) Mach vs z:", " ".join(f"{100*z_of(i):.1f}:{vz[1,i]/CS[1,i]:.2f}" for i in range(82, NZ-1, 3)))
print("  j=60 Mach vs z:     ", " ".join(f"{100*z_of(i):.1f}:{vz[60,i]/CS[60,i]:.2f}" for i in range(2, NZ-1, 8)))
