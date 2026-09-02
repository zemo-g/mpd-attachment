# Research-assistant protocol (local model as claim auditor)

The model NEVER decides a verdict. It writes an independent numeric
check; the harness executes it; the executed PASS/FAIL lines are the
verdict. Model prose is context, not authority.

## Claim files (claims/NNN-slug.md)

    # CLAIM
    One falsifiable statement, with the numbers.
    # CONTEXT
    Where it comes from (formula, constants, code path). Enough to
    audit, not enough to parrot: do NOT include the derivation steps.
    # CHECK HINT
    What an independent check looks like (CODATA, sympy, dimensional).

## What the model is asked to do (see ra_worker.py SYSTEM prompt)

1. Re-derive independently from first principles / CODATA.
2. Emit ONE self-contained Python block (stdlib+numpy+sympy) that
   computes the claim's numbers and prints lines of the exact form:
       CHECK <name>: computed=<value> claimed=<value> -> PASS
       CHECK <name>: computed=<value> claimed=<value> -> FAIL
3. A one-line summary of any disagreement.

## Verdicts (verdicts/NNN.md) - written by the harness

CONFIRMED   every executed CHECK line is PASS
REFUTED     any executed CHECK line is FAIL (a human reads it next)
CHECK-ERROR the script crashed twice (fed back once for repair)

REFUTED and CHECK-ERROR are the valuable outputs. A REFUTED verdict
goes to the session (Claude) for adjudication: either the repo claim
is wrong (fix the repo) or the check is wrong (fix the claim file and
note why). Never delete a REFUTED verdict; resolve it in writing.

## Trust boundary

Generated code executes locally (tmp cwd, clean env, 120 s timeout).
That is acceptable for OUR model on OUR box and nothing else.

## Harness rules learned 2026-09-01 evening
- Verdict lines are counted on STDOUT only, whole-line `^CHECK ... -> PASS|FAIL$`,
  and a nonzero exit code voids every PASS. Reason: a SyntaxError echo of
  the offending source line ("CHECK x: ... -> PASS" printed by the
  interpreter to stderr) was counted as a PASS and produced a false
  CONFIRMED on claim 001. Read the verdict file, not just the ledger line.
- Two tiers: RA_MODEL (fast instruct, ~1 min/claim) answers first; anything
  not CONFIRMED is escalated to RA_MODEL_STRONG (thinking model). The
  strong verdict stands unless it errored. RA_MAX_TOKENS 6000: a 12k
  thinking generation hit the Metal buffer limit and killed the server's
  generation thread while /v1/models kept answering.
- The queue is re-listed before every pick; prefix a claim `001a-` to jump
  it ahead of `002-`.
