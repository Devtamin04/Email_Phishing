"""Section 3.2 / 3.2.1 / 3.2.2 - corpus analysis tools.

* semantic proximity : average TF-IDF cosine similarity of every phishing email to all
                       legitimate emails (Fig. 2: original vs LLM-generated phishing)
* phishing-level     : question-driven scoring - each question is a soft signal, weighted
                       by its alignment with the ground truth, aggregated into one score
                       used to filter low-confidence synthetic samples
* deduplication      : remove near-duplicate emails by TF-IDF cosine similarity
"""
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score

from .text import clean_html


# ---------------------------------------------------------------------------------------
# Fig. 2 - similarity of phishing emails to legitimate emails
# ---------------------------------------------------------------------------------------
def similarity_to_legit(df: pd.DataFrame) -> pd.DataFrame:
    """Vocabulary is built over *all* emails; returns one row per phishing email with its
    average cosine similarity to the legitimate set (TF-IDF rows are L2-normalised, so the
    mean of dot products with the legit matrix = mean of row @ legit_centroid)."""
    vec = TfidfVectorizer(preprocessor=clean_html, stop_words="english")
    X = vec.fit_transform(df.text)
    legit = X[(df.label == 0).to_numpy()]
    centroid = np.asarray(legit.mean(axis=0)).ravel()
    phish_mask = (df.label == 1).to_numpy()
    sims = X[phish_mask] @ centroid
    out = df.loc[phish_mask, ["source"]].copy()
    out["avg_cosine_to_legit"] = sims
    return out


# ---------------------------------------------------------------------------------------
# 3.2.1 - question-driven phishing-level scoring
# ---------------------------------------------------------------------------------------
QUESTIONS = {
    "urgency": "Does this email convey a sense of urgency or panic? Answer 0-100.",
    "flattery": "How much flattery is present in this email? Answer 0-100.",
    "link_suspicion": "How suspicious is the embedded link? Answer 0-100.",
    "marketing": "How closely does this email resemble a marketing message? Answer 0-100.",
    "personal_details": "Does the email address the recipient by name or include overly "
                        "specific details? Answer 0-100.",
    "authority": "To what extent does the message imply consequences for inaction "
                 "(authority)? Answer 0-100.",
    "account_update": "Does the email request account updates or signature actions via a "
                      "link? Answer 0-100.",
    "click_pressure": "How strongly does the email pressure the recipient to click a link "
                      "urgently? Answer 0-100.",
    "scarcity": "Does the email suggest that an offer or opportunity is limited? Answer 0-100.",
}


class LLMQuestionScorer:
    """Asks every question to an LLM (`llm_fn(prompt) -> str`) and parses a 0-100 number."""

    def __init__(self, llm_fn):
        self.llm_fn = llm_fn

    def score(self, email: str) -> dict:
        res = {}
        for k, q in QUESTIONS.items():
            ans = self.llm_fn(f"{q}\nReply with a single number only.\n\nEMAIL:\n{email}")
            m = re.search(r"\d+(\.\d+)?", ans)
            res[k] = min(float(m.group()), 100.0) if m else 0.0
        return res


_LEX = {
    "urgency": r"urgent|immediately|now|today|expires?|within \d+ hours|asap|time-sensitive",
    "flattery": r"congratulations|valued|winner|selected|lucky|exclusive",
    "link_suspicion": r"https?://\S*(verify|login|secure|update|account|bit\.ly)\S*|click here",
    "marketing": r"offer|free|discount|prize|gift|deal|subscription",
    "personal_details": r"\bhi [A-Z][a-z]+|dear [A-Z][a-z]+|as the .* for",
    "authority": r"suspend|closed|deleted|terminated|penalty|returned|restricted|on hold",
    "account_update": r"verify|confirm|update|validate|credentials|password|bank details",
    "click_pressure": r"click|link|portal|follow",
    "scarcity": r"expires?|limited|last chance|only \d+|final",
}


class HeuristicQuestionScorer:
    """Offline stand-in for the LLM: each 'answer' = keyword hits mapped to 0-100."""

    def score(self, email: str) -> dict:
        return {k: min(100.0, 35.0 * len(re.findall(p, email, flags=re.I)))
                for k, p in _LEX.items()}


def phishing_level(df: pd.DataFrame, scorer, labels=None):
    """Returns (per-email answers + composite score, per-question weights).

    Weight of a question = its discriminative power w.r.t. the ground truth
    (AUC - 0.5, clipped at 0), so prompts aligned with phishing count more (cf. Fig. 3).
    """
    answers = pd.DataFrame([scorer.score(t) for t in df.text], index=df.index)
    labels = df.label if labels is None else labels
    weights = {}
    for k in answers:
        try:
            weights[k] = max(roc_auc_score(labels, answers[k]) - 0.5, 0.0)
        except ValueError:  # single class
            weights[k] = 1.0
    w = pd.Series(weights)
    w = w / w.sum() if w.sum() > 0 else pd.Series(1 / len(w), index=w.index)
    answers["phishing_level"] = answers[w.index] @ w
    return answers, w


def filter_low_confidence(df: pd.DataFrame, levels: pd.Series, thr: float = 20.0):
    """Drops synthetic *phishing* samples whose phishing-level score is below `thr`."""
    keep = ~((df.source == "gen") & (df.label == 1) & (levels < thr))
    return df[keep].reset_index(drop=True)


# ---------------------------------------------------------------------------------------
# 3.2.2 - near-duplicate removal
# ---------------------------------------------------------------------------------------
def deduplicate(df: pd.DataFrame, thr: float = 0.9, chunk: int = 2000) -> pd.DataFrame:
    """Greedy: keep an email unless it is >= thr cosine-similar to an earlier kept email."""
    X = TfidfVectorizer(preprocessor=clean_html).fit_transform(df.text)
    n = X.shape[0]
    drop = np.zeros(n, dtype=bool)
    for s in range(0, n, chunk):
        S = (X[s:s + chunk] @ X.T).tocsr()
        for i in range(S.shape[0]):
            gi = s + i
            if drop[gi]:
                continue
            row = S.getrow(i)
            dup = row.indices[(row.data >= thr) & (row.indices > gi)]
            drop[dup] = True
    return df[~drop].reset_index(drop=True)
