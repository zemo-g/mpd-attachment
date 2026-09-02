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
