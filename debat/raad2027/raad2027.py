#!/usr/bin/env python3
"""Raadet 2026-10 (dagsordenen til september-refit 2027) — syv deltagere: seks af de nyeste
flagskibsmodeller via OpenRouter (pr. 2026-10-15) + Claude (Opus 5.5) som erklaeret part og sekretaer.
Mekanikken er raad501.py's (runder, --only, sekretaerfiler, kostlog); kun rosteren og titlen er nye.

Brug:  python raad2027.py round1|round2|round3|round4|round5|round6 [--only slug]

Claude deltager IKKE via API: Claude skriver sit indlaeg direkte til
runder/runde<N>/claude.md FOER runden koeres, saa de andre ser det paa lige fod.
Runde 3+ kraever sekretaer-filer (sekretaer/round3_matrix.md, round4_draft.md, ...),
skrevet af Claude — som er baade sekretaer og part; parternes indlaeg staar ordret.
Svar gemmes i runder/runde<N>/<slug>.md (+ _ALL.md). Kostlog i costs.json.
"""
import json, os, sys, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).parent
API = "https://openrouter.ai/api/v1/chat/completions"
ROUNDS = ("round1", "round2", "round3", "round4", "round5", "round6")

MODELS = [   # de nyeste flagskibe pr. 2026-10-15 (OpenRouter /models, sorteret efter udgivelse)
    dict(slug="sol",      name="GPT-6.1 Sol Pro",      vendor="OpenAI",
         ids=["openai/gpt-6.1-sol-pro", "openai/gpt-6.1-sol"], price=(2.00, 10.00), max_out=16000),
    dict(slug="argon",    name="Gemini 4 Argon",       vendor="Google",
         ids=["google/gemini-4-argon"], price=(2.00, 10.00), max_out=16000),
    dict(slug="fable",    name="Claude Fable 5.1",     vendor="Anthropic (independent instance)",
         ids=["anthropic/claude-fable-5.1"], price=(10.00, 50.00), max_out=8000),
    dict(slug="grok",     name="Grok 4.7",             vendor="xAI",
         ids=["x-ai/grok-4.7"], price=(2.00, 6.00), max_out=12000),
    dict(slug="kimi",     name="Kimi K3",              vendor="Moonshot AI",
         ids=["moonshotai/kimi-k3"], price=(0.45, 16.50), max_out=20000),   # reasoning-model: taenkning taeller med
    dict(slug="deepseek", name="DeepSeek V4 Pro",      vendor="DeepSeek",
         ids=["deepseek/deepseek-v4-pro-0813"], price=(0.66, 1.98), max_out=12000),
    dict(slug="claude",   name="Claude (Opus 5.5)",    vendor="Anthropic — interested party, co-builder and secretary",
         ids=[], price=(0, 0), max_out=0),          # skriver selv til fil
]
EXTERNAL = [m for m in MODELS if m["ids"]]


def get_key():
    k = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if k:
        return k
    for envfile in [Path("C:/Users/Machine/recession/.env"), HERE / ".env"]:
        if envfile.exists():
            for line in envfile.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("FEJL: ingen OPENROUTER_API_KEY")


KEY = get_key()
BRIEF = (HERE / "brief.md").read_text(encoding="utf-8")

SYSMSG = ("You are {name} ({vendor}), one of seven members of an advisory council for a solo "
          "developer's US recession-probability model. You act as a senior macro-econometrician. "
          "Be concrete and quantitative. Disagree openly when you disagree; never agree out of "
          "politeness. No filler, no hedging boilerplate, no compliments. Write in English. "
          "The council advises; Rasmus decides. One councillor, Claude, co-built the model and "
          "wrote the plan under debate — scrutinise its plan at least as hard as the others'.")


