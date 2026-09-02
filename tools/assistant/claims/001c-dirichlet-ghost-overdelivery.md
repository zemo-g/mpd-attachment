# CLAIM
If the inlet ghost cell were instead given the reservoir density
rho_in = 0.014707 kg/m^3 (Dirichlet) while the adjacent fluid cell is
near vacuum (rho_c ~ 0), the Lax-Friedrichs face flux
F = 0.5*(F_c + F_g) - (dz/(4 dt)) * (rho_c - rho_g)
carries a diffusive mass influx of (rho_in/4)*(dz/dt) per unit area.
With dz = 0.00125 m and dt = 5e-9 s that is 919 kg/m^2/s, about 208x
the nominal 4.412 kg/m^2/s. So a density-floored ghost cannot meter.
# CONTEXT
This is why option B (ghost density floor) was rejected in favour of a
prescribed-flux inlet face. Also compute the ratio at dt = 2e-8 s (the
first-order segments' typical dt) to show it is not a small-dt artefact.
# CHECK HINT
CHECK lines: diffusive_flux_5e-9, ratio_5e-9, ratio_2e-8.
