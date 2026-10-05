"""Text analysis: persuasion cues (explainable lexicon, vi + en) + a learned text model.

Text models (same interface: predict_proba(texts) -> P(phishing), explain(text) -> words):
  * KDTextModel     - the paper's distilled BiLSTM + multi-head attention (phishkd), explained
                      by the attention each word receives
  * LinearTextModel - TF-IDF + logistic regression, explained by per-word contributions
"""
import json
import os
import re

import numpy as np

from .evidence import Evidence

CUES = {
    "urgency": ("Tạo áp lực thời gian", 0.15, [],
                r"khẩn( cấp)?|ngay lập tức|ngay hôm nay|trước \d{1,2}h\d*( hôm nay)?|trong vòng \d+ "
                r"(giờ|phút|ngày)|hạn chót|\bgấp\b|hết hạn|sớm nhất|số lượng có hạn|chỉ còn \d+|"
                r"urgent|immediately|within \d+ hours|expires?\b|act now|\basap\b|final (notice|warning)",
                "Kẻ gian tạo cảm giác gấp để bạn hành động trước khi kịp suy nghĩ."),
    "threat": ("Đe dọa hậu quả", 0.2, [],
               r"bị khóa|khóa (tài khoản|thẻ)|tạm khóa|đình chỉ|vô hiệu hóa|xóa vĩnh viễn|bị hủy|"
               r"cấm thi|mất quyền|cảnh cáo|kỷ luật|phí phạt|bị phạt|suspend(ed)?|terminated|"
               r"will be (deleted|closed)|locked|penalty|legal action",
               "Đe dọa (khóa tài khoản, cấm thi, phạt) là đòn tâm lý phổ biến nhất."),
    "reward": ("Dụ dỗ bằng lợi ích", 0.15, ["scam"],
               r"chúc mừng|trúng thưởng|quà tặng|\btặng \d|miễn phí|hoàn tiền|học bổng|phần thưởng|"
               r"được chọn|may mắn|thu nhập [\d.]+|congratulations|winner|\bprize\b|gift card|"
               r"\bfree\b|reward|refund",
               "Lời hứa có lợi bất ngờ (học bổng, quà, việc nhẹ lương cao) cần được kiểm chứng qua "
               "kênh chính thức."),
    "credential": ("Yêu cầu đăng nhập / cung cấp thông tin", 0.25, ["credential_harvest"],
                   r"mật khẩu|đăng nhập|xác (minh|thực|nhận)( lại)? (thông tin|tài khoản)|xác minh|"
                   r"mã otp|\botp\b|cập nhật (thông tin|số tài khoản)|số cccd|\bcccd\b|số thẻ|"
                   r"tên đăng nhập|password|log ?in\b|sign ?in\b|verify your|credentials|"
                   r"account information",
                   "Tổ chức uy tín không yêu cầu bạn nhập mật khẩu/OTP qua liên kết trong email."),
    "payment": ("Yêu cầu chuyển tiền / thanh toán", 0.25, ["payment_fraud"],
                r"chuyển khoản|chuyển tiền|chuyển gấp|thanh toán|đóng phí|nộp tiền|số tài khoản|"
                r"tài khoản mới|thẻ cào|mã thẻ|phí vận chuyển|phí giữ chỗ|tạm ứng|wire transfer|"
                r"bank details|gift cards?|payment",
                "Mọi yêu cầu chuyển tiền qua email cần xác minh trực tiếp bằng kênh khác."),
    "secrecy": ("Yêu cầu giữ bí mật / né xác minh", 0.3, ["payment_fraud"],
                r"giữ kín|bí mật|không trao đổi qua điện thoại|đang họp|không nghe máy|không tiện "
                r"nghe|đừng (gọi|nói)|keep (this )?confidential|in a meeting|don'?t call",
                "'Đang họp, đừng gọi, giữ bí mật' là dấu hiệu kinh điển của lừa đảo mạo danh "
                "lãnh đạo/thầy cô."),
    "risky_action": ("Hướng dẫn thao tác nguy hiểm", 0.25, ["malware"],
                     r"enable (content|editing|macros?)|bật (macro|enable)|giải nén|quét (mã )?qr|"
                     r"scan the qr|tải (hóa đơn|tệp|file)|download the attached|open the attached",
                     "Bật macro, giải nén tệp có mật khẩu hay quét QR lạ có thể dẫn tới mã độc "
                     "hoặc trang giả."),
    "generic": ("Lời chào chung chung", 0.08, [],
                r"kính gửi quý khách|dear (customer|user|client|member)|kính gửi người dùng",
                "Email hàng loạt thường không gọi đúng tên bạn."),
}
_CUE_RE = {k: re.compile(v[3], re.I) for k, v in CUES.items()}
_REASSURE = re.compile(r"không bao giờ yêu cầu|không cần thực hiện thêm|never ask", re.I)


