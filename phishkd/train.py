"""Training / evaluation loops.

* baselines  : Adam(lr=1e-3), BCE, batch 32, 5 epochs (Table 2)
* teacher    : MobileBERT fine-tuning, AdamW + linear warmup schedule, CE (Sec 4.7.3)
* KD student : Algorithm 1 - frozen teacher, Adam(lr=1e-4), alpha=0.5, tau=2, 3 epochs, batch 32
"""
import copy
import time
from dataclasses import dataclass

import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, TensorDataset
from tqdm.auto import tqdm

from .models import BASELINES, KDStudent, build_teacher, count_params, distillation_loss
from .text import Word2VecVocab, clean_html


@dataclass
class Config:
    batch_size: int = 32
    # baselines
    w2v_dim: int = 100
    w2v_max_len: int = 200
    base_lr: float = 1e-3
    base_epochs: int = 5
    # teacher
    teacher_name: str = "google/mobilebert-uncased"
    bert_max_len: int = 512          # paper: m <= 512; lower it on CPU
    teacher_lr: float = 5e-5
    teacher_epochs: int = 2
    teacher_min_steps: int = 120   # small corpora: add epochs until this many updates
    warmup_frac: float = 0.1
    max_grad_norm: float = 1.0
    # distillation
    kd_lr: float = 1e-4
    kd_epochs: int = 3
    alpha: float = 0.5
    tau: float = 2.0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    verbose: bool = True


def metrics(y_true, y_pred) -> dict:
    return {
        "acc": 100 * accuracy_score(y_true, y_pred),
        "precision": 100 * precision_score(y_true, y_pred, zero_division=0),
        "recall": 100 * recall_score(y_true, y_pred, zero_division=0),
        "f1_weighted": 100 * f1_score(y_true, y_pred, average="weighted", zero_division=0),
    }


def _loader(*tensors, batch_size, shuffle):
    return DataLoader(TensorDataset(*tensors), batch_size=batch_size, shuffle=shuffle)


def _trim(ids, mask):
    """Drop all-padding columns of a batch (dynamic padding)."""
    L = int(mask.sum(1).max().clamp(min=1))
    return ids[:, :L], mask[:, :L]


# ---------------------------------------------------------------------------------------
# Baselines: LSTM / BiLSTM / BiLSTM+SH / BiLSTM+MH
# ---------------------------------------------------------------------------------------
def run_baseline(name, tr, va, te, cfg: Config) -> dict:
    dev = cfg.device
    vocab = Word2VecVocab(cfg.w2v_dim, cfg.w2v_max_len).fit(tr.text.tolist())
    enc = lambda d: torch.as_tensor(vocab.encode(d.text.tolist()))  # noqa: E731
    lab = lambda d: torch.as_tensor(d.label.values, dtype=torch.float32)  # noqa: E731
    model = BASELINES[name](vocab.embedding_matrix).to(dev)
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=cfg.base_lr)

    @torch.no_grad()
    def predict(ids):
        model.eval()
        out = [torch.sigmoid(model(b.to(dev))).cpu()
               for (b,) in _loader(ids, batch_size=256, shuffle=False)]
        return (torch.cat(out) >= 0.5).long().numpy()

    Xtr, ytr, Xva = enc(tr), lab(tr), enc(va)
    best, best_f1 = None, -1.0
    t0 = time.perf_counter()
    for ep in range(cfg.base_epochs):
        model.train()
        for xb, yb in _loader(Xtr, ytr, batch_size=cfg.batch_size, shuffle=True):
            loss = F.binary_cross_entropy_with_logits(model(xb.to(dev)), yb.to(dev))
            opt.zero_grad()
            loss.backward()
            opt.step()
        f1 = f1_score(va.label, predict(Xva), average="weighted")
        if f1 > best_f1:
            best_f1, best = f1, copy.deepcopy(model.state_dict())
    train_time = time.perf_counter() - t0
    model.load_state_dict(best)

    t0 = time.perf_counter()
    pred = predict(enc(te))
    test_time = time.perf_counter() - t0
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"params": trainable, "train_s": train_time, "test_s": test_time,
            **metrics(te.label, pred)}


# ---------------------------------------------------------------------------------------
# Teacher: fine-tune MobileBERT
# ---------------------------------------------------------------------------------------
def tokenize(tok, df, max_len):
    enc = tok([clean_html(t) for t in df.text], truncation=True, max_length=max_len,
              padding="max_length", return_tensors="pt")
    return enc["input_ids"], enc["attention_mask"]


@torch.no_grad()
def predict_logits(model, ids, mask, cfg: Config, is_hf: bool):
    model.eval()
    out = []
    for i, m in _loader(ids, mask, batch_size=64, shuffle=False):
        i, m = _trim(i, m)
        z = model(input_ids=i.to(cfg.device), attention_mask=m.to(cfg.device))
        out.append((z.logits if is_hf else z).float().cpu())
    return torch.cat(out)


