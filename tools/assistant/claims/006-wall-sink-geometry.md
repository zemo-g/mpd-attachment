# CLAIM
For a cylindrical-coordinate cell at radius r with widths dr, dz
(volume V = 2 pi r dr dz), conduction through a wall face evaluated at
distance dx/2 contributes energy-density loss rate
kappa (T - T_w)/(dx/2) * A/V equal to kappa (T - T_w) * G with:
G = 2 r_f / (r dr^2) for a radial face at r_f = r +/- dr/2 (area
2 pi r_f dz), and G = 2 / dz^2 for an axial face (area 2 pi r dr).
# CONTEXT
rail/mpd_solver.rail mv_wall_cell, shipped 2026-09-01, guarded by
selftest check 36.
# CHECK HINT
Pure algebra: A/(V * dx/2) for both face types, sympy.
