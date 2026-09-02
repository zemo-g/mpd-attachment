# CLAIM
Bremsstrahlung power density for Z=1: P_br = 1.69e-38 * n_e * n_i *
sqrt(T_eV)  W/m^3 with densities in m^-3.
# CONTEXT
Unit conversion of the NRL formulary expression; used in
tools/sink_estimate.py to falsify radiation as an energy sink (0.06% of
Ohmic on the reference state).
# CHECK HINT
Start from the standard fusion-literature form P = 5.35e-37 n_e n_i
sqrt(T_keV) W/m^3 (or the NRL erg/cm^3/s form) and convert; also verify
the known benchmark n=1e20 m^-3, T=1 keV -> ~5.35e3 W/m^3.