def call_model(m, user_prompt, temperature):
    last_err = None
    for model_id in m["ids"]:
        payload = dict(model=model_id,
                       messages=[{"role": "system", "content": SYSMSG.format(**m)},
                                 {"role": "user", "content": user_prompt}],
                       max_tokens=m["max_out"], temperature=temperature)
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(
                    API, data=json.dumps(payload).encode("utf-8"),
                    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                             "HTTP-Referer": "https://localhost/raadet", "X-Title": "Raadet 2027"})
                with urllib.request.urlopen(req, timeout=600) as r:
                    data = json.loads(r.read().decode("utf-8"))
                if data.get("error"):
                    raise RuntimeError(str(data["error"])[:300])
                msg = data["choices"][0]["message"]
                text = (msg.get("content") or "").strip() or (msg.get("reasoning") or "").strip()
                if not text:
                    raise RuntimeError("tomt svar")
                u = data.get("usage", {})
                return dict(ok=True, model_id=model_id, text=text,
                            prompt_tokens=u.get("prompt_tokens", 0),
                            completion_tokens=u.get("completion_tokens", 0), raw=data)
            except urllib.error.HTTPError as e:
                try:
                    body = e.read().decode("utf-8")[:400]
                except Exception:
                    body = ""
                last_err = f"HTTP {e.code}: {body}"
                if e.code == 429:
                    time.sleep(30)
                elif e.code in (400, 404):
                    break
                else:
                    time.sleep(10 * attempt)
            except Exception as e:
                last_err = repr(e)[:300]
                time.sleep(8 * attempt)
    return dict(ok=False, model_id=m["ids"][0] if m["ids"] else "-", text=f"[KALD FEJLEDE: {last_err}]",
                prompt_tokens=0, completion_tokens=0, raw=None)


def read_round(n):
    d = HERE / "runder" / f"runde{n}"
    out = {}
    for m in MODELS:
        f = d / f"{m['slug']}.md"
        if f.exists():
            t = f.read_text(encoding="utf-8")
            if not t.startswith("[KALD FEJLEDE"):
                out[m["slug"]] = t
    return out


def joined(texts, heading):
    return "\n\n---\n\n".join(f"### {heading}: {m['name']} ({m['vendor']})\n\n{texts[m['slug']]}"
                              for m in MODELS if m["slug"] in texts)


def secretary(fname):
    f = HERE / "sekretaer" / fname
    if not f.exists():
        sys.exit(f"FEJL: mangler sekretaer-fil {f}")
    return f.read_text(encoding="utf-8")


def require_round(n, what):
    r = read_round(n)
    if len(r) < len(MODELS):
        missing = [m["name"] for m in MODELS if m["slug"] not in r]
        sys.exit(f"FEJL: runde {n} mangler {missing} — {what}")
    return r


def build_prompt(round_name, m):
    if round_name == "round1":
        return BRIEF + (
            "\n\n# YOUR TASK — ROUND 1, INDEPENDENT PROPOSAL\n"
            f"You are {m['name']}. Without seeing the other councillors:\n"
            "A) Answer every numbered agenda question: 2–6 sentences each. Take a position; no fence-sitting. "
            "Where you specify a computation, give the formula or the exact procedure.\n"
            "B) Your verdict on Claude's draft positions: which you keep as written, which you amend (how), "
            "which you strike.\n"
            "C) The single biggest risk in your own proposal.\n"
            "Hard limit: about 1200 words.")
    if round_name == "round2":
        r1 = require_round(1, "koer round1 og skriv claude.md foerst")
        return BRIEF + "\n\n# ROUND 1 — ALL SEVEN PROPOSALS\n\n" + joined(r1, "PROPOSAL") + (
            "\n\n# YOUR TASK — ROUND 2, ATTACK AND REVISE\n"
            f"You are {m['name']}. 1) Attack: for at least two other councillors, quote the specific "
            "claim you reject and show why it is wrong — with a mechanism or a number, not an opinion. "
            "2) Steelman: the single best idea from another councillor that your Round 1 missed. "
            "3) Revise your positions on the agenda questions where warranted; say explicitly what you changed. "
            "4) Finish with exactly three labeled lists:\nAGREE: points the council already agrees on\n"
            "DISAGREE: live disputes, naming the sides\nCHANGED-MY-MIND: what you moved on and why.\n"
            "Hard limit: about 800 words.")
    if round_name == "round3":
        matrix = secretary("round3_matrix.md")
        r2 = require_round(2, "koer round2 og skriv claude.md foerst")
        return BRIEF + "\n\n# SECRETARY'S DISAGREEMENT MATRIX (written by Claude — a party to the debate; " \
            "the positions are quoted, the framing is Claude's and may be challenged)\n\n" + matrix + \
            "\n\n# ROUND 2 — ALL POSITIONS\n\n" + joined(r2, "POSITION") + (
            "\n\n# YOUR TASK — ROUND 3, CONVERGE\n"
            f"You are {m['name']}. For each OPEN dispute in the matrix: your final position in 1–2 "
            "sentences, then the compromise you can live with. Mark any point you would VETO (block "
            "consensus over) and state the evidence that would change your mind. If the secretary's "
            "framing misrepresents you, say so first. Do not reopen settled points. "
            "Hard limit: about 600 words.")
    if round_name in ("round4", "round5", "round6"):
        draft = secretary(f"{round_name}_draft.md")
        prev = read_round(int(round_name[-1]) - 1)
        return BRIEF + "\n\n# CONSENSUS DRAFT (assembled by the secretary from the debate)\n\n" + draft + \
            "\n\n# PREVIOUS ROUND — ALL POSITIONS\n\n" + joined(prev, "POSITION") + (
            f"\n\n# YOUR TASK — {round_name.upper()}, RATIFY\n"
            f"You are {m['name']}. First line must be exactly 'VOTE: APPROVE' or 'VOTE: REJECT'.\n"
            "If APPROVE: up to 3 reservations for the record (they do not block consensus).\n"
            "If REJECT: the minimal concrete amendments that would flip you to APPROVE.\n"
            "Hard limit: about 350 words.")
    sys.exit(f"ukendt runde: {round_name}")


