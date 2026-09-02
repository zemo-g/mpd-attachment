# CLAIM
The wall sink (mv_wall_cell) removes energy density dE = kappa_wall
(T - T_wall) dt G per step from every fluid cell touching an electrode
or wall, with G = A_face / (V_cell dx/2) summed over touching faces:
r-face G_r = 2 r_f / (r dr^2), z-face G_z = 2 / dz^2. With dr = 0.0005,
dz = 0.00125, r_j = (j - 0.5) dr, at j = 20 (r = 0.00975) the r- face
gives G_r- = 7.795e6 m^-2 and a z face gives G_z = 1.280e6 m^-2.
The cooling time of such a cell, tau = rho c_v / (kappa_wall G), with
rho = 1e-3 kg/m^3, c_v = 1.5 k / m_Ar = 312.2 J/kg/K and kappa_wall = 1
W/m/K, is 4.0e-8 s, i.e. 1.34 timesteps at dt = 3e-8 s. The solver
clamps dE at 0.5 e_int per step, so at kappa_wall = 1 every wall-touching
cell is CLAMP-limited (loses half its internal energy per step) and the
effective sink no longer depends on kappa_wall anywhere in the band
[0.3, 3] W/m/K that tools/sink_estimate.py bracketed.
# CONTEXT
rail/mpd_solver.rail mv_wall_cell; kappa_wall = 1.0, t_wall = 300.
The sink was added because adiabatic walls omitted 16x-160x total
Ohmic. If the claim holds, the "kappa band" is not being scanned at all:
the two overnight sink chains are running an unphysical half-energy-per-
step boundary condition, which would explain the cold dense gas piling
up at the wall (mdot_out stuck at a third of the inflow). The fix
direction is an implicit or rate-limited sink (or a much smaller
effective kappa for a half-cell conduction length), owner's call.
# CHECK HINT
Compute G_r-, G_z, rho c_v, tau, tau/dt from the stated numbers and
print CHECK lines. Also derive G from first principles (flux kappa
(T - T_w) / (dx/2) through area A into volume V) and confirm the r-face
form 2 r_f / (r dr^2) with A = 2 pi r_f dz, V = 2 pi r dr dz.
