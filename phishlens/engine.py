"""Runs every analyzer on an EmailDoc and fuses the evidence into an explainable verdict."""
import html
import time

from . import config
from .content import CUES, analyze_text
from .evidence import CATEGORIES, Evidence, noisy_or
from .media import analyze_attachment, analyze_images
from .sender_links import analyze_links, analyze_sender

ATTACKS = {
    "credential_harvest": "Đánh cắp tài khoản / mật khẩu",
    "payment_fraud": "Lừa chuyển tiền / mạo danh người quen (BEC)",
    "malware": "Phát tán mã độc qua tệp hoặc liên kết",
    "quishing": "Lừa đảo qua mã QR (quishing)",
    "scam": "Dụ dỗ nhận quà / học bổng / việc làm giả",
}
TECHNIQUES = {
    "spoofing": "Giả mạo tên miền người gửi",
    "impersonation": "Mạo danh đơn vị / người có thẩm quyền",
    "evasion": "Né bộ lọc: giấu nội dung vào ảnh, tệp nén có mật khẩu, HTML",
    "quishing": "Giấu liên kết trong mã QR",
}
ADVICE = {
    "credential_harvest": "Nếu lỡ nhập mật khẩu: đổi mật khẩu ngay, bật xác thực 2 lớp và báo "
                          "Phòng CNTT.",
    "payment_fraud": "Gọi trực tiếp cho người được cho là gửi thư (bằng số điện thoại bạn đã biết "
                     "từ trước) để xác minh. Không chuyển tiền, không gửi mã thẻ.",
    "malware": "Không mở tệp, không bật macro, không giải nén. Nếu đã mở: ngắt mạng và báo ngay "
               "bộ phận CNTT.",
    "quishing": "Không quét mã QR trong email yêu cầu đăng nhập hay xác thực tài khoản.",
    "scam": "Kiểm tra thông tin học bổng/quà tặng trên website hoặc văn phòng chính thức của "
            "trường.",
}


def level_of(score):
    for thr, key, label, icon in config.LEVELS:
        if score >= thr:
            return {"key": key, "label": label, "icon": icon}


def _highlight(text, spans, bad_urls):
    marks = sorted(spans, key=lambda s: (s[0], -(s[1] - s[0])))
    for u in bad_urls:
        i = text.find(u)
        while i >= 0:
            marks.append((i, i + len(u), "url"))
            i = text.find(u, i + len(u))
    marks.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    out, pos = [], 0
    for a, b, k in marks:
        if a < pos:
            continue
        out.append(html.escape(text[pos:a]))
        title = "Liên kết đáng ngờ" if k == "url" else CUES[k][0]
        out.append(f'<mark class="cue-{k}" title="{html.escape(title)}">'
                   f"{html.escape(text[a:b])}</mark>")
        pos = b
    out.append(html.escape(text[pos:]))
    return "".join(out)


