# Rail: top-level float constant references cost a runtime atof each

Found 2026-09-01 profiling the first Saha-EOS binary (175 ms/step vs
~50 expected; `sample` showed ~35% of wall time in strtod_l/atof/
localeconv plus os_unfair_lock churn from the locale lock).

## The behavior

A reference to a top-level float constant, e.g.

    saha_c = 2.8976196474863585e22
    f x = x * saha_c        -- every call re-parses "2.89...e22" via atof

compiles the constant as a tiny function whose body calls atof on the
literal string, evaluated at EVERY reference (~50ns + locale lock,
measured: 20M references = 1s). Inline literals in expressions are
embedded at compile time and cost nothing; function arguments cost
nothing.

    loopc x n = loopc (x + myconst) (n-1)     -- 1s / 20M   (atof)
    loopl x n = loopl (x + 1.0e-7) (n-1)      -- 0s / 20M   (embedded)
    loopa x c n = loopa (x + c) c (n-1)       -- 0s / 20M   (register)

Confirmed by otool: DYLD-STUB$$atof call sites inside the compiled
bodies of constants and of every function referencing them
(mv_ghost_cell had 43).

## The rule for hot loops

Never reference a named top-level float constant inside a per-cell or
per-iteration loop. Hoist it once outside (`let kb = 1.0 * k_boltz`)
and pass it as an argument, or write the literal inline. See
eos_temp_bi in rail/mpd_solver.rail for the pattern (all 4 invariants
hoisted into args; 8 args = the TCO limit).

## Compiler improvement candidate (compile.rail session)

Pool float constants: parse each top-level literal once at startup (or
embed the bit pattern like inline literals - they already take that
path, so the machinery exists) instead of emitting atof per reference.
This would speed every Rail program with named constants in hot code.
Probably related to (but distinct from) the const-arg garbling bug in
notes/rail-const-arg-bug.md - both stem from constants-as-functions.
