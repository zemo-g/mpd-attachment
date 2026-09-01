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
$RAIL run rail/selftest.rail                   # 31 checks; grep the last line, exit code lies
```
- Checks 22-25 lock the implicit Thomas operator (22 is boundary-order
  by design, do NOT "fix" it to exact). Check 26 is the mass gate: one
  measured step, dm == dt * boundary rate to 1e-6 rel, floor silent.
  Checks 27-31 lock the Saha EOS and the partially-ionized eta against
  independently computed Python references.
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

- **Top-level float-const references are runtime atofs** (~50ns + a
  locale lock, EACH evaluation). Inline literals and args are free.
  Hoist constants out of hot loops. notes/rail-const-atof.md.
- **scr is 55641 floats** (er 0 / ez 13780 / parr 27560 / fmass 41340 /
  tri 41341-41860 / eta cache 41861+); **fb is 25**. Anything calling
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
- The ignition transient under partially-ionized eta detonates a
  frozen dt within ~50 steps: always adapt dt (the runner recomputes
  every 4 steps; if a segment still detonates, add an energy-based
  limiter dt < c * e_int / (eta j^2)).
- stdlib mhd_mpd.rail double-counts Lorentz and has the wrong B_theta
  axial flux sign; rail/mpd_solver.rail is the corrected reference.

## Physics state in one paragraph (2026-09-01)

Conservation is machine-exact (interior creates nothing, metered
inlet, gas-prefill start). The Saha EOS is in; the ionization-sink
hypothesis for the +29% tip over-pressure was REFUTED (pinch pressure
is momentum balance vs J^2). The alpha map showed the real defect: a
uniform capped eta kept the arc at 7 kW Ohmic vs a ~400 kW real arc,
cold (9200 K max) and neutral (alpha < 3.5%). Now running: partially
ionized eta (Spitzer + electron-neutral via the Saha alpha, caps
numeric-only) so arc constriction, the attachment mechanism itself,
can emerge. Judgment at the plateau: tip/wall/profile/thrust vs Cory
AND whether current constricts onto the cathode tip.