def train_teacher(tr, va, cfg: Config):
    from transformers import get_linear_schedule_with_warmup
    tok, model = build_teacher(cfg.teacher_name)
    model.to(cfg.device)
    ids, mask = tokenize(tok, tr, cfg.bert_max_len)
    y = torch.as_tensor(tr.label.values)
    vids, vmask = tokenize(tok, va, cfg.bert_max_len)
    dl = _loader(ids, mask, y, batch_size=cfg.batch_size, shuffle=True)
    epochs = max(cfg.teacher_epochs, -(-cfg.teacher_min_steps // len(dl)))
    steps = len(dl) * epochs
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.teacher_lr)
    sched = get_linear_schedule_with_warmup(opt, int(cfg.warmup_frac * steps), steps)
    best, best_f1 = None, -1.0
    t0 = time.perf_counter()
    for ep in range(epochs):
        model.train()
        for i, m, yb in tqdm(dl, desc=f"teacher ep{ep + 1}", disable=not cfg.verbose):
            i, m = _trim(i, m)
            out = model(input_ids=i.to(cfg.device), attention_mask=m.to(cfg.device),
                        labels=yb.to(cfg.device))  # Eq (19): cross-entropy
            opt.zero_grad()
            out.loss.backward()
            # MobileBERT pools the raw [CLS] state (huge magnitude) -> initial loss ~1e7;
            # clipping (HF Trainer default max_grad_norm=1.0) keeps fine-tuning stable
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.max_grad_norm)
            opt.step()
            sched.step()
        vpred = predict_logits(model, vids, vmask, cfg, True).argmax(-1).numpy()
        f1 = f1_score(va.label, vpred, average="weighted")
        if f1 > best_f1:
            best_f1, best = f1, copy.deepcopy(model.state_dict())
    train_time = time.perf_counter() - t0
    model.load_state_dict(best)
    return tok, model, train_time


def evaluate_hf_or_student(model, tok, te, cfg: Config, is_hf: bool) -> dict:
    ids, mask = tokenize(tok, te, cfg.bert_max_len)
    t0 = time.perf_counter()
    pred = predict_logits(model, ids, mask, cfg, is_hf).argmax(-1).numpy()
    test_time = time.perf_counter() - t0
    return {"params": count_params(model), "test_s": test_time, **metrics(te.label, pred)}


# ---------------------------------------------------------------------------------------
# Algorithm 1 - knowledge distillation into BiLSTM + multi-head attention
# ---------------------------------------------------------------------------------------
def distill(teacher, tok, tr, va, cfg: Config, cache_teacher_logits: bool = True):
    dev = cfg.device
    for p in teacher.parameters():                       # 1: freeze teacher
        p.requires_grad_(False)
    teacher.eval()
    student = KDStudent.from_teacher(teacher).to(dev)    # Eq (24)
    opt = torch.optim.Adam(student.parameters(), lr=cfg.kd_lr)  # 2

    ids, mask = tokenize(tok, tr, cfg.bert_max_len)
    y = torch.as_tensor(tr.label.values)
    vids, vmask = tokenize(tok, va, cfg.bert_max_len)
    # The teacher is frozen and in eval mode, so its logits are a deterministic function of
    # the input: computing them once is equivalent to the per-batch forward of Algorithm 1
    # (line 5) and saves (E-1) teacher passes over the training set.
    t0 = time.perf_counter()
    z_t_all = predict_logits(teacher, ids, mask, cfg, True) if cache_teacher_logits else None
    idx = torch.arange(len(y))
    best, best_f1 = None, -1.0
    for ep in range(cfg.kd_epochs):                      # 3
        student.train()
        for (bi,) in tqdm(_loader(idx, batch_size=cfg.batch_size, shuffle=True),  # 4
                        desc=f"distill ep{ep + 1}", disable=not cfg.verbose):
            i, m = _trim(ids[bi], mask[bi])
            i, m, yb = i.to(dev), m.to(dev), y[bi].to(dev)
            if cache_teacher_logits:
                z_t = z_t_all[bi].to(dev)
            else:
                with torch.no_grad():
                    z_t = teacher(input_ids=i, attention_mask=m).logits      # 5
            z_s = student(i, m)                                              # 7
            loss = distillation_loss(z_s, z_t, yb, cfg.alpha, cfg.tau)       # 6, 8-11
            loss.backward()                                                  # 12
            opt.step()                                                       # 13
            opt.zero_grad()                                                  # 14
        vpred = predict_logits(student, vids, vmask, cfg, False).argmax(-1).numpy()
        f1 = f1_score(va.label, vpred, average="weighted")
        if f1 > best_f1:
            best_f1, best = f1, copy.deepcopy(student.state_dict())
    train_time = time.perf_counter() - t0
    student.load_state_dict(best)
    return student, train_time                           # 15


def summarize(rows):
    df = pd.DataFrame(rows)
    num = ["params", "train_s", "test_s", "acc", "precision", "recall", "f1_weighted"]
    return df.groupby(["model", "scenario"], sort=False)[num].mean().round(2).reset_index()

