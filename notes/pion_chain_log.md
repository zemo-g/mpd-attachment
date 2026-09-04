# Partially-ionized eta convergence chain (2026-08-31 ->)

Binary /tmp/p2pion2 (compiled from 6485c39, run_resume = 1.0, 20k
steps/segment, ~155 ms/step on the Studio => ~52 min/segment).
Each segment resumes from out/phase2_ckpt.f32.

Judge the plateau on the TREND of every column, never one endpoint.

## Per-segment endpoint (from the log's last periodic print + tail)

| seg | mass (kg) | vmax (m/s) | ptip (Pa) | pwall (Pa) | mdot_out | identity | floor |
|-----|-----------|------------|-----------|------------|----------|----------|-------|
| pion1 start | 3.842e-6 | 3017 | 2600 | 1380 | 5.671e-3 | - | - |
| pion1 end (18k) | 2.875e-6 | 4445 | 3497 | 2768 | 7.091e-3 | -9.21e-5 | 0 |
| pion1 checkpoint | 2.799e-6 | 4509 | 3434 | 2703 | 7.070e-3 | | |
| pion2 end (18k) | 2.128e-6 | 5258 | 2812 | 2069 | 6.963e-3 | -8.20e-5 | 0 |
| pion2 checkpoint | - | - | 2737 (tip p) | 1992 (bp wall) | 6.866e-3 | | |

Inlet is 6.000e-3 kg/s. pion1 is still draining at ~1.09e-3 kg/s, so
mass has ~2.6 ms of relaxation left against 0.71 ms per segment: expect
3-5 more segments before mdot_out meets the inlet.

Ignition transient: ptip peaked 4208 Pa at step 2000 and has fallen
monotonically since. No detonation, no floor activation.

## Mechanism trace (tools/attachment_map.py, run on each saved state)

eta recomputed from (rho, p) with the CURRENT mv_eta_calc formula, so
rows are comparable to each other but NOT to the "7 kW" figure in
CLAUDE.md, which was measured under the old eta_cap = 2e-5.

| state | eta med | at cap | alpha mean/max | T mean/max (K) | Ohmic (kW) | V_arc | peak/mean | top 1% vol -> % P |
|-------|---------|--------|----------------|----------------|------------|-------|-----------|-------------------|
| capped-eta baseline (22:10 state, new formula applied) | 1.00e-3 | 97.8% | 0.0003 / 0.035 | 3708 / 8878 | 329 | 41.2 V | - | 14.8% |
| pion1 (mid-transient) | 1.31e-4 | 15.2% | 0.0419 / 0.276 | 8438 / 10993 | 54.8 | 6.9 V | 115x | 19.0% |
| pion2 (mid-transient) | 1.18e-4 | 10.2% | 0.0511 / 0.312 | 8621 / 11027 | 47.7 | 6.0 V | 100x | 19.8% |

The eta fix is doing what it was greenlit to do: the cap no longer binds
(97.8% -> 15.2%), eta has real spatial structure (16.6x dynamic range),
the gas is 2.3x hotter and alpha is up ~140x. Dissipation also got MORE
peaked (top 1% of volume 14.8% -> 19.0% of the power).

**Open watch item: V_arc = 6.9 V is low** for an 8 kA MPD arc (terminal
voltage is tens of volts, though much of that is electrode falls this
model has no sheaths for, Phase 3). Hotter plasma is a better conductor,
so Spitzer eta ~ T^-3/2 dropped the volumetric dissipation as the arc
heated. Watch whether it recovers as the state converges; if it stays
this low at the plateau it is a finding, not a bug, but it needs saying.

## Tool note

tools/attachment_map.py, written 2026-08-31. Validated two ways:
- it reproduces the PRESCRIBED cathode distribution exactly (I_in/J
  falls 0.997 -> 0.200 along the barrel = mp_ienc_cath with phi = 0.2),
  confirming it reads the field correctly;
- on-axis j_z matches the analytic c/pi (I -> c r^2 near r = 0) to 4
  digits.
Bug found and fixed the same hour: gradients must be taken on the FULL
array (ghosts included) and sliced after. Slicing first gives one-sided
differences on every domain edge, exactly 2x too large at the axis.
Remember the axis ghost has r < 0 and B antisymmetric, so I[0] == I[1].


## 2026-09-01 00:10 -- the chain runs OPPOSITE to both prior steady states

Worth stating plainly because it changes what "converged" will look like.
Both earlier converged/relaxing states were FILLING (mdot_out below the
6.0e-3 inlet); the partially-ionized chain is DRAINING (mdot_out above
it). Endpoints for comparison:

| run | EOS / eta | mass (kg) | vmax | ptip | pwall | mdot_out |
|-----|-----------|-----------|------|------|-------|----------|
| cold2 (converged) | ideal | 3.30e-6 | 3778 | 2717 | 1335 | 5.845e-3 |
| saha2 (still filling) | Saha, capped eta | 3.81e-6 | 3039 | 2554 | 1382 | 5.644e-3 |
| pion2 (draining) | Saha, partial-ion eta | 2.13e-6 | 5258 | 2812 | 2069 | 6.866e-3 |

This is the expected consequence of the fix, not a fault: the arc is
2.3x hotter, so it exhausts faster and the steady state must sit at
LOWER density. The chamber is finding a new, thinner equilibrium.

**It is turning over, not stalling.** Within pion2 mdot_out sat flat at
~7.05e-3 for 16k steps and then began falling with an ACCELERATING
slope: 7.048, 7.044, 7.032, 7.008, 6.963, 6.866e-3. Segment-to-segment
the endpoint moved -2.04e-4. It needs 8.7e-4 more to meet the inlet.

**It is not the cold1 death spiral.** That signature was mass 8x down,
vmax 110k, dt 1.4e-9. Here dt is easing 3.33e-8 -> 2.85e-8 (-14%/seg)
tracking vmax, and vmax is 5258. Tame. But mass is down 45% from the
pion1 start and only ~2.1e-6 kg remains, so the drain must decelerate
within the next 2-3 segments or the run is emptying rather than
converging. That is the thing to watch, and it is why the trend table
above exists.

## Watch item, now a trend and not a one-off: the arc is too quiet

V_arc 6.9 -> 6.0 V and total Ohmic 54.8 -> 47.7 kW, both still FALLING
as the plasma heats (Spitzer eta ~ T^-3/2, so a hotter arc dissipates
less). A real PBT at 8 kA runs tens of volts terminal. Some of that gap
is electrode falls, which this model has no sheaths for until Phase 3.
But the MPD literature's standard answer for exactly this gap is
ANOMALOUS (turbulent/microinstability) resistivity, which classical
Spitzer + electron-neutral does not contain by construction. If V_arc is
still ~5 V at the plateau, that is the honest finding to report and the
natural candidate for the block after this one -- not a bug to hunt.


## 2026-09-01 morning: the chain was VOID, root cause found and fixed

Segment 3 crossed below the inlet and the mass budget stopped closing:
dm/dt sat pinned at -1.395e-3 kg/s all segment while the printed
mdot_out swung 6.87e-3 -> 5.61e-3. A constant imbalance against a
varying term means one of the two reported numbers was not the real
boundary flux.

phase2_massaudit on the pion3 checkpoint:

    inlet (nominal 0.006): 0.00420011 kg/s   <-- 70% of nominal
    outflow:              -0.00561019 kg/s
    net d(mass)/dt =      -0.00144306 kg/s   (run observed -1.406e-3)

The audit net matches the run's observed dm/dt, so the INTERIOR is
conserving mass exactly and the standing gate closes. The boundary was
the problem: `in_vg_cap` clips the ghost at rho_fluid * 2000 m/s, the
annulus needs rho > 0.0044 to stay uncapped, and the hotter arc had
thinned the near-inlet gas to 8.6e-4 .. 1.3e-3. 19 of 29 inlet cells
clipped. An independent hand-calculation of the clipped face flux
reproduces the audit to four digits (0.004200 both ways).

Baselines audited and CLEAN, so only this chain is affected:
  ideal6g (cold2, published)   5.9786e-3   valid
  saha_capped6g                5.99999e-3  valid
  pion1..3                     4.2001e-3   VOID at 6 g/s

**The near-miss worth remembering.** pion3 printed tip p 2074 vs Cory
2104, a 1.4% match on the headline validation number after months of a
stubborn +29%. It is an artifact of running at 70% mass flow. Read off
the log alone it looks like the partially-ionized eta cracked the
problem. It did not.

Shipped (greenlit): counter first, then the fix, then the guards.
  - mv_inlet_rate (reuses mv_bmass_face verbatim, so it is the scheme's
    own flux); runner prints MEASURED mdot_in every period.
  - cap engages only below in_vac_rho = 2e-4 (0.1 * fill_rho).
  - selftest 32 (exact at operating density) / 33 (vacuum guard fires).
    Both verified to FAIL with the defect reintroduced, not just to pass.
  - Re-audit of the SAME thin checkpoint: inlet 5.99999578e-3, bit
    identical to the clean baselines. Net dm/dt flips to +3.57e-4.

