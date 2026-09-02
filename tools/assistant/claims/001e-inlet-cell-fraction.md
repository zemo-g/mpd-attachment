# CLAIM
The inlet occupies fluid rows j = 20..36 (annulus, rho_in = 0.014707)
and j = 71..82 (ring, rho_in = 0.0064220) on the backplate, each cell an
annulus of radial width dr = 0.0005 m at radius r_j = j*dr (check also (j+0.5)*dr; report which reproduces the nominal), all
injecting at v_in = 300 m/s. The nominal total is
sum_j 2*pi*r_j*dr*rho_in(j)*v_in. Compute it, and check whether it
equals 0.00599999578365988 kg/s (the solver's exact nominal). Then find
which subset of rows (contiguous from the ring end, or from the annulus
end) delivering 4.5 percent of nominal reproduces the observed
2.87e-3 kg/s total; report the number of clipped rows.
# CONTEXT
Diagnosis of the mdot_in collapse. The row range is our best reading of
rail/mhd_pbt.rail (mp_j_in1b = 36 is the last annulus row); if the
nominal does not reproduce 0.005999995784 to 1e-9 relative, say so, the
row bounds are then wrong and the verdict is REFUTED for that line.
# CHECK HINT
CHECK lines: nominal_total (vs 0.00599999578365988, rel 1e-9),
clipped_rows_for_2.87e-3.
