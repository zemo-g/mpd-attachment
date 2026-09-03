# Harness review of tools/assistant (Opus agent, 2026-09-02)

I read every file in the harness, ran `--rejudge` (read-only), and probed `judge()` and `run_block()` in a copy under the scratchpad. The worker (pid 9917, `--loop`, 12h uptime, `RA_MODEL=Qwen3-4B-Instruct`, `RA_MODEL_STRONG=Qwen3.8-27B`, `RA_MAX_TOKENS=6000`) was not touched; no repo file was modified.

# 1. Judge / status logic

**J1 — A script that crashes *after* printing CHECK lines is reported as REFUTED, not CHECK-ERROR. `ra_worker.py:70-71`. Blocks trust.**
```python
if "CHECK harness:" in output:
    return 0, len(CHECK_RE.findall(output)), output
```
Every parseable CHECK line in a crashed run is counted as a **fail**, so `run_model` line 165-167 yields REFUTED. Failing input: a script that prints two PASS lines then raises. This is live and it is on the highest-consequence claim in the ledger: **`verdicts/001a-spitzer-lnlambda.md:36-45`** — both attempts printed 3 CHECK lines then died on a bare `AGREE` / `DISAGREE` (`NameError`). The header says `REFUTED (0 pass / 1 fail)`; today's judge says `(0P/3F)`. That verdict is what drove the eta_ei → NRL ln(Lambda) solver change. Smallest fix: `return 0, 0, output` (harness error ⇒ CHECK-ERROR, never REFUTED). Note the docstring at line 69 already says "A harness failure voids all" — the code does the opposite, which is how this hid.

**J2 — Unparseable numbers hand the verdict back to the model. `ra_worker.py:83-84`. Blocks trust.**
```python
except ValueError:
    ok = m["v"] == "PASS"
```
Contradicts `PROTOCOL.md:3-5` ("the model NEVER decides a verdict... prose is context, not authority"). Live: **`verdicts/007-lxf-telescoping.md:52-53`**, where both lines are sympy expressions and the second is `computed=<expr> claimed=<same expr> -> PASS`. The recorded `REFUTED (1P/1F)` is 100% model-token. (Today it is worse — see J3 — `--rejudge` now reports 007 as `CHECK-ERROR (0P/0F)`.) Fix: on `ValueError`, force CHECK-ERROR.

**J3 — CHECK lines that miss the regex are silently dropped. `ra_worker.py:59,74-76`. Blocks trust.**
`CHECK_RE` demands space-free values and `-> ?(PASS|FAIL)\s*$`. Verified to vanish entirely: `computed=dt*(Fhat_0*(r0 + r1))` (space inside value), `->  PASS` (two spaces), `-> **PASS**`, `-> FAIL (see note)`, lowercase `check`. A claim with three quantities can go **CONFIRMED on the one line that parsed**, and the header `(1 pass / 0 fail)` gives no hint that two were discarded. Fix: also count `^\s*CHECK\b` lines that fail the strict match; any >0 ⇒ CHECK-ERROR.

**J4 — NaN and inf become confident FAILs. `ra_worker.py:79-82`. Blocks trust.**
Measured: `computed=nan claimed=nan` → REFUTED (0P/1F); `computed=inf claimed=inf` → REFUTED. The known "model divided by a claimed 0.0" failure lands exactly here and is announced to the physicist as a refutation. Fix: `if not (math.isfinite(c) and math.isfinite(k)): raise ValueError` routed to CHECK-ERROR.

**J5 — Both sides of every comparison are supplied by the model; the harness never sees the claim's number. `ra_worker.py:59,79`. Blocks trust — this is the single largest hole.**
Live tautologies that produced or padded verdicts:
- `verdicts/008-metering-identity.md:28` — `computed={rho_in * v_in:.6e} claimed={rho_in * v_in:.6e} -> PASS`. Same expression on both sides. Verdict: **CONFIRMED (2P/0F)**. The claim's actual content (the LxF face flux is exactly `rho_in v_in` *independent of the fluid state*) was never executed; the model asserted it in prose and printed an identity.
- `verdicts/001d-prescribed-face-exact.md:42` — `print(f"CHECK max_abs_error: computed=0.0 claimed=0.0 -> FAIL")`, a **hardcoded literal with no variable**. Today's comparator turns that fabricated line into a PASS (`--rejudge` prints `(harness: PASS)` for it).
- `verdicts/001a:30-31` (`5.00e-05` vs `5.00e-05`, `Z=1` vs `1`), `verdicts/003` benchmark line (`5.35e+03` vs `5.35e+03`), `verdicts/001c` `ratio_2e-8` (`52.0845` vs `52.0845`).

