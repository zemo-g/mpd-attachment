# MPD Current-Attachment Program

Working repo for the program defined in `program.md`: the deliverable is a
*current-attachment predictor*; the analytic scaling relations are the
baseline to beat. Validation target is the Princeton Benchmark Thruster
(PBT). Solver work lands in Rail; source papers live in `refs/`.

## Status

- **Phase 0 - scoreboard: DONE.** `out/measured_ct.csv`, 244 rows of
  measured C_T(J, mdot, propellant) with self-assigned error bars, from two
  sources (see `data/README.md` for provenance and caveats):
  - Choueiri & Ziemer JPP-2001 Table 2 thrust fits, sampled inside their
    valid ranges: argon 1/3/6 g/s, xenon 3/6 g/s
  - digitized IEPC-97-121 fig 1 points (Gilland argon 3/6 g/s), which carry
    the deep low-current C_T rise the database years don't reach
- **Phase 1 - the bar: DONE.** `out/phase1_residuals.csv` + printed summary.
  Numbers to beat (C_T rms per series): Maecker 0.38-1.24; xi relation
  0.09-0.26 on the database range, **1.19 on low-current fig-1 argon 3 g/s**
  (max residual 4.9 at xi = 0.26, over-predicting the rise). That low-xi
  window is where a solver has room to be interesting.
