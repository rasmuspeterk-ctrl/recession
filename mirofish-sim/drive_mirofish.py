#!/usr/bin/env python3
"""Driver: koerer hele MiroFish-pipelinen mod backend paa :5001.
Stadier: ontology -> build -> create -> prepare -> start -> run -> report.
Genoptagelig via state.json. Printer fremdrift loebende (laeses af Claude)."""
import json, mimetypes, sys, time, urllib.request, urllib.error, uuid
from pathlib import Path

BASE = "http://localhost:5001/api"
HERE = Path(__file__).parent
SEED = HERE / "seed.md"
STATE_F = HERE / "state.json"

SIM_REQ = (
    "Predict whether the US economy enters a recession within the next 12 months "
    "(by August 2027). Simulate how the key actors (the Fed, households, retail "
    "investors, institutional investors, corporations, homebuilders, media "
    "commentators) react to incoming economic data and to each other over the "
    "coming months, given the 'low spark, high fuel' configuration: quiet real "
    "economy, extreme valuation and leverage. Track: (1) whether an equity/credit "
    "repricing occurs and whether it transmits to the real economy, (2) whether "
    "inflation re-acceleration forces the Fed to tighten again, (3) whether labor "
    "market cracks appear. Output should support a final verdict: probability of "
    "US recession within 12 months, the most likely trigger chain, and early "
    "warning indicators to monitor."
)

def state():
    return json.loads(STATE_F.read_text()) if STATE_F.exists() else {}

def save(**kw):
    s = state(); s.update(kw); STATE_F.write_text(json.dumps(s, indent=1))
    return s

def api(method, path, payload=None, timeout=600):
    req = urllib.request.Request(BASE + path, method=method)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def api_multipart(path, fields, filepath, timeout=900):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    ctype = mimetypes.guess_type(filepath.name)[0] or "text/markdown"
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; "
                 f"filename=\"{filepath.name}\"\r\nContent-Type: {ctype}\r\n\r\n".encode())
    parts.append(filepath.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def must(resp, ctx):
    if not resp.get("success"):
        print(f"[FEJL] {ctx}: {json.dumps(resp, ensure_ascii=False)[:600]}", flush=True)
        sys.exit(1)
    return resp["data"]

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def main():
    s = state()

    # 1) ontologi + projekt
    if "project_id" not in s:
        log("STADIE 1/6: ontology/generate (uploader seed, LLM analyserer)...")
        d = must(api_multipart("/graph/ontology/generate",
                               dict(simulation_requirement=SIM_REQ,
                                    project_name="US Recession Watch 2026",
                                    additional_context="Focus on macro-financial dynamics, not one company."),
                               SEED), "ontology")
        s = save(project_id=d["project_id"])
        ents = [e.get("name", "?") for e in d.get("ontology", {}).get("entity_types", [])]
        log(f"  projekt {s['project_id']}, entitetstyper: {', '.join(ents[:10])}")

    # 2) byg Zep-graf
    if "graph_done" not in s:
        log("STADIE 2/6: graph/build (Zep-ingestion)...")
        d = must(api("POST", "/graph/build", dict(project_id=s["project_id"])), "build")
        task = d.get("task_id")
        while task:
            time.sleep(15)
            t = must(api("GET", f"/graph/task/{task}"), "task-poll")
            st, prog = t.get("status"), t.get("progress", "")
            log(f"  build: {st} {prog}")
            if st in ("completed", "success"):
                break
            if st in ("failed", "error"):
                print(f"[FEJL] build fejlede: {json.dumps(t, ensure_ascii=False)[:600]}", flush=True)
                sys.exit(1)
        s = save(graph_done=True)

    # 3) opret simulation
    if "simulation_id" not in s:
        log("STADIE 3/6: simulation/create...")
        d = must(api("POST", "/simulation/create", dict(project_id=s["project_id"])), "create")
        s = save(simulation_id=d["simulation_id"])
        log(f"  simulation {s['simulation_id']}")

    # 4) forbered (personas + config, async)
    if "prepared" not in s:
        log("STADIE 4/6: simulation/prepare (LLM genererer agent-personas)...")
        d = must(api("POST", "/simulation/prepare",
                     dict(simulation_id=s["simulation_id"], parallel_profile_count=5)), "prepare")
        while True:
            time.sleep(20)
            t = must(api("POST", "/simulation/prepare/status",
                         dict(simulation_id=s["simulation_id"])), "prepare-poll")
            st = t.get("status", "?")
            log(f"  prepare: {st} {t.get('progress', '')} {t.get('message', '')[:80]}")
            if st in ("ready", "completed", "success"):
                break
            if st in ("failed", "error"):
                print(f"[FEJL] prepare fejlede: {json.dumps(t, ensure_ascii=False)[:600]}", flush=True)
                sys.exit(1)
        s = save(prepared=True)

    # 5) start simulation (maks 30 runder jf. README-anbefaling om <40)
    if "started" not in s:
        log("STADIE 5/6: simulation/start (parallel, max_rounds=30)...")
        d = must(api("POST", "/simulation/start",
                     dict(simulation_id=s["simulation_id"], max_rounds=30)), "start")
        s = save(started=True)
        log(f"  runner: {d.get('runner_status')} pid={d.get('process_pid')}")

    # 6) vent paa afslutning, generer rapport
    if "report_id" not in s:
        log("STADIE 6/6: venter paa simulationen...")
        while True:
            time.sleep(30)
            t = must(api("GET", f"/simulation/{s['simulation_id']}/run-status"), "run-poll")
            st = t.get("runner_status", t.get("status", "?"))
            log(f"  simulation: {st} runde={t.get('current_round', '?')}/{t.get('max_rounds', '?')}")
            if st in ("completed", "finished", "success", "stopped"):
                break
            if st in ("failed", "error"):
                print(f"[FEJL] simulation: {json.dumps(t, ensure_ascii=False)[:600]}", flush=True)
                sys.exit(1)
        log("  simulation faerdig — genererer rapport...")
        must(api("POST", "/report/generate", dict(simulation_id=s["simulation_id"])), "report")
        while True:
            time.sleep(20)
            t = must(api("POST", "/report/generate/status",
                         dict(simulation_id=s["simulation_id"])), "report-poll")
            st = t.get("status", "?")
            log(f"  rapport: {st} {t.get('progress', '')}")
            if st in ("completed", "success"):
                s = save(report_id=t.get("report_id", ""))
                break
            if st in ("failed", "error"):
                print(f"[FEJL] rapport: {json.dumps(t, ensure_ascii=False)[:600]}", flush=True)
                sys.exit(1)

    r = must(api("GET", f"/report/by-simulation/{s['simulation_id']}"), "hent-rapport")
    out = HERE / "rapport.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"FAERDIG. Rapport gemt: {out}")

if __name__ == "__main__":
    main()
