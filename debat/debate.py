#!/usr/bin/env python3
"""Raadets debat-orkestrator. Kalder 7 modeller via OpenRouter, runde for runde.

Brug:  python debate.py round1|round2|round3|round4|round5
Kraever OPENROUTER_API_KEY i miljoeet eller i C:/Users/Machine/recession/.env
Runde 3-5 kraever en sekretaer-fil (skrives af Claude mellem runderne):
  secretary/round3_matrix.md, secretary/round4_draft.md, secretary/round5_draft.md
"""
import json, os, sys, time, re
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).parent
API = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    dict(slug="gpt_sol",   name="GPT-5.6 Sol",          vendor="OpenAI",
         ids=["openai/gpt-5.6-sol"], free=False, price=(5.00, 30.00)),
    dict(slug="kimi_k3",   name="Kimi K3",              vendor="Moonshot AI",
         ids=["moonshotai/kimi-k3"], free=False, price=(3.00, 15.00)),
    dict(slug="gemini_pro", name="Gemini Pro (latest)",  vendor="Google",
         ids=["~google/gemini-pro-latest", "google/gemini-3.1-pro-preview"], free=False, price=(2.00, 12.00)),
    dict(slug="grok_45",   name="Grok 4.5",             vendor="xAI",
         ids=["x-ai/grok-4.5"], free=False, price=(2.00, 6.00)),
    dict(slug="nemotron_ultra", name="Nemotron 3 Ultra 550B", vendor="NVIDIA (free)",
         ids=["nvidia/nemotron-3-ultra-550b-a55b:free"], free=True, price=(0, 0)),
    dict(slug="gemma_4",   name="Gemma 4 31B",          vendor="Google (free)",
         ids=["google/gemma-4-31b-it:free", "google/gemma-4-26b-a4b-it:free",
              "nvidia/nemotron-3-super-120b-a12b:free"], free=True, price=(0, 0)),
    dict(slug="gpt_oss",   name="GPT-OSS-20B",          vendor="OpenAI (free)",
         ids=["openai/gpt-oss-20b:free"], free=True, price=(0, 0)),
]

def get_key():
    k = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if k:
        return k
    for envfile in [Path("C:/Users/Machine/recession/.env"), HERE / ".env"]:
        if envfile.exists():
            for line in envfile.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("FEJL: ingen OPENROUTER_API_KEY fundet (env eller C:/Users/Machine/recession/.env)")

KEY = get_key()
BRIEF = (HERE / "brief.md").read_text(encoding="utf-8")

