# Wall energy sink: design (written during the cfl15 window, 2026-09-01)

## Why walls and not radiation

tools/sink_estimate.py on the pf2 state (honest 6 g/s, pre-runaway):

| sink | magnitude | vs 42.8 kW Ohmic |
|------|-----------|------------------|
| bremsstrahlung (exact) | 0.026 kW | 0.06% |
| total radiation, x100 line band | 2.6 kW | 6.1% |
| wall conduction, kappa 0.3 W/m/K | 670 kW | 16x |
| wall conduction, kappa 3.0 W/m/K | 6700 kW | 157x |

Radiation cannot brake anything at these densities: FALSIFIED without a
solver session. Wall conduction is the dominant omitted sink by 2-3
orders of magnitude. The current solid-face ghosts (mv_ghost_gas
mirrors, mask 1/2/4/5) are adiabatic free-slip: the model's electrodes
absorb NOTHING, where real MPD electrode heat loss is a first-order
power channel.

The estimate is an instantaneous upper scale (a real thermal boundary
layer self-limits); the honest question - does wall cooling brake the
8 kA / 6 g/s runaway - is answered by one segment, not by the estimate.

## Two implementations

(a) COLD-WALL GHOST: set ghost e_int so the face sits at 300 K, keep
    ghost rho copied (mass flux through walls stays EXACTLY zero, so
    selftest 26 and the audit are untouched). The LxF diffusive term
    (dx/4dt)(en_g - en_c) then carries heat out through the scheme's
    own face flux.
    + zero new constants, no dt-stability question (implicit in scheme)
    - the implied conductivity is the LxF numerical one (~0.5 v dx):
      resolution- and velocity-dependent, physically arbitrary.

(b) EXPLICIT WALL-FLUX SINK: subtract q = kappa_eff(T, alpha) *
    (T - 300) / (dx/2) * A_face / V_cell from e in every solid-adjacent
    fluid cell, kappa_eff = electron (Spitzer ~ T^2.5) + neutral argon,
    with a dt limiter (sink per step <= half the cell's thermal energy).
    + physical, defensible, tunable only through literature kappa
    - new constants + a limiter; kappa band [0.3, 3] is a real
      uncertainty; boundary layer at 0.5 mm cells is under-resolved
      either way.

RECOMMENDED: (b), because the whole point is a PHYSICAL brake whose
magnitude we can defend; (a)'s effective kappa changes with the very
velocity runaway we are trying to diagnose. Ship with a per-face energy
accounting counter (P_wall printed at segment end) BEFORE tuning
anything - counter first, per the repo law.

## Gate plan

- selftest before/after; new check: wall sink removes energy at the
  analytic rate on a uniform hot state, and total mass is untouched.
- One segment from phase2_ckpt_pf2_honest6g.f32. Compare vmax(t)
  against pf3 with tools/compare_runs_t.py.
- Possible outcomes: (i) brakes to a plateau -> chain to convergence and
  judge attachment honestly; (ii) slows but still runs away -> the
  missing brake is in the momentum/current channel, anomalous
  resistivity (option B) moves up; (iii) unchanged -> wall cooling is
  not the mechanism; B moves up unambiguously.

## Standing caveat

This does NOT touch the "arc too quiet" finding: wall cooling REMOVES
energy, it does not add the missing arc voltage. If the runaway brakes
but V_arc stays ~5 V at the plateau, anomalous resistivity remains the
open physics item for the voltage, separately from the stability
question.
