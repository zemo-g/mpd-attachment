# CLAIM
For the r-direction update u_j' = u_j - (dt/(r_j dr)) [r_{j+1/2}
Fhat_{j+1/2} - r_{j-1/2} Fhat_{j-1/2}], the volume-weighted sum
sum_j r_j u_j' - sum_j r_j u_j telescopes to boundary face terms ONLY,
for ARBITRARY face fluxes Fhat, provided the two cells sharing a face
use the same Fhat value. Interior faces cancel identically.
# CONTEXT
The conservation property behind the solver's exact mass gate (selftest
26); the claim is that it is independent of the flux FORM (so a MUSCL
upgrade cannot break interior conservation).
# CHECK HINT
sympy with N=6 cells and symbolic Fhat per face; show the sum equals
boundary terms exactly.
