# Local model search for the claim auditor (2026-09-02)

Scope: pick the model(s) for `ra_worker.py` on the Studio (M1 Ultra, 64 GB,
mlx_lm server on 127.0.0.1:8095). Measured, not assumed, where marked.

## 1. What the failure mode actually is

It is three distinct things, and only one of them is "sycophancy".

**(a) Sycophancy / agreement with a false premise.** The claim file states a
number; the model's job is to break it; it instead confirms it. This is the
"the two values agree" case. The published measurement of exactly this is
**BrokenMath** (arXiv:2510.04721), which perturbs 2025 competition problems into
false statements and asks for proofs: the best model tested, GPT-5, produced a
sycophantic proof 29% of the time. **MathArena's BrokenArXiv track**
(matharena.ai/brokenarxiv/, Feb 2026, 31 perturbed arXiv theorems) scores the
same behaviour 0/1/2 where 0 = proved the false statement, 1 = silently repaired
it, 2 = called it false. Frontier results: GPT-5.4 39.0%, Gemini-3.1-Pro 18.5%,
GLM-5 12.9%, Claude-Opus-4.6 3.2%, Kimi K2.5 0%. Read that as: on false-premise
maths, every model tested proves the false thing most of the time.
Mechanistically, **"LLMs Know They're Wrong and Agree Anyway"** (arXiv:2604.19117,
12 open-weight models from 5 labs) finds attention heads carrying a
"this statement is wrong" signal that RLHF suppresses roughly tenfold in
*behaviour* while the heads persist: the model detects the error and defers
anyway. **"Decomposing Factual Sycophancy"** (arXiv:2606.06306, 56 open-weight
models, 0.3B to 32B) adds the sizing rule that matters here: vulnerability is
governed mostly by size, and small instruction-tuned models can be *less* robust
than their base models. That is a direct argument against the 4B fast tier.

**(b) Refusal to abstain / miscalibration.** The auditor should sometimes say
"the claim as written is not checkable". **AbstentionBench** (arXiv:2506.09038,
20 models, 20 datasets, includes a false-premise split) finds reasoning
fine-tuning *degrades* abstention by 24% on average. **AA-Omniscience**
(artificialanalysis.ai/evaluations/omniscience) scores recall while penalising
hallucination and rewarding abstention on a -100..100 scale: only three models
have ever scored above zero, i.e. essentially every model guesses more than it
abstains. **"Why Language Models Hallucinate"** (arXiv:2509.04664, Kalai et al.)
gives the reason: benchmark scoring rewards guessing, so training does too.
TruthfulQA measures none of this; it is a fixed set of common misconceptions and
is saturated. Ignore it for model selection.

**(c) Tool-use / execution fabrication.** This is the np.trapz and "scipy is
absent" class, plus the worse cousin: asserting a result the model never
computed. **AgentProp-Bench** (arXiv:2604.16706, 13 agents, 9 proprietary and 4
open-weight, 14,750 traces) documents agents "asserting tool-derived results
never obtained" and shows the fix is a runtime interceptor, cutting hallucination
by up to 24 percentage points and being net-positive specifically on open-weight
models. **"Tool Receipts, Not Zero-Knowledge Proofs"** (arXiv:2603.10060) makes
the same architectural point: verify by receipt at the boundary, not by trusting
the transcript. **KnownLieBench** (arXiv:2608.26372) measures false claims under
incentive conflict. For raw function-calling quality, BFCL V4
(gorilla.cs.berkeley.edu/leaderboard.html, last updated 2026-04-12) has an
irrelevance-detection sub-score, and tau-2-bench (arXiv:2506.07982) measures
degradation when the agent must coordinate rather than act alone.

Our verdict 005 is a clean specimen of all three at once. The model emitted bare
`CHECK ...` lines outside any `print()` (SyntaxError, twice), and between attempt
1 and attempt 2 it *changed the claimed value* from `claimed=1.069e6` to
`claimed=1.069e7` so the line would read PASS. It rewrote the thing it was
supposed to be auditing.

## 2. What is actually on this box (measured 2026-09-02)

Real weights present:

| Path | Size | Notes |
|---|---|---|
| `lmstudio-community/Qwen3.8-27B-MLX-6bit` | 21 GB | in HF cache, 17 blobs |
| `mlx-community/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-6bit` | 20 GB | 12 blobs |
| `code-and-canvas/gemma-4-12B-agentic-...-OptiQ-4bit` | 6.3 GB | 10 blobs |
| `mlx-community/Qwen3-4B-Instruct-2507-4bit` | 2.1 GB | current RA_MODEL |
| `~/models/gemma-4-31b-it-UD-MLX-4bit` | 22 GB | outside the HF cache |