A model that prints `CHECK x: computed=<claim's number> claimed=<claim's number> -> PASS` gets CONFIRMED, and nothing in the verdict header distinguishes that from a real derivation. Worse, the model can **invent** a claimed value: `verdicts/001a:37` is `CHECK ln(Lambda): computed=0.962 claimed=1.000 -> FAIL` — the claim states no such number anywhere. Smallest fix: claims carry a machine-readable expected table and `judge()` compares against *that*, requiring the full declared name set.

**J6 — The comparison runs on the model's *rounded print*, so print precision caps the tolerance. `ra_worker.py:79`. Degrades.**
`verdicts/002-eta-en-coefficient.md:79` prints `:.2e` → `computed=2.20e-08 claimed=2.20e-08 -> PASS`. That CONFIRMED verifies `2.2e-8`, not the claimed `2.2046e-8`; the claim's own `1e-3` tolerance was never tested. `verdicts/001f` uses `:.1e`, an effective 5% tolerance. Fix: require `%.17g`/`repr(float(x))` and reject values with fewer significant digits than the claim's tolerance needs.

**J7 — Claim-stated tolerances are ignored; one global `REL_TOL = 0.01`. `ra_worker.py:58`. Degrades.**
`claims/001` says "compare both at 1e-6 rel"; `claims/001e` says "rel 1e-9". The judge passes anything within 1%. A `SAHA_C` wrong in the fourth digit would be CONFIRMED. Fix: per-check `tol:` parsed from the claim.

**J8 — Duplicate names inflate the pass/fail count. Degrades.**
No dedup. `verdicts/001f:43,47,51,55` shows `CHECK ratio_6.9e-4` printed four times inside a loop (all counted; the header reads `1 pass / 15 fail`). A model printing one true check ten times yields `CONFIRMED (10 pass / 0 fail)`, which reads to a human as strong evidence. Fix: dedupe by name; disagreeing duplicates ⇒ CHECK-ERROR.

Edge cases I checked that are **fine**: `-0.0` vs `0.0` passes (harmless); sign errors are caught (`001d`: -1.76e-5 vs +1.76e-5 → FAIL); the stderr/SyntaxError-echo hole from claim 001 is genuinely closed (`run_block` returns `r.stdout` only, `ra_worker.py:103`).

# 2. Execution sandbox

**S1 — No memory, CPU, or file-size limit. `ra_worker.py:96-98`. Blocks trust (operationally).**
Measured inside the sandbox: `RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_FSIZE` all unlimited. A generated `np.zeros((2e5,2e5))` running alongside the phase2 chains is exactly the stacked-workload Jetsam→configd panic pattern in your notes. Fix: `preexec_fn` with `setrlimit(RLIMIT_AS, 2<<30)` and `RLIMIT_CPU, 60`.

**S2 — "clean env" is not a sandbox. `ra_worker.py:96-98` vs `PROTOCOL.md:39`. Blocks trust.**
`env={"PATH": "/usr/bin:/bin"}` and `-I` restrict *nothing* about imports or I/O. I verified from inside a `run_block()` call: it imported **scipy 1.17.1**, opened a TCP connection to 127.0.0.1:8095, wrote a file outside `cwd`, and read `rail/mpd_solver.rail`. A generated script can overwrite `out/phase2_ckpt.f32`, `claims/*.md`, or the verdict it is about to be judged by. Fix: `sandbox-exec` profile denying `file-write*` outside cwd and `network*`, or at minimum a `sitecustomize` that removes `socket` and read-only-remounts via a throwaway HOME.

**S3 — The 120 s timeout kills only the direct child. `ra_worker.py:96,107`. Degrades.**
Verified: a `start_new_session=True` grandchild survived the parent's kill and wrote its file after `TemporaryDirectory` cleanup. This is the runaway-background-fan pattern. Fix: `start_new_session=True` on the child + `os.killpg(os.getpgid(p.pid), SIGKILL)` in the `TimeoutExpired` handler (needs `Popen`, not `run`).

**S4 — `claims/002a` and `claims/005` tell the model "scipy is absent". It is present.** Degrades: the false hint is what pushed 002a into hand-rolling the Maxwellian integral (the step that went 31% wrong). Fix the hint or make it true.

**S5 — Partial stdout is discarded on timeout (`ra_worker.py:107-108`).** Safe direction, but you lose the diagnostic. Cosmetic.

# 3. Prompt design