- **Phase 1b - semi-empirical Maxwell-stress model: DONE.**
  `rail/semi_lib.rail` implements eqs 13-16, 22-24 with Rudolph attachment
  + Cory pressures (argon 6 g/s). Reproduces the paper's fig 6 per-surface
  decomposition (BP blowing 1.908 constant; all other terms < 0.45 in C_T)
  and back-infers the fig 4 p(r_c, z0) curve from measured thrust:
  ~1600 N/m^2 at 7-8 kA falling to ~800 near 12 kA, then tracking Cory's
  p(r_ch) as the paper says it must above 14 kA. The flat-profile variant
  (Rudolph's assumption) gives C_T 2.74 where measurement says 4.18 at
  7.2 kA - the doc's "cannot reproduce the low-current rise", quantified.
  These surface integrals are the harness Phase 2's per-surface split
  check compares against; the inferred p(r_c, z0) curve is the published
  target Phase 3 must hit without being told.
- **Phase 2 - solver, attachment prescribed: FIRST LIGHT (2026-08-31).**
  `rail/mpd_solver.rail` (forked axisym core, attachment as B_theta
  Dirichlet ghosts from `rail/mhd_pbt.rail`), 130x106 face-aligned grid.
  20k-step run at 8 kA argon 6 g/s to t = 0.92 ms (~20 flow-throughs), in
  the numerical-resistivity regime (explicit eta off; LxF diffusivity
  ~0.5 v dx is the same order as Spitzer eta/mu0 at this grid). Checks:
  - **stress identity: PASS**, T_vol/T_surf - 1 = 8.9e-4 (layer-0 machinery
    validated at 1e-15 on analytic fields first)
  - **per-surface blowing: PASS**, BP/AIF/CT match eqs 13/14/flat-tip to 0.1%
  - **cathode-tip pressure: 2196 Pa vs Cory's 2104 (4.4%)** - the solver
    reproduces the measured tip-pressure fit without being told it
  - backplate profile: peaked at the cathode (1021 Pa vs 377 at the wall) -
    the qualitative low-current mechanism; levels run ~40-60% of the
    parabola inferred from measured thrust (`tools/compare_bp_profile.py`)
  - T_exhaust 18.6 N vs ~24.6 N measured (76%); mdot_out 2x inlet (vacuum
    floor still feeding some mass; not fully steady)
  Images: `out/img/phase2_8ka_hero.png` (pressure + exact current
  streamlines, mirrored section), `out/img/phase2_8ka_fields.png`;
  renderer `tools/render_fields.py`. Pathological curl-eta state kept as
  `*patho*` for the before/after record.
- **Phase 2 - REAL RESISTIVITY, implicit (2026-08-31 evening).** The
  numerical-resistivity regime proved metastable (its only damping, LxF
  diffusion ~0.5 v dx, fades as the flow converges; a tracking re-run
  detonated at t ~ 0.7 ms), and every explicit Spitzer-eta form detonates
  at dr = 0.5 mm (sub-cell resistive layer vs pinned Dirichlet faces;
  A/B-isolated, commit 8864ef3). Fix: **operator-split implicit diffusion**
  in `rail/mpd_solver.rail` - backward-Euler Thomas tridiagonal solve per
  z-line then per r-line, prescribed faces folded into the matrix (no
  ghost feedback), axis face regularized g = 2B/r, magnetic-energy pairing
  + explicit Ohmic heating dt eta j^2. eta = Spitzer capped [1e-7, 2e-5],
  physical band; the resistive dt limit is gone (unconditional stability).
  20k-step run at 8 kA argon 6 g/s (out/phase2_run_implicit.log):
  - **stress identity -5.8e-5** (15x better than first light)
  - **cathode-tip pressure 2167 Pa vs Cory 2104 (3.0%)**
  - backplate wall p 886 vs Cory 465 (1.9x, was 14.8x in the no-eta run)
  - T_exhaust 25.9 N vs ~25 N measured at 8 kA; mdot_out 1.5x inlet
    (still converging - mass and vmax still trending at 20k steps;
    `run_resume = 1.0` chains segments from `out/phase2_ckpt.f32`)
  - vmax decays monotonically through the old detonation window; floor
    mass budget exactly 0 (healthy regime never touches the floor)
  - HALL SMOKE PASS on the resistive checkpoint (identity held, bounded)
  Selftest 25 checks: 22-25 lock the implicit operator (exact
  preservation of B~r through the axis path and both Dirichlet folds,
  linear-z; c/r held to boundary order - the ghost fold is linear
  extrapolation, so curved profiles are O(dr^2) at faces, by design).
- **Inlet was NOT metering 6 g/s (found + fixed 2026-08-31 night).**
  `rail/phase2_massaudit.rail` decomposes the LxF mass flux across every
  boundary face by surface family (the scheme's face flux is
  0.5(F_c+F_g) - (dx/4dt)(rho_g-rho_c), so attribution is exact). On the
  seg-2 state: walls leak exactly zero (mirror ghosts cancel both flux
  halves), but the naive inlet Dirichlet ghost admitted **8.04e-3 kg/s
  against 6.0e-3 nominal (1.34x)** - the face flux adds the fluid-side
  momentum average and a rho-diffusion influx on top of what the ghost
  declares. Every earlier "6 g/s" number was really ~8 g/s. The inlet is
  now a mass-flow-controller ghost (rho copied from the fluid cell, mz
  reflected around nominal, face flux exactly rho_in v_in); the audit is
  the standing check (inlet row must read ~0.006). Correcting the BC set
  off a large relaxation - the domain sheds the ~2.7x excess mass through
  a damped breathing mode (tip p ringing 3563..4344 Pa, mass still
  draining at seg-3 end) - so **no observable from before the plateau is
  a validation number**. Segments chain via `run_resume` until mass,
  vmax, ptip, pwall, and mdot_out (all in the periodic print) settle.
  **Open:** ride out the relaxation to the true 6 g/s steady state, then
  re-judge tip/wall/backplate-profile vs Cory and T vs measured; Hall via
  subcycling/IMEX; the J-sweep (phase 2 sign-off); then Phase 3 sheath
  BCs.

## Run

```bash
cd ~/projects/mpd-attachment
RAIL=~/projects/rail/rail_native
$RAIL run rail/phase0_scoreboard.rail --out-prefix /tmp/rail_mpd0
$RAIL run rail/phase1_baselines.rail  --out-prefix /tmp/rail_mpd1
$RAIL run rail/semi_model.rail        --out-prefix /tmp/rail_mpds
$RAIL run rail/selftest.rail          --out-prefix /tmp/rail_mpdt   # expect SELFTEST PASS
```

Regenerate the digitized points (needs poppler + py311 PIL/numpy):
`/opt/homebrew/bin/python3.11 tools/digitize_fig1.py`

## Corrections vs `program.md` (verified against the papers)

1. **The Choueiri relation has xi^2 INSIDE the log**: eq 36/37/39 of
   IEPC-97-121 read `C_T = nu/xi^4 + ln(ra/rc + xi^2)`, not
   `... + ln(ra/rc) + xi^2`. Outside-the-log over-predicts every
   high-current point by ~0.7; inside matches to rms ~0.1-0.26.
2. **Argon mass flows**: the JPP-2001 database measured 1/3/6 g/s (not
   1.5/3/6; the 1.5 g/s series is Gilland-1988 and only exists in
   IEPC-97-121 fig 7, undigitized so far). Xenon gained a 3 g/s series.
3. **Measured low-current slope is ~J^-1.3** over xi < 0.6 on the digitized
   fig-1 points, not the J^(-3..-4) the doc (and the paper's text) quote.
   The steep exponent may only hold below the lowest digitized point, or
   the claim is about the model's asymptote, not data. Standing finding.
4. **Two typos in IEPC-97-121 itself**: eq 13 drops the J^2 factor (the
   program doc has it right), and eq 23's final log is printed ln(ra/rc)
   where the face integral derives ln(ra/rch) - the printed form drives
   the inferred p(r_c, z0) negative above 14 kA, contradicting the paper's
   own fig 4; the derived form reproduces it. Selftest locks the variant.

## Layout

- `program.md` - the program doc (verbatim copy of the Desktop original)
- `refs/` - source PDFs (IEPC-97-121, JPP-2001 database paper)
- `data/` - digitized points + provenance notes (`data/README.md`)
- `rail/pbt.rail` - PBT geometry, constants, Table 2 fits, baselines, Rudolph/Cory prescriptions
- `rail/semi_lib.rail` / `rail/semi_model.rail` - Maxwell-stress decomposition (phase 1b)
- `rail/phase0_scoreboard.rail` / `rail/phase1_baselines.rail` - runners
- `rail/selftest.rail` - 25 transcription/data/scoreboard/model/phase2 guards
- `out/` - generated CSVs (rebuilt by the runners)
