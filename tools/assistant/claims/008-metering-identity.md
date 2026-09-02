# CLAIM
With a ghost-cell inlet where ghost density copies the fluid cell
(rho_g = rho_c) and ghost momentum is mz_g = 2 rho_in v_in - mz_c, the
LxF face flux 0.5 (mz_c + mz_g) - (dz/(4 dt)) (rho_g - rho_c) equals
EXACTLY rho_in v_in, independent of the fluid state. If mz_g is instead
clipped at |mz_g| <= rho_c v_cap with v_cap = 2000 m/s, metering breaks
whenever rho_c < (2 rho_in v_in - mz_c) / v_cap; for the annulus
(rho_in = 0.014707, v_in = 300, mz_c ~ 0) that threshold is
rho_c ~ 4.4e-3 kg/m^3.
# CONTEXT
The 2026-09-01 metered-inlet defect: 19/29 inlet cells clipped at
near-inlet densities of 8.6e-4..1.3e-3, delivering 4.2e-3 of a nominal
6.0e-3 kg/s.
# CHECK HINT
Algebra for the exact-metering identity; numeric for the threshold.
