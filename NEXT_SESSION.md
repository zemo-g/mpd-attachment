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

## Priority 1: reach steady state, then judge the profile

Segment 1 (20k steps, t = 0.69 ms) is still trending: mass +4%/0.1ms and
vmax -3%/0.1ms at the end. Chain resume segments (each 20k ~ 17 min on
the Mini; sed `run_resume = 1.0`, compile, copy binary, run) until mass
and vmax plateau and mdot_out ~ inlet 0.006 (was 1.5x at seg-1 end, down
from 2x at first light). THEN the two open physics reads:

- backplate profile vs the phase-1b parabola (`tools/compare_bp_profile.py
  8000`): at seg-1 end the solver profile is flatter (0.6x the inferred
  parabola at the cathode, 1.9x Cory at the wall, rms 0.40). Do not
  interpret until converged.
- mass balance closure. If mdot_out stays high at plateau, look at the
  inlet Dirichlet interaction with heated backplate pressure.

Long chains belong on the Studio (clone repo, run via fleet :9101 async).

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
$RAIL rail/selftest.rail          # 25 checks
/opt/homebrew/bin/python3.11 tools/render_fields.py 8000 <tag>
/opt/homebrew/bin/python3.11 tools/compare_bp_profile.py 8000
```
