# CLAIM
For azimuthal field B_theta regular on the axis, with enclosed current
I(r) -> c * r^2 as r -> 0, the on-axis axial current density is
j_z = c / pi. With the measured c = I/r^2 = 1.680e7 A/m^2 on a saved
state, j_z(axis) = 5.35e6 A/m^2; a one-sided finite difference of I at
the first cell overestimates it by exactly 2x when the axis ghost
carries I(ghost) = I(first cell).
# CONTEXT
tools/attachment_map.py axis handling; a factor-2 bug of exactly this
form was found and fixed on 2026-08-31.
# CHECK HINT
j_z = (1/(2 pi r)) dI/dr symbolically with I = c r^2; then discrete:
cells at r = (j-1/2)dr, ghost mirror r<0 with B antisymmetric.
Sandbox note: numpy here has NO np.trapz (removed in numpy 2); use np.trapezoid or a hand-written sum. scipy is absent.
