# MPD Current-Attachment Program

**Thesis:** the deliverable is a *current-attachment predictor*. The thruster
model exists to turn attachment into a checkable number. The analytic scaling
relations are the baseline to beat, not the goal.

---

## Constants and closed-form models

### Notation

| Symbol | Meaning |
|---|---|
| `J` | total discharge current (A) |
| `ṁ` | mass flow rate (kg/s) |
| `r_a`, `r_c` | anode / cathode radius (m) |
| `B_θ` | self-induced azimuthal field (T) |
| `C_T` | dimensionless thrust coefficient |
| `ξ` | dimensionless current, `J / J_ci` |
| `φ` | fraction of total current attaching at cathode tip |
| `j_i`, `j_o` | current density on anode inner / outer face |

### Thrust coefficient

    C_T ≡ (4π/μ₀) · T / J²

### Maecker (baseline 1 — the null hypothesis)

    T = (μ₀/4π) · [ ln(r_a/r_c) + 3/4 ] · J²
    C_T = ln(r_a/r_c) + 3/4

Independent of `J`, `ṁ`, and propellant. That independence is exactly what the
data contradicts:

- overpredicts `C_T` by >20% at high current
- measured `C_T` reaches >250% of Maecker at low current
- low-current scaling goes as `J^(-n)`, `n` between 3 and 4

The low-current rise is **not** electrothermal. It is the gasdynamic pressure
distribution on the backplate induced by the *pinching* component of the
Lorentz force.

### Critical ionization velocity

    u_ci = sqrt( 2·ε_i / m_a )

| Propellant | `u_ci` (km/s) |
|---|---|
| Xenon | 4.22 |
| Argon | 8.72 |
| Lithium | 12.24 |

### Critical ionization current and ξ

    J_ci = [ ṁ · u_ci / ( (μ₀/4π) · C_T ) ]^(1/2)
    ξ    = J / J_ci

Use `C_T ≈ ln(r_a/r_c)` to first order; near `ξ ≈ 1`, `ln(r_a/r_c) + 1` is
better.

### Choueiri scaling (baseline 2 — the bar to beat)

    C_T = ν/ξ⁴ + ln(r_a/r_c) + ξ²
    ν   = ṁ / ṁ*,   ṁ* = 66 g/s

Held across argon and xenon, three mass flows, two thrusters of different
scale. **Failed on hydrogen** — high and ill-defined `u_ci` for a diatomic.

### Onset / full-ionization current

    T = b·I²           for I ≥ I_fi
    T = b·I_fi·I       for I ≤ I_fi
    I_fi = sqrt( ṁ · u_ci / b )

Check case: argon, 660 mg/s, `b = 1.8e-7 N/A²` → `I_fi = 5600 A`.
This is the same quantity as `J_ci`. Two independent derivations agreeing —
treat `ξ ≈ 1` as the onset boundary.

### Applied-field (only if you go there)

    T_AF = k · J · B_A · r_a,    k ≈ 0.2

Total thrust taken as AF + self-field + gasdynamic. The explicit constant has
an inverse cathode-length dependence that makes it unsuitable for recessed
cathodes.

---

## Governing equations for the solver

Single-fluid momentum:

    ρ · Du/Dt = j × B − ∇p

Generalized Ohm's law — **retain the Hall term**, it is what drives the anode
region and without it onset is unreachable:

    E = j/σ − ∇p_e/(n·e) + (j × B)/(n·e) − u × B

Ampère (self-field closure):

    ∇ × B = μ₀ · j

Exact identity for the blowing thrust, via the Maxwell stress tensor — this is
your best solver test, since any mismatch is a bug rather than physics:

    T_b = ∫_V (j_r · B_θ) dV = ∮_S (β̃ · dS)_z

For a coaxial self-field MPDT with azimuthal-only `B`, `β̃` is diagonal with
entries `(−B_θ²/2, −B_θ²/(2r²), −B_θ²/2) / μ₀`. Only the four surfaces
perpendicular to the thrust axis contribute: backplate, anode inner face, anode
outer face, cathode tip.

