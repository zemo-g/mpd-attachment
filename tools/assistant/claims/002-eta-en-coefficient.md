# CLAIM
Electron-neutral resistivity for argon with sigma_en = 1e-19 m^2:
eta_en = 2.2046e-8 * sqrt(T_K) * (1 - alpha) / alpha  [Ohm m].
# CONTEXT
From eta_en = m_e nu_en / (n_e e^2), nu_en = n_n sigma_en v_te,
v_te = sqrt(8 k T / (pi m_e)), n_n = (1-alpha) n, n_e = alpha n.
Used in rail/mpd_solver.rail mv_eta_calc and tools/attachment_map.py.
# CHECK HINT
Assemble the coefficient from CODATA m_e, e, k_B; the n dependence must
cancel; compare 2.2046e-8 at 1e-3 rel.
