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
  **Open for the next solver session:** energy-consistent explicit
  resistivity (curl form is checkerboard-transparent and slowly diverges;
  compact diffusion detonates at Dirichlet corners via quadratic ghost
  feedback - both isolated by A/B, see commit 8864ef3), Hall-on run
  (whistler dt ~100x), state checkpointing for run continuation, mass
  budget accounting for the vacuum floor.

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
- `rail/selftest.rail` - 17 transcription/data/scoreboard/model guards
- `out/` - generated CSVs (rebuilt by the runners)
