"""Section 4 - models.

Baselines (Word2Vec input, 1 sigmoid output, BCE):
    LSTMClassifier         - Sec 4.2, Eqs (1)-(4)
    BiLSTMClassifier       - Sec 4.3, Eqs (5)-(7)
    BiLSTMSingleHead       - Sec 4.4/4.5, Eqs (8)-(11)
    BiLSTMMultiHead        - Sec 4.6, Eqs (12)-(15), Table 2 (H=4, D=64 -> 256)
Teacher:
    build_teacher          - Sec 4.7, MobileBERT + 2-way classification head
Student (distilled):
    KDStudent              - Sec 4.8.1: WordPiece ids -> embedding initialised from the
                             teacher -> BiLSTM -> multi-head attention -> residual + LayerNorm
                             -> global average pooling -> dropout -> 2 logits
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


def masked_mean(h, mask):
    m = mask.unsqueeze(-1).type_as(h)
    return (h * m).sum(1) / m.sum(1).clamp(min=1.0)


class MultiHeadAttention(nn.Module):
    """head_i = softmax(X W_i^Q (X W_i^K)^T / sqrt(d_k)) X W_i^V ; Output = Concat(heads) W^O + b^O.
    n_heads=1 gives the single-head attention of Eqs (8)-(9)."""

    def __init__(self, d_in, n_heads=4, d_head=64, d_out=None):
        super().__init__()
        self.h, self.d = n_heads, d_head
        self.q = nn.Linear(d_in, n_heads * d_head)
        self.k = nn.Linear(d_in, n_heads * d_head)
        self.v = nn.Linear(d_in, n_heads * d_head)
        self.o = nn.Linear(n_heads * d_head, d_out or d_in)

    def forward(self, x, mask=None, return_attn=False):
        B, T, _ = x.shape
        split = lambda t: t.view(B, T, self.h, self.d).transpose(1, 2)  # noqa: E731
        q, k, v = split(self.q(x)), split(self.k(x)), split(self.v(x))
        scores = q @ k.transpose(-1, -2) / math.sqrt(self.d)          # (B, h, T, T)
        if mask is not None:
            scores = scores.masked_fill(~mask[:, None, None, :], float("-inf"))
        attn = scores.softmax(-1)
        ctx = (attn @ v).transpose(1, 2).reshape(B, T, self.h * self.d)  # concat heads
        out = self.o(ctx)
        return (out, attn) if return_attn else out


class _W2VBase(nn.Module):
    """Frozen Word2Vec input layer: (B, T) ids -> (B, T, F=100)."""

    def __init__(self, embedding_matrix, freeze=True):
        super().__init__()
        self.emb = nn.Embedding.from_pretrained(torch.as_tensor(embedding_matrix),
                                                freeze=freeze, padding_idx=0)


class LSTMClassifier(_W2VBase):
    def __init__(self, embedding_matrix, hidden=32, dropout=0.5, bidirectional=False):
        super().__init__(embedding_matrix)
        self.rnn = nn.LSTM(self.emb.embedding_dim, hidden, batch_first=True,
                           bidirectional=bidirectional)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden * (2 if bidirectional else 1), 1)

    def forward(self, ids):
        lengths = (ids != 0).sum(1).clamp(min=1).cpu()
        packed = nn.utils.rnn.pack_padded_sequence(self.emb(ids), lengths, batch_first=True,
                                                   enforce_sorted=False)
        _, (h_n, _) = self.rnn(packed)
        h = torch.cat([h_n[-2], h_n[-1]], -1) if self.rnn.bidirectional else h_n[-1]
        return self.fc(self.drop(h)).squeeze(-1)  # logit; sigmoid in the loss


class BiLSTMClassifier(LSTMClassifier):
    def __init__(self, embedding_matrix, hidden=32, dropout=0.5):
        super().__init__(embedding_matrix, hidden, dropout, bidirectional=True)


class BiLSTMAttention(_W2VBase):
    """BiLSTM (Table 2: 128-d output) -> attention -> pooled sentence vector -> dropout -> dense."""

    def __init__(self, embedding_matrix, hidden=64, n_heads=4, d_head=64, dropout=0.5):
        super().__init__(embedding_matrix)
        self.rnn = nn.LSTM(self.emb.embedding_dim, hidden, batch_first=True, bidirectional=True)
        self.attn = MultiHeadAttention(2 * hidden, n_heads, d_head, d_out=2 * hidden)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(2 * hidden, 1)

    def forward(self, ids, return_attn=False):
        mask = ids != 0
        mask[:, 0] |= ~mask.any(1)  # avoid all-masked rows for empty emails
        h, _ = self.rnn(self.emb(ids))
        a, w = self.attn(h, mask, return_attn=True)
        logit = self.fc(self.drop(masked_mean(a, mask))).squeeze(-1)
        return (logit, w) if return_attn else logit


class BiLSTMSingleHead(BiLSTMAttention):
    def __init__(self, embedding_matrix, hidden=64, dropout=0.5):
        super().__init__(embedding_matrix, hidden, n_heads=1, d_head=2 * hidden, dropout=dropout)


class BiLSTMMultiHead(BiLSTMAttention):
    def __init__(self, embedding_matrix, hidden=64, dropout=0.5):
        super().__init__(embedding_matrix, hidden, n_heads=4, d_head=64, dropout=dropout)


BASELINES = {
    "lstm": LSTMClassifier,
    "bilstm": BiLSTMClassifier,
    "bilstm_sh": BiLSTMSingleHead,
    "bilstm_mh": BiLSTMMultiHead,
}


# ---------------------------------------------------------------------------------------
# Teacher & student
# ---------------------------------------------------------------------------------------
TEACHER_NAME = "google/mobilebert-uncased"


def build_teacher(name: str = TEACHER_NAME):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(name, num_labels=2)
    return tok, model


class KDStudent(nn.Module):
    def __init__(self, vocab_size, emb_dim=128, hidden=128, n_heads=4, d_head=64,
                 dropout=0.5, pad_id=0):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=pad_id)
        self.rnn = nn.LSTM(emb_dim, hidden, batch_first=True, bidirectional=True)
        self.attn = MultiHeadAttention(2 * hidden, n_heads, d_head, d_out=2 * hidden)
        self.norm = nn.LayerNorm(2 * hidden)
        self.drop = nn.Dropout(dropout)
        self.fc = nn.Linear(2 * hidden, 2)  # two-logit head for softmax-based distillation

    @classmethod
    def from_teacher(cls, teacher, **kw):
        """Eq (24): E_student = E_teacher (MobileBERT word-piece embedding, V x 128)."""
        E = teacher.get_input_embeddings().weight.detach().clone()
        pad = teacher.config.pad_token_id or 0
        student = cls(E.shape[0], E.shape[1], pad_id=pad, **kw)
        student.emb.weight.data.copy_(E)
        return student

    def forward(self, input_ids, attention_mask):
        mask = attention_mask.bool()
        h, _ = self.rnn(self.emb(input_ids))
        h = self.norm(h + self.attn(h, mask))  # residual normalisation
        return self.fc(self.drop(masked_mean(h, mask)))


def distillation_loss(z_s, z_t, y, alpha=0.5, tau=2.0):
    """Eqs (20)-(23): L = a * CE(y, z_S) + (1 - a) * tau^2 * KL(softmax(z_T/tau) || softmax(z_S/tau))."""
    hard = F.cross_entropy(z_s, y)
    soft = F.kl_div(F.log_softmax(z_s / tau, -1), F.softmax(z_t / tau, -1),
                    reduction="batchmean")
    return alpha * hard + (1 - alpha) * tau ** 2 * soft