Side finding: at the 2e-3 prefill the old cap was clipping from init on
EVERY run (needs rho > 4.4e-3 to disengage), releasing only as the
chamber filled. Benign for the converged baselines but it means every
run's early transient under-delivered.

Chain restarted from the pion3 checkpoint (saved as
phase2_ckpt_pion_4g2_void.f32) with the fixed binary /tmp/p2fix, log
out/phase2_pionfix1.log. Thermal and ionization structure are already
relaxed there; only the density has to refill.

## 2026-09-01 morning, second event: the restart itself spiralled

Resuming the FIXED binary from the void chain's own checkpoint diverged
inside one segment:

| step | dt | mass | vmax | mdot_in | mdot_out |
|------|----|------|------|---------|----------|
| 0     | 2.31e-8 | 1.323e-6 | 8018  | 5.99999e-3 | 5.610e-3 |
| 4000  | 1.24e-8 | 1.276e-6 | 12110 | 5.99999e-3 | 9.013e-3 |
| 8000  | 7.77e-9 | 1.118e-6 | 19315 | 5.99999e-3 | 1.022e-2 |
| 12000 | 7.77e-9 | 9.556e-7 | 19304 | 5.99999e-3 | 1.055e-2 |
| 16000 | 7.62e-9 | 8.510e-7 | 19700 | 5.99999e-3 | 9.144e-3 |

That is the cold1 magnetic-pump death spiral: dt collapsing, vmax
running away, mass draining, outflow 75% over the inlet. Killed at 16k.

**The inlet fix behaved correctly throughout** - mdot_in reads exactly
nominal except at steps 10000 and 14000 (5.40e-3, 5.39e-3), where
near-inlet cells genuinely fell below in_vac_rho and the vacuum guard
fired as designed. The counter did its job: the clipping was VISIBLE
this time instead of silent.

**The restart choice was the error.** The pion3 checkpoint was already
inside the pump regime - its vmax had climbed 5333 -> 8018 over the
final void segment - and honest mass flow does not rescue a state
already spiralling. Reasoning that "the thermal and ionization
structure are already relaxed, only density has to refill" was wrong.
Resume from a DENSE, correctly-metered checkpoint instead.

Log kept as out/phase2_pionfix_spiral_void.log.

## Chain restarted: out/phase2_pf1.log

From phase2_ckpt_saha_capped6g.f32 (inlet audited 5.99999578e-3), which
is what the original chain resumed from, now with honest metering.
Start: mass 3.842e-6, vmax 3017, ptip 2600, pwall 1380,
mdot_in 5.99999578e-3, mdot_out 5.671e-3 (FILLING, not draining).

Nothing about the partially-ionized steady state is measured yet. Every
mechanism number in the tables above came from void-chain states and is
provisional until re-measured at an honest plateau.

## pf1 (2026-09-01, first HONEST segment) -- clean

Resumed from saha_capped6g with the fixed inlet. mdot_in read exactly
5.99999578e-3 at EVERY print. identity -9.48e-5, floor 0.

| point | mass (kg) | vmax | ptip | pwall | mdot_out |
|-------|-----------|------|------|-------|----------|
| step 0     | 3.842e-6 | 3017 | 2600 | 1380 | 5.671e-3 |
| step 2000  | 3.689e-6 | 4155 | 4221 | 3404 | 7.521e-3 |
| step 18000 | 2.835e-6 | 4499 | 3457 | 2728 | 7.133e-3 |
| checkpoint | -        | -    | 3395 (tip p) | 2663 (bp wall) | 7.132e-3 |

Ignition transient peaks ~4221 Pa at step 2000 and eases, same shape as
the void chain. T_exhaust 48.7 N.

### The failure account, falsified properly

Prediction made before looking: pf1 should track the void pion1 closely
through the ignition transient and separate LATER, because
saha_capped6g audits clean (5.99999e-3), so the void chain also STARTED
with honest metering and only began clipping as the chamber thinned.

Test: the mass-budget residual, dm/dt - (6.0e-3 - mdot_out), per
interval. A clipping inlet makes it grow; an honest one does not.

| step | pion1 (void) | pf1 (fixed) |
|------|--------------|-------------|
| 10000 | -4.800e-5 | -4.773e-5 |
| 12000 | -4.573e-5 | -4.553e-5 |
| 14000 | -5.135e-5 | -4.419e-5 |
| 16000 | -5.709e-5 | -4.326e-5 |

Identical to 3 digits through step 12000, then the void chain's residual
GROWS while the fixed chain's keeps shrinking. Clipping begins around
step 14000 of segment 1 and compounds from there (it reached a 1.8e-3
deficit by segment 3). The shared ~-4.4e-5 floor is the cathode/anode
diffusive wall term the audit itemizes (-4.74e-5 / +1.44e-5), not a
leak.

The account holds. Chaining pf2.

## pf2: the honest chain DIVERGES where the void chain appeared to converge

Both segments clean (pf2 identity -9.99e-5, floor 0, mdot_in exactly
nominal at every print). The difference is in the physics, not the
numerics.

| seg | mass | vmax | ptip | pwall | mdot_out |
|-----|------|------|------|-------|----------|
| pion1 (void) | 2.875e-6 | 4445 | 3497 | 2768 | 7.091e-3 |
| pion2 (void) | 2.128e-6 | 5258 | 2812 | 2069 | 6.963e-3 |
| pion3 (void) | 1.389e-6 | 6309 | 2130 | 1356 | 5.707e-3 |
| pf1 (honest) | 2.835e-6 | 4499 | 3457 | 2728 | 7.133e-3 |
| pf2 (honest) | 2.056e-6 | 5885 | 2773 | 2008 | 7.578e-3 |

mdot_out within pf2 rose MONOTONICALLY at every print, 7.132 -> 7.578e-3,
with vmax 4577 -> 5885. The void chain's mdot_out FELL over the same
segment, 7.070 -> 6.866e-3.

**The void chain's apparent convergence was the starvation itself.** A
30% short inlet throttles the chamber, so less mass leaves; mdot_out
walking down toward 6.0e-3 read as an approach to steady state. With
honest metering the outflow runs AWAY from the inlet.

Trajectory: mdot_out +0.45e-3 per segment and accelerating, vmax +1400
per segment and accelerating. Extrapolating, pf3 ends near vmax 7500-8500
- which is where the void chain's checkpoint sat when a resume from it
spiralled outright (vmax 8018 -> 25463 within one segment).

### Reading, to be confirmed or killed by pf3

This links to the standing "the arc is too quiet" finding rather than
being separate from it. Partially-ionized eta makes the hot core a very
good conductor (Spitzer ~ T^-3/2; measured V_arc 6.0-6.9 V, total Ohmic
~48-55 kW). Low eta means the field's energy is not being dissipated as
heat, so it goes into KINETIC energy instead: the J x B pump accelerates
the plasma, density falls, v_A ~ B/sqrt(rho) rises, acceleration
increases. That is a positive feedback with no classical brake in the
model.

If pf3 confirms, the honest statement is: **with classical
Spitzer + electron-neutral resistivity and attachment prescribed, the
solver has no steady state at 8 kA / 6 g/s** - it accelerates into the
magnetic-pump spiral. Anomalous (turbulent) resistivity, the standard
MPD answer for the missing arc voltage, is also the natural candidate
for the missing brake. Two findings, one cause.

Do NOT conclude this from two segments. pf3 decides, and the monitor
fires on vmax > 10 km/s.

## pf3 CONFIRMS: no steady state at 8 kA / 6 g/s with classical eta

Monotone, accelerating runaway. Every print, no turnover:

| step | dt | mass | vmax | mdot_out |
|------|----|------|------|----------|
| 0     | 2.41e-8 | 1.973e-6 |  6221 | - |
| 4000  | 2.12e-8 | 1.805e-6 |  7061 | - |
| 8000  | 1.84e-8 | 1.635e-6 |  8157 | - |
| 12000 | 1.54e-8 | 1.465e-6 |  9725 | - |
| 14000 | 1.39e-8 | 1.381e-6 | 10800 | 8.960e-3 |
| 16000 | 1.24e-8 | 1.298e-6 | 12132 | - |

vmax increments GROW every print (393, 447, 508, 588, 703, 865, 1075,
1333): positive feedback, not a decaying transient. mdot_out 8.96e-3
against a 6.0e-3 inlet that metered exactly nominal the whole time.
Three honest segments, vmax 3017 -> 12132, no plateau anywhere.

pf2 checkpoint preserved as phase2_ckpt_pf2_honest6g.f32 (audited:
inlet 5.99999578e-3 exact, net dm/dt -1.728e-3).

### This is NOT the device being unsteady

