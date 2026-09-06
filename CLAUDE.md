# CLAUDE.md - MPD current-attachment program

Predict current attachment in self-field MPD thrusters; validation
target is the Princeton Benchmark Thruster (argon, 6 g/s, 8 kA).
Everything is Rail plus a few Python post-processors. **Current state
and next block: NEXT_SESSION.md. Full history: README.md. The physics
program: program.md.** Style: no em-dashes anywhere.

## Where things run (since 2026-09-01)

**The Studio is the compute and operating node.** The Mini remains a
dev mirror; keep the two in sync with rsync when working across them.

- Compile ON the Studio with the master rail clone:
  `RAIL=~/projects/rail-public/rail_native` (verified 31/31 here).
  Do NOT use `~/projects/rail` on the Studio: it sits on an
  experimental branch (`next`) and its binary SEGFAULTS this repo's
  code. Never touch that clone's state; it is parallel work.
- On the Mini the usual `~/projects/rail/rail_native` works.

## The rhythm

Diagnose before coding: evidence of root cause, ~2 approaches with
tradeoffs, greenlight, then execute without ceremony. "Plan" means
plan, do not implement. Every human-found defect ships as fix AND a
same-day selftest check. Never quote our own numbers from docs;
re-measure (published numbers lag the work).

## Gates (run before AND after any solver change)

```bash
cd ~/projects/mpd-attachment
RAIL=~/projects/rail-public/rail_native        # Studio (Mini: ~/projects/rail/rail_native)
$RAIL run rail/selftest.rail                   # 41 checks; grep the last line, exit code lies
```
- Checks 22-25 lock the implicit Thomas operator (22 is boundary-order
  by design, do NOT "fix" it to exact). Check 26 is the mass gate: one
  measured step, dm == dt * boundary rate to 1e-6 rel, floor silent.
  Checks 27-31 lock the Saha EOS and the partially-ionized eta against
  independently computed Python references. Checks 32-33 lock the
  prescribed-flux inlet: counter exact at operating density; the face
  the scheme consumes exact on a VACUUM inlet row (S = 2 rho_in v_in,
  jump 0) with the counter agreeing.
  Checks 34-35 lock the MUSCL reconstruction (exact on linear data,
  clipped at extrema). Check 36 locks the wall sink (analytic rate,
  mass untouched, counter books the same Joules). Check 37 locks the
  Ohmic counter (fb slot 41: dt eta j^2 V_fluid with bt = c r, V_fluid
  summed independently of the current stencil). Checks 30-31 carry the
  Coulomb-logarithm references (NRL ln(Lambda) 5.33 / 6.22). Check 38
  locks `wall_kappa` (neutral argon 0.0177 (T/300)^0.7 weighted
  1 - alpha, Spitzer electron conduction weighted alpha; fails 28x on a
  constant kappa). Check 39 locks the pressure-outlet ghost (three
  branches: subsonic outflow carries amb_p, supersonic zero-gradient,
  backflow ambient at rest; bt negated) and `mv_exit_probe` (mass-flux-
  weighted exit Mach, backflow count, min exit p); the old zero-gradient
  ghost fails it. Checks 40-41 lock the FREE cathode (btp slot 0 = 1.0):
  tip ghost copies the fluid B, barrel ghost carries B_f r_f / r_g, the
  corner takes the tip form, slot 0 = 0.0 restores 2 face - fluid; and
  the Neumann fold `mv_tri_neu_l` is EXACT (1e-12) on c/r and on a
  z-uniform line where the Dirichlet fold is only boundary-order (7e-4).
- Run the selftest FROM THE REPO DIR (imports resolve relative to cwd;
  from elsewhere it dies in ld with `_run_hall` undefined).
- After a converged run, the standing gate: `phase2_massaudit`'s
  boundary net must match the run's observed dm/dt trend.
- The stress identity prints at every segment end (expect ~1e-4).

## Running convergence segments

```bash
$RAIL rail/phase2_run.rail && cp /tmp/rail_out /tmp/p2bin
nohup /tmp/p2bin > out/phase2_<tag>N.log 2>&1 &
tail -f out/phase2_<tag>N.log   # self-reports wall=..s ..ms/step eta ..min every 2000 steps
```
- `run_resume = 1.0` in rail/phase2_run.rail chains from
  out/phase2_ckpt.f32 (written at each segment end). ~96 ms/step on
  the Mini M4, ~155 on the Studio M1; 20k steps per segment.
- Judge the plateau on the periodic print (mass, vmax, ptip, pwall,
  mdot_out all flat), never a single segment's endpoint.
- Named baseline checkpoints: phase2_ckpt_ideal6g.f32 (ideal EOS),
  phase2_ckpt_saha_capped6g.f32 (Saha EOS, old capped eta).

## Post-processing (needs /opt/homebrew/bin/python3.11 + numpy/matplotlib)

