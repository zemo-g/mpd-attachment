# CLAIM
The solver's conservative update for a z-face is
  u_new = u + (d_plus - d_minus)/4 - cz*(S_plus - S_minus),  cz = dt/(2 dz)
where for each face S = F_left + F_right (sum of the two physical
fluxes) and d = u_right - u_left (the state jump). If at the inlet face
(the cell's minus face) we set S_minus = 2*F_in and d_minus = 0 with
F_in = rho_in*v_in for the mass equation, then the mass delivered to the
cell through that face in one step is exactly F_in*dt/dz, independent of
the cell's own state (density, velocity, neighbours), to machine
precision. With rho_in = 0.014707, v_in = 300, dz = 0.00125, dt = 5e-9
the per-step density increment is 1.7648e-5 kg/m^3.
# CONTEXT
Design of the prescribed-flux inlet face replacing the metered ghost.
Verify by writing the update for the mass equation with the plus face
computed from random cell states (any random S_plus, d_plus), and the
minus face prescribed; show delta_u - (-cz*(-2*F_in)) contribution from
the minus face equals F_in*dt/dz exactly (isolate the minus-face
contribution by differencing against the same update with F_in = 0).
Use several random draws.
# CHECK HINT
CHECK lines: minus_face_increment (vs 1.7648e-5), max_abs_error over
draws (vs 0, tolerance 1e-18).
