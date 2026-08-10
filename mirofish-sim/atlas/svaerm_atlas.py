#!/usr/bin/env python3
"""Trigger-atlas: 7 MiroFish-koersler (6 styrede kanaler + 1 fri kontrol).
Neutralt seed uden modeltal. Ekstraktion via interview/all MENS miljoeet koerer,
derefter stop. Resumérbar via atlas_state.json. Koer: python svaerm_atlas.py"""
import json, mimetypes, sys, time, urllib.request, urllib.error, uuid
from pathlib import Path

BASE = "http://localhost:5001/api"
HERE = Path(__file__).parent
SEED = HERE / "seed_v2_neutral.md"
STATE_F = HERE / "atlas_state.json"
OUT = HERE / "atlas_raw"
MAX_ROUNDS = 20

FAELLES = (" Trace it concretely. The simulation's purpose is to identify: (1) the step-by-step "
           "transmission chain, (2) the EARLIEST OBSERVABLE data series + threshold that would "
           "confirm this path is active before the real economy breaks, (3) a realistic timeline "
           "from trigger to recession onset, (4) what would abort or falsify this path.")

RUNS = [
    ("kontrol_fri", "Simulate the next 12 months of this economy with no assumed trigger. "
     "If a recession begins, identify what actually triggered it; if none begins, identify "
     "what came closest to breaking and why it held." + FAELLES),
    ("inflation_fed", "ASSUME the trigger is inflation re-acceleration: CPI pushes past 4%, "
     "forcing the Fed to resume hiking into an already-leveraged economy, re-inverting the "
     "yield curve. Simulate how this unfolds across all actors." + FAELLES),
    ("kredit_refi", "ASSUME the trigger is a credit event: the 2027 corporate refinancing wall "
     "meets high real rates; high-yield spreads blow out from 271bp; private-credit and CRE "
     "losses surface; banks tighten lending standards sharply. Simulate the unfolding." + FAELLES),
    ("aktie_repricing", "ASSUME the trigger is an equity repricing: CAPE 42, negative equity "
     "risk premium and record margin debt (+51.5% y/y) unwind in a self-reinforcing margin-call "
     "spiral; reverse wealth effect hits consumption and capex. Simulate the unfolding." + FAELLES),
    ("arbejdsmarked", "ASSUME the trigger is an endogenous labor-market crack: hiring freezes "
     "quietly become layoffs; claims trend up from 199k; Sahm crosses 0.50; consumption spirals "
     "down. No financial shock initiates it. Simulate the slow-bleed unfolding." + FAELLES),
    ("fiskal_termpraemie", "ASSUME the trigger is fiscal: deficit fears push the 10-year term "
     "premium sharply higher (long-end selloff, bond vigilantes); mortgage rates spike; equity "
     "duration reprices; financial conditions tighten without Fed action. Simulate the unfolding." + FAELLES),
    ("eksogent_chok", "ASSUME the trigger is an exogenous shock: a geopolitical event disrupts "
     "oil and shipping (oil +60% in three months) amid already-negative real cash yields and "
     "extreme valuations. Simulate the transmission and policy dilemma (stagflation)." + FAELLES),
]

SPOERGSMAAL = [
    "The simulation has concluded. From YOUR perspective and role: what was the decisive trigger chain? Answer stepwise: trigger -> transmission -> real-economy impact. Be specific.",
    "What was the EARLIEST OBSERVABLE warning - name the specific data series and the threshold value - that signaled this path had become active, visible BEFORE the real economy broke?",
    "What could have PREVENTED or falsified this path (policy action, data surprise)? And give your realistic timeline in months from trigger to recession onset.",
]

def state():
    return json.loads(STATE_F.read_text()) if STATE_F.exists() else {}

def save(run, **kw):
    s = state(); s.setdefault(run, {}).update(kw); STATE_F.write_text(json.dumps(s, indent=1))
    return s[run]

def api(method, path, payload=None, timeout=600):
    req = urllib.request.Request(BASE + path, method=method)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"success": False, "http": e.code, "body": e.read().decode()[:300]}

