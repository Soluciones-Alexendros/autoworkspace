#!/usr/bin/env python3
"""
Deterministic router for Soluciones-Alexendros/autoworkspace — OpenCode-first
No LLM, vendor-neutral, pure Python TF + trigger boost.
Usage:
  python tools/skill-router/route.py "audita y publica este repo" --top 3
  python tools/skill-router/route.py --interactive
"""

import argparse
import json
import math
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX_PATHS = [
    ROOT / "skill-index.json",
    pathlib.Path("skill-index.json"),
]


def load_index():
    for p in INDEX_PATHS:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    print("skill-index.json not found", file=sys.stderr)
    sys.exit(1)


def tokenize(s: str):
    return re.findall(r"[a-z0-9áéíóúñ]+", s.lower())


def tfidf_score(query_tokens, doc_tokens, query_counter):
    doc_counter = Counter(doc_tokens)
    score = 0.0
    for t, qf in query_counter.items():
        if t in doc_counter:
            tf = doc_counter[t]
            # simple TF-IDF without IDF corpus (corpus small)
            score += tf * (1.0 + math.log(1.0 + qf)) * 1.5
    # length normalization
    if doc_tokens:
        score = score / (math.sqrt(len(doc_tokens)) + 1)
    return score


def route(prompt: str, top: int = 3):
    data = load_index()
    qtok = tokenize(prompt)
    qcounter = Counter(qtok)
    ranked = []
    for sk in data.get("skills", []):
        text = " ".join(
            [
                sk.get("name", ""),
                sk.get("description", ""),
                " ".join(sk.get("keywords", [])),
                " ".join(sk.get("triggers", [])),
            ]
        )
        dtok = tokenize(text)
        score = tfidf_score(qtok, dtok, qcounter)
        # exact trigger boost — critical for Spanish
        pl = prompt.lower()
        for trig in sk.get("triggers", []):
            if trig.lower() in pl:
                score += 5.0
        for kw in sk.get("keywords", []):
            if kw.lower() in pl:
                score += 2.0
        ranked.append((score, sk))
    ranked.sort(key=lambda x: x[0], reverse=True)
    # Lexical score is not calibrated confidence. Abstain when all scores are zero.
    ranked = [(s, sk) for s, sk in ranked if s > 0]
    if not ranked:
        return []
    return ranked[:top]


def main():
    parser = argparse.ArgumentParser(description="Skill router for OpenCode")
    parser.add_argument("prompt", nargs="*", help="User prompt")
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.interactive:
        while True:
            try:
                p = input("prompt> ").strip()
                if not p:
                    continue
                if p in ("exit", "quit"):
                    break
                for sc, sk in route(p, args.top):
                    print(f"{sc:.2f} {sk['name']} -> {sk['entry']}")
            except (EOFError, KeyboardInterrupt):
                break
        return

    prompt = " ".join(args.prompt)
    if not prompt:
        prompt = sys.stdin.read().strip()
    results = route(prompt, args.top)
    if not results:
        payload = {
            "abstain": True,
            "reason": "no lexical signal (score=0); refusing automatic first-catalog pick",
            "score_kind": "lexical_not_probabilistic",
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("ABSTAIN: no lexical signal — do not auto-select a skill")
        return
    if args.json:
        print(
            json.dumps(
                [
                    {"score": sc, "name": sk["name"], "entry": sk["entry"], "score_kind": "lexical_not_probabilistic"}
                    for sc, sk in results
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for sc, sk in results:
            print(f"{sc:.2f} {sk['name']} -> {sk['entry']}  keywords={','.join(sk.get('keywords', [])[:4])}")


if __name__ == "__main__":
    main()
