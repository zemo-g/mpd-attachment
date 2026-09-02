# CLAIM
(1) A choked injector (sonic orifice fed by a mass-flow controller)
delivers a mass flow independent of downstream pressure as long as
p_down/p_up < 0.487 (argon, gamma 5/3), so "a mass-flow controller
cannot force 6 g/s into vacuum" is false: into vacuum it delivers the
same 6 g/s, the gas just expands.
(2) The maximum speed argon can reach expanding from a 300 K stagnation
reservoir into vacuum is sqrt(2 cp T0) = 558.7 m/s with
cp = 2.5 R/M, R = 8.314462618, M = 0.039948 kg/mol; the solver's
inlet speed in_v = 300 m/s is subsonic (a = sqrt(gamma R T/M) = 322.6 m/s).
(3) The solver's vacuum cap: ghost momentum clipped to rho_c * 2000 with
rho_c = 2e-4 kg/m^3 gives 0.4 kg/m^2/s; the face mass flux is
0.5*(mz_c + 0.4) with mz_c ~ 0, i.e. 0.2 kg/m^2/s against the nominal
rho_in*v_in = 0.014707*300 = 4.412 kg/m^2/s: 4.5 percent of nominal.
# CONTEXT
rail/mpd_solver.rail inlet ghost (mask 6). The cap engaged in every
second-order segment (mdot_in fell from 6.0e-3 to 2.87e-3 kg/s) and the
code comment justified it with the false statement in (1). We are
replacing the ghost with a prescribed-flux inlet face. Verify (1) by
computing the critical pressure ratio (2/(gamma+1))^(gamma/(gamma-1)),
(2) and (3) numerically.
# CHECK HINT
Three CHECK lines: crit_ratio, v_max_expansion, cap_fraction.
