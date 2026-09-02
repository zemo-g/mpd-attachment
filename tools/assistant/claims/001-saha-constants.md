# CLAIM
For argon single ionization with partition-function ratio 2 U_i/U_0 = 2*6/1
folded in, the Saha equation n_e n_i / n_0 = S(T) with
S = SAHA_C * T^1.5 * exp(-CHI_K/T) uses SAHA_C = 2.8976196474863585e22
(SI, m^-3 K^-1.5) and CHI_K = 182882.69143808 K, for chi = 15.759611 eV.
# CONTEXT
Constants from rail/mpd_solver.rail eos block, used by the solver EOS and
three Python post-processors. S folds (2 pi m_e k / h^2)^1.5 and the
degeneracy ratio. CODATA 2018 constants.
# CHECK HINT
Recompute SAHA_C = 12 * (2 pi m_e k_B / h^2)^1.5 and CHI_K = chi/k_B from
CODATA; compare both at 1e-6 rel.
