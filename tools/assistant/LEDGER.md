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
2026-09-01 22:28  002a  CHECK-ERROR  (0P/0F)
2026-09-01 22:35  002b  REFUTED  (2P/3F)
2026-09-01 22:42  005  CHECK-ERROR  (0P/0F)
2026-09-02 09:20 owner-side adjudication (Claude, from the overnight states):
  002b REFUTED, but for the right reason only by accident: the model's G_r was 105x off (8.2e8; correct 2/(r dr^2) scale); G_z and rho c_v passed. Empirically on the A_sink seg-1 and sink_lnl seg-8 states the clamp fires in 4/330 and 0 wall-adjacent hot cells (median de_raw/(0.5 e_int) 0.10 and 0.03): the sink is NOT clamp-limited; the boundary cells are already cold (T median 790 / 1929 K). The real defect was the constant kappa itself (P_wall 90% of P_ohm); fixed as wall_kappa (T, alpha), selftest 38.
  002a CHECK-ERROR was tooling (numpy has no trapz in the sandbox; use np.trapezoid). Re-queue with that hint.
  005  CHECK-ERROR, same cause. Re-queue with the hint.
2026-09-02 09:53  002a  CONFIRMED  (3P/0F)
2026-09-02 09:59  005  CHECK-ERROR  (0P/0F)
2026-09-02 09:53  002a  CONFIRMED (3P/0F)  <- FALSE PASS: judge() had an absolute "both < 1e-12 means zero" shortcut, so 1e-20 m^2 cross-sections always passed. Fixed (relative only, or both exactly 0); rejudge changes ONLY 002a.
  002a re-adjudicated: REFUTED on numbers, CONFIRMED in direction. Independent integration of the claim's own table gives sigma_eff 1.19e-20 / 3.13e-20 / 6.67e-20 m^2 at 0.5 / 1 / 2 eV (claim said 1.72 / 4.35 / 8.73e-20, 31% high). Either way the solver's constant 1e-19 is 3-8x HIGH in the 0.5-1 eV band. The model also flags the table's 0.1 eV point (5e-21) as inconsistent with 0.3-0.5 eV. Owner call, later: sigma_en(T_e) in eta_en; not a knob to turn while the kappa(T) chains run.
2026-09-02 09:59  005  CHECK-ERROR again (model tooling, two attempts). Parked; the on-axis jz factor is covered by the 2026-08-31 fix note and can be checked by hand.
2026-09-02 15:30  RECORD CORRECTIONS (from the harness review): the 005 CHECK-ERRORs were NOT np.trapz. Both attempts pasted bare `CHECK ...` lines into the Python source (SyntaxError); the np.trapezoid hint fixed nothing. And "scipy is absent" in the 002a/005 sandbox notes was false: scipy 1.17 imports in the sandbox. Both claim files corrected. The 005 model also changed the claimed value between attempts (1.069e6 -> 1.069e7) to make the line read PASS.
2026-09-02 15:30  PARKED (owner: "it may hurt us right now till we do better solutions"). Worker loop (pid 9917) stopped. Nothing is queued or judged until the harness owns every comparison (OPTIONS_2026-09-02.md, option B). Verdict headers stand as LEADS only: REFUTED is worth twenty minutes, CONFIRMED is not evidence. Claim checking in the meantime: one-shot Sonnet helpers with numpy on the real state files, results logged in notes/, not here.
