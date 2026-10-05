"""Section 5 - five scenarios x K-fold CV for every model (Tables 4-7).

    python scripts/run_experiments.py --models lstm,bilstm,bilstm_sh,bilstm_mh
    python scripts/run_experiments.py --models teacher,kd --scenarios mixture --bert-max-len 128
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd  # noqa: E402

from phishkd.data import SCENARIOS, load_corpus, scenario_folds, set_seed  # noqa: E402
from phishkd.train import (Config, distill, evaluate_hf_or_student, run_baseline,  # noqa: E402
                           summarize, train_teacher)

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data/corpus.csv")
ap.add_argument("--models", default="lstm,bilstm,bilstm_sh,bilstm_mh,teacher,kd")
ap.add_argument("--scenarios", default=",".join(SCENARIOS))
ap.add_argument("--folds", type=int, default=5)
ap.add_argument("--max-folds", type=int, help="only run the first N folds (quick runs)")
ap.add_argument("--bert-max-len", type=int, default=512)
ap.add_argument("--teacher-epochs", type=int, default=2)
ap.add_argument("--kd-epochs", type=int, default=3)
ap.add_argument("--base-epochs", type=int, default=5)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--out", default="results/results.csv")
args = ap.parse_args()

cfg = Config(bert_max_len=args.bert_max_len, teacher_epochs=args.teacher_epochs,
             kd_epochs=args.kd_epochs, base_epochs=args.base_epochs)
models = args.models.split(",")
df = load_corpus(args.data)
rows = []
for scen in args.scenarios.split(","):
    for k, tr, va, te in scenario_folds(df, scen, args.folds, seed=args.seed):
        if args.max_folds is not None and k >= args.max_folds:
            break
        print(f"\n=== {scen} | fold {k + 1}/{args.folds} | train {len(tr)} val {len(va)} "
              f"test {len(te)} ===")
        for name in [m for m in models if m not in ("teacher", "kd")]:
            set_seed(args.seed + k)
            r = run_baseline(name, tr, va, te, cfg)
            rows.append({"model": name, "scenario": scen, "fold": k, **r})
            print(f"{name:10s} F1={r['f1_weighted']:.2f} acc={r['acc']:.2f} params={r['params']}")
        if "teacher" in models or "kd" in models:
            set_seed(args.seed + k)
            tok, teacher, t_train = train_teacher(tr, va, cfg)
            if "teacher" in models:
                r = {"train_s": t_train, **evaluate_hf_or_student(teacher, tok, te, cfg, True)}
                rows.append({"model": "mobilebert", "scenario": scen, "fold": k, **r})
                print(f"mobilebert F1={r['f1_weighted']:.2f} params={r['params']:,}")
            if "kd" in models:
                student, s_train = distill(teacher, tok, tr, va, cfg)
                r = {"train_s": s_train, **evaluate_hf_or_student(student, tok, te, cfg, False)}
                rows.append({"model": "kd_bilstm_mh", "scenario": scen, "fold": k, **r})
                print(f"kd_bilstm  F1={r['f1_weighted']:.2f} params={r['params']:,}")
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        pd.DataFrame(rows).to_csv(args.out, index=False)

summary = summarize(rows)
summary.to_csv(args.out.replace(".csv", "_summary.csv"), index=False)
print("\n" + summary.to_string(index=False))
