# CLAIM
The old metered inlet ghost copied the fluid density rho_c and set its
momentum to mz_g = 2*rho_in*v_in - mz_c so the face MASS flux averaged
to exactly rho_in*v_in. But the Lax-Friedrichs MOMENTUM flux through
that face is 0.5*(mz_c*v_c + p_c + mz_g*v_g + p_g) with v_g = mz_g/rho_c,
so the ghost half alone is 0.5*mz_g^2/rho_c. With rho_in = 0.014707,
v_in = 300, mz_c ~ 0 and rho_c = 3.5e-4 kg/m^3 (the pf3 inlet-row
density) that ghost term is 1.1e5 Pa, about 84x the physical momentum
flux rho_in*v_in^2 = 1323 Pa (about 41x the total rho_in v_in^2 + p_in
with p_in = rho_in*62444 = 918 Pa), and the implied ghost velocity is
2.5e4 m/s. The spurious term scales as 1/rho_c: thinning the inlet row
strengthens the jet that thins it (positive feedback). At the smoke's
rho_c = 6.9e-4 the ratio to rho_in v_in^2 is about 43x.
# CONTEXT
Post-mortem of the vmax "runaway" in segments pf2, pf3, m2cfl15: the
saved states put vmax IN the inlet row (i = 1, j = 34..35) at 3179,
11950 and 16618 m/s with rho 1.2e-3, 3.5e-4, 2.6e-4 kg/m^3. We claim the
runaway was at least partly this boundary artefact, now removed by the
prescribed-flux face. Compute the ghost momentum term and ratios at
rho_c = 3.5e-4, 6.9e-4, 1.2e-3, 2.6e-4 and report each ratio.
# CHECK HINT
CHECK lines: ghost_term_3.5e-4 (vs 1.1e5 Pa), ratio_to_rho_v2_3.5e-4
(vs 84), ghost_velocity_3.5e-4 (vs 2.5e4), ratio_6.9e-4 (vs 43).
