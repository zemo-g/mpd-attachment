# Next session: Phase 2 hardening, then the J-sweep

State as of 2026-08-31 evening: README Status section is current. Phases
0/1/1b done; Phase 2 first light passed (identity 8.9e-4, tip pressure
4.4% of Cory, thrust 76%) in the numerical-resistivity regime. Selftest
21/21. Checkpointing + floor mass budget landed; Hall smoke harness at
`rail/phase2_hall_smoke.rail`.

## Priority 1: explicit resistivity - now REQUIRED, not optional

**Late addition (v2 run, out/phase2_run_v2.log): the numerical-resistivity
regime is METASTABLE.** Its only damping is LxF diffusion ~0.5 v dx, which
fades as the flow converges; a re-run tracking the good run through step
14k destabilized at t ~ 0.7 ms as vmax settled (good run stopped healthy
at 0.92 ms by phase luck). True steady state therefore needs real
resistivity. That makes this priority the gate for everything below.

Tonight's finding (A/B-isolated, commits 8864ef3 + this one): explicit
Spitzer eta (eta/mu0 ~ 16 m^2/s) is unstable at dr = 0.5 mm no matter how
the term is written, because the resistive boundary layer sqrt(D t) ~ 0.4mm
is sub-cell against pinned Dirichlet faces:
- curl-form eta j: checkerboard-transparent, diverges over ~10k steps
- compact 5-point diffusion: detonates at Dirichlet corners with
  extrapolated (2p-f) ghosts via quadratic ghost-pressure feedback
- first-order ghosts + energy-consistent pairing (dE = B dB/mu0 + eta j^2,
  code still present in `mv_diff_cell`): still detonates (sub-cell layer)

**Recommended fix: operator-split implicit diffusion.** Thomas tridiagonal
solve per r-line and per z-line (unconditionally stable, keeps dt at CFL,
~40 lines of Rail). Dirichlet faces enter the tridiagonal RHS directly, no
ghost feedback. Alternative: subcycled explicit with face-flux Dirichlet
form; weaker but simpler. Grid refinement near surfaces is the expensive
third option.

Gate: 1000-step probe must hold identity < 1e-2 and tip p within 2x Cory
BEFORE a 20k run (probe recipe: sed run_nsteps in phase2_run.rail, see
tonight's /tmp/phase2_v.rail flow in the log).

## Priority 2: Hall, for real

`run_hall = 1.0` activates curl-form Hall + grad-pe (gated in `mv_step`).
Whistler dt at the vacuum Hall floor (n = 1e19) is ~3e-13 s: explicit is
hopeless for converged runs. After P1's implicit machinery exists, do IMEX
or Hall subcycling. The smoke harness resumes `out/phase2_ckpt.f32` and
checks boundedness only. Long converged Hall runs belong on the Studio
(clone the repo there; rail_native is ARM64-native; drive via fleet :9101
async jobs).

## Priority 3: run hygiene

- **Resume**: `mv_load_state`/`mv_save_state` exist (f32); the healthy
  checkpoint is `out/phase2_ckpt.f32` (12k steps, t ~ 0.55 ms, inside the
  stable window). Add a run_resume flag and chain segments AFTER P1 lands
  (chaining without real eta just walks into the metastability edge).
- **Floor budget**: printed at end of every run now. If it stays a
  significant fraction of mdot, lower rho_min_state or make the floor
  momentum-conserving.
- **Mass balance**: mdot_out was 2x inlet at first light; recheck after
  longer convergence + floor accounting.

## Then the actual physics program

1. **J sweep**: 8/10/12/14 kA at 6 g/s (current BCs handle J <= J_t2; for
   J > 14 kA add the outer-face j_o prescription and extend the domain to
   r_ao). Produce solver C_T(J) vs the Phase 0 scoreboard + Cory profile
   comparison per J (`tools/compare_bp_profile.py J`). That comparison IS
   the Phase 2 sign-off in the program doc's terms.
2. **Low-current points** (3-5 kA, 3 g/s inlet variant): can the solver's
   backplate pinching reproduce the C_T rise the xi-relation over-predicts
   (rms 1.19 window)? This is where it earns its complexity.
3. **Phase 3** (the research): replace the B_theta Dirichlet electrode
   faces with sheath BCs and let attachment distribute. Predict
   j_i/j_o/phi vs Rudolph, p(r_c,z0) vs the phase-1b inferred curve.
   Wire experiment-loop here per program.md.

## Standing traps for this repo (cost hours tonight; do not relearn)

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

## Commands

```bash
cd ~/projects/mpd-attachment
RAIL=~/projects/rail/rail_native
$RAIL rail/phase2_run.rail && cp /tmp/rail_out /tmp/p2bin && /tmp/p2bin   # full run
$RAIL rail/phase2_hall_smoke.rail && cp /tmp/rail_out /tmp/hs && /tmp/hs  # needs ckpt
$RAIL rail/phase2_identity.rail   # layer-0 diagnostics (always green)
$RAIL rail/selftest.rail          # 21 checks
/opt/homebrew/bin/python3.11 tools/render_fields.py 8000 <tag>
/opt/homebrew/bin/python3.11 tools/compare_bp_profile.py 8000
```