Blowing contributions:

    [T_b]_BP = (μ₀/4π) · ln(r_ch / r_c) · J²        (backplate)
    [T_b]_CT = (μ₀ φ² J² / 4π) · (3/2 − 2·ln 2)     (cathode tip)

(Anode inner/outer face terms are longer; see Choueiri IEPC-97-121 eqs. 14–15.)

Pinching, backplate — the interesting one, since the second integral vanishes
there and the pressure gradient is balanced by the radial flow term alone:

    p(r, z₀) = b − a·r²
    a = [p(r_c) − p(r_ch)] / (r_ch² − r_c²)
    b = p(r_c) + a·r_c²
    [T_p]_BP = b·π·(r_ch² − r_c²) − (a·π/2)·(r_ch⁴ − r_c⁴)

Setting `p(r_c,z₀) = p(r_ch,z₀)` recovers the flat-profile assumption and
**cannot** reproduce the low-current rise in `C_T`.

---

## Validation case: Princeton Benchmark Thruster

Geometry (metres unless noted):

    r_c   = 0.0095      cathode radius
    r_a   = 0.051       anode inner radius
    r_ch  = 0.064       chamber radius
    r_ao  = 0.093       anode outer radius
    t_a   = 0.0095      anode thickness
    l_c   = 0.10        cathode length

Measured attachment, argon at 6 g/s:

    J ≤ J_t1          : j_i = J/S_i,      j_lip = 0,                   j_o = 0
    J_t1 ≤ J ≤ J_t2   : j_i = J_t1/S_i,   j_lip = (J−J_t1)/S_lip,      j_o = 0
    J > J_t2          : j_i = J_t1/S_i,   j_lip = (J_t2−J_t1)/S_lip,   j_o = (J−J_t2)/S_o

    J_t1 = 3.7 kA
    J_t2 = 14 kA
    φ    ≈ 0.2   (essentially constant)

Measured pressures, argon at 6 g/s:

    p(r_ch, z₀)   = 6.5e-4 · J^1.5   N/m²     (Cory)
    p(r_c, z_tip) = 0.263 · J        N/m²

Thrust data: argon at 1.5, 3, 6 g/s; xenon at 6 g/s; `J` up to ~25 kA.
Thrust is order 100 N.

Neglected and safe to neglect: cold-gas thrust `T_c`; viscous forces (order
1e-2 N/cm² over ~100 cm² of wall, versus ~100 N of thrust).

---

## What is fitted, not physics — do not carry these forward

| Quantity | Status |
|---|---|
| `ṁ* = 66 g/s` | fitted, no derivation, "universal" only across 2 propellants / 2 similar thrusters |
| `J_t1`, `J_t2`, `φ` | measured on PBT (Rudolph 1981) — **inputs**, not predictions |
| `p(r_ch,z₀)`, `p(r_c,z_tip)` fits | measured on PBT (Cory 1971) |
| `p(r_c,z₀)` | back-inferred from thrust data; the single free parameter of the whole model |
| `k ≈ 0.2` | stated outright as per-thruster |
| ξ⁻⁴ and ξ² *exponents* | **keep** — held across propellants and scales, structural |
| Maxwell stress derivation | **keep** — exact |
| `u_ci` formula | **keep** — atomic physics |
| ξ ≈ 1 ↔ `I_fi` coincidence | **keep** — two independent derivations agreeing |

Also discard: all AF-MPDT hardware material (HTS coils, cryocoolers, TRL
levels) as irrelevant to simulation, and hydrogen as a validation propellant.

---

## Open problems — the actual targets

1. **Current attachment.** Every analytic model measures it and feeds it in.
   None predicts it. Primary target.
2. **`p(r_c, z₀)`.** Back-inferred today; a solver computes it directly. Has a
   published curve to check against. Cleanest well-posed win.
3. **A derivation for the ξ⁻⁴ coefficient.** Currently fitted only.
4. **Onset mechanism.** Four live candidates: anode starvation, full
   ionization, run-away Joule heating, excessive back-EMF. Simulation leans
   toward starvation; not closed.