Using the repo's own relation, j_ci = sqrt(mdot * u_ci / (mu0_4pi *
ln(ra/rc))): J_ci(argon, 6 g/s) = 17645 A, so **xi = J/J_ci = 0.453** at
8 kA. The operating point sits at less than half the critical ionization
current, well below onset, and the real PBT runs there stably - the
Phase 0 scoreboard has measured C_T at exactly this point. A model that
cannot hold a steady state at xi = 0.45 is missing physics, not
discovering an instability.

### Candidate causes, none yet eliminated

1. **Numerical.** Low-density LxF artifact. The identity holds ~1e-4 and
   the mass gate closes, which argues against it, but neither test
   probes the low-density momentum balance. CHEAPEST DISCRIMINATOR:
   halve cfl_c (0.30 -> 0.15) and re-run one segment from
   phase2_ckpt_pf2_honest6g.f32. If the runaway is unchanged in PHYSICAL
   time it is physical; if it moves materially it is numerical. One
   constant, one segment, no restructuring.
2. **Missing dissipation (anomalous resistivity).** Classical Spitzer +
   e-n gives V_arc 6 V against a real arc's tens of volts. Low eta means
   field energy goes to KINETIC energy instead of heat: J x B pumps, rho
   falls, v_A ~ B/sqrt(rho) rises, pumping increases. The standard MPD
   answer for the missing voltage is also the natural missing brake.
3. **Missing energy sinks (radiation / wall).** These COOL the plasma,
   which RAISES eta through the electron-neutral term, which also
   brakes. Already on the runway ahead of the J-sweep.
4. **The prescribed attachment itself.** Forcing current through a thin
   near-cathode region gives large J x B per unit mass; a real arc would
   redistribute. Only Phase 3 (sheath BCs) tests this.

Do not pin this on (2) because it is the tidiest story. (1) is cheap and
must go first: if it is numerical, all physics work on it is wasted.

## Mechanism trend at HONEST mass flow (pf1..pf3)

These are the first eta/alpha/Ohmic numbers measured at a metered
6 g/s. They describe a RUNAWAY, not a steady state - no plateau exists
in this chain. Read them as the mechanism of the divergence.

| state | V_arc | Ohmic | eta med | at cap | alpha mean/max | T max (K) | peak |j| at |
|-------|-------|-------|---------|--------|----------------|-----------|------------|
| pf1 | 6.8 V | 54.5 kW | 1.307e-4 | 14.8% | 0.042 / 0.276 | 10990 | tip corner (0.88, 10.06) |
| pf2 | 5.3 V | 42.8 kW | 1.137e-4 |  7.1% | 0.054 / 0.300 | 10976 | tip corner (0.88, 10.06) |
| pf3 | 3.7 V | 29.4 kW | 7.009e-5 |  0.4% | 0.238 / 1.000 | 65153 | BACKPLATE (1.82, 0.06) |

The feedback loop, visible: plasma heats -> fully ionizes (alpha_max
reaches 1.0) -> Spitzer eta collapses (median halves, cap binding
14.8% -> 0.4%) -> Ohmic dissipation falls 54.5 -> 29.4 kW -> less field
energy becomes heat and more becomes kinetic -> faster exhaust ->
thinner gas -> hotter still. V_arc 6.8 -> 5.3 -> 3.7 V is the "arc is
too quiet" finding confirmed at honest mass flow, and it WORSENS as the
runaway proceeds.

**Two signs that argue against declaring the physics story won:**
- T_max 65153 K with alpha_max exactly 1.0000 is a hot SPOT, not a
  smooth field, and it appeared in the same segment the stress identity
  degraded from -9.99e-5 to -2.01e-4 (first material move).
- Peak |j| RELOCATED from the cathode tip corner to the backplate. A
  qualitative restructuring of the current path.

Both are consistent with real physics AND with a solution ceasing to be
resolved. That is exactly why the cheap cfl_c test must precede any
resistivity work: if this is an under-resolved low-density artifact, the
tidy anomalous-resistivity story is a trap.

## Chain STOPPED here, pending a call on the next block

Studio idle. Resume point: phase2_ckpt_pf2_honest6g.f32 (audited, inlet
5.99999578e-3 exact). pf3's own checkpoint is in out/phase2_ckpt.f32 but
is deep in the runaway - do NOT resume from it (see the spiral entry).
Saved states: phase2_state_pf{1,2,3}.csv.

Recommended first move: cfl_c 0.30 -> 0.15, one segment from the pf2
checkpoint, compare the runaway in PHYSICAL time. Cheap, decisive
between candidate (1) and everything else.

## Step A verdict (out/phase2_cfl15.log vs pf3, matched physical time)

DIFFUSION-SENSITIVE. Halving cfl_c (0.30 -> 0.15, which DOUBLES the LxF
numerical dissipation D ~ dx v / 4 cfl) does not merely slow the
runaway, it REVERSES it, from the identical pf2 checkpoint:

| t (s) | vmax cfl.30 | vmax cfl.15 | mass .30 | mass .15 |
|-------|-------------|-------------|----------|----------|
| 4.7e-5 | 6614 | 6766 | 1.889e-6 | 1.933e-6 |
| 1.3e-4 | 7569 | 7101 (peak) | 1.720e-6 | 1.922e-6 |
| 1.7e-4 | 8157 rising | 7067 FALLING | 1.635e-6 | 1.926e-6 RISING |

cfl15 ends with mdot_out 5.72e-3 BELOW the 6.0e-3 inlet (filling),
identity -5.5e-5, floor 0. vmax e-folding ratio 0.35.
Checkpoint kept: phase2_ckpt_cfl15_stab.f32 (cfl-tainted; record only).

**Consequences.**
- The earlier "no steady state with classical eta" reading is WITHDRAWN.
  Neither fate is knowable at this scheme/resolution: the answer
  currently belongs to the artificial viscosity, not the physics.
- STANDING ACCEPTANCE GATE from here on: no fate/observable conclusion
  counts unless it is cfl-INVARIANT (0.30 vs 0.15 agreeing in physical
  time). cfl_c restored to 0.30; comment at the constant records this.
- Self-consistent reading: the model has essentially no physical
  dissipation in momentum/energy (no viscosity, small eta, adiabatic
  walls). Where physics is absent, numerics decides. The wall sink
  (sink_estimate: 16x+ Ohmic scale, radiation falsified at 6% max) is
  the dominant omitted physical dissipation.

## Second-order scheme SHIPPED (2026-09-01 afternoon, user call)

MUSCL piecewise-linear reconstruction with minmod, on rho/mr/mz/en/bt
AND the cached p (p reconstructed directly: no EOS inversion per face).
Unified face-flux form: faces carry S = F(U_L)+F(U_R) and d = U_R-U_L;
with zero slopes this is algebraically the old scheme.

Discipline of the build, in order:
1. Equivalence refactor FIRST: face machinery with mv_mm forced to 0.0,
   verified against the pre-refactor binary over 200 steps of the pf2
   state - worst relative deviation 8.9e-12 (pure float regrouping).
2. Minmod enabled. Selftest green both sides of the flip.
3. Checks 34 (faces exact on linear data) and 35 (minmod clips at
   extrema). Suite now 35 checks.
Safety property: any face whose 4-cell stencil touches a non-fluid cell
drops to first order, so ghost cancellations (metered inlet included)
and the audit's boundary fluxes are bit-preserved; selftest 26
telescoping is flux-form independent at interior faces. fb is 40 now
(callers updated: runner, smoke, hall smoke, selftest).
Cost: 157 -> 228 ms/step (+45%).

Decisive pair now running from phase2_ckpt_pf2_honest6g.f32:
out/phase2_m2cfl30.log, then the invariance twin at cfl 0.15
(/tmp/p2m2cfl15 staged). ACCEPTANCE: the two must agree in physical
time; then whatever fate appears is attributable to physics.

## m2cfl30: the second-order fate, and the dissipation ledger closes

out/phase2_m2cfl30.log, from the pf2 checkpoint. Violent adjustment
(the state was equilibrated to first-order diffusion), then sustained
large-amplitude pulsation: vmax cycling 18-25 km/s, ptip swinging
2731 -> 3901 Pa, and by segment end a breakout - vmax 36.9k, dt 4.1e-9,
mdot_in clipped to 2.9e-3 (the vacuum guard firing because the
near-inlet gas genuinely fell below 2e-4), backplate p at the cathode
base down to 5.9 Pa. The chamber is EVACUATING. Identity at the end
print: -8.9e-6 (excellent), floor 0.

Discrimination on the end state (tools built for it):
- The vmax region is SMOOTH (alternation fraction 0.14; the r~1 cm jet
  decays 14.1 -> 5.6 km/s over 24 cells). The pulsation is large-scale
  dynamics, not ringing.
- A perfect 2-cell zigzag DOES exist, but only in near-vacuum cells and
  only in v = m/rho (momentum amplitude negligible). Control: pf3
  (first order) alternation 0.01 vs m2cfl30 0.36-0.47. KNOWN ISSUE, new
  with the reconstruction, cosmetic for now; cheap targeted fix if ever
  needed: raise the face fallback threshold so rarefied cells go first
  order. The pre-identified Rusanov fix is WITHDRAWN as a cure for this
  - its local coefficient is smaller than the current global 1/4
  everywhere, so it cannot damp what 1/4 does not.