def main():
    round_name = sys.argv[1] if len(sys.argv) > 1 else ""
    if round_name not in ROUNDS:
        sys.exit("brug: python raad2027.py round1..round6 [--only slug]")
    if "--only" in sys.argv and sys.argv.index("--only") + 1 >= len(sys.argv):
        sys.exit("brug: --only <slug>")
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    active = [m for m in EXTERNAL if only is None or m["slug"] == only]
    if not active:
        sys.exit(f"ukendt slug: {only}")
    temperature = 0.7 if round_name == "round1" else 0.4
    n = int(round_name[-1])
    outdir = HERE / "runder" / f"runde{n}"
    outdir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print(f"== {round_name}: kalder {len(active)} modeller parallelt ==", flush=True)
    results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(call_model, m, build_prompt(round_name, m), temperature): m for m in active}
        for fut in as_completed(futs):
            m = futs[fut]
            r = fut.result()
            results[m["slug"]] = r
            arkiv = outdir / f"{m['slug']}.md"           # et fejlet genkald overskriver aldrig et arkiveret svar
            if not r["ok"] and arkiv.exists() and not arkiv.read_text(encoding="utf-8").startswith("[KALD FEJLEDE"):
                print(f"  [FEJL] {m['name']}: kaldet fejlede — det arkiverede svar i {arkiv.name} bevares", flush=True)
                continue
            arkiv.write_text(r["text"], encoding="utf-8")
            if r["raw"] is not None:
                (outdir / f"{m['slug']}.json").write_text(json.dumps(r["raw"], indent=1)[:200000], encoding="utf-8")
            cost = (r["prompt_tokens"] * m["price"][0] + r["completion_tokens"] * m["price"][1]) / 1e6
            print(f"  [{'OK ' if r['ok'] else 'FEJL'}] {m['name']:<18} via {r['model_id']:<32} "
                  f"in={r['prompt_tokens']:>6} out={r['completion_tokens']:>6} ~${cost:.3f}", flush=True)

    total = sum((results[m["slug"]]["prompt_tokens"] * m["price"][0]
                 + results[m["slug"]]["completion_tokens"] * m["price"][1]) / 1e6 for m in active)
    on_disk = read_round(n)
    combined = [f"# {round_name.upper()} — samlet\n"]
    for m in MODELS:
        if m["slug"] in on_disk:
            combined.append(f"\n\n---\n\n## {m['name']} ({m['vendor']})\n\n{on_disk[m['slug']]}")
    (outdir / "_ALL.md").write_text("".join(combined), encoding="utf-8")

    costlog = HERE / "costs.json"
    hist = json.loads(costlog.read_text()) if costlog.exists() else {}
    hist[round_name] = round(hist.get(round_name, 0) + total, 4)
    hist["_total"] = round(sum(v for k, v in hist.items() if not k.startswith("_")), 4)
    costlog.write_text(json.dumps(hist, indent=1))
    print(f"== faerdig paa {time.time()-t0:.0f}s, rundens pris ~${total:.2f}, samlet ~${hist['_total']:.2f} ==", flush=True)


if __name__ == "__main__":
    main()
