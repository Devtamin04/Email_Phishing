"""Robustness of phishing detectors against LLM rewriting and modality shifting.

Seeds come from *held-out* templates (never seen in training). Every phishing seed is turned
into 6 variants; legitimate seeds get the same carriers to measure false alarms. Sender
headers are held neutral so that only the content carrier changes.

Detectors
  text-only  : P(phishing) of the text model on the email body           (threshold 0.5)
  PhishLens  : full multimodal pipeline (OCR, QR, attachments, links)     (score >= 50)

    python scripts/robustness_eval.py --n 30
"""
import argparse
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd  # noqa: E402

from phishlens.content import KDTextModel, LinearTextModel  # noqa: E402
from phishlens.engine import analyze  # noqa: E402
from phishlens.parser import EmailDoc, Part, extract_urls  # noqa: E402
from phishlens.samples import FONT_PATHS, notice_image  # noqa: E402
from phishlens.synth import REWRITES, make_vi_corpus  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=30, help="phishing and legit seeds each")
ap.add_argument("--seed", type=int, default=3)
ap.add_argument("--out", default="results/robustness")
ap.add_argument("--from-csv", action="store_true", help="only recompute the summary")
args = ap.parse_args()
rng = random.Random(args.seed)

TRANSFORMS = [
    ("orig", "Gốc (văn bản)", "email lừa đảo nguyên bản trong thân thư"),
    ("llm", "LLM viết lại", "paraphrase + masking + personalization"),
    ("image", "Chuyển vào ảnh", "nội dung (đã viết lại) được đặt trong ảnh, thân thư gần như trống"),
    ("qr", "Ảnh + mã QR", "như trên, liên kết được giấu trong mã QR"),
    ("docx", "Tệp Word đính kèm", "nội dung nằm trong tệp .docx (không macro)"),
    ("html", "Tệp HTML đính kèm", "nội dung nằm trong tệp .html (không có form)"),
]
URL_RX = re.compile(r"(?:https?://|www\.)\S+")
QR_URLS = ["http://m365-dhdemo.verify-login.click/auth", "http://portal-sinhvien.click/dang-nhap"]
LEGIT_QR = "https://dhdemo.edu.vn/thong-bao"
SENDER = ("Văn phòng", "vanphong@mail-notify.org")


def docx_bytes(text):
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", '<?xml version="1.0"?><w:document xmlns:w="http://schemas.'
                   'openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
                   + text.replace("&", "&amp;").replace("<", "&lt;") + "</w:t></w:r></w:p>"
                   "</w:body></w:document>")
    return buf.getvalue()


def make_doc(text, kind, phish):
    """Builds an EmailDoc carrying `text` with the given carrier."""
    doc = EmailDoc(subject="Thông báo", from_name=SENDER[0], from_addr=SENDER[1])
    if kind in ("orig", "llm"):
        doc.text = text
    elif kind in ("image", "qr"):
        doc.text = "Thông báo chi tiết trong ảnh bên dưới."
        body, qr = text, None
        if kind == "qr":
            urls = URL_RX.findall(text)
            body = URL_RX.sub("(quét mã QR bên dưới)", text)
            qr = urls[0] if urls else (rng.choice(QR_URLS) if phish else LEGIT_QR)
        doc.images = [Part("thongbao.png", "image/png", notice_image("THÔNG BÁO", [body], qr=qr))]
    elif kind == "docx":
        doc.text = "Thông tin chi tiết trong tệp đính kèm."
        doc.attachments = [Part("ThongBao.docx", "application/vnd.openxmlformats-officedocument."
                                "wordprocessingml.document", docx_bytes(text))]
    elif kind == "html":
        doc.text = "Thông tin chi tiết trong tệp đính kèm."
        doc.attachments = [Part("ThongBao.html", "text/html",
                                f"<html><body><p>{text}</p></body></html>".encode())]
    doc.links = extract_urls(doc.text, "body")
    return doc


def body_text(text, kind):
    return text if kind in ("orig", "llm") else make_doc(text, kind, True).text


def main():
    assert any(os.path.exists(p) for p in FONT_PATHS), "need a Vietnamese-capable font"
    models = {"linear": LinearTextModel.load("models/linear.joblib")}
    if os.path.exists("models/kd_bilstm/student.pt"):
        models["kd"] = KDTextModel("models/kd_bilstm")
    dets = []
    for k, m in models.items():
        short = "KD-BiLSTM" if k == "kd" else "TF-IDF"
        dets.append({"key": f"text_{k}", "label": f"Chỉ văn bản – {short}", "short": f"VB/{short}",
                     "model": k, "full": False})
    for k, m in models.items():
        short = "KD-BiLSTM" if k == "kd" else "TF-IDF"
        dets.append({"key": f"full_{k}", "label": f"PhishLens đa kênh – {short}",
                     "short": f"ĐK/{short}", "model": k, "full": True})

    if args.from_csv:
        return summarize(pd.read_csv(args.out + ".csv"), dets)
    held = make_vi_corpus(n_per_template=60, seed=args.seed, split="heldout")
    phish = held[(held.label == 1) & (held.source == "orig")].sample(args.n, random_state=args.seed)
    legit = held[held.label == 0].sample(args.n, random_state=args.seed)
    print(f"held-out templates: phishing {sorted(phish.template.unique())}, "
          f"legit {sorted(legit.template.unique())}")

    rows = []
    t0 = time.time()
    for label, seeds in ((1, phish), (0, legit)):
        for _, r in seeds.iterrows():
            base = r.text
            rewritten = base
            for c in ("paraphrase", "masking", "personalization"):
                rewritten = REWRITES[c](rewritten, rng)
            print(f"  label={label} seed {len([1 for x in rows if x['label'] == label]) // (len(TRANSFORMS) * len(dets)) + 1}/{len(seeds)}  ({time.time() - t0:.0f}s)", flush=True)
            for tk, _, _ in TRANSFORMS:
                text = base if tk == "orig" else (rewritten if label == 1 else base)
                doc = make_doc(text, tk, label == 1)
                for d in dets:
                    m = models[d["model"]]
                    if d["full"]:
                        res = analyze(doc, m, use_ocr=True)
                        pred, score = res["score"] >= 50, res["score"]
                    else:
                        p = float(m.predict_proba([doc.subject + "\n\n" + doc.text])[0])
                        pred, score = p >= 0.5, round(100 * p)
                    rows.append({"label": label, "attack": r.attack, "template": r.template,
                                 "transform": tk, "detector": d["key"], "pred": int(pred),
                                 "score": score})
        print(f"label {label} done ({time.time() - t0:.0f}s)")

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out + ".csv", index=False)
    summarize(df, dets)