def analyze(doc, model=None, use_ocr=True):
    t0 = time.perf_counter()
    ev = analyze_sender(doc)

    shown = (f"{doc.subject}\n\n" if doc.subject else "") + (doc.text or "")
    e, spans, model_info = analyze_text(shown, model, "nội dung email")
    ev += e

    e, img_texts, img_links, img_info = analyze_images(doc.images, use_ocr)
    ev += e
    for where, t in img_texts:
        e, _, _ = analyze_text(t, model, where)
        for x in e:
            x.category = "image"
        ev += e
    ocr_len = sum(len(t) for _, t in img_texts)
    if doc.images and len((doc.text or "").strip()) < 150 and (ocr_len > 60 or not use_ocr):
        ev.append(Evidence(
            "image", "Nội dung chính nằm trong ảnh",
            "Phần chữ của email rất ít, thông điệp thật được đặt trong ảnh"
            + (f" (OCR đọc được {ocr_len} ký tự)." if ocr_len else "."),
            0.3, "Đưa chữ vào ảnh là cách né các bộ lọc chỉ đọc văn bản.", "hình ảnh",
            ["evasion"]))

    att_links, att_info = [], []
    for a in doc.attachments:
        e, texts, links, info = analyze_attachment(a.filename, a.data)
        ev += e
        att_links += links
        att_info.append(info)
        for where, t in texts:
            e2, _, _ = analyze_text(t, model, where)
            for x in e2:
                x.category = "attachment"
            ev += e2

    where_map = {"body": "nội dung email", "html": "nội dung email"}
    all_links = doc.links + img_links + att_links
    for l in all_links:
        if l.source.startswith("qr:"):
            where_map[l.source] = f"mã QR trong ảnh {l.source[3:]}"
        elif l.source.startswith("ocr:"):
            where_map[l.source] = f"chữ trong ảnh {l.source[4:]}"
        elif l.source.startswith("att:"):
            where_map[l.source] = f"tệp {l.source[4:]}"
    seen, link_ev = set(), []
    for x in analyze_links(all_links, where_map):
        key = x.detail.split("\n", 1)[0]
        if key not in seen:
            seen.add(key)
            link_ev.append(x)
    ev += link_ev

    risk_ev = [x for x in ev if not x.good]
    cats = {}
    for c in CATEGORIES:
        cats[c] = noisy_or(x.strength for x in risk_ev if x.category == c)
    score = round(100 * noisy_or(cats.values()))
    level = level_of(score)

    tag_w = {}
    for x in risk_ev:
        for t in x.tags:
            tag_w[t] = tag_w.get(t, 0) + x.strength
    attacks = sorted(((k, w) for k, w in tag_w.items() if k in ATTACKS), key=lambda kv: -kv[1])
    techniques = [TECHNIQUES[k] for k in TECHNIQUES if k in tag_w]
    if attacks:  # keep only attack types with substantial support
        attacks = [(k, w) for k, w in attacks if w >= 0.4 * attacks[0][1]][:3]
    if score < 25:
        attacks = []

    risk_ev.sort(key=lambda x: -x.strength)
    recs = []
    if score >= 50:
        recs.append("Không bấm liên kết, không mở tệp đính kèm, không trả lời email này.")
        recs.append("Báo cáo cho Phòng CNTT của trường (chuyển tiếp kèm tệp .eml) rồi xóa email.")
    elif score >= 25:
        recs.append("Kiểm tra kỹ người gửi và liên kết trước khi làm theo yêu cầu; nếu nghi ngờ, "
                    "hỏi lại đơn vị qua kênh chính thức.")
    else:
        recs.append("Chưa thấy dấu hiệu lừa đảo rõ ràng. Vẫn không cung cấp mật khẩu/OTP hoặc "
                    "chuyển tiền chỉ vì một email.")
    recs += [ADVICE[k] for k, _ in attacks[:2]]

    top = [x.title for x in risk_ev[:3]]
    summary = (f"Email được đánh giá **{level['label']}** ({score}/100)."
               + (" Lý do chính: " + "; ".join(top) + "." if top and score >= 25 else ""))
    bad_urls = [x.detail.split("\n", 1)[0] for x in link_ev]
    bad_hosts = {u for u in bad_urls}
    return {
        "score": score, "level": level, "summary": summary,
        "categories": [{"key": c, "label": CATEGORIES[c], "score": round(100 * s)}
                       for c, s in cats.items()],
        "attacks": [{"key": k, "label": ATTACKS[k], "weight": round(w, 2)} for k, w in attacks],
        "techniques": techniques,
        "evidence": [x.to_dict() for x in risk_ev],
        "good": [x.to_dict() for x in ev if x.good],
        "recommendations": recs,
        "model": model_info,
        "email": {
            "subject": doc.subject, "from_name": doc.from_name, "from_addr": doc.from_addr,
            "reply_to": doc.reply_to, "to": doc.to, "date": doc.date,
            "body_html": _highlight(shown, spans, bad_urls).replace("\n", "<br>"),
            "links": [{"href": l.href, "text": l.text, "where": where_map.get(l.source, l.source),
                       "suspicious": l.href in bad_hosts} for l in all_links],
            "images": img_info, "attachments": att_info,
        },
        "elapsed_ms": round(1000 * (time.perf_counter() - t0)),
    }
