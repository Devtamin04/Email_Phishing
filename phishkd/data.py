"""Corpus handling (Section 3) and the five train/test scenarios (Section 5.2).

Unified corpus format (CSV): text,label,source
    label  : 1 = phishing, 0 = legitimate
    source : "orig" (real-world: Cambridge, Nazario, Chakraborty, Phishing Pot, Enron)
             "gen"  (LLM-generated / rewritten samples)

The real datasets are not redistributed here; `make_toy_corpus` builds a small synthetic
corpus with the same structure so the pipeline can be run end-to-end.
"""
import random

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

from .augment import COMPANIES, NAMES, PROJECTS, RuleAugmenter, augment_corpus

SCENARIOS = ("orig-orig", "gen-gen", "orig-gen", "gen-orig", "mixture")


def load_corpus(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    assert {"text", "label", "source"} <= set(df.columns), "need columns text,label,source"
    df = df.dropna(subset=["text"]).reset_index(drop=True)
    df["label"] = df["label"].astype(int)
    return df


# ---------------------------------------------------------------------------------------
# Toy corpus
# ---------------------------------------------------------------------------------------
_PHISH = [
    "Dear customer, your {svc} account has been suspended due to unusual activity. Click here "
    "to verify your password immediately or your account will be closed within {n} hours!",
    "URGENT: Security alert from {svc}. We detected a login from {country}. Verify your "
    "account now at {url} to avoid permanent suspension!!!",
    "Congratulations! You are the winner of a ${amt} gift card. Click here to claim your free "
    "prize. Act now, offer expires in {n} hours!",
    "Your {svc} invoice #{inv} is overdue. Update your bank details at {url} immediately to "
    "avoid a late penalty of ${amt}.",
    "Final warning: your mailbox storage is full. Click here to verify your password and "
    "upgrade your quota or all incoming email will be deleted.",
    "Dear user, the IT helpdesk requires you to update your login credentials. Your password "
    "expires today. Click here: {url}",
    "We could not deliver your package #{inv}. Pay the ${amt} customs fee at {url} or the "
    "parcel will be returned. Act now!",
    "Your {svc} payment was declined. Verify your card information immediately at {url} to "
    "keep your subscription active.",
]
_LEGIT = [
    "Hi team, the meeting about {proj} is moved to {day} at {hour}. Please bring the latest "
    "figures. Thanks, {name}",
    "Hello {name}, attached are the minutes from yesterday's discussion on {proj}. Let me "
    "know if I missed anything.",
    "Reminder: the office will be closed on {day} for maintenance. Remote work is encouraged. "
    "Facilities team",
    "Hi {name}, could you review the draft report for {proj} before {day}? Comments in the "
    "shared document are fine.",
    "Thanks for joining the {proj} kickoff. Next steps: finalize the scope and share the "
    "timeline by {day}.",
    "Lunch & learn on {day} at {hour}: an overview of {proj}. Snacks provided, no "
    "registration needed.",
    "Hi {name}, the contract with {comp} was signed today. Legal will circulate the final "
    "copy next week.",
    "Quarterly newsletter: highlights from {proj}, new hires in the {dept} team and upcoming "
    "events.",
]
_GEN_LEGIT_TOPICS = [
    "Hi {name}, following up on {proj}: I have updated the tracker and flagged two open "
    "items for the {dept} team. Happy to walk through them on {day}. Best, {sender}",
    "Hello {name}, as discussed with your manager, please find the agenda for the {proj} "
    "review on {day} at {hour}. No action needed beforehand. Regards, {sender} - {comp}",
    "Hi {name}, a quick note to confirm that the {dept} budget for {proj} was approved. "
    "Finance will share the breakdown in the usual channel. Thanks, {sender}",
    "Dear {name}, thank you for your feedback on {proj}. We incorporated your comments and "
    "will present the revised plan on {day}. Kind regards, {sender}",
]
_FILL = dict(
    svc=["PayPal", "Microsoft 365", "Netflix", "Amazon", "DHL", "Apple ID", "Chase", "Dropbox"],
    country=["Russia", "Brazil", "Nigeria", "China", "Romania"],
    url=["http://secure-login.verify-acct.com", "http://bit.ly/x9k2", "http://update-info.net/login",
         "http://account-check.co/auth"],
    day=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    hour=["9am", "10:30", "2pm", "4pm"],
    dept=["finance", "HR", "engineering", "sales", "legal"],
    name=[n.split()[0] for n in NAMES], sender=NAMES, proj=PROJECTS, comp=COMPANIES,
)


def _fill(tpl, rng):
    vals = {k: rng.choice(v) for k, v in _FILL.items()}
    vals.update(n=rng.randint(2, 72), amt=rng.randint(50, 5000), inv=rng.randint(10000, 99999))
    return tpl.format(**vals)


def make_toy_corpus(n_orig: int = 600, n_gen: int = 600, phish_ratio: float = 0.5,
                    seed: int = 42, augmenter=None) -> pd.DataFrame:
    rng = random.Random(seed)
    augmenter = augmenter or RuleAugmenter(seed)
    rows = []
    n_op = int(n_orig * phish_ratio)
    rows += [(_fill(rng.choice(_PHISH), rng), 1, "orig", "") for _ in range(n_op)]
    rows += [(_fill(rng.choice(_LEGIT), rng), 0, "orig", "") for _ in range(n_orig - n_op)]
    # Gen: phishing seeds rewritten with paraphrase / masking / personalization
    n_gp = int(n_gen * phish_ratio)
    seeds = [_fill(rng.choice(_PHISH), rng) for _ in range(n_gp)]
    for r in augment_corpus(seeds, augmenter, seed=seed):
        rows.append((r["text"], 1, "gen", r["behaviour"]))
    rows += [(_fill(rng.choice(_GEN_LEGIT_TOPICS + _LEGIT), rng), 0, "gen", "")
             for _ in range(n_gen - n_gp)]
    df = pd.DataFrame(rows, columns=["text", "label", "source", "behaviour"])
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


# ---------------------------------------------------------------------------------------
# Scenarios + 5-fold CV with a 72 / 8 / 20 train / val / test partition
# ---------------------------------------------------------------------------------------
def scenario_folds(df: pd.DataFrame, scenario: str, n_folds: int = 5, val_frac: float = 0.1,
                   seed: int = 42):
    """Yields (fold, train_df, val_df, test_df).

    In-distribution (orig-orig, gen-gen, mixture): stratified K-fold over one pool; each fold
    holds out 20% as test and 10% of the rest (8% overall) as validation.
    Cross-distribution (orig-gen, gen-orig): K-fold run in parallel over both pools - train
    and validate on the train-domain folds, test on the matching fold of the other domain.
    """
    tr_src, te_src = {
        "orig-orig": ("orig", "orig"), "gen-gen": ("gen", "gen"),
        "orig-gen": ("orig", "gen"), "gen-orig": ("gen", "orig"),
        "mixture": (None, None),
    }[scenario]
    pick = lambda s: df if s is None else df[df.source == s]  # noqa: E731
    pool_tr = pick(tr_src).reset_index(drop=True)
    pool_te = pick(te_src).reset_index(drop=True)
    skf = StratifiedKFold(n_folds, shuffle=True, random_state=seed)
    folds_tr = list(skf.split(pool_tr, pool_tr.label))
    folds_te = folds_tr if tr_src == te_src else list(skf.split(pool_te, pool_te.label))
    for k in range(n_folds):
        tr_idx, _ = folds_tr[k]
        _, te_idx = folds_te[k]
        tr = pool_tr.iloc[tr_idx]
        tr, va = train_test_split(tr, test_size=val_frac, stratify=tr.label, random_state=seed)
        yield k, tr.reset_index(drop=True), va.reset_index(drop=True), \
            pool_te.iloc[te_idx].reset_index(drop=True)


def set_seed(seed: int):
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