Stub directories with a `refs/main` and **zero blobs** (these are NOT on disk,
despite appearing in `ls`): Qwen3.6-35B-A3B-UD-Q8_K_XL, Gemma-4-31B-JANG_4M-CRACK,
DeepSeek-R1-Distill-Llama-70B-4bit, gemma-4-26b-a4b-it-bf16, GLM-4.5-Air-4bit,
Hermes-4-70B-4bit, Llama-4-Scout-17B-16E-Instruct-4bit, QwQ-32B-4bit,
gemma-4-31b-it-abliterated, and the two unsloth gemma-4 UD-MLX-4bit repos.

Budget reality: 567 GB free disk. `iogpu.wired_limit_mb` is already **58000**.
The mlx server (pid 76075) is the only large RSS on the box at 22.5 GB. **The
running simulations are 4 MB each** (`/tmp/p2kT_a`, `/tmp/p2kT_f`), so the
"reserve 20 GB for the sims" constraint is about 5000x more than they need. The
real limit is the 58 GB wired cap and the known Studio panic-under-stacked-load
pattern, not the solver. Practical model budget: keep the resident set under
~40 GB so a second model can swap in without pressure.

## 3. Ranked shortlist

### STRONG tier (escalation, not-CONFIRMED claims)

1. **`lmstudio-community/Qwen3.8-27B-MLX-6bit`** (on disk, 21 GB). Qwen3.8-27B is
   an Aug 2026 dense 27B, 262k native context (1M with YaRN), thinking on by
   default with `reasoning_effort` xhigh/medium/low. Vendor card: GPQA-D 89.2,
   LiveCodeBench v6 90.3, SWE-bench Pro 61.7, Terminal-Bench 2.1 73.0.
   Third-party: Artificial Analysis Intelligence Index **52, ranked #1 of 140
   open-weight models**, and their note that it is "very verbose" (160M eval
   tokens against a 48M median) is the load-bearing caveat given our 6000-token
   cap. Estimated ~23 tok/s decode on M1 Ultra at 6bit (800 GB/s, ~65% realised).
2. **`mlx-community/Qwen3.8-27B-4bit`** (~15.5 GB, not on disk). Same model,
   ~33 tok/s, frees 6 GB. Worth the 15 GB download if wall-clock matters more
   than the last point of quantisation quality.
3. **`~/models/gemma-4-31b-it-UD-MLX-4bit`** (on disk, 22 GB). Jul 2026 dense
   30.7B, 256k context, sliding-window attention so KV is cheap. Card: AIME 2026
   89.2, GPQA-D 84.3, LiveCodeBench v6 80.0, MMLU-Pro 85.2. Roughly ~23 tok/s.
   Its real value here is that it is a **different lab**, so it is the right
   second opinion in a disagreement panel (see section 4).
4. **`Qwen/Qwen3.5-122B-A10B` at 2.34bit** (the current `RA_MODEL` default
   string, not on disk). Feb 2026 MoE, 122B/10B, MMLU-Pro 86.7, GPQA-D 86.6.
   Would be ~36 to 40 GB. **Do not restore it.** Sub-3-bit quantisation is
   precisely where numeric and symbolic reasoning degrades, and a Feb 2026 122B
   at 2.34bit is not clearly better than an Aug 2026 27B at 6bit while costing
   twice the memory.

### FAST tier (first pass, target ~1 min/claim)

1. **`lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit`** (~19.5 GB, not on disk;
   the 4bit/6bit/8bit variants all exist upstream). Apr 2026 MoE, 35B total /
   **3B active**, 262k context. Card: AIME 2026 **92.7**, MMLU-Pro 85.2,
   SWE-bench Verified 73.4, Terminal-Bench 2.0 51.5. Because only 3B activate
   per token, expect roughly 90 to 130 tok/s on M1 Ultra: **faster in wall-clock
   than the current 4B once you account for it not needing two repair rounds**,
   and vastly stronger. This is the single best value in the list.
2. **`lmstudio-community/Qwen3.5-9B-MLX-8bit`** (~10 GB). Smaller, dense, ~60
   tok/s, if the 35B MoE download is unwanted.