```bash
/opt/homebrew/bin/python3.11 tools/render_fields.py 8000 <tag>   # hero + 4-panel from state.csv
/opt/homebrew/bin/python3.11 tools/alpha_map.py <tag>            # Saha ionization map + stats
/opt/homebrew/bin/python3.11 tools/compare_bp_profile.py 8000    # backplate profile vs Cory
$RAIL rail/phase2_massaudit.rail && cp /tmp/rail_out /tmp/p2a && /tmp/p2a
```

## Standing traps (hard-won, do not relearn)

- **2026-09-05 audit resolutions (read notes/audit_2026-09-05.md and the
  2026-09-05 entry of notes/pion_chain_log.md before touching any of
  these).** (1) The exit face (`mv_face_zout`) and the open radial
  boundary past the anode (mask 8, `mv_face_rout`) carry the choked or
  expanded face state from `mv_out_state`, with NO LxF jump; the
  runner's `mdot_out` / `T_exhaust` read the face (exit plane + side).
  `M_exit=` is the exit CELL Mach and reads ~0.95-1.05 by construction
  now; it is no longer the boundary-health signal (p_exit is). (2) Solid
  faces (masks 1/2/4/5) carry no B and no energy in the hyperbolic step
  (`mv_face_solid`); the wall force keeps the pair form. (3) The three
  corner ghosts get per-face mirror states (`mv_face_rcorner`,
  `mv_face_zcorner_in/out`); electrode families in the massaudit are 0.
  (4) j = 129 is mask 8 for z past the anode outer face: no wall, no
  sink there. (5) `mv_eta_calc` is the Braginskii TRANSVERSE Spitzer on
  the Hall parameter `eos_hall_x` plus the e-n term on the Maxwellian
  averaged `eos_sig_en(T)`; `wall_kappa n a t b` takes |B|. (6) The
  ANODE is free (`run_free_anode = 1.0`, btp slot 1): bore d(rB)/dr = 0,
  faces dB/dz = 0, `mv_tri_neu_r`. (7) `mv_step` = `mv_step_res` then
  `mv_step_hyp`; the mass gate reads the boundary rate AFTER the
  resistive phase (the exit face depends on p). (8) The step line prints
  `E_tot=` and `P_impl=` (scr_dme); the thrust target is
  `thrust_meas_ar6_8ka` 24.0 +- 0.9 N (fig-1 digitized; "24.6" was
  never derived); tip 2104 and root 1662 are INFERRED, not Cory data.
  Every number from before 2026-09-05 sat on the cfl-dependent scheme:
  cfl 0.15 moved wall/tip/V_arc/P_wall by 10-16% on the old model.

- **The cathode is a FREE ideal conductor (2026-09-03, `run_free_cath =
  1.0`).** Anode, backplate, wall and inlet faces stay prescribed
  (mp_build_btp); the cathode faces are E_t = 0 with no sheath, which
  with zero normal velocity is eta j_t = 0: barrel j_z = 0 (d(rB)/dr = 0)
  and tip j_r = 0 (dB/dz = 0). Backplate face pins J at the root, axis
  pins 0, so J still enters the cathode; WHERE along the surface is now
  the solution (read I_enc(z) from B at j = 20 in the state csv). Every
  tip/wall/profile number before this sat on the prescribed 80/20
  linear split with the pressure maximum at the cathode ROOT. Set
  run_free_cath = 0.0 to reproduce the prescribed model; never edit the
  split in mhd_pbt to "tune" attachment.

- **`$RAIL run file.rail` compiles AND RUNS it in the current dir.** For
  phase2_run.rail that means a full 20k-step segment resuming from
  `out/phase2_ckpt.f32` in the REPO, which it then overwrites. Build
  production binaries with the compile-only form `$RAIL file.rail && cp
  /tmp/rail_out ...` (as the recipes above do) and run them in their
  own working dir. Bit 2026-09-01 late: guard ckpt restored from
  /tmp/ckpt_guard.f32.
- **The outflow ghost (mv_ghost_exit, 2026-09-02) is superseded at the face by mv_face_zout (2026-09-05, above); the ghost still feeds the sweeps and the backflow branch.** History: The
  old mask-7 ghost was a zero-gradient copy; on a subsonic exit nothing
  set the incoming characteristic, so the chamber sat on an arbitrary
  pressure floor (2.2 kPa on the nosink plateau, 23 kPa on the filled
  sink state, p RISING toward the exit, exit Mach 0.04-0.85) and two
  attractors coexisted. Now a subsonic exit cell sees amb_p in its
  ghost, the exit chokes (smoke: M_exit 0.58 -> 1.06 in 400 steps,
  p_exit 1728 -> 195 Pa, no dt dip). Step lines print `M_exit=`, `bf=`
  (backflowing exit cells) and `p_exit=`; a plateau with M_exit < 1 or
  bf > 0 is a boundary problem before it is physics. Every tip/wall/
  profile number from before this change sat on that floor.
