# CLAIM
The solver's electron-neutral resistivity uses a CONSTANT argon
momentum-transfer cross-section sigma_en = 1e-19 m^2 (mv_eta_calc,
"Ramsauer-averaged first cut"). Against a Phelps-style argon
momentum-transfer cross-section, the Maxwellian-averaged effective
cross-section sigma_eff(T_e) = <sigma v> / <v> is
  T_e = 0.5 eV: 1.72e-20 m^2 (0.17x the solver's 1e-19)
  T_e = 1.0 eV: 4.35e-20 m^2 (0.44x)
  T_e = 2.0 eV: 8.73e-20 m^2 (0.87x)
so eta_en is 2-6x too HIGH in the 0.5-1 eV band where the arc lives
(A_sink state: hottest cells ~1 eV, median 0.5 eV).
# CONTEXT
Coarse log-log table used for the claimed numbers (energy eV, sigma m^2),
approximating Phelps' argon momentum-transfer set with its Ramsauer
minimum near 0.3 eV:
  0.01 4e-20 | 0.1 5e-21 | 0.2 2e-21 | 0.3 1.5e-21 | 0.5 2e-21 |
  1.0 1.5e-20 | 2.0 5e-20 | 3.0 7e-20 | 5.0 1.2e-19 | 8.0 1.8e-19 |
  12 2.0e-19 | 20 1.3e-19
Two things to check: (1) the integration of THIS table reproduces the
claimed sigma_eff values; (2) the table is a fair reading of the real
argon momentum-transfer cross-section (state any point you believe is
off by more than 2x, and whether the 1 eV conclusion survives).
Consequence if confirmed: in weakly ionized gas the solver overstates
eta_en, which raises Ohmic heating there and makes cold gas MORE
insulating than it is; arc constriction onto the tip could be
partly a sigma_en artefact.
# CHECK HINT
Maxwellian in energy: f(e) ~ sqrt(e) exp(-e/T). sigma_eff = int sigma(e)
sqrt(e) f(e) de / int sqrt(e) f(e) de, log-log interpolate the table,
integrate 1e-3..1e2 eV. Print CHECK lines for the three ratios.
Sandbox note: numpy here has NO np.trapz (removed in numpy 2); use np.trapezoid or a hand-written sum. scipy is absent.
