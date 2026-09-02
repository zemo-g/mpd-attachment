# CLAIM
The solver's electron-ion resistivity eta_ei = 5.0e-5 / T_eV^1.5
[Ohm m] corresponds to Spitzer resistivity with a SPECIFIC implied
Coulomb logarithm; state what ln(Lambda) it implies and whether that
value is reasonable (5-15) for n_e ~ 1e20-1e22 m^-3, T ~ 1 eV plasmas.
# CONTEXT
rail/mpd_solver.rail mv_eta_calc; the coefficient predates this
session. If the implied ln(Lambda) is far outside 5-15, that is a
finding, not a rounding issue: eta_ei sets the arc's Ohmic dissipation
and V_arc ~ 5 V is a standing puzzle.
# CHECK HINT
Spitzer eta = 5.2e-5 Z ln(Lambda) / T_eV^1.5 (perpendicular differs);
solve for ln(Lambda). Use a standard form and cite which.
