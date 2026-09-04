# Next session: converge the partially-ionized chain at TRUE 6 g/s

**Read `notes/pion_chain_log.md` first** - it is the segment-by-segment
trend table and the account of what went wrong on 2026-09-01.

**State in one breath.** Saha EOS is in and the ionization-sink
hypothesis is REFUTED (pinch pressure is momentum balance vs J^2). The
alpha map found the real defect - a uniform capped eta erasing arc
constriction - and the greenlit fix (partially-ionized eta, e96c812)
demonstrably works: cap binding 97.8% -> 10.2% of cells, 16.9x eta
dynamic range, T_mean 3708 -> 8621 K, alpha_mean 0.0003 -> 0.051, peak
|j| at the cathode tip corner. **But the first convergence chain ran at
4.2e-3 kg/s, not 6e-3, and is void** (metered inlet clipped; see below).
The chain has been restarted from `saha_capped6g` as `out/phase2_pf1.log`.

## JUDGED 2026-09-04 00:30: free cathode split (read this first)

Full account: notes/pion_chain_log.md "2026-09-04 00:30". The split,
freed, moves the attachment to the tip: tip-face share 0.15 -> 0.29,
60% of J within 1 cm of the tip (was 33%), peak |j| at the tip corner,
pressure maximum on the axis 0.5 cm past the tip at 3303 Pa (Cory tip
2104, +57%; the tip-face probe reads 1138). That was the question and
it is answered: Cory's picture, no sheath needed for it. The cost: the
chamber refilled 2.4x (exit throughput fell to 3.5 g/s at the old
inventory), so wall 1114 (2.4x Cory), root 2827, profile rms 0.50,
thrust 18.4 N (u_exit 2.1 vs 4.1 km/s). The floor is the exit
condition for a choked 6 g/s at 12 kK; the wall excess IS the exhaust-
velocity deficit. Massaudit PASS 7e-12; cathode corner-ghost leak now
1.4% of inflow (was 0.4%), worth fixing. Ranked next in the log entry:
exit/exhaust velocity, reservoir/wall sheet, corner leak, sheath last.
Chain CLOSED at seg 16 (04:28): wall 1132, tip 1161, thrust 18.5 N,
mass 4.00e-6, +0.15%/seg; numbers above are seg 12, plateau to ~2%.

## RUNNING NOW (2026-09-03 11:55, FREE cathode split; judged above)

Owner greenlit "free the cathode split". Shipped: cathode faces are an
ideal conductor (E_t = 0, no sheath): barrel j_z = 0, tip j_r = 0 as
Neumann ends of the implicit sweeps; anode/backplate/wall/inlet still
prescribed; `run_free_cath = 1.0`, selftest 41/41 (checks 40-41 new).
Full account and smoke numbers: notes/pion_chain_log.md "2026-09-03
11:55". Chain: /tmp/run_free_fromA (binary /tmp/p2free, 8 segs from
the outlet fromA seg 12 checkpoint), chain.log has segment stamps,
run_segN.log / out/ckpt_segN.f32 / out/state_segN.csv per segment.

Judgement routine at the plateau (mass, tip, wall, thrust flat over
3 segments): (1) I_enc(z) from bt at j = 20 in the state csv, tip share
= I_enc(i=81)/8000 (prescribed model gave 0.15; smoke 0.17 after 8.6
us); (2) tip p vs 2104, wall vs 465, compare_bp_profile rms, thrust vs
24.6 N, M_exit >= 1, bf 0; (3) rebuild the massaudit binary from the
new solver (`$RAIL rail/phase2_massaudit.rail && cp /tmp/rail_out
/tmp/p2a`), run it in the chain dir; (4) render/attachment/alpha maps
with a `free_segN` tag; (5) write the log entry and this section.
Uncommitted: solver, mhd_pbt, runner, selftest, CLAUDE.md, notes, this
file. Commit only when the owner asks.

## JUDGED 2026-09-03 01:30: pressure-outlet plateau (previous block)

Full account: notes/pion_chain_log.md "2026-09-03 01:30". The outlet
chains plateaued (fromA seg 6-8 flat to 0.3%): wall 841 Pa (Cory 465,
1.8x; was 4.6x on the floor BC), tip 1104 (Cory 2104, -48%; was +18%),
thrust 19.16 N (Cory ~24.6), M_exit 1.18, bf 0, massaudit 2.3e-7 PASS,
profile rms 0.29 (was 1.53) with the RIGHT SHAPE: matches Cory's
parabola at r 3.0-3.4 cm, sits on a 1030 Pa outer-reservoir shelf at
r > 5.5 cm where Cory falls to 465. Images/state/ckpt saved as
out/*A_exit_seg8*. fromfill (uniqueness) sits on a second plateau 10%
lower in mass (1.46 vs 1.64e-6), wall 768, tip 943, thrust 19.0: the
difference is ONLY the outer reservoir (12% rho, 7% T), the arc column,
exit and thrust agree. Reservoir conduction time ~14 ms vs 3.4 ms run:
a slow mode, not two arc solutions. Watch CLOSED at seg 12 (06:35):
both static to four figures, gap closing at ~1e-9 kg/seg (> 100 segs to
meet). Arc, exit and thrust are unique (1%); the outer reservoir, and
with it wall (763-840) and tip (939-1104), are NOT pinned by the present
physics. No chain processes running; outputs in /tmp/run_exit_*/out.

