"""Section 3 pipeline (Fig. 1): collect -> LLM generation -> phishing-level validation ->
deduplication -> combined corpus. Also prints the Fig. 2 similarity analysis.

    python scripts/prepare_data.py                       # toy corpus, rule-based "LLM"
    python scripts/prepare_data.py --input my.csv        # your own text,label,source CSV
    python scripts/prepare_data.py --ollama llama3       # use a local LLM for gen + scoring
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from phishkd.analysis import (HeuristicQuestionScorer, LLMQuestionScorer, deduplicate,  # noqa: E402
                              filter_low_confidence, phishing_level, similarity_to_legit)
from phishkd.augment import LLMAugmenter, RuleAugmenter, local_llm_fn  # noqa: E402
from phishkd.data import load_corpus, make_toy_corpus  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--input", help="CSV with text,label,source (skip toy generation)")
ap.add_argument("--n-orig", type=int, default=1500)
ap.add_argument("--n-gen", type=int, default=1500)
ap.add_argument("--ollama", help="local Ollama model name to use as the LLM")
ap.add_argument("--level-thr", type=float, default=20.0)
ap.add_argument("--dedup-thr", type=float, default=0.95)
ap.add_argument("--out", default="data/corpus.csv")
args = ap.parse_args()

llm = local_llm_fn(args.ollama) if args.ollama else None
if args.input:
    df = load_corpus(args.input)
else:
    aug = LLMAugmenter(llm) if llm else RuleAugmenter()
    df = make_toy_corpus(args.n_orig, args.n_gen, augmenter=aug)
print(f"raw corpus: {len(df)}\n{df.groupby(['source', 'label']).size()}\n")

sim = similarity_to_legit(df)
print("Fig. 2 - avg TF-IDF cosine similarity of phishing emails to legitimate emails")
print(sim.groupby("source").avg_cosine_to_legit.describe().round(4), "\n")
os.makedirs("results", exist_ok=True)
sim.to_csv("results/similarity_to_legit.csv", index=False)

scorer = LLMQuestionScorer(llm) if llm else HeuristicQuestionScorer()
answers, weights = phishing_level(df, scorer)
print("3.2.1 - question weights (alignment with ground truth):")
print(weights.round(3).sort_values(ascending=False).to_string(), "\n")
answers.assign(label=df.label, source=df.source).to_csv("results/phishing_level.csv", index=False)
n = len(df)
df = filter_low_confidence(df, answers.phishing_level, args.level_thr)
print(f"filtered low-confidence synthetic phishing: {n - len(df)} removed")

n = len(df)
df = deduplicate(df, args.dedup_thr)
print(f"3.2.2 - near-duplicates removed: {n - len(df)} -> final corpus {len(df)}")
print(df.groupby(["source", "label"]).size())
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
df.to_csv(args.out, index=False)
print(f"saved {args.out}")