5. **Post-onset regime.** Steady-flow formulations stop at the limit. Largely
   empty — and out of scope here.
6. **Erosion rates.** Sets lifetime; coupled to all of the above.

---

## Phases

### Phase 0 — scoreboard before model

Encode PBT as a fixed test case: geometry, Cory pressures, Rudolph attachment,
digitized `C_T` vs `J` curves for argon (1.5/3/6 g/s) and xenon (6 g/s).

**Deliverable:** `measured_CT(J, ṁ, propellant)` plus self-assigned error bars.
Nothing else gets built first.

### Phase 1 — the bar

Implement Maecker and the ξ relation. Log residuals against Phase 0.

**Gate:** anything built later that cannot beat the ξ relation on PBT data is
not earning its complexity. Residual structure tells you where the solver has
room to be interesting.

### Phase 2 — solver validation, attachment prescribed

Axisymmetric resistive MHD, Hall term on. Feed it Rudolph's attachment. One
question only: does the interior physics work?

**Checks:**
- reproduce Cory's radial backplate pressure profile
- recover the per-surface blowing/pinching split
- confirm `∫_V j_r B_θ dV == ∮_S (β̃·dS)_z` — exact, so any mismatch is a bug

**Kill criterion:** if these fail with attachment handed to it, stop. Do not
proceed to Phase 3.

### Phase 3 — release attachment (the research)

Replace prescribed current density with a sheath boundary condition. Let the
solver distribute current.

**Predict:** `j_i`, `j_o`, `φ` vs Rudolph. Then compute `p(r_c,z₀)` directly and
compare to the published inferred curve. If it lands without being told the
answer, the model stops being semi-empirical.

This is the phase that can genuinely fail. Wire in experiment-loop here.

### Phase 4 — onset as a competition

Add two-temperature, non-equilibrium ionization, resolved anode boundary layer.
Implement the *conditions* under which each of the four onset theories would
fire; sweep `J²/ṁ` upward and see which triggers first.

Accept up front: steady-flow means you predict the approach to onset, not past
it.

---

## Standing conventions

- **Non-dimensionalize on magnetic Reynolds number and Hall parameter**, not on
  PBT dimensions — otherwise everything learned is welded to one 1980s thruster.
- **Every run stores the attachment field**, not just thrust. Thrust is one
  scalar; attachment is the output.
- Phases 3–4 are branching parameter sweeps. That is what experiment-loop is
  for; wire it at Phase 3 rather than retrofitting.

## Scoping honesty

Phases 0–2 are engineering with known answers, and success is well-defined.
Phase 3 may fail. Phase 4 may not resolve at all. Set it up so that a validated
MHD solver in Rail is the deliverable regardless, and Phase 3 is upside.

**Binding constraint is validation data, not theory.** One good public dataset
exists — PBT, argon and xenon, ~5 cm anode, 1980s. Modern work is paywalled,
proprietary, or published without geometry. Pick targets where being
qualitatively right is useful.

---

## Sources

- Choueiri, *On the Thrust of Self-Field MPD Thrusters*, IEPC-97-121 (1997) —
  primary; scaling relation, stress tensor derivation, PBT constants
- Choueiri, *Scaling of Thrust in Self-Field MPDTs*, J. Prop. Power 14(5) 1998
- Rudolph, PhD thesis, Princeton 1981 — attachment measurements, first-principles
  thrust analysis
- Cory, PhD thesis, Princeton 1971 — pressure measurements
- Maecker, Z. Phys. 141(1) 1955
- Jahn, *Physics of Electric Propulsion*, McGraw-Hill 1968
- Tikhonov et al., IEPC-93-076 — alternative `C_T`, applied-field relation
- Han & Rana, *Applied-Field MPD Thrusters for Deep Space Exploration*,
  arXiv:2410.17478 (2024) — onset theory review
- Heiermann & Auweter-Kurtz, J. Prop. Power 21(1) 2005 — numerical support for
  anode starvation
- Schrade et al., NASA TM 91-022 — run-away Joule heating onset theory
