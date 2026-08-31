# Next session: conservative-in-r transport, then converge for real

State as of 2026-08-31 night: README Status is current. Phases 0/1/1b
done. **Implicit resistivity is CLOSED** (Thomas per line, physical
Spitzer eta, unconditionally stable; identity ~1e-4 through every regime
visited, floor never fires, Hall smoke PASS). **Inlet metering is CLOSED**
(flux-metered ghost; audit reads 0.00599999.. on the live state). What
those two exposed is the new gate:

## Priority 1 - THE GATE: interior mass creation (needs a greenlight on approach)

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

**Approach (b) - recommended: area-weight the r-transport.** Keep the
state unweighted; multiply r-face fluxes by r_face/r_cell and replace
the quarter-average's r-neighbors with (r_nb/r_cell)-weighted averages;
mass geometric source then DROPS (it is the continuum residue of exactly
this weighting); re-derive the m_r hoop source in the weighted form
(p_t appears with + sign, B^2/mu0 stays), m_z/E sources drop too.
Localized to mv_flux_r/mv_lxf_field/mv_geom_src; conserves mass/m_z/E to
machine precision; m_r keeps a true source (fine, momentum has one).
**Approach (a): full rewrite in r-weighted conserved variables (rU).**
Same algebra made structural; more invasive, same result. Either way:
re-validate the stress identity and per-surface splits, add a selftest
check (uniform-state + solid-body-ish field must conserve total mass to
1e-12 over N steps - the same-day mechanism for this defect), and
COLD-START a metered run (do not relax from the polluted seg-4 state).
An audit run's "net" line must then match the run's dm/dt trend - that
comparison is the standing gate (if two things must agree, something
must compare them).

## Priority 2: converge at true 6 g/s, judge everything at the plateau

Cold-start post-fix, chain 40-60k segments (~50 ms/step on the Mini)
until mass/vmax/ptip/pwall/mdot_out (all in the periodic print) settle.
Then: tip/wall p vs Cory, backplate profile vs the phase-1b parabola
(`tools/compare_bp_profile.py 8000`), T_exhaust vs ~25 N measured, and
the mass audit. ALL pre-fix numbers (3.0% tip match included) ran at
~8 g/s with a mass-creating interior and are void as validation. The
solver is single-threaded; the M4 Mini is the fastest core in the fleet
(Studio is for the parallel J-sweep, not single chains).

## Priority 3: Hall, for real (IMEX)

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

## Priority 4: the J-sweep = Phase 2 sign-off

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