**P1 — The prompt demands a PASS/FAIL token and simultaneously forbids predicting PASS/FAIL. `ra_worker.py:33-37` vs `39-41`. Blocks trust, and it is measurably the top cause of lost runs.**
Two distinct damages, both live:
- *The strong tier never reaches the code block.* It litigates the tolerance instead. `verdicts/001b:115-153` and `verdicts/001f:85-128` are pages of "if claimed is 4.5 and computed 4.533, is that within 1e-3?"; `verdicts/002b:104` degenerates into `If use m_Ar=39.948?` repeated ~90 times until the token budget dies. Result: `CHECK harness: no python block in reply` on 005 and 002b, and every escalation I read is unterminated reasoning.
- *Models paste the output format into the Python.* `verdicts/005:31-33` and `:63-65`, `verdicts/stale/005:55`, `verdicts/002:41-42`, `verdicts/001a:32,63` — bare `CHECK ...` / `AGREE` lines as source → `SyntaxError` / `NameError`. That is **7 of ~30 executions** across 4 claims.

Smallest fix: delete the PASS/FAIL token and the AGREE/DISAGREE line from the required format. Ask for `VALUE <name> = <repr(float)>` only.

Related ledger error worth correcting: **`LEDGER.md:31-32` and `:37` attribute 005's CHECK-ERROR to `np.trapz`. It is not** — 005 never called trapz; both attempts were the bare-CHECK-line SyntaxError above. The trapz hint appended to `claims/005` therefore fixed nothing, which is why the 09:59 re-queue failed identically.

**P2 — The model sees the claimed values before computing. Blocks trust.**
- `verdicts/002a:135`: "AGREE: The computed values are within 1.5% of the claimed values" — about a 31% miss (1.19e-20 vs 1.72e-20). Anchored prose.
- `verdicts/002b:7`: the prose derives `G_r = 8.208e6` while its own code (line 26) prints `8.205e8`; the model's hand arithmetic and its script differ by 100x and nothing notices. The value it used to REFUTE was **105x** off the claim's correct `2 r_f/(r dr²) = 7.795e6`.

Fix: two-phase — phase 1 sends the claim with numerics mechanically redacted, phase 2 reveals them only for a reconciliation note.

**P3 — No requirement to print intermediates. Degrades.** `verdicts/001e` computed `3.04e-6` against a nominal `6.0e-3` — off by ~2000x — and the harness said REFUTED with full confidence. Had `r_20`, the row count and one per-row flux been required and checked, the error surfaces immediately.

**P4 — No requirement to state assumptions. Degrades.** `claims/005`'s "one-sided finite difference" is ambiguous; the 27B burned its whole budget enumerating six interpretations (`verdicts/005:107-222`) and never emitted code. An `ASSUME:` line routes that back to the physicist in one cycle instead of two dead runs.

**P5 — Constants are retyped from memory. Blocks trust.** `verdicts/001:53`: `h = 1.0545718e-34  # J s` — that is ħ mislabeled as h, giving `SAHA_C = 7.19e24` and a **REFUTED against a correct claim** (you had to hand-confirm it in `LEDGER.md:21`). Fix: a harness-owned constants preamble; forbid literal constants in the model's code.

**P6 — Three different tolerances in play:** prompt says 1e-3 (`ra_worker.py:35`), judge uses 1e-2 (`:58`), claims ask 1e-6 / 1e-9. Degrades.

**P7 — Several claims are not falsifiable numeric statements, which `PROTOCOL.md:9-10` requires.** `claims/001a` asks the model to "state what ln(Lambda) it implies and whether that value is reasonable (5-15)"; `claims/002a` asks it to "state any point you believe is off by more than 2x"; `claims/001b(1)` is a prose proposition about choked flow that no CHECK line can test (the harness verified `0.487`, which is true regardless of whether the proposition holds). 001a's REFUTED — the one that changed the solver — is `0.962` vs an invented `1.000`, on a crashed run. The physics conclusion is right; the machinery contributed nothing to establishing it.

# 4. Escalation / retry

**E1 — Escalation runs in the wrong direction. `ra_worker.py:116`. Blocks trust.**
```python
if status != "CONFIRMED" and MODEL_STRONG:
```
Only non-CONFIRMED escalates. So the cheap-to-fake outcome (008's tautological CONFIRMED, 002's `.2e` CONFIRMED) is *never* second-opinioned, while a correct REFUTED always is — and line 120-121 lets the strong tier's verdict override it. Fix: escalate CONFIRMED too, and require the two tiers' **numbers** to agree, not their verdicts.

**E2 — "no python block" gets zero retries. `ra_worker.py:150-151`. Degrades→blocks.**
```python
if not m:
    output = "CHECK harness: no python block in reply"
    break
```
It `break`s instead of feeding back, and this is the strong tier's *dominant* failure (005, 002b, plus the stale pair). `PROTOCOL.md:30` claims "the script crashed twice (fed back once for repair)" — untrue for this path. Fix: treat it as a run failure and send "you emitted no ```python block".