The finding that matters: the pressure MAXIMUM is at the cathode ROOT
on the backplate (1930-2100 Pa), not at the tip. The prescribed linear
split forces 80% of J into the cathode along its length, so the model
cannot produce Cory's tip pinch. Peak |j| is on the axis just past the
tip (r 0.12, z 10.31 cm), hottest 1% of volume = 18% of Ohmic.
Ranked next (owner call): (1) free the cathode surface split, the
program's actual question; (2) reservoir/wall physics (sigma_en(T_e),
cold-sheet sink) for the 1030 vs 465 outer shelf; (3) LxF global-dt
exit dissipation only if the exit T undershoots.

Housekeeping: 09-02 afternoon + 09-03 judgement COMMITTED as 4739c01 (solver, selftest
39, runner, CLAUDE.md, notes, assistant files); commit only when asked.
The kT chains' outputs remain in /tmp/run_kT_*; the old nosink state is
out/phase2_state_A_nosink_seg8.csv. out/phase2_state.csv = fromA seg8.
Assistant PARKED by the owner (worker loop killed); Sonnet helpers one
at a time for numpy checks only. Opus reports in tools/assistant/
(OPTIONS_2026-09-02.md) still await the A/B/C/D decision. Studio
/etc/hosts still pins api.github.com (gh unusable until the owner
deletes the line with sudo).

## The next block

1. Chain segments until mass, vmax, ptip, pwall, mdot_in, mdot_out all
   go flat. Judge the plateau on the TREND across segments, never one
   endpoint.
2. At the plateau run the standing gate and the full judgment set:
   ```bash
   $RAIL rail/phase2_massaudit.rail && cp /tmp/rail_out /tmp/p2a && /tmp/p2a
   /opt/homebrew/bin/python3.11 tools/alpha_map.py <tag>
   /opt/homebrew/bin/python3.11 tools/attachment_map.py 8000 <tag>
   /opt/homebrew/bin/python3.11 tools/render_fields.py 8000 <tag>
   /opt/homebrew/bin/python3.11 tools/compare_bp_profile.py 8000
   ```
3. Judge tip/wall/profile/thrust vs Cory AND the real question: does the
   current constrict onto the cathode tip? **Be honest about what is
   predicted.** `mp_bt_presc` prescribes B_theta on the electrode faces
   from `mp_ienc_cath` (linear along the barrel, `pbt_phi = 0.2` at the
   tip), so the surface attachment split is an INPUT. What is free is
   the interior channel: `attachment_map.py`'s dissipation concentration,
   Ohmic power centroid radius, and peak-|j| location. The surface split
   only becomes a prediction in Phase 3, with sheath BCs.

## Open finding to carry into the judgment

**The arc is too quiet.** Across the void chain V_arc fell 6.9 -> 6.0 V
(total Ohmic 54.8 -> 47.7 kW) and was still falling, because a hotter
plasma is a better conductor (Spitzer eta ~ T^-3/2). A real PBT at 8 kA
runs tens of volts. Part of that gap is electrode falls this model has
no sheaths for until Phase 3, but the standard answer in the MPD
literature for exactly this gap is ANOMALOUS (turbulent /
microinstability) resistivity, which classical Spitzer + electron-neutral
cannot contain by construction. Re-measure at the honest plateau. If it
is still ~5-7 V there, that is the finding and the natural next block -
not a bug to hunt. (Numbers above came from void-chain states; treat as
provisional until re-measured.)

## What shipped 2026-09-01 (fix + guards, greenlit)

The metered inlet silently stopped metering: the ghost-velocity cap was
gated on the reflected momentum (`cap = rho_fluid * in_vg_cap`, always
active) and the annulus needs rho > 4.4e-3 to stay uncapped, but the
hotter arc thinned the near-inlet gas to 8.6e-4. 19/29 inlet cells
clipped; 4.2e-3 delivered against a nominal 6.0e-3, for three segments.
The log's `(in 0.006)` was a hardcoded constant.

- `mv_inlet_rate` in `rail/mpd_solver.rail` reuses `mv_bmass_face`
  verbatim, so the counter IS the scheme's own flux; the runner prints
  measured `mdot_in` every period.
- The cap now engages only below `in_vac_rho = 2e-4` (0.1 * fill_rho).
- Selftest **32/33**: metering exact at operating density; vacuum guard
  still clips. Both verified to FAIL with the defect reintroduced.
- Suite is **33 checks**. Gate was green before (31/31) and after.

**Compile on the Studio with `~/projects/rail-public/rail_native`.** (An
earlier version of this file said to compile on the Mini and scp; that
is superseded - see CLAUDE.md.)

## Do not repeat these

- **A converged-looking match can be a wrong-flow artifact.** The void
  chain printed tip p 2074 vs Cory 2104 (+1.4%) on the program's
  headline number, purely from running at 70% mass flow. Verify
  `mdot_in` before believing any agreement.
