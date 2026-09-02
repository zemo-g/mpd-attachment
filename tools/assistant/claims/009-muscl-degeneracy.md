# CLAIM
A MUSCL scheme with minmod limiter degenerates EXACTLY to the
first-order scheme wherever the reconstructed slopes are zero, and
minmod slopes are zero (a) at any local extremum and (b) whenever
either one-sided difference is zero. On exactly linear data the face
states from both sides equal the exact midpoint value.
# CONTEXT
The equivalence-mode gate used before enabling reconstruction
(verified numerically at 8.9e-12 over 200 steps) and selftest checks
34/35.
# CHECK HINT
minmod(a,b) definition; symbolic linear data q_j = a + b*j; extremum
cases numerically.
