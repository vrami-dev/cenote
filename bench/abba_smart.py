"""Routing modes A/B on ONE fresh server, every mode switched per request (strata_tune), so whatever else loads the PC
slows all modes alike. Per prompt: one warm-up, then the modes in a rotation and its reverse (each mode's mean position
is the same). Greedy, thinking off, 400 tokens.

Per request: decode tok/s, the engine's route meter (expert picks that differ from exact routing, router weight kept),
the expert-tier counts and how many characters match the exact answer (that last one turned out too chaotic to use).

  python bench\\abba_smart.py [--config deepseek\\strata-ds41-1017dsx-win.json] [--out bench\\results\\run.json]

Stops any running local model first (scripts\\stop-all.py). Needs psutil.
"""
import argparse
import json
import os
import re
import statistics as st
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--config", default=str(ROOT / "deepseek" / "strata-ds41-1017dsx-win.json"))
ap.add_argument("--xolotl", default=str(ROOT / "engines" / "xolotl"))
ap.add_argument("--python", default=None, help="the server's Python (default: <xolotl>\\.venv-serve\\Scripts\\python.exe)")
ap.add_argument("--out", default=str(ROOT / "bench" / "results" / f"routing-modes-{time.strftime('%Y%m%d-%H%M')}.json"))
args = ap.parse_args()
PY_SERVE = args.python or str(Path(args.xolotl) / ".venv-serve" / "Scripts" / "python.exe")

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
URL = "http://127.0.0.1:8150"
MODES = {   # strata_tune per mode
    "exact": {"route_bias": 0.0, "route_bias_file": 0.0, "route_protect": 0, "route_pool": 0},
    "fast": {"route_bias": 0.5, "route_bias_file": 0.3, "route_protect": 0, "route_pool": 0},
    "light": {"route_bias": 0.25, "route_bias_file": 0.15, "route_protect": 0, "route_pool": 0},
    "smart": {"route_bias": 1.0, "route_bias_file": 0.6, "route_protect": 2, "route_pool": 12},
    "smart-half": {"route_bias": 0.5, "route_bias_file": 0.3, "route_protect": 2, "route_pool": 12},
}
ORDER = list(MODES)
PROMPTS = {
    "prose": "Write about 350 words explaining how a car insurance deductible works, with one worked example.",
    "code": "Write a Python class LRUCache with get/put in O(1) using a dict and a doubly linked list, with docstrings "
            "and 4 asserts at the end. Code only.",
    "agent": "Return ONLY a JSON array of 12 objects for a CRM import, each with keys name, phone, email, zip, "
             "vehicle_year, vehicle_make, vehicle_model, current_carrier, renewal_date, notes. Realistic fake data.",
}
P_SPEED = re.compile(r"serve: (\d+) tokens in [\d.]+ s = ([\d.]+) tok/s \(\w+\); experts: (\d+) hit, (\d+) cpu, (\d+) pcie, (\d+) file")
P_METER = re.compile(r"serve: routing vs exact: ([\d.]+)% of expert picks swapped, ([\d.]+)% of router weight kept")
P_TPP = re.compile(r"DSpark \d+ passes, ([\d.]+) tokens/pass")

cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
cfg["env"]["STRATA_RB_SMART"] = "1"   # the per-request ranks and the meter
LOG = Path(os.environ.get("TEMP", ".")) / "cenote-bench-ds41.log"
cfg["log"] = str(LOG)
cfg_path = Path(os.environ.get("TEMP", ".")) / "cenote-bench-config.json"
cfg_path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")

subprocess.run([sys.executable, str(ROOT / "scripts" / "stop-all.py")], capture_output=True)
time.sleep(3)
if LOG.exists():
    LOG.unlink()
srv = subprocess.Popen([PY_SERVE, "-I", r"tools\v41\serve\serve_ds41.py", "--engine", "strata", "--config", str(cfg_path),
                        "--port", "8150"], cwd=args.xolotl, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                       env={**os.environ, "STRATA_TEXT_LOG": "0"})
t0 = time.time()
while True:
    try:
        with urllib.request.urlopen(URL + "/health", timeout=3) as r:
            if json.loads(r.read()).get("loaded"):
                break
    except Exception:
        pass
    if srv.poll() is not None or time.time() - t0 > 400:
        sys.exit("server did not come up")
    time.sleep(2)
print(f"server up in {time.time() - t0:.0f} s", flush=True)


def log_tail(n0):   # read the log as bytes: a text offset drifts on non-ASCII lines
    with open(LOG, "rb") as f:
        f.seek(n0)
        return f.read().decode("utf-8", errors="replace")


def ask(mode, text):
    body = {"model": cfg["model_name"], "strata_tune": MODES[mode], "messages": [{"role": "user", "content": text}],
            "max_tokens": 400, "temperature": 0, "reasoning_effort": "none"}
    n0 = LOG.stat().st_size
    req = urllib.request.Request(URL + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        out = json.loads(r.read())
    sp = me = tp = []
    for _ in range(20):   # the engine's per-request lines land just after the response
        time.sleep(0.25)
        tail = log_tail(n0)
        sp, me, tp = P_SPEED.findall(tail), P_METER.findall(tail), P_TPP.findall(tail)
        if sp and me:
            break
    return {"mode": mode, "tok_s": out["timings"]["predicted_per_second"], "n": out["timings"]["predicted_n"],
            "exp": [int(x) for x in sp[-1][2:]] if sp else None,
            "swap_pct": float(me[-1][0]) if me else None, "kept_pct": float(me[-1][1]) if me else None,
            "tpp": float(tp[-1]) if tp else None, "text": out["choices"][0]["message"]["content"]}


def common_prefix(a, b):
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n


res = {}
for name, text in PROMPTS.items():
    ask("fast", text + "   ")   # warm-up on this prompt (not counted)
    res[name] = []
    for rep, order in enumerate([ORDER, ORDER[::-1]]):
        rows = [ask(mode, text + " " * rep) for mode in order]
        ref = next(r["text"] for r in rows if r["mode"] == "exact")
        for r in rows:
            r["rep"] = rep
            r["match_chars"] = common_prefix(r["text"], ref)
            r["ref_chars"] = len(ref)
            print(f"{name:5s} rep {rep} {r['mode']:10s} {r['tok_s']:5.1f} tok/s  swapped {r['swap_pct']}%  "
                  f"weight kept {r['kept_pct']}%  tpp {r['tpp']}", flush=True)
        res[name] += rows
Path(args.out).parent.mkdir(parents=True, exist_ok=True)
Path(args.out).write_text(json.dumps(res, indent=1), encoding="utf-8")

print("--- medians per mode (tok/s per prompt, avg; route meter)")
for mode in ORDER:
    sp = [st.median(r["tok_s"] for r in res[k] if r["mode"] == mode) for k in PROMPTS]
    rs = [r for k in PROMPTS for r in res[k] if r["mode"] == mode]
    sw = [r["swap_pct"] for r in rs if r["swap_pct"] is not None]
    kp = [r["kept_pct"] for r in rs if r["kept_pct"] is not None]
    print(f"{mode:10s} prose {sp[0]:5.1f} code {sp[1]:5.1f} agent {sp[2]:5.1f} avg {sum(sp) / 3:5.1f} | "
          f"swapped {st.median(sw) if sw else None}%  weight kept {st.median(kp) if kp else None}%")
print("wrote", args.out)
subprocess.run([sys.executable, str(ROOT / "scripts" / "stop-all.py")], capture_output=True)