def find_cues(text):
    """-> {cue: [matched phrases]}, [(start, end, cue)]"""
    found, spans = {}, []
    for k, rx in _CUE_RE.items():
        for m in rx.finditer(text or ""):
            found.setdefault(k, []).append(m.group(0))
            spans.append((m.start(), m.end(), k))
    return found, spans


# ---------------------------------------------------------------------------------------
# Text models
# ---------------------------------------------------------------------------------------
_URL = re.compile(r"(?:https?://|www\.)\S+", re.I)
_MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def model_text(t):
    """Links/addresses are judged by the link & sender analyzers; masking them keeps the text
    model on *language* and stops it from learning domain-name shortcuts."""
    return _MAIL.sub(" EMAILADDR ", _URL.sub(" WEBLINK ", t or ""))


class LinearTextModel:
    name = "TF-IDF + Logistic Regression"

    def fit(self, texts, labels):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                   token_pattern=r"(?u)\b\w\w+\b")
        X = self.vec.fit_transform([model_text(t) for t in texts])
        self.clf = LogisticRegression(C=4.0, max_iter=2000, class_weight="balanced").fit(X, labels)
        return self

    def predict_proba(self, texts):
        return self.clf.predict_proba(self.vec.transform([model_text(t) for t in texts]))[:, 1]

    def explain(self, text, k=8):
        x = self.vec.transform([model_text(text)])
        contrib = x.data * self.clf.coef_[0][x.indices]
        names = self.vec.get_feature_names_out()[x.indices]
        order = np.argsort(-contrib)
        return [(names[i], float(contrib[i])) for i in order[:k] if contrib[i] > 0]

    def save(self, path):
        import joblib
        joblib.dump({"vec": self.vec, "clf": self.clf}, path)

    @classmethod
    def load(cls, path):
        import joblib
        m, d = cls(), joblib.load(path)
        m.vec, m.clf = d["vec"], d["clf"]
        return m


