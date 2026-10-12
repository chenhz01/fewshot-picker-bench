#!/usr/bin/env python3
"""fewshot-picker-bench — deterministic few-shot example picker + selection quality self-report.

Pure stdlib. Pipeline: tokenize -> TF-IDF relevance vs query -> MMR diversity
re-ranking -> quality self-report (redundancy / coverage / label spread).
"""
import argparse
import json
import math
import re
import sys

TOKEN_RE = re.compile(r"\w+", re.UNICODE)
GENERIC = {"", "the", "a", "an", "and", "or", "of", "to", "in", "is", "for", "on"}


def tokenize(text):
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in GENERIC]


def term_counts(tokens):
    tc = {}
    for t in tokens:
        tc[t] = tc.get(t, 0) + 1
    return tc


def build_corpus_vectors(examples):
    """Return (list of tf dicts, idf dict) over the example corpus."""
    tfs = [term_counts(tokenize(e.get("text", ""))) for e in examples]
    df = {}
    for tf in tfs:
        for t in tf:
            df[t] = df.get(t, 0) + 1
    n = max(len(examples), 1)
    idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
    return tfs, idf


def tfidf_vector(tf, idf):
    return {t: (1.0 + math.log(c)) * idf.get(t, 1.0) for t, c in tf.items()}


def cosine(a, b):
    if not a or not b:
        return 0.0
    if len(b) < len(a):
        a, b = b, a
    dot = sum(v * b.get(t, 0.0) for t, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def mmr_select(query_vec, cand_vecs, k, lam):
    """Deterministic MMR. Ties broken by lower original index."""
    rel = [cosine(query_vec, cv) for cv in cand_vecs]
    selected = []
    remaining = list(range(len(cand_vecs)))
    while remaining and len(selected) < k:
        best_i, best_score = None, None
        for i in remaining:
            div = 0.0
            for j in selected:
                s = cosine(cand_vecs[i], cand_vecs[j])
                if s > div:
                    div = s
            score = lam * rel[i] - (1.0 - lam) * div
            if best_score is None or score > best_score + 1e-12:
                best_i, best_score = i, score
        selected.append(best_i)
        remaining.remove(best_i)
    return selected, rel


def quality_report(query_tokens, cand_tokens, selected, labels, lam, rel):
    sel_tokens = [cand_tokens[i] for i in selected]
    mean_sim = 0.0
    pairs = 0
    for i in range(len(sel_tokens)):
        for j in range(i + 1, len(sel_tokens)):
            mean_sim += jaccard(sel_tokens[i], sel_tokens[j])
            pairs += 1
    redundancy = mean_sim / pairs if pairs else 0.0
    qset = set(query_tokens)
    covered = set()
    for tk in sel_tokens:
        covered |= set(tk)
    coverage = (len(qset & covered) / len(qset)) if qset else 0.0
    coverage_profile = {"covered": sorted(qset & covered), "missed": sorted(qset - covered)}
    sel_labels = [labels[i] for i in selected if labels[i] is not None]
    distinct = len(set(sel_labels)) / len(sel_labels) if sel_labels else None
    return {
        "redundancy": round(redundancy, 4),
        "query_coverage": round(coverage, 4),
        "coverage_profile": coverage_profile,
        "label_diversity": round(distinct, 4) if distinct is not None else None,
        "mean_relevance": round(sum(rel[i] for i in selected) / len(selected), 6) if selected else 0.0,
        "lambda": lam,
    }


def pick(examples, query, k=5, lam=0.7):
    """Return dict with selected entries, indices and quality report."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if k < 0:
        raise ValueError("k must be >= 0")
    if not (0.0 <= lam <= 1.0):
        raise ValueError("lambda must be in [0, 1]")
    cand_tokens = [tokenize(e.get("text", "")) for e in examples]
    tfs, idf = build_corpus_vectors(examples)
    cand_vecs = [tfidf_vector(tf, idf) for tf in tfs]
    q_tf = term_counts(tokenize(query))
    query_vec = tfidf_vector(q_tf, idf)
    k_eff = min(k, len(examples))
    selected, rel = mmr_select(query_vec, cand_vecs, k_eff, lam)
    labels = [e.get("label") for e in examples]
    report = quality_report(tokenize(query), cand_tokens, selected, labels, lam, rel)
    out = []
    for i in selected:
        row = dict(examples[i])
        row["_index"] = i
        row["_relevance"] = round(rel[i], 6)
        out.append(row)
    return {"selected": out, "quality": report, "pool_size": len(examples), "k_requested": k}


def load_jsonl(path):
    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError as e:
                raise ValueError("bad JSON on line %d: %s" % (ln, e))
            if not isinstance(obj, dict):
                raise ValueError("line %d is not a JSON object" % ln)
            if not isinstance(obj.get("text"), str):
                raise ValueError("line %d missing string field 'text'" % ln)
            examples.append(obj)
    return examples


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pick", description="Deterministic few-shot example picker (TF-IDF + MMR) with quality self-report.")
    ap.add_argument("file", help="JSONL file of examples with a 'text' field")
    ap.add_argument("--query", required=True, help="query text to rank examples against")
    ap.add_argument("--k", type=int, default=5, help="number of examples to pick (default 5)")
    ap.add_argument("--lambda", dest="lam", type=float, default=0.7, help="relevance vs diversity tradeoff in [0,1]")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args(argv)
    try:
        examples = load_jsonl(args.file)
        result = pick(examples, args.query, args.k, args.lam)
    except (ValueError, TypeError, OSError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for row in result["selected"]:
            print("[%d] rel=%.4f  %s" % (row["_index"], row["_relevance"], row.get("id", row["text"][:60])))
        print("quality: %s" % json.dumps(result["quality"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