def call_model(m, user_prompt, temperature, max_tokens):
    """Kald en model med fallback-id'er, retries og 429-haandtering."""
    sysmsg = (f"You are {m['name']} ({m['vendor']}), serving on a seven-model advisory council "
              "for a solo developer's US recession-probability model. You act as a senior "
              "macro-econometrician. Be concrete and quantitative. Disagree openly when you "
              "disagree; never agree out of politeness. No filler, no hedging boilerplate, "
              "no compliments. Write in English. The council advises; Rasmus decides.")
    last_err = None
    for model_id in m["ids"]:
        payload = dict(model=model_id,
                       messages=[{"role": "system", "content": sysmsg},
                                 {"role": "user", "content": user_prompt}],
                       max_tokens=max_tokens, temperature=temperature)
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(
                    API, data=json.dumps(payload).encode("utf-8"),
                    headers={"Authorization": f"Bearer {KEY}",
                             "Content-Type": "application/json",
                             "HTTP-Referer": "https://localhost/raadet",
                             "X-Title": "Raadets Kollegium - recessionsmodel"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    data = json.loads(r.read().decode("utf-8"))
                if "error" in data and data["error"]:
                    raise RuntimeError(str(data["error"])[:300])
                msg = data["choices"][0]["message"]
                text = (msg.get("content") or "").strip()
                if not text and msg.get("reasoning"):
                    text = msg["reasoning"].strip()  # sidste udvej
                if not text:
                    raise RuntimeError("tomt svar")
                usage = data.get("usage", {})
                return dict(ok=True, model_id=model_id, text=text,
                            prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0),
                            raw=data)
            except urllib.error.HTTPError as e:
                body = ""
                try:
                    body = e.read().decode("utf-8")[:400]
                except Exception:
                    pass
                last_err = f"HTTP {e.code}: {body}"
                if e.code == 429:
                    time.sleep(65)          # gratis-tier ratelimit
                elif e.code in (400, 404):
                    break                    # proev naeste model-id
                else:
                    time.sleep(10 * attempt)
            except Exception as e:
                last_err = repr(e)[:300]
                time.sleep(8 * attempt)
    return dict(ok=False, model_id=m["ids"][0], text=f"[KALD FEJLEDE: {last_err}]",
                prompt_tokens=0, completion_tokens=0, raw=None)

def read_round(n):
    d = HERE / "rounds" / f"round{n}"
    out = {}
    for m in MODELS:
        f = d / f"{m['slug']}.md"
        if f.exists():
            t = f.read_text(encoding="utf-8")
            if not t.startswith("[KALD FEJLEDE"):
                out[m["slug"]] = t
    return out

def joined(texts, heading):
    parts = []
    for m in MODELS:
        if m["slug"] in texts:
            parts.append(f"### {heading}: {m['name']} ({m['vendor']})\n\n{texts[m['slug']]}")
    return "\n\n---\n\n".join(parts)

def secretary(fname):
    f = HERE / "secretary" / fname
    if not f.exists():
        sys.exit(f"FEJL: mangler sekretaer-fil {f}")
    return f.read_text(encoding="utf-8")

def build_prompt(round_name, m):
    if round_name == "round1":
        return BRIEF + (
            "\n\n# YOUR TASK - ROUND 1, INDEPENDENT PROPOSAL\n"
            f"You are {m['name']}. Without seeing the other councillors, give your proposal for v5:\n"
            "A) Verdict on the v4 architecture: keep / kill / change, one line each for LAG 1, LAG 2, "
            "LAG 3 and the verdict layer.\n"
            "B) Q1-Q8: numbered answers, 1-4 sentences each. Take a position; no fence-sitting.\n"
            "C) Your top-3 highest-impact changes, ranked, each with the concrete walk-forward test "
            "that would validate or reject it.\n"
            "D) The single biggest risk in your own proposal.\n"
            "Hard limit: about 700 words.")
    if round_name == "round2":
        r1 = read_round(1)
        return BRIEF + "\n\n# ROUND 1 - ALL SEVEN PROPOSALS\n\n" + joined(r1, "PROPOSAL") + (
            "\n\n# YOUR TASK - ROUND 2, CRITIQUE AND REVISE\n"
            f"You are {m['name']}. 1) Attack: name the specific councillors you disagree with, quote "
            "or paraphrase the claim, and say why it is wrong. 2) Steelman: the single best idea from "
            "another councillor that your own Round 1 missed. 3) Revise your Q1-Q8 positions where "
            "warranted. 4) Finish with exactly three labeled lists:\nAGREE: points the council already "
            "agrees on\nDISAGREE: live disputes, naming the sides\nCHANGED-MY-MIND: what you moved on and why.\n"
            "Hard limit: about 600 words.")
    if round_name == "round3":
        matrix = secretary("round3_matrix.md")
        r2 = read_round(2)
        return BRIEF + "\n\n# SECRETARY'S DISAGREEMENT MATRIX (state of the debate)\n\n" + matrix + \
            "\n\n# ROUND 2 - ALL POSITIONS\n\n" + joined(r2, "POSITION") + (
            "\n\n# YOUR TASK - ROUND 3, CONVERGE\n"
            f"You are {m['name']}. For each OPEN dispute in the matrix: your final position in 1-2 "
            "sentences, then the compromise you can live with. Mark any point you would VETO (block "
            "consensus over) and state the evidence that would change your mind. Do not reopen "
            "settled points. Hard limit: about 500 words.")
    if round_name in ("round4", "round5", "round6"):
        draft = secretary(f"{round_name}_draft.md")
        return BRIEF + "\n\n# CONSENSUS DRAFT (assembled by the secretary from the debate)\n\n" + draft + (
            f"\n\n# YOUR TASK - {round_name.upper()}, RATIFY\n"
            f"You are {m['name']}. First line must be exactly 'VOTE: APPROVE' or 'VOTE: REJECT'.\n"
            "If APPROVE: up to 3 reservations for the record (they do not block consensus).\n"
            "If REJECT: the minimal concrete amendments that would flip you to APPROVE.\n"
            "Hard limit: about 300 words.")
    sys.exit(f"ukendt runde: {round_name}")

def main():
    round_name = sys.argv[1] if len(sys.argv) > 1 else ""
    if round_name not in ("round1", "round2", "round3", "round4", "round5", "round6"):
        sys.exit("brug: python debate.py round1|round2|round3|round4|round5 [--only slug]")
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    active = [m for m in MODELS if only is None or m["slug"] == only]
    if not active:
        sys.exit(f"ukendt slug: {only}")
    temperature = 0.7 if round_name == "round1" else 0.4
    outdir = HERE / "rounds" / round_name
    outdir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print(f"== {round_name}: kalder {len(active)} modeller parallelt ==", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=7) as ex:
        futs = {}
        for m in active:
            prompt = build_prompt(round_name, m)
            mt = 3500 if m["free"] else 9000
            futs[ex.submit(call_model, m, prompt, temperature, mt)] = m
        for fut in as_completed(futs):
            m = futs[fut]
            r = fut.result()
            results[m["slug"]] = r
            (outdir / f"{m['slug']}.md").write_text(r["text"], encoding="utf-8")
            if r["raw"] is not None:
                (outdir / f"{m['slug']}.json").write_text(
                    json.dumps(r["raw"], indent=1)[:200000], encoding="utf-8")
            cost = (r["prompt_tokens"] * m["price"][0] + r["completion_tokens"] * m["price"][1]) / 1e6
            status = "OK " if r["ok"] else "FEJL"
            print(f"  [{status}] {m['name']:<24} via {r['model_id']:<40} "
                  f"in={r['prompt_tokens']:>6} out={r['completion_tokens']:>6} ~${cost:.3f}", flush=True)

    # samlet fil (flettes fra disk, saa --only-retries bevarer de andres svar) + kostlog
    total_cost = 0.0
    for m in active:
        r = results[m["slug"]]
        total_cost += (r["prompt_tokens"] * m["price"][0] + r["completion_tokens"] * m["price"][1]) / 1e6
    on_disk = read_round(int(round_name[-1]))
    combined = [f"# {round_name.upper()} — samlet\n"]
    for m in MODELS:
        if m["slug"] in on_disk:
            combined.append(f"\n\n---\n\n## {m['name']} ({m['vendor']})\n\n{on_disk[m['slug']]}")
    (outdir / "_ALL.md").write_text("".join(combined), encoding="utf-8")

    costlog = HERE / "costs.json"
    hist = json.loads(costlog.read_text()) if costlog.exists() else {}
    hist[round_name] = round(hist.get(round_name, 0) + total_cost, 4)
    hist["_total"] = round(sum(v for k, v in hist.items() if not k.startswith("_")), 4)
    costlog.write_text(json.dumps(hist, indent=1))

    fails = [m["name"] for m in active if not results[m["slug"]]["ok"]]
    print(f"== faerdig paa {time.time()-t0:.0f}s, rundens pris ~${total_cost:.2f}, "
          f"samlet ~${hist['_total']:.2f} ==", flush=True)
    if round_name in ("round4", "round5", "round6"):
        votes = {}
        for m in MODELS:
            if m["slug"] not in on_disk:
                continue
            first = on_disk[m["slug"]].strip().splitlines()[0].upper() if on_disk[m["slug"]].strip() else ""
            votes[m["name"]] = "APPROVE" if "APPROVE" in first else ("REJECT" if "REJECT" in first else "UKLAR")
        print("STEMMER: " + ", ".join(f"{k}={v}" for k, v in votes.items()), flush=True)
    if fails:
        print("FEJLEDE: " + ", ".join(fails), flush=True)
        sys.exit(2)

if __name__ == "__main__":
    main()
