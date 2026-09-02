#!/opt/homebrew/bin/python3.11
"""Autonomous claim auditor: local LLM writes checks, execution judges.

Usage:
  ra_worker.py                 process all unverdicted claims once
  ra_worker.py --loop          poll claims/ every 5 min, forever
  ra_worker.py --claim NNN     process one claim

Env: RA_URL   (default http://127.0.0.1:8095/v1, the Studio mlx server)
     RA_MODEL (default Qwen3.5-122B-A10B-heretic-v2-2.34bit-msq)
"""
import json, os, re, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = os.environ.get("RA_URL", "http://127.0.0.1:8095/v1")
MODEL = os.environ.get("RA_MODEL", "Qwen3.5-122B-A10B-heretic-v2-2.34bit-msq")
# two tiers: the fast model answers first; anything not CONFIRMED is
# escalated to the strong model (thinking models burn 10 min and can
# blow the Metal buffer limit on 12k-token generations, so they only
# get the hard ones)
MODEL_STRONG = os.environ.get("RA_MODEL_STRONG", "")
MAX_TOKENS = int(os.environ.get("RA_MAX_TOKENS", "12000"))

SYSTEM = """You are an adversarial mathematical auditor for a plasma
physics / CFD program. You are given a CLAIM with numbers. Your job is
to try to BREAK it by independent re-derivation. Do not trust the
context; re-derive from first principles and CODATA 2018 constants.

Output format, exactly:
1. A brief independent derivation (max 30 lines).
2. ONE python code block (```python ... ```), self-contained, stdlib +
   numpy + sympy only, that computes the claim's numbers independently
   and prints one line per checked quantity in EXACTLY this form:
   CHECK <name>: computed=<value> claimed=<value> -> PASS
   or -> FAIL (use relative tolerance 1e-3 unless the claim states one).
3. One line: AGREE or DISAGREE plus the single strongest reason.
Never print PASS unless your computed value actually matches.

CRITICAL: do NOT do arithmetic by hand in your reasoning, and do not
try to predict PASS or FAIL yourself. The harness EXECUTES your python
block and the executed prints are the verdict. Keep any reasoning to a
few sentences of derivation strategy, then write the code block. All
numbers are computed by the script, none by you."""


def ask(messages, model):
    body = json.dumps({"model": model, "messages": messages,
                       "temperature": 0.2, "max_tokens": MAX_TOKENS}).encode()
    req = urllib.request.Request(URL.rstrip("/") + "/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        msg = json.loads(r.read())["choices"][0]["message"]
        # reasoning models put chain-of-thought in .reasoning and may
        # leave .content empty; keep both, content first
        return (msg.get("content") or "") + "\n" + (msg.get("reasoning") or "")


REL_TOL = float(os.environ.get("RA_REL_TOL", "0.01"))
CHECK_RE = re.compile(r"^CHECK (?P<name>[^:]+): computed=(?P<c>[^ ]+) claimed=(?P<k>[^ ]+) -> ?(?P<v>PASS|FAIL)\s*$", re.M)


def judge(output):
    """The harness owns the comparison. Models compared with exact
    equality (558.747 vs 558.7 -> FAIL), divided by a claimed 0.0, or
    reused one claimed value across cases; their PASS/FAIL token is
    advisory. Re-judge every CHECK line: PASS if |c - k| <= REL_TOL *
    max(|k|, |c|), or both exactly zero (SI numbers live at 1e-20 and
    1e-23; an absolute floor is a false PASS). Unparseable
    numbers keep the model's token. A harness failure voids all."""
    if "CHECK harness:" in output:
        return 0, len(CHECK_RE.findall(output)), output
    passes = fails = 0
    lines = []
    for line in output.splitlines():
        m = CHECK_RE.match(line)
        if not m:
            lines.append(line); continue
        try:
            c, k = float(m["c"]), float(m["k"])
            # relative only: an absolute "both ~0" shortcut passed a 31%
            # miss on 1e-20 m^2 cross-sections (002a, 2026-09-02).
            ok = (c == 0.0 and k == 0.0) or abs(c - k) <= REL_TOL * max(abs(k), abs(c))
        except ValueError:
            ok = m["v"] == "PASS"
        tag = "PASS" if ok else "FAIL"
        passes += ok; fails += (not ok)
        lines.append(line + ("" if tag == m["v"] else f"   (harness: {tag})"))
    return passes, fails, "\n".join(lines)


def run_block(code):
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, "check.py")
        open(f, "w").write(code)
        try:
            r = subprocess.run([sys.executable, "-I", f], cwd=td, timeout=120,
                               capture_output=True, text=True,
                               env={"PATH": "/usr/bin:/bin"})
            # only STDOUT carries verdict lines; stderr (tracebacks,
            # SyntaxError echoes of the offending source line) must never
            # be able to spell "-> PASS". A nonzero exit is a harness
            # failure whatever stdout says.
            out = r.stdout
            if r.returncode != 0:
                out += f"\nCHECK harness: exit {r.returncode}\n" + r.stderr
            return out
        except subprocess.TimeoutExpired:
            return "CHECK harness: TIMEOUT after 120 s"