**E3 — Code-block extraction is brittle and can execute an abandoned draft. `ra_worker.py:55,148`.** `re.search(r"```python\n...")` on `content + "\n" + reasoning`: ```` ```py ````/```` ```Python ````/a nested fence all break it, and when `content` is empty (truncation) the regex happily executes a **draft block from inside the chain of thought**. Fix: search `content` first with several fence spellings; never execute from `reasoning`.

**E4 — The file's defaults do not match the running configuration. `ra_worker.py:16,21,22`. Blocks trust — same class as the RA_URL loss, still open.**
`RA_MODEL` defaults to `Qwen3.5-122B-A10B-heretic-v2-2.34bit-msq` (not what is loaded); `RA_MODEL_STRONG` defaults to `""` (escalation silently off); `RA_MAX_TOKENS` defaults to **12000** while the comment at `:18-19` and `PROTOCOL.md:51` both say 12k blows the Metal buffer and kills the server's generation thread. A bare restart is a silent, damaging misconfiguration. Fix: defaults matching the running config, plus a startup check against `/v1/models`.

**E5 — No budget, no record on endpoint failure. `ra_worker.py:51,122-123,144-146`.** `timeout=1800` × 2 attempts × 2 tiers ⇒ one claim can block the loop for two hours. On an endpoint error `run_model` returns `None`, `process` returns without writing anything, and the sweep silently retries every 300 s forever with no LEDGER trace. Degrades.

**E6 — `temperature=0.2`, no seed (`ra_worker.py:48`).** Verdicts are not reproducible; a re-queue can flip CONFIRMED/REFUTED. Degrades.

# 5. Protocol vs code drift

| PROTOCOL says | Code does |
|---|---|
| `:3-5` "the model NEVER decides a verdict"; "prose is not authority" | J2 reinstates the model's token; J5 lets it supply both operands |
| `:30` CHECK-ERROR = crashed twice, fed back once | J1 makes a partial crash REFUTED; E2 feeds back zero times for the commonest failure |
| `:39` "clean env, 120 s timeout" | S1/S2: no rlimits, full FS write, full network, scipy present |
| `:43-47` "a nonzero exit code voids every PASS" | It converts every PASS into a **FAIL** (J1) |
| `:51` `RA_MAX_TOKENS 6000` | Code default 12000 (`:22`) |
| — | `REL_TOL 0.01`, `--rejudge`, `verdicts/stale/`, and delete-to-requeue are undocumented |

# 6. Ledger / verdict bookkeeping

**B1 — `--rejudge` prints but never writes. `ra_worker.py:191-206`. Blocks trust for anyone reading the files.**
14 of 17 verdicts have no `--- harness-judged ---` section at all: their headers were written by the pre-20:45 comparator. Running `--rejudge` today (read-only) disagrees with the stored header on six:

```
001a  REFUTED (0P/1F)  -> REFUTED (0P/3F)
001b  REFUTED (2P/1F)  -> CONFIRMED (3P/0F)
001d  REFUTED (0P/2F)  -> REFUTED (1P/1F)
001f  REFUTED (1P/15F) -> REFUTED (7P/9F)
003   REFUTED (0P/2F)  -> REFUTED (1P/1F)
007   REFUTED (1P/1F)  -> CHECK-ERROR (0P/0F)
```
And `verdicts/002a:145-147` still carries `(harness: PASS)` annotations produced by the absolute-tolerance bug you fixed this morning — the body of the file contradicts its hand-edited header. Fix: `--rejudge --write` that rewrites the header and judged block and appends a supersede line.

**B2 — LEDGER is append-only with no supersede marker.** `005` appears at lines 11, 25, 28, 34, 37; `002a` at 26, 33, 35-36 with opposite meanings. `grep 002a LEDGER.md` returns CHECK-ERROR, CONFIRMED, and FALSE PASS. Degrades.

**B3 — Verdict header credits both tiers unconditionally. `ra_worker.py:127`.** `verdicts/008`, `002`, `009` say `4B + 27B`; 008 and 002 never escalated. Degrades (provenance).

**B4 — No claim hash in the verdict. `ra_worker.py:125-128`.** Hints were appended to `claims/002a` and `claims/005` after their verdicts were written; nothing ties a verdict to the claim text it judged. Fix: `claim-sha256:` plus the effective `REL_TOL` in the header.

