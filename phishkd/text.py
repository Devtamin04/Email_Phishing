"""Section 4.1 - Tokenization for the non-distilled baselines (LSTM / BiLSTM / attention).

lowercase -> remove digits -> remove punctuation -> remove stopwords -> token sequence
-> Word2Vec (CBOW, 100-d) dense vectors.
"""
import re

import numpy as np
from gensim.models import Word2Vec
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_HTML = re.compile(r"<[^>]+>")
_DIGITS = re.compile(r"\d+")
_PUNCT = re.compile(r"[^\w\s]|_")
_WS = re.compile(r"\s+")

PAD, UNK = "<pad>", "<unk>"


def clean_html(text: str) -> str:
    """Section 4.7.2 normalisation: strip HTML tags, special chars, extra whitespace."""
    return _WS.sub(" ", _HTML.sub(" ", str(text))).strip()


def preprocess(text: str) -> list[str]:
    text = clean_html(text).lower()
    text = _DIGITS.sub(" ", text)
    text = _PUNCT.sub(" ", text)
    return [t for t in text.split() if t not in ENGLISH_STOP_WORDS and len(t) > 1]


class Word2VecVocab:
    """Trains Word2Vec on the training corpus and maps emails to padded index sequences.

    The embedding matrix is used as a (frozen) input layer, so the model input is the
    sequence matrix X in R^{T x F} with F = 100 as in the paper.
    """

    def __init__(self, dim: int = 100, max_len: int = 200, sg: int = 0, min_count: int = 2,
                 epochs: int = 10, seed: int = 42):
        self.dim, self.max_len, self.sg = dim, max_len, sg
        self.min_count, self.epochs, self.seed = min_count, epochs, seed

    def fit(self, texts):
        sents = [preprocess(t) for t in texts]
        w2v = Word2Vec(sents, vector_size=self.dim, window=5, min_count=self.min_count,
                       sg=self.sg, epochs=self.epochs, seed=self.seed, workers=4)
        self.itos = [PAD, UNK] + list(w2v.wv.index_to_key)
        self.stoi = {w: i for i, w in enumerate(self.itos)}
        emb = np.zeros((len(self.itos), self.dim), dtype=np.float32)
        emb[1] = np.random.default_rng(self.seed).normal(0, 0.1, self.dim)
        emb[2:] = w2v.wv.vectors
        self.embedding_matrix = emb
        return self

    def encode(self, texts) -> np.ndarray:
        out = np.zeros((len(texts), self.max_len), dtype=np.int64)
        for i, t in enumerate(texts):
            ids = [self.stoi.get(w, 1) for w in preprocess(t)][: self.max_len]
            out[i, : len(ids)] = ids
        return out