def process(claim_path):
    out_path = os.path.join(HERE, "verdicts", os.path.basename(claim_path))
    if os.path.exists(out_path):
        return
    status, transcript, passes, fails = run_model(claim_path, MODEL)
    if status != "CONFIRMED" and MODEL_STRONG:
        s2, t2, p2, f2 = run_model(claim_path, MODEL_STRONG)
        transcript += "\n\n=== ESCALATED to " + MODEL_STRONG + " ===" + t2
        # the strong tier's verdict stands unless it errored
        if s2 != "CHECK-ERROR":
            status, passes, fails = s2, p2, f2
    if status is None:
        return
    nnn = os.path.basename(claim_path).split("-")[0]
    open(out_path, "w").write(
        f"# {status}  ({passes} pass / {fails} fail)\n"
        f"model: {MODEL}" + (f" + {MODEL_STRONG}" if MODEL_STRONG else "") +
        f"\nclaim: {claim_path}\n{transcript}\n")
    line = f"{time.strftime('%Y-%m-%d %H:%M')}  {nnn}  {status}  ({passes}P/{fails}F)\n"
    open(os.path.join(HERE, "LEDGER.md"), "a").write(line)
    print(f"[{nnn}] {status} ({passes}P/{fails}F)", flush=True)


def run_model(claim_path, model):
    nnn = os.path.basename(claim_path).split("-")[0]
    claim = open(claim_path).read()
    print(f"[{nnn}] asking {model} ...", flush=True)
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": claim}]
    transcript, output = "", ""
    for attempt in (1, 2):
        try:
            reply = ask(msgs, model)
        except Exception as e:
            print(f"[{nnn}] endpoint error: {e}", flush=True)
            return None, f"endpoint error: {e}", 0, 0
        transcript += f"\n\n--- model reply (attempt {attempt}) ---\n{reply}"
        m = re.search(r"```python\n(.*?)```", reply, re.S)
        if not m:
            output = "CHECK harness: no python block in reply"
            break
        output = run_block(m.group(1))
        transcript += f"\n\n--- executed output ---\n{output}"
        if "CHECK harness:" in output or not re.search(r"^CHECK .*-> ?(PASS|FAIL)\s*$", output, re.M):
            msgs += [{"role": "assistant", "content": reply},
                     {"role": "user", "content":
                      "Your check script failed to run:\n" + output[-2000:] +
                      "\nRepair it. Same output format."}]
            continue
        break
    passes, fails, output = judge(output)
    transcript += "\n\n--- harness-judged ---\n" + output
    if passes and not fails:
        status = "CONFIRMED"
    elif fails:
        status = "REFUTED"
    else:
        status = "CHECK-ERROR"
    print(f"[{nnn}] {model}: {status} ({passes}P/{fails}F)", flush=True)
    return status, transcript, passes, fails


def next_claim():
    # re-list every time: claims added or renamed mid-sweep are honoured
    # in sorted order (prefix a claim 001a.. to jump the queue)
    for f in sorted(os.listdir(os.path.join(HERE, "claims"))):
        if f.endswith(".md") and not os.path.exists(
                os.path.join(HERE, "verdicts", f)):
            return os.path.join(HERE, "claims", f)
    return None


def sweep():
    while True:
        c = next_claim()
        if c is None:
            return
        process(c)


def rejudge():
    vd = os.path.join(HERE, "verdicts")
    for f in sorted(os.listdir(vd)):
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(vd, f)).read()
        outs = re.findall(r"--- executed output ---\n(.*?)(?=\n--- |\n=== |\Z)", t, re.S)
        if not outs:
            continue
        passes, fails, judged = judge(outs[-1])
        status = "CONFIRMED" if passes and not fails else ("REFUTED" if fails else "CHECK-ERROR")
        old = t.split("\n", 1)[0]
        print(f"{f:40s} {old[:24]:24s} -> {status} ({passes}P/{fails}F)")
        for l in judged.splitlines():
            if "(harness:" in l:
                print("    " + l)


if __name__ == "__main__":
    if "--rejudge" in sys.argv:
        rejudge(); sys.exit(0)
    if "--claim" in sys.argv:
        n = sys.argv[sys.argv.index("--claim") + 1]
        for f in os.listdir(os.path.join(HERE, "claims")):
            if f.startswith(n):
                process(os.path.join(HERE, "claims", f))
    elif "--loop" in sys.argv:
        while True:
            sweep(); time.sleep(300)
    else:
        sweep()
