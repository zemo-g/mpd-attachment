# Data provenance

## fig1_points.csv

Digitized from IEPC-97-121 figure 1 (page 2), Gilland-1988 argon thrust data
on the PBT, by `tools/digitize_fig1.py`: 300 dpi render, tick-mark axis
calibration, blob detection with chain splitting for touching markers,
filled/open classification by fill ratio. 39 points (23 at 3 g/s, 16 at
6 g/s). Verification overlay: `fig1_overlay.png` (red = 3 g/s, blue =
6 g/s, green box = excluded legend).

Caveats:
- Pixel readout worth ~0.05-0.08 in C_T, ~60 A in J.
- Near 17-18 kA the two series overlap at C_T ~ 2; 2-3 points there carry
  series-swap risk. One or two overlap points around 14-15 kA may be
  missing (merged blobs). Structure is unaffected.
- Error model (self-assigned, in `rail/pbt.rail`):
  sigma = sqrt(0.08^2 + (0.03 C_T)^2).

## Table 2 fits (encoded in rail/pbt.rail, not stored as CSV)

Choueiri & Ziemer, "Quasi-Steady Magnetoplasmadynamic Thruster Performance
Database" (AIAA-98-3472 / JPP 2001), Table 2, T-vs-J fourth-order fits.
Transcription verified digit-by-digit against a 300 dpi render (first
extraction misread Xe 6 g/s a5 as e-14; it is -4.5162e-15 - the selftest
guards this). Paper states measurement errors well below 2%; error model
assigns 5% of C_T to fit-derived points for fit smoothing.

Valid J ranges are NOT from the paper (it says "valid for the range of
parameters shown in the corresponding plot" without numbers). Lower ends
were trimmed to where each polynomial is monotone and tracks the scatter
plots (figs 8/10); read-off worth +-0.5 kA:
argon 6.5-12.5 / 10-21 / 11-24 kA, xenon 8.5-15.5 / 7.5-20.5 kA.

## Measured attachment / pressures (program.md, not yet encoded)

Rudolph-1981 transition currents (J_t1 = 3.7 kA, J_t2 = 14 kA, phi ~ 0.2)
and Cory-1971 pressure fits are quoted in `program.md` and enter at
Phase 2; encode them in `rail/pbt.rail` when the solver needs them.