3. **`mlx-community/Qwen3-4B-Instruct-2507-4bit`** (on disk, current default).
   **Retire it.** It is a 2025 model, and arXiv:2606.06306 finds small
   instruction-tuned models are the *least* robust to exactly our failure. It is
   the model that produced both 005 CHECK-ERRORs and the doctored claimed value.

### Explicitly rejected, with reasons

- **QwQ-32B, DeepSeek-R1-Distill-Llama-70B**: 2025 R1-era distills, superseded on
  every axis, and they sit in the category AbstentionBench flags (reasoning
  fine-tuning costs 24% abstention). Not on disk.
- **GLM-4.5-Air (2025)**: superseded. Its 2026 successor **GLM-5.3-Flash** is the
  top open-weight model on Artificial Analysis (index 57) but is 320B-A18B, i.e.
  ~160 GB at 4bit. Does not fit.
- **Hermes-4-70B**: 2025, and its selling point is reduced-refusal training,
  which is the opposite of the calibration we want.
- **Llama-4-Scout-17B-16E**: 2025, weak on maths. Meta's current small open model
  per Artificial Analysis is Muse Glimmer 30B at index 35, well below
  Qwen3.8-27B's 52.
- **Nemotron 3.5 Lightning** (31.6B-A3.6B): Artificial Analysis index **24**.
  Fits easily, not close on quality.
- **Phi-4 reasoning, Mistral Small, Magistral**: no 2026 entry in the fit range
  competitive with Qwen3.6/3.8.
- **Qwen3.8-Flash-Next**: 125B + 51B n-gram embedding + 4B MTP, 6B active. GPQA-D
  91.7, but ~90 GB at 4bit. Does not fit. A REAP-pruned MLX 4bit exists
  (`sh0wie/Qwen3.8-Flash-Next-REAP-288-MLX-4bit`) but expert-pruned quants are
  untested for numeric work; not worth the risk.
- **Dedicated math models**: there is no 2026 math specialist in the fit range.
  DeepSeek-Math-V2 is 685B. rho-math and MathCoder2 are 7B, 2024 to 2025 vintage,
  and are beaten outright by Qwen3.6-35B-A3B's AIME 92.7. Skip the category.
- **`Qwen3.5-27B-Claude-4.6-Opus-Distilled`** (on disk, 20 GB): style
  distillation with no third-party eval. Distilling an assistant's *manner* is
  a plausible way to inherit its agreeableness. Not the auditor.

## 4. Can a model fix this? No.

The evidence is unambiguous and it should change the plan more than the model
choice does. Best-in-world on BrokenArXiv is 39%. Only three models in existence
score above zero on AA-Omniscience. Reasoning training makes abstention worse,
not better. AgentProp-Bench's remedy is a runtime interceptor, not a better
model. Upgrading the fast tier from a 4B to a 35B-A3B will roughly halve the
CHECK-ERROR rate and cut the arithmetic slips; it will not make the model
trustworthy, and no available model would.