def api_multipart(path, fields, filepath, timeout=900):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; "
                 f"filename=\"{filepath.name}\"\r\nContent-Type: text/markdown\r\n\r\n".encode())
    parts.append(filepath.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    req = urllib.request.Request(BASE + path, data=b"".join(parts), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def log(run, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{run}] {msg}", flush=True)

def do_run(slug, requirement):
    s = state().get(slug, {})
    if s.get("done"):
        log(slug, "allerede faerdig — springer over")
        return True
    OUT.mkdir(exist_ok=True)

    if "project_id" not in s:
        log(slug, "ontologi...")
        r = api_multipart("/graph/ontology/generate",
                          dict(simulation_requirement=requirement,
                               project_name=f"Atlas: {slug}",
                               additional_context="Macro-financial scenario tracing; keep entity types focused on economic actors."),
                          SEED)
        if not r.get("success"):
            log(slug, f"FEJL ontologi: {str(r)[:200]}"); return False
        s = save(slug, project_id=r["data"]["project_id"])
    if not s.get("graph_done"):
        log(slug, "zep-graf...")
        r = api("POST", "/graph/build", dict(project_id=s["project_id"]))
        if not r.get("success"):
            log(slug, f"FEJL build: {str(r)[:200]}"); return False
        task = r["data"].get("task_id")
        while task:
            time.sleep(12)
            t = api("GET", f"/graph/task/{task}")
            st = t.get("data", {}).get("status", t.get("status", "?"))
            if st in ("completed", "success"):
                break
            if st in ("failed", "error"):
                log(slug, f"FEJL build: {str(t)[:200]}"); return False
        s = save(slug, graph_done=True)
    if "simulation_id" not in s:
        r = api("POST", "/simulation/create", dict(project_id=s["project_id"]))
        if not r.get("success"):
            log(slug, f"FEJL create: {str(r)[:200]}"); return False
        s = save(slug, simulation_id=r["data"]["simulation_id"])
        log(slug, f"simulation {s['simulation_id']}")
    if not s.get("prepared"):
        log(slug, "personas...")
        api("POST", "/simulation/prepare", dict(simulation_id=s["simulation_id"], parallel_profile_count=5))
        while True:
            time.sleep(15)
            t = api("POST", "/simulation/prepare/status", dict(simulation_id=s["simulation_id"]))
            st = t.get("data", {}).get("status", t.get("status", "?"))
            if st in ("ready", "completed", "success"):
                break
            if st in ("failed", "error"):
                log(slug, f"FEJL prepare: {str(t)[:200]}"); return False
        s = save(slug, prepared=True)
    if not s.get("sim_done"):
        log(slug, f"simulerer ({MAX_ROUNDS} runder)...")
        api("POST", "/simulation/start", dict(simulation_id=s["simulation_id"], max_rounds=MAX_ROUNDS, force=False))
        stale = 0
        last_round = -1
        while True:
            time.sleep(25)
            t = api("GET", f"/simulation/{s['simulation_id']}/run-status")
            d = t.get("data", t)
            st = d.get("runner_status", "?")
            cur = d.get("current_round", 0) or 0
            if cur != last_round:
                last_round, stale = cur, 0
            else:
                stale += 1
            if st in ("completed", "finished", "stopped"):
                break
            if cur >= MAX_ROUNDS and stale >= 3:
                break                      # runder faerdige, runner haenger — interview nu
            if st in ("failed", "error"):
                log(slug, f"FEJL sim: {str(d)[:150]}"); return False
        s = save(slug, sim_done=True)
        log(slug, f"runder faerdige (runde {last_round})")
    if not s.get("interviewed"):
        answers = {}
        for i, q in enumerate(SPOERGSMAAL, 1):
            log(slug, f"interview {i}/3...")
            r = api("POST", "/simulation/interview/all",
                    dict(simulation_id=s["simulation_id"], prompt=q, timeout=240), timeout=300)
            answers[f"Q{i}"] = dict(prompt=q, svar=r.get("data", r))
            time.sleep(3)
        (OUT / f"{slug}.json").write_text(json.dumps(answers, ensure_ascii=False, indent=1), encoding="utf-8")
        s = save(slug, interviewed=True)
    api("POST", "/simulation/stop", dict(simulation_id=s["simulation_id"]))
    save(slug, done=True)
    log(slug, "FAERDIG")
    return True

def main():
    ok = 0
    for slug, req in RUNS:
        try:
            if do_run(slug, req):
                ok += 1
        except Exception as e:
            log(slug, f"UNDTAGELSE: {repr(e)[:200]}")
    print(f"\n=== ATLAS FAERDIGT: {ok}/{len(RUNS)} koersler lykkedes; svar i {OUT} ===", flush=True)

if __name__ == "__main__":
    main()
