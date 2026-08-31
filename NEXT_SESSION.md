# Next session: converge the cold conservative run, then judge vs Cory

State as of 2026-08-31 late night: README Status is current. Phases
0/1/1b done. Three solver gates CLOSED the same day: **implicit
resistivity** (Thomas per line, physical Spitzer eta, identity ~1e-4
through every regime, Hall smoke PASS), **inlet metering** (flux-metered
ghost, audit reads 0.00599999.. live), and **interior mass conservation**
(greenlit and SHIPPED, commit f0f7fb8 - see below). The cold
conservative run is chaining toward the true 6 g/s steady state.

## CLOSED 2026-08-31 night: interior mass creation (kept for the record)

**Evidence.** `rail/phase2_massaudit.rail` decomposes boundary mass flux
with the scheme's own face-flux form (validated: reproduces the run's
mdot_out; walls exactly 0; metered inlet exactly 0.006). On seg 4
(out/phase2_run_implicit_seg4.log, the post-fix relaxation): boundary
net = +2.0e-3 kg/s while the domain gains ~8.8e-3 kg/s => **the interior
discretization manufactures ~7e-3 kg/s - more than the physical inlet
flow**. Cross-check on the milder seg-2 state: boundary -0.96e-3 vs
observed +0.33e-3 => +1.3e-3 created. Cause: the update is
non-conservative in r - the LxF quarter-average and the unweighted
r-fluxes move rho between cells of different radius, so the r-weighted
volume integral drifts at O(dr/r) per cell (O(1) at the axis, j=1 has
dr/r = 2), amplified by 1/dt when the state is violent (the LxF
diffusive velocity is dx/4dt). No steady state computed on this scheme
is a mass balance; convergence chasing is pointless until this closes.

**The fix as shipped (approach b, refined):** fields 0..3 update in
face-flux form on the conserved r*U - every r-face flux is
r_f [0.5(F_c+F_nb) - (dr/4dt)(U_nb-U_c)], update divided by r_j. So
sum(r_j U_j) telescopes to the boundary EXACTLY; r_f = 0 kills the axis
face automatically; r_f+ + r_f- = 2 r_j keeps the self-weight identical
to the flat quarter-average (no stability change); every mirror-ghost /
metered-inlet cancellation carries over. Geometric sources reduce to the
exact residue: m_r gets +(p - B^2/2mu0)/r, mass/mz/E get none. bt stays
FLAT (azimuthal induction dB/dt + d_r(vr B) + d_z(vz B) = 0 is a flat 2D
law - do NOT area-weight it). Selftest check 26 is the mechanism: after
a 50-step warm-up, one step's d(total mass) must equal dt * boundary
rate (mv_bmass_rate); measured residual 1.6e-22 on dm 4.2e-13.

