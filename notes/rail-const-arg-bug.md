# Rail compiler bug: top-level float constant as user-fn argument garbles a callee branch

Found 2026-08-31 during phase 2 (commit 5a83537 has the workaround).

## Symptom

In the `rail/phase2_run.rail` compilation unit, calling

    let btp = mp_build_btp run_jtot      -- run_jtot = 8000.0, top-level

produced a prescription array whose CATHODE TIP branch values were bit
garbage (9.5637e12 instead of 0.0328) while sibling branches (cathode
side, backplate, wall) computed correctly. Calling the same function with
the literal `8000.0`, or with `let jt = 0.0 + run_jtot` and passing `jt`,
is correct. Deterministic, bit-identical garbage across recompiles.

## What it is NOT

- Not the nested-user-call marker quirk: hardening every intermediate
  with let-bound `1.0 *` did not change the garbage value.
- Not an identifier-prefix clash: renaming `mp_i_tip_r` (prefix-extends
  constant `mp_i_tip`) changed nothing.
- Not unit-global miscompilation: a trivial `main` in the SAME unit
  (same imports + all runner functions) computes the same call correctly.
  Only the original `main`'s call site with the constant argument fails.

## Repro

In `~/projects/mpd-attachment` (commit 5a83537 or later), revert the
workaround in `rail/phase2_run.rail`: replace `mp_build_btp jt` with
`mp_build_btp run_jtot` (and drop the `let jt = 0.0 + run_jtot` line),
rebuild, run: `btp(19,80)` prints 9.5637e12. The affected callee chain is
`mp_build_btp -> mp_build_btp_loop -> mp_bt_presc -> (mask-1, i==tip
branch) -> mp_ienc_tip / mp_bt_of` in `rail/mhd_pbt.rail`.

## Workaround (in force, guarded)

Bind `let jt = 0.0 + run_jtot` once in main and pass `jt` everywhere
(the mixed float+int O-handler's runtime tag test launders the value).
Same treatment for `run_hall` inside `rail/mpd_solver.rail`.
`rail/selftest.rail` check 21 ("tip prescription sane") fails loudly if
the bug re-manifests.

## Next step

Bisect to a standalone repro in a compiler session (the trigger seems to
need the unit's size/shape, so shrink from phase2_run.rail downward),
then file in rail-bugs and fix in tools/compile.rail.