class KDTextModel:
    """Loads a student saved by scripts/train_text_models.py --kd."""
    name = "KD-BiLSTM + Multi-Head Attention (kế thừa từ bài báo)"

    def __init__(self, path, max_len=256):
        import torch
        from transformers import AutoTokenizer

        from phishkd.models import KDStudent
        cfg = json.load(open(os.path.join(path, "config.json")))
        self.tok = AutoTokenizer.from_pretrained(path)
        self.model = KDStudent(cfg["vocab_size"], cfg["emb_dim"], pad_id=cfg["pad_id"])
        self.model.load_state_dict(torch.load(os.path.join(path, "student.pt"), map_location="cpu"))
        self.model.eval()
        self.max_len, self.torch = max_len, torch

    def _enc(self, texts):
        return self.tok([model_text(t) for t in texts], truncation=True, max_length=self.max_len, padding=True,
                        return_tensors="pt")

    def predict_proba(self, texts):
        out = []
        with self.torch.no_grad():
            for i in range(0, len(texts), 64):
                e = self._enc(texts[i:i + 64])
                z = self.model(e["input_ids"], e["attention_mask"])
                out.append(z.softmax(-1)[:, 1])
        return self.torch.cat(out).numpy() if out else np.zeros(0)

    def explain(self, text, k=8):
        """Attention received by each word (mean over heads and query positions), mapped back
        to the original (accented) words via the tokenizer's offset mapping."""
        m, src = self.model, model_text(text)
        e = self.tok([src], truncation=True, max_length=self.max_len, return_tensors="pt",
                     return_offsets_mapping=True)
        ids, mask = e["input_ids"], e["attention_mask"].bool()
        with self.torch.no_grad():
            h, _ = m.rnn(m.emb(ids))
            _, attn = m.attn(h, mask, return_attn=True)
        score = attn[0].mean(0).mean(0).numpy()
        toks = self.tok.convert_ids_to_tokens(ids[0])
        spans = []  # [start, end, score] per word
        for tok, (a, b), s in zip(toks, e["offset_mapping"][0].tolist(), score):
            if tok in self.tok.all_special_tokens or a == b:
                continue
            if tok.startswith("##") and spans:
                spans[-1][1], spans[-1][2] = b, spans[-1][2] + s
            else:
                spans.append([a, b, s])
        words = {}
        for a, b, s in spans:
            w = src[a:b].lower()
            if len(w) > 2 and w.isalnum() and w not in ("weblink", "emailaddr"):
                words[w] = max(words.get(w, 0), float(s))
        return sorted(words.items(), key=lambda x: -x[1])[:k]


def load_text_model(model_dir="models", prefer="kd"):
    kd, lin = os.path.join(model_dir, "kd_bilstm"), os.path.join(model_dir, "linear.joblib")
    if prefer == "kd" and os.path.exists(os.path.join(kd, "student.pt")):
        return KDTextModel(kd)
    if os.path.exists(lin):
        return LinearTextModel.load(lin)
    return None


# ---------------------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------------------
def analyze_text(text, model=None, where="nội dung email"):
    """-> (evidences, spans, model_info)"""
    ev, info = [], None
    text = (text or "").strip()
    if not text:
        return ev, [], info
    found, spans = find_cues(text)
    reassured = bool(_REASSURE.search(text))
    for k, phrases in found.items():
        label, s, tags, _, tip = CUES[k]
        if reassured and k in ("credential", "reward"):
            s *= 0.3
        uniq = list(dict.fromkeys(p.lower() for p in phrases))
        ev.append(Evidence("content", label, "Cụm từ: " + ", ".join(f"“{p}”" for p in uniq[:6]),
                           s, tip, where, list(tags)))
    if reassured:
        ev.append(Evidence("content", "Có lời nhắc an toàn",
                           "Email nhắc rằng tổ chức không yêu cầu cung cấp thông tin qua email.",
                           good=True, source=where))
    if model is not None:
        p = float(model.predict_proba([text])[0])
        words = model.explain(text)
        info = {"model": model.name, "prob": p, "top_words": [w for w, _ in words]}
        if p >= 0.5:
            ev.append(Evidence(
                "content", f"Mô hình AI đánh giá nội dung giống lừa đảo ({p:.0%})",
                f"Mô hình: {model.name}. Từ ngữ được chú ý nhiều nhất: "
                + ", ".join(w for w, _ in words[:6]),
                0.15 + 0.5 * (p - 0.5) * 2,
                "Mô hình học từ nhiều email lừa đảo (kể cả email do AI viết lại) nên nhận ra văn "
                "phong và ngữ cảnh đáng ngờ dù không có từ khóa lộ liễu.", where))
        elif p < 0.3:
            ev.append(Evidence("content", f"Mô hình AI đánh giá nội dung bình thường ({p:.0%})",
                               f"Mô hình: {model.name}.", good=True, source=where))
    return ev, spans, info