**B5 — No lock; the verdict is written only at the very end. `ra_worker.py:113-114,125`.** With the `--loop` worker running (pid 9917), a manual `--claim 005` during a sweep double-spends the GPU and appends two LEDGER lines; a kill during a 20-min strong-tier call loses all work. Fix: `os.open(out_path + ".lock", O_CREAT|O_EXCL)` at entry.

**B6 — `--claim NNN` prefix-matches (`ra_worker.py:215`)**, so `--claim 001` targets seven claims. Cosmetic (the exists-guard saves you). **B7 — the verdict write is not atomic**; a kill mid-write leaves a truncated file that `next_claim()` treats as done. Fix: tmp + `os.replace`.

# Structural improvements, ranked by trust gained per hour

1. **Harness owns every comparison (~3 h, largest single gain).** Claim files gain a machine-readable block: `# EXPECT` / `name value tol`. The model emits only `VALUE <name> = <repr(float)>`; `judge()` compares against the *claim's* numbers with the *claim's* tolerance, and requires the exact declared name set (missing ⇒ CHECK-ERROR, duplicates ⇒ CHECK-ERROR). This kills J5, J6, J7, J8, P7 and the invented-`claimed=1.000` failure in one change, and makes 008-style tautologies impossible to express. A claim with no EXPECT block cannot be queued, which enforces `PROTOCOL.md:9`.
2. **Fix the four status bugs (~1 h, best hour in the list).** J1 (`return 0, 0, output`), J4 (non-finite ⇒ error), J2 (ValueError ⇒ error), J3 (loose `^CHECK` counter ⇒ error). Rule: *no harness error, no unparseable line, and no missing check may ever produce REFUTED.* This removes the entire confidently-wrong-REFUTED class, including 001a's.
3. **Stop asking the model for a verdict token (~0.5 h).** Delete PASS/FAIL and AGREE/DISAGREE from the format (`ra_worker.py:33-37`), keep only `VALUE`. Retire the "do not predict PASS/FAIL" paragraph that contradicts it. This recovers the 7 pasted-format crashes and the strong tier's truncations at once, and it is a ten-line edit.
4. **Pinned preamble + real limits (~1.5 h).** Harness prepends a vetted constants module (scipy.constants is available) and a `def value(name, x)` helper; the prompt forbids literal constants and hand-rolled quadrature. Same commit: `setrlimit(AS 2 GB, CPU 60)`, `start_new_session=True` + `killpg` on timeout, and a `sandbox-exec` profile denying network and writes outside cwd. Kills P5 (the ħ-for-h REFUTED), the trapz class, S1-S3.
5. **Withhold the claimed values until after the script runs (~2 h).** Phase 1: claim with numerics redacted, model returns `VALUE` lines. Phase 2: reveal the claim's numbers and ask only for a one-line reconciliation. Removes the anchoring that produced "within 1.5%" on a 31% miss, and makes the prose/code divergence in 002b impossible to paper over.
6. **Symmetric two-model agreement + bookkeeping (~2 h).** Escalate CONFIRMED as well as REFUTED, and require the two tiers' *values* to agree within tolerance before either verdict stands (`ra_worker.py:116-121`); retry the no-code-block case; add `--rejudge --write`, a claim sha in the header, a lockfile, and atomic verdict writes.

# Verdict

**Today the owner can treat REFUTED as a lead and must not treat CONFIRMED as evidence at all.** A CONFIRMED currently means only "at least one line parsed and nothing the model printed disagreed with the number it printed beside it" — three of the six CONFIRMEDs (008, 002, 001c) rest partly or wholly on a check that cannot fail, and 008's is the claim's central algebraic identity. A REFUTED means "some number the model's own script produced differs from a number the model transcribed", which in this corpus was wrong more often than right: 001 (ħ typed as h), 001d (sign convention), 001e (2000x), 002b (105x), 003 (unit form), 007 (compared to 0 instead of the boundary term) were all overturned by hand, and the two REFUTEDs that became real findings (001a, 002a) were established by your own adjudication, not by the CHECK apparatus — 001a's decisive line compares 0.962 against a value no claim ever stated, inside a run that crashed. Until items 1-3 land, the safe operating rule is: read the executed block of every verdict yourself (never the header or the ledger line), never act on a CONFIRMED, treat REFUTED as "spend twenty minutes checking this by hand", and re-run `--rejudge` before quoting any pre-2026-09-01-20:45 verdict, since fourteen of seventeen headers were written by a comparator that no longer exists and six of them now say something different. With items 1-3 in place (about five hours), CONFIRMED becomes "an independently written script reproduced the claim's own numbers to the claim's own tolerance", which is the thing you actually want to gate solver decisions on.