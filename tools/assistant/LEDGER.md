2026-09-01 18:33  004  CONFIRMED  (2P/0F)
2026-09-01 19:14  001  REFUTED  (1P/1F)
2026-09-01 19:21  001a  REFUTED  (0P/1F)
2026-09-01 19:28  001b  REFUTED  (2P/1F)
2026-09-01 19:35  001c  CONFIRMED  (3P/0F)
2026-09-01 19:42  001d  REFUTED  (0P/2F)
2026-09-01 19:50  001e  REFUTED  (0P/2F)
2026-09-01 19:57  001f  REFUTED  (1P/15F)
2026-09-01 19:57  002  CONFIRMED  (1P/0F)
2026-09-01 20:04  003  REFUTED  (0P/2F)
2026-09-01 20:11  005  CHECK-ERROR  (0P/0F)
2026-09-01 20:25  006  CONFIRMED  (3P/0F)
2026-09-01 20:32  007  REFUTED  (1P/1F)
2026-09-01 20:32  008  CONFIRMED  (2P/0F)
2026-09-01 20:32  009  CONFIRMED  (3P/0F)
2026-09-01 20:45  ADJUDICATION (harness now re-judges CHECK lines at rel 1e-2; --rejudge run):
  001b CONFIRMED (558.747 vs 558.7 was an exact-compare artefact): choked injector delivers regardless of downstream p; v_max 559 m/s; cap fraction 4.5%.
  001d CONFIRMED by hand: |increment| 1.76484e-5 exact, sign is the model's face orientation; max error 0.0. Independently: selftest 33 + massaudit 4.3e-11.
  001e CONFIRMED by hand: sum 2 pi (j-0.5) dr dr rho_in v_in over rows 20-36, 71-82 = 0.005999995783659879 (mp_r_of = (j-0.5) dr); the model lost a factor ~2000. Claim's "r_j = j dr" was the wrong guess, as the claim allowed.
  001f CONFIRMED: every claimed number passes (1.1e5 Pa, 84x, 2.5e4 m/s, 42.6x); the FAILs reuse the 3.5e-4 claimed values at other densities.
  001  CONFIRMED by hand: saha_c = 2.8976e22 = 12 x (2 pi m_e k / h^2)^1.5 = 2 x g(Ar+)/g(Ar)=6 x 2.4147e21. The model's 7.19e24 used a different constant.
  003  CONFIRMED: model's 5.35e3 is the keV-form coefficient (5.35e-37 sqrt(T_keV)) fed T in eV, = 1.69e-38 sqrt(T_eV) x 31.6. Claim stands.
  007  CONFIRMED in substance: the symbolic sum reduces to Fhat_0 and Fhat_4 terms only, i.e. pure boundary flux; the model compared it to 0 instead of to the boundary term.
  001a REFUTED = FINDING: implied ln(Lambda) = 5.0e-5/5.2e-5 = 0.96. A physical ln(Lambda) at n_e 1e20-1e22, 1 eV is 5-10, so the solver's Spitzer resistivity is 5-10x LOW. Candidate root cause of the too-quiet arc (V_arc 5 V). Owner's call: raise eta_ei coefficient to 5.2e-5 ln(Lambda) with ln(Lambda) computed from n_e, T (gates before/after).
  005  CHECK-ERROR: retry queued (delete verdict to re-run).
