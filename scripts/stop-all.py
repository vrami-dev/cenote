"""Stop whichever local model is serving (DeepSeek on Xolotl, GLM on Project Maya, Swift / Qwen on Strata): the
launcher window, the server and the engine. Needs psutil (pip install psutil).

Matched by command line: serve_ds41.py, Maya's maya.py, Strata's serve\\server.py, the engines' executables, and the
start-*.cmd windows from this folder.
"""
import psutil

MARKERS = ("serve_ds41.py", "maya.py", "serve\\server.py", "serve/server.py", "start-deepseek.cmd", "start-swift.cmd",
           "start-glm.cmd")
ENGINES = ("ds41_generate.exe", "strata.exe", "strata-vision.exe")
targets = []
for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        name = (p.info["name"] or "").lower()
        cmd = " ".join(p.info["cmdline"] or []).lower()
    except (psutil.Error, TypeError):
        continue
    if name in ENGINES or any(m in cmd for m in MARKERS):
        targets.append(p)
if not targets:
    print("No local model is running")
    raise SystemExit(0)
procs = []
for p in targets:
    try:
        procs += p.children(recursive=True) + [p]
    except psutil.Error:
        pass
procs = list({p.pid: p for p in procs}.values())
for p in procs:
    try:
        p.terminate()
    except psutil.Error:
        pass
gone, alive = psutil.wait_procs(procs, timeout=10)
for p in alive:
    try:
        p.kill()
    except psutil.Error:
        pass
print(f"Stopped {len(procs)} process(es); RAM and VRAM are released")