- **An assumption in a comment is not a check.** "The cap disengages in
  the operating regime" was true at ideal-EOS density and expired
  silently when the regime changed.
- **Do not resume from a state already inside the magnetic-pump
  regime.** A restart from the void chain's own checkpoint diverged
  (vmax 8018 -> 25463, dt 2.31e-8 -> 5.9e-9, mass 1.32e-6 -> 8.5e-7);
  honest mass flow does not rescue a state already spiralling. Kept as
  `out/phase2_pionfix_spiral_void.log`. Resume from a dense,
  correctly-metered checkpoint.

## Named checkpoints

- `phase2_ckpt_ideal6g.f32` - ideal EOS, converged, inlet 5.9786e-3 CLEAN
- `phase2_ckpt_saha_capped6g.f32` - Saha EOS + old capped eta, inlet
  5.99999e-3 CLEAN (the current chain's start)
- `phase2_ckpt_pion_4g2_void.f32` - the void chain's end state; inlet was
  metering 4.2e-3. Keep for the record, do NOT resume from it.

# Prior runway: the partially-ionized pivot, as written 2026-09-01

**2026-09-01 pivot, in one breath:** the Saha EOS shipped (P1) and its
re-converged state REFUTED the sink-alone hypothesis - tip +21%, wall
2.97x, thrust 33.6 N all survive, because pinch pressure is momentum
balance against J^2, not energy. The alpha map then showed WHY: the
state is cold and neutral (T_max 9200 K, alpha_max 3.5%), the old eta
cap 2e-5 bound in 100% of cells, and total Ohmic input was 7 kW against
a ~400 kW arc. A uniform capped eta erases arc constriction - the
attachment mechanism this program exists to predict. Greenlit fix
(e96c812): partially-ionized resistivity, eta = Spitzer +
2.2046e-8 sqrt(T)(1-a)/a, caps numeric-only [1e-7, 1e-3]. Work now
RUNS ON THE STUDIO (user call): compile on Mini (Studio's tios-branch
rail segfaults our build), scp the binary, nohup there; logs
self-report wall/ms-per-step/ETA. Baseline checkpoints kept:
phase2_ckpt_ideal6g.f32, phase2_ckpt_saha_capped6g.f32.

**Next block:** chain out/phase2_pion1.log segments to the plateau,
then judge: tip/wall/profile/thrust vs Cory AND the alpha + current
maps (does the arc constrict onto the cathode tip?). Watch the
ignition transient (Ohmic is ~15x stronger; if a segment detonates,
add an energy-based dt limiter dt < c e_int / (eta j^2)). Then
radiation/wall losses if still over-pressured; Hall (P2); J-sweep
(P3). Two-temperature T_e is the eventual (c) - user flagged it
plausibly right long-term.


# Prior runway (for the record): energy sinks (ionization first), then Hall, then the J-sweep

**CONVERGED 2026-09-01 00:00 (out/phase2_cold2.log): the first
mass-honest steady state.** Prefilled 60k run, 2.13 ms arc; every
observable flat for the last 0.8 ms; identity -8.0e-5; floor 0; blowing
split matches eqs 13/14 to 0.13%; the standing gate CLOSES (audit net
+1.07e-4 vs observed dm/dt +0.99e-4, both just the last 1.7% of fill;
inlet meters 5.979e-3; walls zero). Steady at 8 kA, TRUE 6 g/s:
tip p 2717 vs Cory 2104 (+29%); wall p 1337 vs 465 (2.87x); backplate
profile RISES toward the wall (cathode-side 271) - inverse of the
pinch-peaked parabola; T_exhaust 34.2 N vs ~25 measured (+37%).

**Read on the discrepancy: the model has NO energy sinks, and the
biggest missing one is ionization.** 6 g/s argon at 15.76 eV/atom is a
~230 kW sink against a ~400 kW arc; it is the physics behind u_ci (the
program's own critical ionization velocity - the xi scaling exists
BECAUSE of this sink). A coherent over-pressure everywhere (+29% tip,
2.9x wall, +37% thrust) is exactly what an adiabatic model of a
half-power-sunk device produces. Recommended P1: an ionization energy
sink (track ionization fraction via Saha or a simple burn-through to
full ionization at the u_ci scale; subtract eps_i * ionization rate
from p's energy), THEN re-judge tip/wall/profile/thrust. Radiation and
wall losses after. The wall-rising backplate profile may also implicate
the free-slip chamber wall. Images:
out/img/phase2_steady6g_{hero,fields}.png.

# Prior runway (for the record)

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
- scr is 55641 floats (er 0 / ez 13780 / parr 27560 / fmass 41340 /
  tridiagonal lanes 41341..41860 / eta cache 41861+) and fb is 25 (4
  neighbor flux vectors + the cell's own r-flux at offset 20). Every
  runner that calls mv_step must allocate those sizes. Anything calling
  mv_rco/mv_zco/mv_heat_loop DIRECTLY must fill the eta cache first
  (mv_eta_loop st scr 0) or the operators run with eta = 0.

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