**Cold-start detonation found en route (also fixed):** the metered inlet
ghost paired reflected momentum with the copied near-vacuum density
(ghost vz ~ 3e5 m/s, invisible to mv_dt's fluid-only CFL scan) and blew
the inlet row within steps. Ghost vz is now capped at in_vg_cap = 600
m/s (later 2000): the choked valve-opening transient; the cap
disengages in the operating regime, where metering stays exact.
**Follow-up finding: a cold start from near-vacuum does not fill AT
ALL** - the full 8 kA field is a magnetic pump, the chamber empties
faster than the choked valve feeds it, v_A rises, dt collapses
(out/phase2_cold1.log: mass 8x DOWN, vmax 110k, dt 1.4e-9 at 60k
steps). Real devices flow gas before striking the arc. Fix (d7e4825):
mv_init prefills 300 K argon at fill_rho = 2e-3 (the expected steady
mean; the steady state does not depend on the init), which also drops
init v_A ~15x so dt0 is ~7x bigger; cap raised to 2000 m/s.

## Priority 1: converge at true 6 g/s, judge everything at the plateau

out/phase2_cold2.log is the first PREFILLED conservative segment (60k;
cold1 was the death-spiral record). Chain via run_resume (~50 ms/step
on the Mini) until
mass/vmax/ptip/pwall/mdot_out (all in the periodic print) settle. Then:
tip/wall p vs Cory, backplate profile vs the phase-1b parabola
(`tools/compare_bp_profile.py 8000`), T_exhaust vs ~25 N measured, and
`phase2_massaudit` (its net must match the run's dm/dt trend - that
comparison is the standing gate). ALL pre-conservative numbers (3.0% tip
match included) ran at ~8 g/s with a mass-creating interior and are void
as validation. The solver is
single-threaded; the M4 Mini is the fastest core in the fleet (Studio is
for the parallel J-sweep, not single chains).

## Priority 2: Hall, for real (IMEX)

`run_hall = 1.0` still uses explicit curl-form Hall at whistler dt
(~3e-13 s): hopeless for converged runs. Now that the Thomas machinery
exists, the Hall term wants either (a) IMEX with the Hall flux treated
implicitly along lines - note Hall in pure-B_theta axisym is a nonlinear
advection of B along its own contours (whistler drift), so a
Picard-lagged coefficient linearization per line solve is the natural
form; or (b) super-time-step subcycling of the Hall term alone between
fluid steps. Start with (b): it reuses the smoke harness gate and needs
no new linear algebra; measure how far dt_hall can stretch before the
identity drifts.

## Priority 3: the J-sweep = Phase 2 sign-off

8/10/12/14 kA at 6 g/s from converged states (current BCs handle
J <= J_t2 = 14 kA; above that add the outer-face j_o prescription and
extend the domain to r_ao). Produce solver C_T(J) vs the Phase 0
scoreboard + per-J Cory profile comparison. Then the low-current window
(3-5 kA): can backplate pinching reproduce the C_T rise the xi relation
over-predicts (rms 1.19)? That is where the solver earns its complexity.

Then Phase 3 (sheath BCs, attachment released) per program.md - wire
experiment-loop there.

## Standing traps for this repo (do not relearn)

- **Rail compiler bug**: top-level float constant passed as a user-fn arg
  garbles a callee branch. Launder with `let x = 0.0 + const`. Repro:
  `notes/rail-const-arg-bug.md`; selftest check 21 guards it. Needs a
  compile.rail session.
- Float-marker quirks: let-bind every user-fn float result; force with
  `1.0 *` before comparisons.
- `rail_native run` IGNORES --out-prefix (passes it to the program).
  Long/parallel runs: compile, `cp /tmp/rail_out <private>`, run that.
- Loop TCO reliable through 8 args; 9+ silently corrupts. Bundle arrays.
- Imports don't dedupe: library files import nothing; runners import the
  chain (pbt, semi_lib, mhd_pbt, stress_diag, mpd_solver).
- stdlib mhd_mpd.rail double-counts the Lorentz force and has the wrong
  B_theta axial flux sign; the fork in rail/mpd_solver.rail is the
  corrected reference. Upstream a fix when convenient.
- The implicit solver's Dirichlet fold is ghost = 2*face - cell (linear
  extrapolation): exact for linear profiles, O(dr^2) for curved ones.
  Selftest 22/25 encode which is which - don't "fix" 22 to be exact.
- scr is 41861 floats (er 0 / ez 13780 / parr 27560 / fmass 41340 /
  tridiagonal lanes 41341+) and fb is 25 (4 neighbor flux vectors + the
  cell's own r-flux at offset 20). Every runner that calls mv_step must
  allocate those sizes.

## Commands

```bash
cd ~/projects/mpd-attachment
RAIL=~/projects/rail/rail_native
$RAIL rail/phase2_run.rail && cp /tmp/rail_out /tmp/p2bin && /tmp/p2bin   # full run (~17 min)
# resume chain: sed 's/run_resume = 0.0/run_resume = 1.0/' then compile+copy+run
$RAIL rail/phase2_hall_smoke.rail && cp /tmp/rail_out /tmp/hs && /tmp/hs  # needs ckpt
$RAIL rail/phase2_identity.rail   # layer-0 diagnostics (always green)
$RAIL rail/phase2_massaudit.rail && cp /tmp/rail_out /tmp/p2a && /tmp/p2a  # boundary mass flux by family
$RAIL rail/selftest.rail          # 26 checks
/opt/homebrew/bin/python3.11 tools/render_fields.py 8000 <tag>
/opt/homebrew/bin/python3.11 tools/compare_bp_profile.py 8000
```
