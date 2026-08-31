# Next session: converge, Hall IMEX, then the J-sweep

State as of 2026-08-31 late evening: README Status is current. Phases
0/1/1b done. **Phase 2 Priority 1 (implicit resistivity) is CLOSED**:
operator-split backward-Euler Thomas solve per z-line and r-line, faces
folded into the tridiagonal, physical Spitzer eta [1e-7, 2e-5], Ohmic
heating on, resistive dt limit removed. Selftest 25/25 (checks 22-25 lock
the implicit operator). 20k-step 8 kA run: identity -5.8e-5, tip p 3.0%
of Cory, T_exhaust 25.9 N vs ~25 measured, vmax decays monotonically
through the old detonation window, floor never fires. Hall smoke PASS on
the resistive checkpoint. `run_resume = 1.0` chains segments.

## Priority 1: ride out the relaxation, then judge everything

**The inlet was not metering (found by `rail/phase2_massaudit.rail`,
fixed same night, commit e64c9b4): the naive Dirichlet ghost admitted
1.34x nominal through the LxF face flux, so every pre-fix number ran at
~8 g/s, not 6.** The metered-inlet BC set off a big relaxation: the
domain sheds ~2.7x excess mass through a damped breathing mode (period
~0.3-0.4 ms; tip p rang 3563..4344 Pa during seg 3; mass still draining
at its end). Numerics stayed clean throughout (identity ~1e-4, floor 0,
dt healthy) - it is dynamics, not instability.

Chain 40-60k-step segments (sed `run_resume = 1.0`, compile, copy
binary, run; ~50 ms/step on the Mini) until mass, vmax, ptip, pwall,
mdot_out (all in the periodic print) settle. Only then:

- tip p and wall p vs Cory (pre-fix snapshots hit 3.0% / 1.9x but at the
  wrong mdot - they are void as validation numbers)
- backplate profile vs the phase-1b parabola
  (`tools/compare_bp_profile.py 8000`)
- T_exhaust vs measured ~25 N at 8 kA
- `phase2_massaudit` on the settled checkpoint: inlet ~0.006, and the
  net should match the (near-zero) mass trend

If the breathing mode is too weakly damped to settle in a few segments,
consider starting COLD with the metered inlet (the cold fill may reach
the true state faster than relaxing from the over-dense one). Note the
solver is single-threaded and the M4 Mini is the fastest core in the
fleet - the Studio's role is the parallel J-sweep, not single long
chains.

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
  tridiagonal lanes 41341+). Every runner that calls mv_step must
  allocate that size.

## Commands

```bash
cd ~/projects/mpd-attachment
RAIL=~/projects/rail/rail_native
$RAIL rail/phase2_run.rail && cp /tmp/rail_out /tmp/p2bin && /tmp/p2bin   # full run (~17 min)
# resume chain: sed 's/run_resume = 0.0/run_resume = 1.0/' then compile+copy+run
$RAIL rail/phase2_hall_smoke.rail && cp /tmp/rail_out /tmp/hs && /tmp/hs  # needs ckpt
$RAIL rail/phase2_identity.rail   # layer-0 diagnostics (always green)
$RAIL rail/phase2_massaudit.rail && cp /tmp/rail_out /tmp/p2a && /tmp/p2a  # boundary mass flux by family
$RAIL rail/selftest.rail          # 25 checks
/opt/homebrew/bin/python3.11 tools/render_fields.py 8000 <tag>
/opt/homebrew/bin/python3.11 tools/compare_bp_profile.py 8000
```