### The dissipation ledger, now monotone

| run | scheme | numerical dissipation | fate |
|-----|--------|----------------------|------|
| cfl15 (1st order) | most | 2x LxF | STABILIZES (vmax turns over, fills) |
| pf1-3 (1st order, cfl .30) | middle | 1x LxF | slow runaway |
| m2cfl30 (2nd order) | least | minmod-reduced | drains hard + pulsation |

Less dissipation -> more drain, monotonically. The D -> 0 tendency is
the DRAIN. The first-order cfl15 "stabilization" was the
numerical-diffusion artifact, not the other way around. Pending the
second-order cfl-invariance twin (m2cfl15, running): if its envelope
and mean-flow statistics agree with m2cfl30, the scheme is converged in
dissipation and the fate is attributable to the MODEL PHYSICS: at
8 kA / 6 g/s with classical eta, prescribed attachment, and adiabatic
walls, the chamber empties. Then the missing physics goes in (wall
sink first, per notes/wall_sink_design.md) with the cfl-pair gate as
standing acceptance.

Note the acceptance gate is ENVELOPE/statistics agreement (mean vmax,
mean mdot_out, drain rate over the overlap window), not point-wise
trajectory match - point-wise is the wrong test for an oscillatory
solution.

## Second-order cfl-invariance twin: FATE IS SCHEME-ROBUST

m2cfl15 (out/phase2_m2cfl15.log) vs m2cfl30, envelope statistics over
the post-adjustment overlap (t in [2e-5, 9.9e-5] s): mean vmax ratio
0.79, max vmax 1.02, mean ptip 0.82, mean pwall 1.02, mean mdot_out
0.89, drain dm/dt ratio 0.56. Both drain, both pulse in the same band,
both evacuate the cathode base (backplate cathode p 5.9 Pa vs 1e-6 Pa).
The first-order pair gave OPPOSITE fates under this same test.

VERDICT, now earned: with classical Spitzer+e-n eta, prescribed
attachment, and adiabatic walls, the model has NO steady state at
8 kA / 6 g/s - it evacuates and pulses, robustly across scheme order
and the dissipation knob. Residual quantitative spread (2x on drain
rate) is acknowledged; the FATE is not in doubt. The missing brake is
physical. Next per the greenlit sequence: the wall sink
(notes/wall_sink_design.md, implementation b), judged under the same
envelope gate.

## Wall sink SHIPPED (option C, walls-only after radiation was falsified)

Implementation (b) from notes/wall_sink_design.md:
- mv_wall_cell/mv_wall_loop in mpd_solver.rail: cold-wall conduction on
  every fluid face adjacent to masks 1/2/4/5, dE = kappa_wall (T-300)
  dt G, G exact per face geometry; capped at half the cell's thermal
  energy per step. kappa_wall = 1.0 W/m/K (band [0.3, 3] bracketed by
  the one constant). Runs inside mv_step after the Ohmic heat.
- Counter ships WITH it: fb slot 40 accumulates Joules removed (fb is
  41 now); the runner prints interval-average P_wall every period.
- Selftest 36: analytic removal rate on a single hot wall-adjacent
  cell, total mass untouched, counter books the same Joules. VERIFIED
  TO FAIL with a deliberately mis-scaled sink (0.9x), then restored.
  Suite is 36 checks.
- Two bugs caught in the hour: Rail rejects operator-continuation
  lines (flatten to intermediate lets), and the P_wall print variable
  shadowed the wall-pressure variable pw (pwall briefly printed watts;
  renamed pww).

Smoke (200 steps from the pf2 state): P_wall 2.23 MW at first contact
- matching tools/sink_estimate.py's kappa=1 figure - relaxing to 237 kW
as the wall boundary layer forms; wall-adjacent pressure collapses
1423 -> 130 Pa (the cooling is real, not cosmetic).

Fate pair running: out/phase2_ws30.log from the pf2 checkpoint, twin
/tmp/p2ws15 staged. Same envelope acceptance gate. The open physics
question it answers: is cold-wall conduction the missing brake at
8 kA / 6 g/s, or does the drain survive and anomalous resistivity (B)
move up?

## REVIEW 2026-09-01 evening: the inlet stopped metering in every second-order segment

Reread of the counter we shipped (mdot_in), which nothing was reading:

| segment | first mdot_in < 6.0e-3 | final mdot_in |
|---|---|---|
| pf3 (first-order) | never | 6.00e-3 |
| m2cfl15 | t ~ 9.2e-5 s (end) | 5.59e-3 |
| m2cfl30 | t ~ 7e-5 s | 2.92e-3 |
| ws30 | t ~ 3.5e-5 s | 2.87e-3 (48% of nominal) |

Cause: the in_vac_rho gate (2e-4 kg/m^3) engaged; about half the inlet
rows had fluid rho below it, the ghost copied that rho, the 2000 m/s cap
clipped mz_g to ~0.4 and those rows delivered ~5% of nominal. Less
numerical diffusion (MUSCL) lets the pinch evacuate the near-inlet gas;
the wall sink cools it and pulls it there sooner. Once engaged it
latches (less inflow, emptier rows). The monitor on ws30 watched only
dt/vmax; the log had six lines in the alarm band.

Two things were wrong in what shipped:
1. The cap's physics comment ("a mass-flow controller cannot force
   6 g/s into vacuum") is backwards. A choked injector delivers fixed
   mass flow independent of downstream pressure; into vacuum the gas
   expands at <= sqrt(2 cp T0) ~ 560 m/s. The honest BC delivers 6 g/s
   unconditionally.
2. Found while fixing: the metered ghost fixed the MASS flux only. Its
   MOMENTUM flux carried 0.5 mz_g^2/rho_c with mz_g ~ 8.8 and rho_c the
   fluid density, i.e. ~1e5 Pa at rho_c 3.5e-4 against a physical
   rho_in v_in^2 + p_in of 2.2e3 Pa, scaling as 1/rho_c. The saved
   states put vmax IN THE INLET ROW (i = 1, j = 34..35) for pf2 (3179),
   pf3 (11950) and m2cfl15 (16618 m/s), at rho 1.2e-3 / 3.5e-4 / 2.6e-4.
   A jet that thins the row that feeds it: positive feedback. The
   "runaway" verdicts below the first-order cfl pair and the
   second-order pair are CONTAMINATED by this boundary artefact. The
   fate question is re-opened.

Consequences:
- ws30 is confounded twice over (log kept as
  out/phase2_ws30_confounded.log; killed at step 18000 while detonating,
  vmax 66001, dt 2.3e-9). ws15 never launched.
- Drain / mdot_out tails of m2cfl30 after t ~ 7e-5 are contaminated.
- "Fate is scheme-robust" stands only as: both orders show the SAME
  artefact-driven jet. Not evidence about the physics.

### Fix shipped: prescribed-flux inlet face (approach A)

- mv_face_zin in mpd_solver.rail: when the minus-z neighbour is mask 6
  the face's gas part is S = 2 F_in (mass rho_in v_in, momentum
  rho_in v_in^2 + p_in, energy (e_in + p_in) v_in) and the gas jump is
  0, so the update delivers exactly F_in dt/dz whatever the fluid
  state. Magnetic parts of the momentum/energy flux and the bt
  component are unchanged (field boundary untouched). The mask-6 ghost
  is now a plain reservoir (rho_in, v_in, 300 K) feeding only the
  sweeps and the bt boundary. in_vg_cap / in_vac_rho removed.
- Counter mv_bmass_face and phase2_massaudit report the prescribed flux
  on mask-6 faces. The massaudit gate now SELF-CHECKS: it takes one real
  mv_step and prints |observed dm/dt - floor - family net| / |net|
  (4.3e-11 on the pf2 checkpoint, inlet 0.00599999578365988). The old
  audit was a copy of the face formula and reported 0.211 kg/s at the
  inlet after the change: an audit that copies the scheme is not
  independent of it.
- Selftest 33 rewritten: on a VACUUM inlet row (1e-5 kg/m^3) the face
  the scheme consumes must carry S = 2 rho_in v_in exactly with jump 0,
  and the counter must agree. VERIFIED TO FAIL against the pre-change
  solver (1 of 36), PASS after. Suite 36 checks.
- Smoke (200 steps from pf2): mdot_in exact from step 0; the inlet-row
  jet is gone (row vz 23..790 m/s vs 583..5234 under the old ghost;
  vmax moves to the interior near the cathode, 2847 m/s); P_wall 207 kW
  vs 237 kW; state differs from the old-ghost smoke by rel-L2 12% in
  rho and 24% in vz after 200 steps, all of it the inlet row and its
  wake.

