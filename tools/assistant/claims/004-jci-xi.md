# CLAIM
J_ci = sqrt(mdot * u_ci / (mu0_4pi * ln(r_a/r_c))) with mu0_4pi = 1e-7,
r_a = 0.051 m, r_c = 0.0095 m, u_ci(argon) = 8720 m/s, mdot = 0.006 kg/s
gives J_ci = 17645 A, so xi = J/J_ci = 0.453 at J = 8000 A.
# CONTEXT
rail/pbt.rail critical-ionization current; used to argue the 8 kA / 6 g/s
operating point is far below onset. Also check the formula is
dimensionally an ampere.
# CHECK HINT
Dimensional analysis with mu0/4pi in T m/A, then numeric.
