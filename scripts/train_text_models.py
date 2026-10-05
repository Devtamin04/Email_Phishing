"""Trains the text models used by PhishLens on (Vietnamese school corpus, train templates only)
+ (English toy corpus of the paper reproduction).

    python scripts/train_text_models.py            # linear model (seconds)
    python scripts/train_text_models.py --kd       # + MobileBERT teacher -> KD-BiLSTM student
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from phishkd.data import make_toy_corpus, set_seed  # noqa: E402
from phishlens.content import LinearTextModel, model_text  # noqa: E402
from phishlens.synth import make_vi_corpus  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--kd", action="store_true")
ap.add_argument("--max-len", type=int, default=128)
ap.add_argument("--out", default="models")
args = ap.parse_args()
set_seed(0)
os.makedirs(args.out, exist_ok=True)

vi = make_vi_corpus(split="train")
en = make_toy_corpus(600, 600, seed=1)
df = pd.concat([vi[["text", "label", "source"]], en[["text", "label", "source"]]]).sample(
    frac=1, random_state=0).reset_index(drop=True)
df["text"] = df.text.map(model_text)
tr, va = train_test_split(df, test_size=0.1, stratify=df.label, random_state=0)
print(f"train {len(tr)}  val {len(va)}  (vi {len(vi)}, en {len(en)})")

lin = LinearTextModel().fit(tr.text, tr.label)
acc = ((lin.predict_proba(va.text) >= 0.5) == va.label).mean()
lin.save(os.path.join(args.out, "linear.joblib"))
print(f"linear model saved - val acc {acc:.3f}")

if args.kd:
    from phishkd.train import Config, distill, train_teacher, tokenize, predict_logits
    cfg = Config(bert_max_len=args.max_len, teacher_epochs=2, kd_epochs=3)
    tok, teacher, _ = train_teacher(tr.reset_index(drop=True), va.reset_index(drop=True), cfg)
    student, _ = distill(teacher, tok, tr.reset_index(drop=True), va.reset_index(drop=True), cfg)
    for name, m, hf in (("teacher", teacher, True), ("student", student, False)):
        ids, mask = tokenize(tok, va, cfg.bert_max_len)
        pred = predict_logits(m, ids, mask, cfg, hf).argmax(-1).numpy()
        print(f"{name} val acc {(pred == va.label.values).mean():.3f}")
    d = os.path.join(args.out, "kd_bilstm")
    os.makedirs(d, exist_ok=True)
    torch.save(student.state_dict(), os.path.join(d, "student.pt"))
    tok.save_pretrained(d)
    json.dump({"vocab_size": student.emb.num_embeddings, "emb_dim": student.emb.embedding_dim,
               "pad_id": student.emb.padding_idx or 0, "max_len": args.max_len},
              open(os.path.join(d, "config.json"), "w", encoding="utf-8"))
    print("KD-BiLSTM saved to", d)