### Fate pair re-launched from pf2 with inlet A (cfl 0.30, 20000 steps)

- /tmp/run_A_nosink (kappa_wall = 0): does the runaway survive without
  the inlet artefact? This is the clean model-physics question the
  previous pairs thought they were answering.
- /tmp/run_A_sink (kappa_wall = 1): the wall-sink test, uncontaminated.
Both write their own out/ (working-dir relative); monitor covers
milestones, detonation, mdot_in < 6e-3 (pattern dry-tested against the
ws30 log: 6 hits) and completion.

Assistant claims 001b..001f queued ahead of the rest: choked-inlet
physics, Dirichlet-ghost over-delivery (why B was rejected),
prescribed-face exactness, inlet-row nominal geometry, and the ghost
momentum artefact numbers.

### 2026-09-01 late: fate pair with inlet A finished 20k steps. RUNAWAY GONE.

Both segments resumed from pf2, cfl 0.30, 20000 steps, ~4300 s / 3750 s wall.
Both massaudit gates PASS (nosink 1.1e-10, sink 3.0e-11), mdot_in exact
(0.00599999578365988) at every print in both runs.

| run    | step  | dt      | mass    | sig vmax | ptip | pwall | mdot_out | P_wall |
|--------|-------|---------|---------|----------|------|-------|----------|--------|
| nosink | 0     | 2.4e-8  | 1.87e-6 | 6200     | 2685 | 1423  | 7.7e-3   | 0      |
| nosink | 18000 | 2.80e-8 | 2.31e-6 | 5352     | 2437 | 2055  | 5.22e-3  | 0      |
| sink   | 18000 | 2.95e-8 | 3.25e-6 | 5088     | 1654 | 425   | 2.68e-3  | 89.7kW |

End-of-segment probes: nosink tip 2430 Pa (Cory 2104), wall 2074 (Cory
465), backplate-at-cathode 5848. sink tip 1722 (Cory 2104), wall 448
(Cory 465), backplate-at-cathode 68.

Notes:
- The logged "vmax" is mv_speed = |v| + fast magnetosonic speed, i.e.
  a SIGNAL speed. Flow speed from the state csv: sink max |v| 2440 m/s
  at j=22 i=73 (r 10.75 mm, z 90.6 mm, interior near the tip), nosink
  1965 m/s. Neither lives in the inlet rows (i 0..1) any more. The
  old ghost put 2.5e4 m/s there.
- dt is STEADY (2.80e-8 and 2.95e-8, drifting up not down) across the
  full 20k steps in both runs. Every earlier "dt collapse" verdict was
  the inlet-momentum artefact.
- Neither run is at steady state: mass still rising (nosink +0.04e-6
  per 2k steps, sink +0.17e-6 per 2k steps), mdot_out well below the
  6e-3 inlet. Fill time mass/(in - out): nosink ~3 ms, sink ~1.2 ms per
  e-fold; segment 1 covered 0.5 ms. Chaining continues (segment 2
  launched from each checkpoint in the same working dirs;
  run_seg1.log kept beside run.log).
- Sink wall pressure 448 Pa vs Cory 465 is the first probe in the
  program that lands on Cory without tuning. Tip 1722 vs 2104 is 18%
  low and still rising slowly. The nosink wall is 4.5x Cory: the cold
  wall matters at the backplate, as suspected since the wall-sink
  entry.
- Open suspect promoted by the assistant (claim 001a): the Spitzer
  coefficient in the solver implies ln(Lambda) = 0.96; physical is
  5-10 at these n_e, T. eta_ei is therefore 5-10x low. This is the
  best candidate for the too-quiet arc (V_arc ~5 V). Solver change,
  owner's greenlight needed; gates before/after.

### 2026-09-01 late: Coulomb logarithm (greenlit "A, go ahead")