def summarize(df, dets):
    tpr, fpr = {}, {}
    for tk, _, _ in TRANSFORMS:
        tpr[tk], fpr[tk] = {}, {}
        for d in dets:
            sub = df[(df["transform"] == tk) & (df["detector"] == d["key"])]
            p, n = sub[sub.label == 1], sub[sub.label == 0]
            tpr[tk][d["key"]] = {"rate": p.pred.mean(), "hit": int(p.pred.sum()), "n": len(p)}
            fpr[tk][d["key"]] = {"rate": n.pred.mean(), "hit": int(n.pred.sum()), "n": len(n)}

    findings = []
    tk0 = dets[0]["key"]
    full_keys = [d["key"] for d in dets if d["full"]]
    text_keys = [d["key"] for d in dets if not d["full"]]
    for tk in ("image", "qr", "docx", "html"):
        best_text = max(tpr[tk][k]["rate"] for k in text_keys)
        best_full = max(tpr[tk][k]["rate"] for k in full_keys)
        label = next(l for k, l, _ in TRANSFORMS if k == tk)
        findings.append(f"{label}: mô hình chỉ đọc thân thư phát hiện tối đa {best_text:.0%}, "
                        f"hệ thống đa kênh {best_full:.0%}.")
    findings.append(f"LLM viết lại: chỉ văn bản {tpr['orig'][tk0]['rate']:.0%} → "
                    f"{tpr['llm'][tk0]['rate']:.0%} ({dets[0]['label']}).")
    ph = df[(df.label == 1) & (df["detector"].isin(full_keys))]
    by_att = 1 - ph.groupby("attack").pred.mean()
    names = {"payment": "lừa chuyển tiền / mạo danh (thẻ cào, BEC)", "scam": "dụ dỗ nhận quà",
             "credential": "đánh cắp tài khoản", "malware": "mã độc", "quishing": "QR"}
    worst = by_att.idxmax()
    findings.append(f"Loại khó nhất: {names.get(worst, worst)} - hệ thống đa kênh vẫn bỏ sót "
                    f"{by_att.max():.0%} khi header người gửi bị giữ trung tính (loại này không có "
                    "link/tệp; trong thực tế tín hiệu mạnh nhất là người gửi mạo danh).")
    lg = df[df.label == 0]
    fp = lg.groupby("detector").pred.mean()
    if "full_kd" in fp and "full_linear" in fp:
        findings.append(f"Trên email hợp lệ chưa từng thấy, KD-BiLSTM (tokenizer tiếng Anh, mất dấu "
                        f"tiếng Việt) báo nhầm {fp['full_kd']:.0%} so với {fp['full_linear']:.0%} "
                        "của TF-IDF khi đặt trong hệ đa kênh - cần teacher đa ngôn ngữ (PhoBERT, "
                        "XLM-R) hoặc hiệu chỉnh ngưỡng.")
    worst_fpr = max(fpr[tk][k]["rate"] for tk in fpr for k in full_keys)
    findings.append(f"Báo nhầm cao nhất của hệ thống đa kênh trên email hợp lệ: {worst_fpr:.0%}.")

    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "n_phish": args.n, "n_legit": args.n,
           "detectors": [{k: d[k] for k in ("key", "label", "short")} for d in dets],
           "transforms": [{"key": k, "label": l, "desc": s} for k, l, s in TRANSFORMS],
           "tpr": tpr, "fpr": fpr, "findings": findings,
           "notes": ["Dữ liệu tổng hợp (mẫu tiếng Việt, template giữ lại không dùng để huấn luyện);",
                     "'LLM viết lại' là bộ biến đổi theo luật mô phỏng 3 hành vi trong bài báo;",
                     "thay bằng LLM thật để có kết luận chắc chắn hơn."]}
    json.dump(out, open(args.out + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=float)
    print("\nDetection rate (phishing):")
    print(pd.DataFrame({tk: {d: v["rate"] for d, v in tpr[tk].items()} for tk in tpr}).T.round(2))
    print("\nFalse-positive rate (legit):")
    print(pd.DataFrame({tk: {d: v["rate"] for d, v in fpr[tk].items()} for tk in fpr}).T.round(2))
    print("\n" + "\n".join(findings))


if __name__ == "__main__":
    main()