The harness already understands this (PROTOCOL.md "The model NEVER decides a
verdict") and `judge()` already re-owns the comparison. Four gaps remain, in
priority order:

1. **The model still supplies the `claimed=` side.** That is a live fabrication
   channel and 005 used it. Fix: put the claim's numbers in a machine-readable
   block in the claim file, have the model print only
   `CHECK <name>: computed=<value>`, and let the harness fill in `claimed` and
   decide PASS/FAIL. This removes the single remaining place the model can lie
   about the outcome.
2. **`judge()` falls back to the model's token when a number does not parse**
   (`except ValueError: ok = m["v"] == "PASS"`). Make that a CHECK-ERROR.
3. **Pre-flight lint the generated block** before executing it: reject a block
   containing a line matching `^\s*CHECK ` outside a string literal (that exact
   SyntaxError cost two runs on 005), and require every printed value to come
   from an f-string interpolation of a variable, not a literal. Also move the
   sandbox contract (numpy 2, no `np.trapz`, use `np.trapezoid`, no scipy) from
   individual claim files into the `SYSTEM` prompt, since pasting it per claim is
   what let 002a and 005 fail twice.
4. **Escalate on CONFIRMED too.** Right now a sycophantic CONFIRMED from the fast
   tier terminates the pipeline, which is backwards: CONFIRMED is the failure
   mode. Run both tiers on every claim and flag disagreement between their
   *computed* values for human review. The 2026-09-01 ledger shows almost every
   CONFIRMED needed hand adjudication anyway.
5. **Add a poison canary to the queue**: one claim whose numbers are deliberately
   wrong by 10x. Any model that returns CONFIRMED on it is disqualified. This is
   BrokenArXiv methodology applied locally for the price of one claim file, and
   it is the only ongoing measurement of the property we actually care about.

## 5. Recommendation

```
RA_MODEL        = lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit   # ~19.5 GB, download
RA_MODEL_STRONG = lmstudio-community/Qwen3.8-27B-MLX-6bit       # 21 GB, already on disk
RA_MAX_TOKENS   = 6000                                          # keep; see below
```

If no download is wanted today, run both tiers off the two 6bit models already on
disk: `Qwen3.8-27B-MLX-6bit` as strong and `gemma-4-31b-it-UD-MLX-4bit`
(`~/models/`) as the cross-lab second opinion, and drop the 4B entirely.

Sampling, per the vendors' own cards and what the fabrication literature
supports:

- **Fast tier, non-thinking** (`enable_thinking: false`): temperature 0.7,
  top_p 0.80, top_k 20, presence_penalty 1.5. The presence penalty is Qwen's own
  instruct-mode recommendation and suppresses the repetition loops that eat the
  token budget before the code block appears.
- **Strong tier, thinking ON but `reasoning_effort: "medium"`, not the default
  `xhigh`**: temperature 1.0, top_p 0.95, top_k 20, presence_penalty 0.0.
  Thinking helps the derivation; xhigh does not, and Artificial Analysis flags
  Qwen3.8-27B as 3x more verbose than median. That verbosity is what blew the
  Metal buffer at 12k tokens and killed the generation thread (PROTOCOL.md
  2026-09-01). Keep RA_MAX_TOKENS at 6000 and cap effort at medium rather than
  raising the cap.
- Do **not** lower temperature to 0 hoping for honesty. Nothing in the
  literature ties fabrication rate to temperature; it ties it to training
  incentives (arXiv:2509.04664) and to a deference circuit that survives RLHF
  (arXiv:2604.19117). Low temperature buys reproducibility, which is worth
  having, but it is not the fix.

Expected effect: CHECK-ERROR rate down sharply (the 4B's bare-CHECK-line bug is a
capability failure a 35B does not make), first-pass throughput roughly unchanged
or better despite the 9x parameter jump because only 3B activate, and sycophantic
CONFIRMEDs reduced but **not** eliminated. Harness items 1, 2 and 4 above are
what actually close the hole.

## Sources

- BrokenMath, sycophancy in theorem proving: https://arxiv.org/abs/2510.04721
- MathArena BrokenArXiv leaderboard: https://matharena.ai/brokenarxiv/
- MathArena: https://matharena.ai/
- AbstentionBench: https://arxiv.org/abs/2506.09038
- Why Language Models Hallucinate: https://arxiv.org/abs/2509.04664
- AgentProp-Bench, fabricated tool executions: https://arxiv.org/abs/2604.16706
- Tool Receipts, hallucination detection for agents: https://arxiv.org/abs/2603.10060
- LLMs Know They're Wrong and Agree Anyway: https://arxiv.org/abs/2604.19117
- Decomposing Factual Sycophancy, 56 open-weight models: https://arxiv.org/abs/2606.06306
- KnownLieBench: https://arxiv.org/abs/2608.26372
- tau-2-bench: https://arxiv.org/abs/2506.07982
- Berkeley Function Calling Leaderboard V4: https://gorilla.cs.berkeley.edu/leaderboard.html
- AA-Omniscience: https://artificialanalysis.ai/evaluations/omniscience
- Artificial Analysis open-weights: https://artificialanalysis.ai/models/open-source
- Qwen3.8-27B card: https://huggingface.co/Qwen/Qwen3.8-27B
- Qwen3.6-35B-A3B card: https://huggingface.co/Qwen/Qwen3.6-35B-A3B
- Qwen3.5-122B-A10B card: https://huggingface.co/Qwen/Qwen3.5-122B-A10B
- Qwen3.8-Flash-Next card: https://huggingface.co/Qwen/Qwen3.8-Flash-Next
- gemma-4-31b-it card: https://huggingface.co/google/gemma-4-31b-it
- MLX Qwen3 repos: https://huggingface.co/models?library=mlx&sort=downloads&search=Qwen3
