# Independent audit: pressure-outlet exit ghost (2026-09-02)

Script: `tools/audit_exit_2026-09-02.py` (`/opt/homebrew/bin/python3.11`,
read-only). Re-run to reproduce every number below.

## 1. Exit-plane geometry and mass flux

Exit column i=104 (mp_nzm2); ghost i=105. All three states have fluid
at every j=1..128 there (no wall-blocked exit rows), so exit area
= sum(2*pi*r_j*dr) = 1.2868e-2 m^2 throughout.

| state | mdot_out | mdot_back | M_w | frac M>=1 | p_exit wtd (min) |
|---|---|---|---|---|---|
| nosink (old) | 5.906 g/s | -0.005 g/s (17 c) | 0.554 | 0% | 2415 (2354) Pa |
| fromfill (old) | 7.258 g/s | -1.229 g/s (52 c) | 0.118 | 0% | 23013 (22712) Pa |
| smoke (new) | 11.244 g/s | 0 (0 c) | 1.080 | 71.1% | 940 (171) Pa |

p_exit min matches the step-line field (mv_exit_probe ex[3]); smoke's
171 Pa is close to NEXT_SESSION's logged 195 Pa.

By radial band (thirds of j=1..128), the new outlet shifts flow
outward: nosink puts 60% inner two-thirds, 0.26 g/s outer third; smoke
puts 4.08 g/s (36%) outer third, where fromfill had net INFLOW
(-1.01 g/s).

**Claim confirmed.** Both old states are subsonic everywhere (0%
supersonic, M_w 0.12-0.55); smoke chokes (M_w 1.08, 71% supersonic by
mass flux, per-cell M 0.92-1.38). fromfill also shows severe backflow
(52/128 cells, density ratio up to 1900x) gone once fixed.

**Caveat**: smoke's mdot_out is 11.2 g/s, 1.9x nominal, a 400-step
blowdown from the old 2.2 kPa floor, not converged. Treat p_exit, M_w
above as a transient snapshot.

## 2. Choked-flow prediction vs Cory

From the smoke state's own exit p, rho (gamma=5/3, alpha=0):
mass-flux-weighted exit T=6763 K, c_s=1532 m/s. Solving rho*A*c_s
= 6 g/s at that T gives rho_choke=3.04e-4 kg/m3, **p_choke = 428.5
Pa**.

Cory's backplate wall pressure is 465 Pa. Old nosink floor 2155 Pa is
4.63x Cory, old fromfill 23000 Pa is 49.5x Cory, this estimate is 0.92x
Cory (within 8%). **The outlet fix is the right order of magnitude,
and better, to explain the wall over-pressure; the old floors were
not.**

Saha caveat: mv_speed's comment flags that 5/3*p/rho over-estimates
c_s once ionization bites (gamma_eff < 5/3). chi_ar = 15.76 eV matches
argon's first ionization energy; 6800 K is the low shoulder of that
band, alpha non-negligible by 10-15 kK, substantial by 20 kK. Lower
gamma_eff raises choked rho at fixed T, but ionization also lowers T
for the same energy, lowering c_s further; these partly cancel and I
have not solved the coupled system, so read 428.5 Pa good to roughly
+-30%. Verdict unchanged.

## 3. mv_ghost_exit review

**Subsonic test**: vz vs c_s=sqrt(5/3 p/rho) is the right kind of
classification (one characteristic enters for 0<M<1), but biased: real
c_s in the ionized band is lower than 5/3*p/rho, so some cells it
calls subsonic are already physically sonic. Not a correctness bug,
but the amb_p branch fires more than it should.

**Energy flux**: the subsonic ghost sets e_int = amb_p/gamma_m1 = 1.5
J/m3 while keeping the fluid's rho and momentum, implying a ghost
temperature of a few to a few tens of K, unreachable by adiabatic
expansion from the hot fluid cell. It pins the boundary pressure but
does not model a physical free-jet expansion (which converts thermal
energy to KE, conserving stagnation enthalpy, rather than discarding
it). The flux's diffusive term (`mv_lxf_field`/`mv_step`) uses one
GLOBAL coefficient dt/(2 dz) set by the domain-wide max wave speed
(`mv_dt`), not a local speed at the exit, so a large fluid-ghost energy
gap is diffused at whatever rate the fastest cell anywhere (likely the
cathode tip) sets, over-cooling the exit versus a locally-consistent
scheme. Watch p_exit/vz for an overshoot past the smooth acceleration
already in the data (j=124: vz 542->918 m/s over the last five cells)
into an unphysically sharp drop.

**Mass/momentum/corners/backflow**: no injection subsonic or
supersonic (rho, mr, mz are zero-gradient copies of the fluid cell).
Backflow (vz<=0) sets amb_rho at rest, a bounded reservoir, not
spurious creation, but it held 52/128 cells under the old scheme; keep
it on the watch list though it reads 0 now. Corner ghosts (j=1,i=105;
j=128,i=105) get whichever single rule their one mask value carries;
faces are direction-split (r-faces read r-neighbors, z faces z), so no
interior cell reads a corner as both at once, likely inert, not
independently verified here. Fluid density next to backflow cells ran
8.2e-4 (nosink) to 0.056 kg/m3 (fromfill) against amb_rho=3e-5, 27x to
~1900x; the old scheme survived thousands of steps against it, but a
jump that size will dominate the global CFL when it reappears.

**Watch list**: `M_exit`<1, `bf`=0 for many segments = still subsonic;
`bf`>0 = backflow, check density ratio; `p_exit` relaxing toward amb_p
without settling = healthy; `p_exit` undershoot toward the 1.5 J/m3
floor, or erratic = the over-cooling above; a `dt` drop with `bf` on
= the density-jump CFL hit predicted.

## 4. Physics I am skeptical of

- The LxF dissipation is one GLOBAL coefficient, no per-face wave
  speed, yet the exit and cathode-tip arc have wildly different local
  speeds; every quiet region gets the fastest cell's viscosity, worth
  remembering for any "converged" profile.
- mdot_out=11.2 g/s at 400 steps is not 6 g/s; do not quote p_exit or
  M_w above as steady-state until mdot_out/mdot_in is flat.
- 428.5 Pa vs Cory's 465 Pa is arguably too good given the +-30%
  ionization uncertainty and a first-order, globally-dissipative
  scheme. Call it order-of-magnitude agreement until a converged run
  and Saha-consistent c_s back it up.