- **Monitor pattern for inlet starvation is `mdot_in=0\.00[0-4]|mdot_in=
  0\.0050`**, NOT `0\.00[0-5]` (that matches the healthy 0.00599 and
  fired on step 0). Dry-test against a healthy log: 0 hits.
- **`1.0 * int_const` in a float comparison silently fails** (selftest
  check 39 hit it with `1.0 * mp_nrm2`); write the float literal.
- **The wall sink conducts with the cell's own kappa** (2026-09-02):
  `wall_kappa n a t`, ln(Lambda) shared with eta via `eos_lnl`. The
  constant kappa_wall = 1 filled the chamber overnight (P_wall 90% of
  P_ohm, 45x cold sheet at the wall, exit reversed); it is gone, do not
  bring it back as a knob. Step lines print P_wall; read it against
  V_arc * J.
- **eta_ei carries the NRL Coulomb logarithm** (2026-09-01 late). The
  old 5.0e-5/T^1.5 was ln(Lambda) = 0.96, a 4-5x too-conductive arc in
  the current-carrying cells (assistant claim 001a). Every V_arc / Ohmic
  number from before this change is under the legacy coefficient;
  `tools/attachment_map.py` prints both. The step line now prints
  `V_arc=` (P_ohm / J from fb slot 41).
- **Top-level float-const references are runtime atofs** (~50ns + a
  locale lock, EACH evaluation). Inline literals and args are free.
  Hoist constants out of hot loops. notes/rail-const-atof.md.
- **scr is 55647 floats** (er 0 / ez 13780 / parr 27560 / fmass 41340 / dme 55641 / corner 55642-55645 / anode flag 55646 /
  tri 41341-41860 / eta cache 41861+); **fb is 41 since 2026-09-01** (MUSCL face sums S at 0/5/10/15, face
  jumps d at 20/25/30/35, cumulative wall-sink Joules at 40; it was 25
  before that day). The hyperbolic step is second-order
  (piecewise-linear minmod reconstruction, faces touching any non-fluid
  cell drop to first order so every ghost/metering cancellation is
  bit-preserved). Anything calling
  mv_rco/mv_zco/mv_heat_loop directly must fill the eta cache first
  (mv_eta_loop st scr 0) or the operators silently run eta = 0.
- Rail compiler bug: a top-level float constant passed as a user-fn
  ARG garbles a callee branch; launder `let x = 0.0 + const`
  (notes/rail-const-arg-bug.md, selftest check 21).
- Float-marker: let-bind every user-fn float result; force with `1.0 *`.
- Loop TCO reliable through 8 args; 9+ silently corrupts.
- `rail_native run` IGNORES --out-prefix; compile then run a copied
  binary. Imports do not dedupe (libraries import nothing; runners
  import pbt, semi_lib, mhd_pbt, stress_diag, mpd_solver in order).
- **The inlet is a PRESCRIBED-FLUX face (mv_face_zin, 2026-09-01), not
  a ghost.** History, so it is never rebuilt: the flux-metered ghost
  (ghost rho = fluid rho, momentum reflected around the nominal) metered
  MASS exactly but carried a momentum flux 0.5 mz_g^2/rho_c that scales
  as 1/rho_c: ~1e5 Pa at rho_c 3.5e-4 against a physical 2.2e3 Pa. The
  saved pf2/pf3/m2cfl15 states had vmax IN the inlet row. Its velocity
  cap, however gated, also engaged whenever the row thinned (4.2e-3 of
  6.0e-3 kg/s for three segments; 2.87e-3 in every second-order
  segment) and the comment justifying it ("a mass-flow controller cannot
  force 6 g/s into vacuum") is false: a choked injector delivers fixed
  mass flow regardless of downstream pressure. The face now carries
  rho_in v_in, rho_in v_in^2 + p_in, (e_in + p_in) v_in in every regime.
  **Read `mdot_in`, never the nominal**, and arm every run monitor with
  the corrected starvation pattern above (dry-test it against a healthy
  log first: 0 hits). A counter nobody reads is not a counter.
- **The massaudit gate self-checks now.** It was a COPY of the face
  formula, so it silently audited the OLD scheme after the inlet
  changed (0.211 kg/s at the inlet). It now takes one real mv_step and
  prints |observed dm/dt - floor - net|/|net| with GATE PASS/FAIL
  (4.3e-11 on pf2). If that line fails, the family table is stale, not
  the solver.
- A converged-looking match can be a wrong-flow artifact. That chain hit
  tip p 2074 vs Cory 2104 (+1.4%) on the program's headline number while
  running at 70% mass flow. Verify `mdot_in` before believing any
  agreement.
- The ignition transient under partially-ionized eta detonates a
  frozen dt within ~50 steps: always adapt dt (the runner recomputes
  every 4 steps; if a segment still detonates, add an energy-based
  limiter dt < c * e_int / (eta j^2)).
- stdlib mhd_mpd.rail double-counts Lorentz and has the wrong B_theta
  axial flux sign; rail/mpd_solver.rail is the corrected reference.