Counter first. `mv_heat_cell` now books dt eta j^2 2 pi r dr dz into fb
slot 41; phase2_run/smoke print `V_arc = P_ohm / J` on every step line
(selftest 37: bt = c r gives uniform jz = 2c/mu0, counter equals dt eta
jz^2 V_fluid to 1e-9; verified to FAIL on a halved counter). On the
A_sink segment-1 state the in-run counter says 15.9 V where
attachment_map.py says 19.5 V (tool re-derives eta from p and uses
np.gradient for j; the 20% gap is the tool's, noted, not chased).

Then the change: `mv_eta_calc` eta_ei = 5.2e-5 ln(Lambda) / T_eV^1.5,
ln(Lambda) = clip(23 - ln(sqrt(n_e[cm^-3]) / T_eV^1.5), 2, 20), n_e =
alpha n. Checks 30-31 re-referenced (Python from the same constants:
n = 3e22, 9000 K: lnL 5.332, eta 4.6445e-4; 50000 K: lnL 6.221, eta
3.6170e-5). Gates: selftest 37/37 before and after; massaudit on the
A_sink checkpoint 3.0e-11 PASS before and after (eta does not touch
mass, as expected).

200-step smoke from the A_sink checkpoint: V_arc 33.4 V at step 0
(2.1x the legacy 15.9, matching the tool's 1.98x on frozen j), relaxing
to 27.0 V by step 150 as j redistributes; ptip 1733 -> 2200-2370 Pa
(Cory 2104); pwall 449 -> 452 (Cory 465); dt untouched 2.99e-8 ->
2.94e-8; inlet exact.

Overnight chains (all from the A_sink / A_nosink segment-1 states):
- /tmp/run_A_sink_lnl: ln(Lambda) solver, kappa_wall 1, 8 segments.
  THE MODEL.
- /tmp/run_A_sink, /tmp/run_A_nosink: legacy-eta controls, 6 more
  segments each (no V_arc column in their binaries).
Each dir: chain.log (segment start/done), run_segN.log, out/ckpt_segN
.f32, out/state_segN.csv. Chain driver /tmp/chain_dir.sh.

### 2026-09-02 morning: overnight verdict, the constant sink fell

All three chains completed 8 segments (07:13). Step-18000 values:

| chain | mass kg | ptip Pa | pwall Pa | mdot_out kg/s | plateau |
|---|---|---|---|---|---|
| A_nosink (legacy eta, adiabatic) | 2.61e-6 flat seg 3-8 | 2479 | 2155 | 5.90e-3 | YES |
| A_sink (legacy eta, kappa 1) | 3.25e-6 -> 2.24e-5 linear | 6420 | 4414 | 1.6-2.0e-3 | no |
| A_sink_lnl (NRL eta, kappa 1) | -> 4.04e-5 linear | 13460 | 10584 | -7.2e-4 | no |

Diagnosis (states only, no solver touched): on sink_lnl P_wall / P_ohm
climbed 130/180 kW (seg 1) -> 169/205 (seg 4) -> 218/242 (seg 8), i.e.
90% of the Ohmic input leaves through the chamber wall. Wall-adjacent
cells: rho 6.5e-2 at 762 K against 1.5e-3 at 6677 K in the control (a
45x cold sheet); 34-47% of all mass sits below 1000 K. Outflow-face
median vz 803 (nosink) -> 133 (sink) -> 77 m/s (sink_lnl), 44% of exit
cells backflowing. The exit BC behaves; the gas reaching it is cold and
slow. Pressure rises because mass is trapped, not because the exit is
closed. A constant 1 W/m/K over a half cell is h ~ 4000 W/m^2/K on
5e-2 m^2 of wall, bounded only by cooling the gas to t_wall, which is
exactly what it did.

Claim 002b (sink clamp-limited, tau 4e-8 ~ 1.3 dt) is WRONG
empirically: clamp hits on wall-adjacent cells 4/330 (A_sink seg 1),
0 (sink_lnl seg 8; median de_raw/(0.5 e_int) 0.03). The boundary cells
are already cold, so the per-step sink there is small. The assistant's
REFUTED on 002b came from its own arithmetic (G_r 105x off); adjudicated
by hand: refuted, right conclusion, wrong reasoning. 002a and 005
returned CHECK-ERROR (no np.trapz in the sandbox), no physics verdict.

Greenlit ("throw the sink at A"): the conductivity is now the cell's
own. `wall_kappa n a t` = (1 - alpha) 0.0177 (T/300)^0.7 [neutral
argon, fit to tabulated 300-5000 K within 5%] + alpha kappa_e, kappa_e
= 3.2 k^2 T (n_e tau_e) / m_e with NRL tau_e = 2.30349e-4 T_K T_eV^1.5 /
ln(Lambda) (0.27 W/m/K at 1 eV, ln(Lambda) 10). ln(Lambda) moved into
`eos_lnl`, shared by eta and the sink. The cold sheet chokes its own
sink ~28x; a 15 kK cell still sees ~1 W/m/K. Selftest 38 locks it
(Python references 0.0351683003 at 800 K neutral, 0.99349970 at
n = 1e22, 15000 K; fails 28x on a constant kappa, verified). Gates:
38/38 before (37) and after; smoke on the pf2 guard state runs clean
(dt 2.5e-8, inlet exact). On that hot state the new sink is 127 kW
against the constant's 219 kW (1.7x): Spitzer conduction at 10+ kK is
close to 1 W/m/K, so the self-limiting only shows once a sheet cools.
Whether it plateaus is the empirical question the chains answer.

Chains launched 09:43 (binary /tmp/p2A_sink_kT, 8 segments each):
- /tmp/run_kT_fromA: from the nosink plateau (ckpt_seg8). THE MODEL.
- /tmp/run_kT_fromfill: from the filled sink_lnl seg-8 state. Drain
  test: if the new sink is right, this state must lose mass.

Nosink control judged at its plateau (legacy eta; massaudit 1.7e-7
PASS, net 4.66e-6 kg/s = 0.1% of mass per segment):
- tip 2479 vs Cory 2104 (+18%); wall 2155 vs 465 (4.6x); backplate
  profile flat (5731 at the cathode base, 2455 mid, 2155 wall) against
  Cory's parabola 1662 -> 465, rms 1.53; T_exhaust 37.1 N vs ~24.6
  measured (+51%); stress identity 3e-5.
- Attachment: the surface split is prescribed (I_in/J linear 1.0 -> 0.2
  along the barrel), so "distributed along the shank" is an input, not a
  finding. Free interior: peak |j| 6.26e6 A/m^2 at the tip corner
  (r 0.12 cm, z 10.19); hottest 1% of volume carries 17% of the Ohmic
  power, 5% carries 43.5%, peak/mean 66x; power centroid r_q 1.5-2 cm
  along the barrel, 3.7 cm at the anode plane; channel r_half 3.1 cm
  at z 1 -> 2.1 at z 4-5 -> 5 at the anode. No constriction onto the
  tip beyond the prescribed corner peak. Under NRL eta on the same
  state the tool says 194 kW / 24.3 V (legacy 63 kW / 7.9 V), so the
  "too quiet arc" was mostly the Coulomb logarithm.
Images out/img/phase2_A_nosink_{current,alpha,hero,fields}.png; state
and ckpt in out/ as *_A_nosink_seg8.*.

## 2026-09-02 afternoon: the kappa(T) chains were two attractors, the outflow ghost was the floor

kappa(T) sink chains (binary /tmp/p2A_sink_kT, step 18000 of each
segment; started 09:43, stopped at seg 5 at 15:10):

| chain | seg | mass kg | ptip | pwall | mdot_out | P_wall/P_ohm |
|---|---|---|---|---|---|---|
| fromA | 1 | 2.423e-6 | 1353 | 1180 | 6.07e-3 | 0.44 |
| fromA | 2 | 2.455e-6 | 1461 | 1152 | 5.41e-3 | 0.46 |
| fromA | 3 | 2.700e-6 | 1692 | 1284 | 5.18e-3 | 0.47 |
| fromA | 4 | 3.050e-6 | 1996 | 1504 | 5.08e-3 | 0.48 |
| fromfill | 1 | 2.935e-5 | 21603 | 21065 | 8.79e-3 | 0.60 |
| fromfill | 2 | 2.820e-5 | 23549 | 22878 | 5.01e-3 | 0.74 |
| fromfill | 3 | 2.814e-5 | 23684 | 23022 | 5.63e-3 | 0.74 |
| fromfill | 4 | 2.756e-5 | 23027 | 22405 | 6.00e-3 | 0.73 |

The sink fix did what it was asked (P_wall about half of P_ohm, no cold
sheet, V_arc ~21 V) but neither chain is a plateau: fromA drained once
then refilled at +0.35e-6 kg/segment (in minus out ~0.9e-3 kg/s), and
fromfill lost 6% and stalled in a quasi-steady FILLED state at 23 kPa
with mdot_out = mdot_in. Two attractors of one solver.

Exit-plane analysis (state csv, c_s = sqrt(5/3 p/rho)):

| state | exit Mach med / max | p at r=4 cm, z 5 -> 104 | backflow |
|---|---|---|---|
| nosink seg8 | 0.36 / 0.85 | 2.2 kPa flat | r > 5 cm |
| kT_fromA seg4 | 0.44 / 0.74 | 1978 -> 2208 Pa | r > 5 cm |
| kT_fromfill seg3 | 0.04 / 0.15 | 20394 -> 23657 Pa | r > 3 cm |

Every exit cell subsonic in every state, pressure uniform across the
chamber and RISING toward the exit face. The mask-7 ghost was a
zero-gradient copy of the fluid cell; on subsonic outflow one
characteristic enters from outside and nothing set it, so the exterior
(tank) pressure never entered the problem and the chamber floor was
whatever the transient left. 6 g/s through the exit annulus at ~12 kK
chokes near rho 2e-4, p ~550 Pa: the order of Cory's 465 Pa wall, not
2155 (nosink) or 23000 (fromfill). The 4.6x wall over-pressure, the
flat backplate profile and the +18% tip on the nosink plateau all sat
on this floor.

Greenlit ("Green"), shipped, gates 38/38 before and 39/39 after:
- counter first: `mv_exit_probe` (mass-flux-weighted exit Mach,
  backflowing exit cells, min exit p) on the step line as `M_exit=`,
  `bf=`, `p_exit=`;
- `mv_ghost_exit`: subsonic outflow cell -> ghost carries amb_p (rho and
  momentum zero-gradient); supersonic -> zero-gradient as before;
  backflow -> ambient at rest; bt negated in all three;
- selftest check 39 locks the three branches and the probe; the old
  ghost fails it (verified by swapping it back in).

Smoke, 400 steps from the nosink plateau (/tmp/p2smoke_exit):
M_exit 0.58 -> 0.82 (step 40) -> 0.97 (80) -> 1.06 (360); p_exit 1728
-> 195 Pa; mdot_out 6.3e-3 -> 13.4e-3 peak -> 11.5e-3 (draining);
pwall 2092 -> 1224 within 11 us; bf 0 throughout; dt 2.9e-8 -> 3.2e-8
(no dip). ptip barely moved yet (2472 -> 2249): the pinch is local,
the floor under it is what is leaving.

Running since 15:10: /tmp/run_exit_fromA (nosink seg8 start, THE MODEL)
and /tmp/run_exit_fromfill (kT_fromfill seg4 start, 23 kPa; uniqueness
test, must drain to the same plateau). Binary /tmp/p2exit. Judgement
routine in NEXT_SESSION.md.

Lesson for the log: I judged the nosink plateau this morning against
Cory with a boundary that could not represent the tank. "Plateau" is
necessary, not sufficient; the exit probe now makes the outlet's state
visible on every print, so the next judgement starts from M_exit.

Independent audit (Sonnet helper, notes/exit_audit_2026-09-02.md,
script tools/audit_exit_2026-09-02.py): old states 0% of exit mass flux
supersonic (M_w 0.55 nosink, 0.12 fromfill, fromfill 52/128 exit cells
backflowing); smoke state M_w 1.08, 71% supersonic by mass flux. Choked
6 g/s at the smoke exit temperature profile: rho 3.0e-4, p_floor 428 Pa
(gamma 5/3; +-30% for the Saha c_s), vs Cory 465. Old floors 2155 and
23000. Caveat it raised and I verified in mv_lxf_field: the face
dissipation is Lax-Friedrichs with coefficient dx/(4 dt) on the GLOBAL
dt (dz/4dt ~1e4 m/s, dr/4dt ~4e3 at dt 3e-8), 3-5x the local signal
speed at the exit, so the 1 Pa ghost drains the LAST cell's thermal
energy faster than free expansion would. One cell wide, same scheme
everywhere (header caveat), not a solver change now; watch p_exit and
the exit T for an undershoot.

### Outlet chain progress (segment endpoints, both chains)

| seg | fromA mass | wall | tip | mdot_out | T_exh | M_exit | fromfill mass | wall | tip | mdot_out |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2.00e-6 | 1042 | 1215 | | 20.9 | | 6.44e-6 | 3610 | 3316 | |
| 2 | 1.78e-6 | 913 | 1161 | 6.24e-3 | 19.75 | | 2.66e-6 | 1532 | 1710 | 8.5e-3 |
| 3 | 1.708e-6 | 870 | 1139 | 6.07e-3 | 19.36 | 1.18 | 1.81e-6 | 1005 | 1317 | 6.6e-3 |
| 4 | 1.676e-6 | 862 | 1117 | 6.05e-3 | 19.34 | 1.18 | 1.58e-6 | 853 | 1008 | 6.28e-3 |
| 5 | 1.651e-6 | 849 | 1107 | 6.006e-3 | 19.24 | 1.18 | 1.50e-6 | 798 | 964 | 6.09e-3 |
| 6 | 1.641e-6 | 844 | 1105 | 5.986e-3 | 19.19 | 1.18 | 1.47e-6 | 777 | 949 | 6.02e-3 |
| 7 | 1.637e-6 | 841 | 1104 | 5.978e-3 | 19.16 | 1.18 | 1.458e-6 | 768 | 943 | 5.99e-3 |
| 8 | 1.636e-6 | 841 | 1104 | 5.975e-3 | 19.16 | 1.18 | 1.453e-6 | 765 | 940 | 5.98e-3 |
| 9 | 1.635e-6 | 840 | 1104 | 5.973e-3 | 19.15 | 1.18 | 1.451e-6 | 764 | 939 | 5.97e-3 |
| 10 | 1.635e-6 | 840 | 1104 | 5.972e-3 | 19.15 | 1.18 | 1.450e-6 | 762 | 939 | 5.97e-3 |
| 11 | 1.635e-6 | 840 | 1104 | 5.973e-3 | 19.16 | 1.18 | 1.450e-6 | 763 | 938 | 5.97e-3 |
| 12 | 1.635e-6 | 840 | 1104 | 5.973e-3 | 19.15 | 1.18 | 1.450e-6 | 763 | 939 | 5.97e-3 |

Seg 4 (20:17): fromA drain decelerating (-9, -3.7, -1.7 %/seg), wall
flat at ~862 since seg 3, tip still easing (1145 -> 1117 within the
segment), T_exhaust 19.34 N flat, bf 0, p_exit ~54, P_wall 73.7 kW of
170 kW Ohmic (V_arc 21.3 V). Backplate at cathode 1989 Pa vs tip 1117:
the pressure maximum sits at the backplate/cathode root, not the tip.
fromfill crossed BELOW fromA in mass while still draining (mdot_out
6.3e-3), wall pressure now equal to fromA's (861 vs 862), tip lower
(1023). Same attractor on wall; whether the two meet in mass/tip is the
seg 5-6 question.

Seg 6 fromA (22:49): mass 1.641e-6 (-0.6%/seg), mdot_out 5.986e-3, now
just BELOW the inlet, wall 844, tip 1105, T_exh 19.19 N. fromA is at
its plateau by the CLAUDE.md standard. fromfill (seg 6 step 18k) sits
at 1.471e-6, wall 777, tip 957, mdot_out 6.02e-3, still -2.2%/seg.
Where the 1.4e-7 kg difference lives (state_seg6 vs state_seg5, numpy):
the upstream reservoir z < 8 cm, r 3-6 cm, i.e. the slow outer gas
(|v| ~200 m/s). fromfill's reservoir is 12% less dense and 7% warmer
at nearly the same pressure (1186 vs 1235 Pa); exit region and arc
column agree within a few %. Thrust agrees to 0.3%. So the residual is
a slow thermal mode of the reservoir (wall conduction + recirculation),
not a second arc solution: fromfill passed through fromA's mass without
stopping because its reservoir temperature differed. Decision: let both
run to seg 8; if the reservoirs still differ by > 5% extend both chains
4 segments (compute is free) before judging tip/wall/profile. The wall
number for the judgement is already bracketed: 780-850 Pa vs Cory 465
(1.7-1.8x, was 4.6x), tip 960-1110 vs 2104 (-50%).

## 2026-09-03 01:30: pressure-outlet plateau JUDGED (fromA seg 8)

Plateau by the CLAUDE.md standard: seg 6-8 mass 1.641/1.637/1.636e-6,
wall 844/841/841, tip 1105/1104/1104, T_exh 19.19/19.16/19.16 N,
mdot_out 5.98e-3 vs in 6.00e-3, M_exit 1.18, bf 0, p_exit ~50 Pa,
P_wall 73.6 kW of 179.6 kW Ohmic (V_arc 21.3 V from the counter, 22.5 V
from the map's cell integral). Stress identity -6.4e-5.
Massaudit gate on ckpt_seg8 (binary /tmp/p2a_exit, dir /tmp/audit_exit):
2.3e-7 PASS. Families: inlet 6.000e-3, outflow -5.975e-3, cathode
-9.6e-5, anode +7.2e-5 (the known corner-ghost diffusive leak: a
convex-corner ghost has two fluid neighbours and one rho; planar walls
book 0). Net electrode leak -2.4e-5 = 0.4% of mdot; note, not a fix.

Images out/img/phase2_A_exit_seg8_{hero,fields,current,alpha}.png;
state out/phase2_state_A_exit_seg8.csv, ckpt out/phase2_ckpt_A_exit_seg8.f32.

### Versus Cory (8 kA, 6 g/s)

| quantity | Cory | nosink plateau (09-02 am, floor BC) | outlet plateau fromA | fromfill bracket |
|---|---|---|---|---|
| cathode tip p (Pa) | 2104 | 2479 (+18%) | 1104 (-48%) | 943 (-55%) |
| backplate at wall (Pa) | 465 | 2155 (4.6x) | 841 (1.8x) | 768 (1.65x) |
| backplate profile rms | 0 | 1.53 (flat) | 0.29 | |
| thrust (N) | ~24.6 | 37.1 | 19.16 (-22%) | 19.0 |
| exit Mach (mass-weighted) | >1 | 0.55 | 1.18 | 1.13 |

The profile now has the right SHAPE: Cory's parabola p = 1689 - 2.99e5
r^2 is matched within 0.87-0.97 at r = 3.0-3.4 cm and within 1.16-1.28
at the cathode root; the excess is all at r > 5.5 cm where the solver
sits on a 1030 Pa shelf (the outer reservoir) while Cory falls to 465.
So the wall number is no longer a boundary artefact (the outlet is
choked, p_exit 50 Pa), it is the reservoir: slow outer gas (|v| ~200
m/s, 4300 K) that Cory's data says should be at half our pressure. The
reservoir is also where the two chains differ (12% in rho, 7% in T):
the model's least-determined region and the one that sets the wall.

Constriction: the surface split is still PRESCRIBED (linear, 0.2 of J
at the tip, mp_build_btp), so only the interior channel is a prediction.
Peak |j| 6.4e6 A/m^2 at r = 0.12 cm, z = 10.31 cm: on the axis just
past the tip; hottest 1% of volume carries 18.0% of the Ohmic power
(17% on the nosink plateau), 27% of Ohmic is downstream of the tip
plane. The pressure MAXIMUM, however, sits at the cathode root on the
backplate (1930-2100 Pa, r 1.0-1.2 cm), not at the tip (1104): the
model pinches at the root because 80% of J is forced to enter the
cathode along its length, and the tip pinch that Cory measures
(2104 at the tip vs 1662 inferred at the root) cannot appear while the
split is prescribed. Verdict on the program question: with the split
prescribed the answer is "constricts onto the axis downstream of the
tip, not onto the tip"; the honest next step is to free the surface
attachment (cathode as an equipotential: the surface current density
follows from the interior solution) rather than tune anything.

Thrust -22%: the electromagnetic term scales as J^2 and is fixed by the
split; the deficit is the gasdynamic/pinch part, consistent with the
missing tip pinch.

What the outlet fix bought: wall 4.6x -> 1.8x, profile flat -> right
shape (rms 1.53 -> 0.29), exit choked, thrust 37 -> 19 N (now under
rather than over), two attractors -> two plateaus 10% apart in the
reservoir only. Chains extended to seg 12 (both) as a uniqueness watch;
judgement above does not depend on which plateau wins.

Ranked next steps (owner call):
1. Free the cathode surface split (the program's actual question). The
   prescribed 0.2 tip split is the single largest known model choice
   and it controls tip p, pinch location and thrust.
2. Reservoir/wall: sigma_en(T_e) and the wall sink's cold-sheet physics
   set the reservoir T; the outer shelf 1030 vs 465 is the wall error.
3. LxF global-dt dissipation at the exit (audit caveat): scheme, not
   physics; revisit only if the exit T undershoots.

### 2026-09-03 06:35: uniqueness watch closed (seg 9-12)

Both chains static to four figures over seg 9-12: fromA 1.635e-6 /
wall 840 / tip 1104 / 19.15 N; fromfill 1.450e-6 / wall 763 / tip 939 /
18.97 N. Closing rate of the mass gap ~1e-9 kg/segment, i.e. > 100
segments to meet: on any affordable run the outer reservoir keeps the
state it started with. Read it as: the arc, exit and thrust are
uniquely determined (thrust agrees to 1%); the outer reservoir, and
with it the wall pressure (763-840) and the tip pressure (939-1104), are
NOT pinned by the present physics. The reservoir is where a wall-sheet
model (sigma_en(T_e), sheath-limited sink) would act; that is item 2 of
the ranked list and it is also a uniqueness question, not only an
accuracy one. Chains done; outputs stay in /tmp/run_exit_*/out
(ckpt_seg1-12, state_seg1-12). No processes running.

### 2026-09-03 11:55: cathode split FREED (owner: "go ahead"), chain running

Model change (rail/mpd_solver.rail, mhd_pbt.rail, phase2_run.rail):
the cathode is an ideal conductor with no sheath. E_t = 0 on the
surface with zero normal velocity gives eta j_t = 0, so the barrel
carries j_z = 0 (d(rB)/dr = 0, ghost B = B_f r_f / r_g = B_f 19.5/18.5)
and the tip carries j_r = 0 (dB/dz = 0, ghost B = B_f). The implicit
resistive sweeps fold these as Neumann ends (`mv_tri_neu_l scr fac`:
diag += a0 fac, a0 = 0, rhs unchanged; fac 1 on z-lines, r_j/r_{j-1}
on r-lines so the inner-face flux cancels exactly). Anode, backplate,
wall and inlet stay prescribed; the backplate face pins J at the root
and the axis pins 0, so the total into the cathode is still J and only
its distribution along the surface is free. Flag: btp slot 0 (cell
(0,0), mask 3, otherwise unused) via `mp_set_free_cath`; runner knob
`run_free_cath` (1.0). The tip-corner ghost (19,80) serves two faces
and keeps the tip form (same class as the known corner mass leak).

Gates: selftest 39/39 before, 41/41 after. Check 40 locks the three
ghost forms and the prescribed fallback; check 41 locks the Neumann
fold EXACT to 1e-12 on c/r (the Dirichlet fold is 7e-4 off on the same
line, check 22 is boundary-order by design) and on a z-uniform line.

Smoke (400 steps, 8.6 us, from fromA seg 12): dt 2.08e-8 steady, no
dt dip, mdot_out 6.14e-3, T_exh 19.15 -> 20.01 N, tip p 1104 -> 1671,
wall 840 unchanged, cathode root 2258. I_enc(z) at j = 20 already moved
from the prescribed line (i=40: 4866 A) toward the tip (i=40: 7090 A,
tip share 0.15 -> 0.17); the surface current is walking down the barrel
toward the tip on the resistive time. Direction is right; the plateau
decides.

RUNNING since 11:55: /tmp/run_free_fromA, binary /tmp/p2free, 8
segments from /tmp/run_exit_fromA/out/ckpt_seg12.f32. Judge at the
plateau: I_enc(z) along the barrel (where does J enter: tip vs root),
tip p vs 2104, wall vs 465, profile rms, thrust vs 24.6, M_exit >= 1,
bf 0, massaudit (rebuild /tmp/p2a from the new solver first). If the
tip share saturates below ~0.5 with the pressure max still at the root,
the missing piece is the sheath (Phase 3), not the split.

### 2026-09-04 00:30: free-cathode chain JUDGED at seg 12 (seg 13-16 still running)

Trend (step 18000 of each segment; mass kg, p Pa, mdot kg/s, N):

| seg | mass | ptip(10,81) | pwall | mdot_out | V_arc | T_exh |
|---|---|---|---|---|---|---|
| outlet 12 | 1.635e-6 | 1104 | 840 | 5.97e-3 | 21.3 | 19.15 |
| 1 | 1.956e-6 | 833 | 441 | 3.54e-3 | 18.9 | 13.36 |
| 3 | 2.844e-6 | 980 | 679 | 4.27e-3 | 19.7 | 15.16 |
| 5 | 3.378e-6 | 1040 | 883 | 5.00e-3 | 20.5 | 16.62 |
| 7 | 3.687e-6 | 1088 | 994 | 5.37e-3 | 20.9 | 17.41 |
| 9 | 3.83e-6 | 1132 | 1072 | 5.65e-3 | 21.0 | 18.00 |
| 10 | 3.903e-6 | 1142 | 1090 | 5.72e-3 | 21.1 | 18.19 |
| 11 | 3.936e-6 | 1141 | 1104 | 5.78e-3 | 21.1 | 18.32 |
| 12 | 3.959e-6 | 1138 | 1114 | 5.81e-3 | 21.2 | 18.38 |

Increments shrink geometrically (mass +0.8, +0.6%/seg; wall +13, +9;
tip flat since seg 10): plateau to ~2% at seg 12, massaudit net dm/dt
1.0e-4 kg/s (1.7% of inflow) still filling. dt steady 1.08e-8, exit
choked (M_exit 1.07, bf 0, p_exit 12 Pa), no starvation, no faults.

ATTACHMENT (the program's question): freed, the current LEAVES the
barrel for the tip. Tip-face share of J 0.15 -> 0.29 (fixed since
seg 1, i.e. set on the resistive time, ~10 us); of the barrel current,
50% enters in the last 1.3 cm (z > 8.7 cm) where the prescribed line
had 50% by 5.3 cm; the last 1 cm of barrel carries 31% of J, so 60% of
J attaches within 1 cm of the tip (prescribed: 33%). Peak |j| 1.8e7
A/m^2 at the tip corner (r 0.97, z 9.94). Pressure MAXIMUM moved from
the cathode root (outlet: 2663 Pa at r 1.1, z 0.8 cm) to the axis 0.5
cm past the tip: 3303 Pa (Cory tip 2104, +57%). The tip-face cell
(10,81) that the step line calls ptip reads 1138 (-46% vs 2104); the
pinch sits just downstream of the face, not on it. Hottest 1% of
volume carries 26% of Ohmic (was 18%), 45% of Ohmic is downstream of
the tip plane, V_arc 22.6 V (181 kW). The axis core leaves the exit at
54 kK and 4.3 km/s. The prescribed-split verdict rule (tip share < 0.5
AND p max at the root => sheath) does NOT fire: the max is at the tip.

CHAMBER (the cost): with the current at the tip the exit throughput at
the old inventory dropped to 3.5 g/s, and the chamber refilled 2.4x
(mass 1.64 -> 3.96e-6) until 6 g/s passes again. Every backplate number
rose with it: wall 1114 (2.4x Cory 465; was 1.8x), root 2827 (was
1948), profile rms 0.50 (was 0.29; ratio 1.7 at r_c, 0.94-1.04 at 3.0-
3.4 cm, 1.6-2.3 on the outer shelf 1250 -> 1114 Pa). Thrust 18.4 N (was
19.2; Cory ~24.6): exit u_mean 2.1 km/s vs Cory's 4.1. The floor is the
exit condition: a choked 6 g/s at T_exit 12 kK needs rho ~2e-4 at the
exit, p ~700 there and ~1100-1250 in the reservoir. The wall excess IS
the exhaust-velocity deficit; it is the same reservoir/exit problem
seen on the outlet chain, not an attachment problem any more. The
outer 1 cm annulus at the exit is a cold sheet (2000 K, 620 m/s, rho
1e-3) carrying 18% of the mass.

Massaudit (/tmp/p2a_free on ckpt_seg12): GATE PASS 7.0e-12; cathode
ghost leak -8.5e-5 kg/s = 1.4% of inflow (was 0.4%), anode +6e-6. The
corner ghost (19,80) serving two faces now sits under the pinch; the
leak scales with it. Known class, now worth fixing (single-face corner
treatment) before the next accuracy claim.

Verdict: freeing the split did what it was for (attachment at the tip,
pinch downstream of the tip, Cory's picture). The remaining error is
the reservoir/exit: chamber pressure floor 2.4x with thrust -25%.
Ranked next (owner call):
1. Exit/exhaust: why u_exit is 2.1 not 4.1 km/s at 8 kA (EM thrust
   Maecker ~15.6 N is in hand; the gas-dynamic part and the plume
   expansion past z = 12.94 cm are not). Domain length / where Cory's
   thrust plane sits; the pressure thrust 6.2 N at our exit plane is
   unconverted.
2. Reservoir/wall sheet: sigma_en(T_e), sheath-limited sink; the cold
   dense annulus carries 18% of mdot at 620 m/s.
3. Cathode corner ghost leak 1.4% (two faces, one ghost).
4. Sheath BC at the cathode (Phase 3) only if 1-3 leave the tip wrong.
Images out/img/phase2_A_free_seg12_{hero,fields,current,alpha}.png;
state/ckpt out/*A_free_seg12*; chain outputs /tmp/run_free_fromA/out.

### 2026-09-04 04:30: free-cathode chain closed at seg 16

| seg | mass | ptip(10,81) | pwall | mdot_out | V_arc | T_exh |
|---|---|---|---|---|---|---|
| 13 | 3.975e-6 | 1149 | 1122 | 5.84e-3 | 21.18 | 18.41 |
| 14 | 3.986e-6 | 1163 | 1126 | 5.86e-3 | 21.20 | 18.46 |
| 15 | 3.994e-6 | 1144 | 1129 | 5.87e-3 | 21.20 | 18.46 |
| 16 | 4.000e-6 | 1161 | 1132 | 5.89e-3 | 21.22 | 18.53 |

Plateau: mass +0.15%/seg, wall +3 Pa/seg, tip 1144-1163 (the probe
cell flickers), thrust 18.5 N, mdot_out closing on 6e-3 at 0.1e-3 per
segment. The seg 12 judgement stands with plateau values wall ~1135,
tip-face ~1155, thrust ~18.5. Final ckpt/state: /tmp/run_free_fromA/
out/ckpt_seg16.f32, state_seg16.csv. No chain processes running.
