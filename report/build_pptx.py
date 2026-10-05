"""Builds report/TrinhBay_PhishLens.pptx"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slide_kit import *  # noqa: E402,F401,F403

# =============================================================== 1. title
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = PAGE
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(0.25))
band.fill.solid(); band.fill.fore_color.rgb = ACCENT; band.line.fill.background()
textbox(s, Inches(0.9), Inches(2.0), Inches(11.5), Inches(1.2), [(C.TITLE, {"size": 42, "bold": True})])
textbox(s, Inches(0.9), Inches(3.15), Inches(11.5), Inches(1.0), [(C.SUBTITLE, {"size": 22, "color": INK2})])
textbox(s, Inches(0.9), Inches(4.6), Inches(11.5), Inches(1.2),
        [("Bài báo gốc: " + C.PAPER, {"size": 13, "color": MUTED, "italic": True}),
         (f"Người trình bày: {C.AUTHOR}", {"size": 16, "color": INK})])
N[0] += 1

# =============================================================== 2. agenda
s = new_slide("Nội dung trình bày")
items = [("1", "Bài báo gốc", "Bài toán, phương pháp KD-BiLSTM, kết quả"),
         ("2", "Tái hiện bài báo", "Đã làm đến đâu, số liệu đo được, vấn đề gặp phải"),
         ("3", "Bổ sung & nâng cao", "Những gì vượt ra ngoài bài báo"),
         ("4", "Ứng dụng: PhishLens Edu", "Phân tích rủi ro email đa kênh, có giải thích, cho trường học"),
         ("5", "Đánh giá độ bền", "LLM viết lại, chuyển vào ảnh / QR / tệp đính kèm"),
         ("6", "Hạn chế & hướng tiếp theo", "")]
for i, (n, h, d) in enumerate(items):
    y = Inches(1.65 + i * 0.86)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.9), y, Inches(0.55), Inches(0.55))
    c.fill.solid(); c.fill.fore_color.rgb = ACCENT; c.line.fill.background()
    c.text_frame.text = n
    p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size, p.runs[0].font.bold, p.runs[0].font.color.rgb, p.runs[0].font.name = Pt(18), True, CARD, FONT
    textbox(s, Inches(1.7), y - Inches(0.02), Inches(10), Inches(0.7),
            [("", {"parts": [(h, True), (("  —  " + d) if d else "", False)], "size": 18})])

# =============================================================== 3. paper problem
s = new_slide("Bài toán của bài báo", "1 · Bài báo gốc")
bullets(s, Inches(0.6), Inches(1.6), Inches(7.2), Inches(5), [
    ("LLM giúp viết email lừa đảo ", "trôi chảy, lịch sự, cá nhân hóa → bộ lọc dựa trên từ khóa bị qua mặt"),
    ("Transformer phát hiện tốt nhưng nặng ", "→ khó đặt ở mail gateway / thiết bị đầu cuối"),
    ("Mục tiêu: ", "bộ phát hiện nhỏ, nhanh, chạy CPU, vẫn bền trước email do LLM viết lại"),
    ("Dữ liệu: ", "5 bộ thật (~623K email) + email LLM sinh theo 3 hành vi né tránh:"),
    "- Paraphrase: diễn đạt lại để né chữ ký từ khóa",
    "- Masking: làm mềm dấu hiệu lộ liễu thành giọng công sở",
    "- Personalization: chèn tên, chức danh, dự án của người nhận",
])
card_text(s, Inches(8.2), Inches(1.7), Inches(4.5), Inches(2.1), "Phát hiện của tác giả",
          "Email LLM sinh có độ tương đồng TF-IDF với email hợp lệ cao hơn email lừa đảo gốc "
          "(Fig. 2) → khó phát hiện hơn.")
card_text(s, Inches(8.2), Inches(4.0), Inches(4.5), Inches(2.3), "5 kịch bản đánh giá",
          "Orig-Orig, Gen-Gen, Orig-Gen, Gen-Orig, Mixture · 5-fold, chia 72/8/20. "
          "Hai kịch bản chéo đo khả năng tổng quát hóa giữa email người viết và email LLM.")

# =============================================================== 4. paper method
s = new_slide("Phương pháp: từ LSTM đến KD-BiLSTM", "1 · Bài báo gốc")
steps = [("LSTM", "Word2Vec 100d"), ("BiLSTM", "ngữ cảnh 2 chiều"), ("+ Single-head", "chú ý cụm từ"),
         ("+ Multi-head", "H=4, D=64"), ("KD-BiLSTM", "học từ MobileBERT")]
for i, (h, d) in enumerate(steps):
    x = Inches(0.6 + i * 2.5)
    card_text(s, x, Inches(1.7), Inches(2.1), Inches(1.1), h, d,
              head_color=ACCENT if i == 4 else INK, fill=SOFT if i == 4 else CARD)
    if i < 4:
        arrow(s, x + Inches(2.12), Inches(2.1))
card_text(s, Inches(0.6), Inches(3.2), Inches(6.0), Inches(3.4), "Knowledge distillation (Algorithm 1)",
          "Teacher: MobileBERT 25,3M tham số, fine-tune trên dữ liệu hỗn hợp, sau đó đóng băng.\n"
          "Student: BiLSTM + multi-head attention ~4,5M tham số; embedding khởi tạo từ teacher.\n\n"
          "L = α·CE(y, z_S) + (1−α)·τ²·KL(σ(z_T/τ) ‖ σ(z_S/τ))\nα = 0,5 · τ = 2 · Adam lr 1e-4 · 3 epoch · batch 32",
          size=14)
card_text(s, Inches(6.9), Inches(3.2), Inches(5.8), Inches(3.4), "Điểm khác distillation thông thường",
          "1. Teacher được fine-tune trên dữ liệu có cả email LLM.\n"
          "2. Chưng cất khác kiến trúc: transformer → mạng hồi quy.\n"
          "3. Student được kiểm tra khả năng tổng quát hóa chéo phân phối (Orig↔Gen).", size=14)

# =============================================================== 5. paper results
s = new_slide("Kết quả của bài báo (kịch bản Mixture)", "1 · Bài báo gốc")
rows = [("Mô hình", "Tham số", "F1 (%)", "Thời gian test")] + [
    ((m, ACCENT) if "KD" in m else m, p, f, t + " s") for m, p, f, t in C.PAPER_MIXTURE]
table(s, Inches(0.6), Inches(1.6), Inches(7.4), rows, [3.2, 1.2, 1.1, 1.4], size=13, row_h=0.42)
bullets(s, Inches(8.4), Inches(1.6), Inches(4.4), Inches(5), [
    ("KD-BiLSTM kém transformer tốt nhất ", "~1–2,5 điểm F1"),
    ("Đổi lại: ", "nhanh hơn 5–19 lần, nhỏ hơn 20–800 lần"),
    ("Chỉ học email LLM rồi test email thật (Gen-Orig): ", "recall BiLSTM chỉ 51%"),
    ("Multi-head attention ", "cải thiện rõ khả năng tổng quát hóa chéo"),
    ("Lưu ý: ", "dữ liệu & code chưa công bố; nhiều chi tiết kiến trúc không mô tả đủ"),
], size=16)

# =============================================================== 6. repro status
s = new_slide("Đã tái hiện bài báo đến mức nào?", "2 · Tái hiện")
rows = [("Thành phần", "Bài báo", "Bản tái hiện", "Trạng thái")] + [
    (a, b, c, (d, STATUS_COLOR[d])) for a, b, c, d in C.REPRO]
table(s, Inches(0.6), Inches(1.5), Inches(12.2), rows, [3.0, 3.3, 4.6, 1.1], size=11, row_h=0.43)

# =============================================================== 7. repro numbers
s = new_slide("Tái hiện: số liệu đo được", "2 · Tái hiện")
textbox(s, Inches(0.6), Inches(1.45), Inches(6), Inches(0.4), [("Số tham số", {"size": 16, "bold": True})])
table(s, Inches(0.6), Inches(1.9), Inches(5.9),
      [("Mô hình", "Bài báo", "Tái hiện")] + C.PARAMS, [2.6, 1.3, 1.3], size=12, row_h=0.38)
textbox(s, Inches(6.9), Inches(1.45), Inches(6), Inches(0.4),
        [("F1 kịch bản Orig→Gen (người viết → LLM)", {"size": 16, "bold": True})])
table(s, Inches(6.9), Inches(1.9), Inches(5.9),
      [("Mô hình", "Bài báo", "Tái hiện*")] + C.ORIG_GEN, [2.6, 1.3, 1.3], size=12, row_h=0.38)
card_text(s, Inches(0.6), Inches(4.85), Inches(5.9), Inches(1.75), "Tốc độ suy luận: student vs teacher",
          f"Bài báo: {C.SPEED['paper'][0]} so với {C.SPEED['paper'][1]} ({C.SPEED['paper'][2]} nhanh hơn, GPU)\n"
          f"Tái hiện: {C.SPEED['ours'][0]} so với {C.SPEED['ours'][1]} ({C.SPEED['ours'][2]} nhanh hơn, CPU)", size=13)
card_text(s, Inches(6.9), Inches(4.85), Inches(5.9), Inches(1.75), "* Đọc số liệu thế nào",
          "Dữ liệu toy, 1 fold → chỉ để kiểm tra pipeline. Xu hướng khớp bài báo: "
          "chéo phân phối làm giảm điểm, multi-head và KD giúp tổng quát hóa tốt hơn.", size=13)

# =============================================================== 8. repro issues
s = new_slide("Vấn đề gặp phải khi tái hiện & cách khắc phục", "2 · Tái hiện")
rows = [("Hiện tượng", "Nguyên nhân", "Khắc phục")] + C.FIXES
table(s, Inches(0.6), Inches(1.5), Inches(12.2), rows, [3.2, 4.2, 4.2], size=13, row_h=0.75)
textbox(s, Inches(0.6), Inches(5.6), Inches(12.2), Inches(1),
        [("Các chỗ bài báo không mô tả rõ (pooling sau attention, cách chia fold chéo miền, ngưỡng "
          "lọc/khử trùng lặp, prompt sinh dữ liệu) được tự quyết định và ghi lại trong README.",
          {"size": 14, "color": INK2, "italic": True})])

# =============================================================== 9. extras
s = new_slide("Bổ sung & nâng cao so với bài báo", "3 · Bổ sung")
bullets(s, Inches(0.6), Inches(1.6), Inches(7.4), Inches(5.2), C.EXTRAS, size=16)
card_text(s, Inches(8.4), Inches(1.7), Inches(4.4), Inches(2.3), "Tại sao chia template held-out?",
          "Nếu train và test dùng chung cách viết, mô hình đạt ~100% một cách giả tạo. "
          "Giữ lại 1/3 dạng email chưa từng thấy mới đo được khả năng tổng quát hóa thật.", size=13)
card_text(s, Inches(8.4), Inches(4.2), Inches(4.4), Inches(2.3), "Tại sao che URL?",
          "Liên kết đã có bộ phân tích riêng. Che URL buộc mô hình văn bản học ngôn ngữ "
          "thay vì học 'có tên miền = lừa đảo'.", size=13)

# =============================================================== 10. motivation
s = new_slide("Từ bài báo đến ứng dụng: vì sao cần hướng khác?", "4 · Ứng dụng")
probs = [("Trường đã có bộ lọc", "Gmail / Microsoft 365 Defender đã chặn phần lớn lừa đảo phổ biến. "
          "Thêm một bộ phân loại văn bản nữa ít giá trị."),
         ("Email có ảnh và tệp", "Kẻ tấn công giấu thông điệp vào ảnh, mã QR, PDF, HTML, ZIP có mật khẩu. "
          "Mô hình chỉ đọc thân thư không thấy."),
         ("Chỉ trả lời có/không", "Người dùng không biết vì sao email nguy hiểm → lần sau vẫn bị lừa.")]
for i, (h, d) in enumerate(probs):
    card_text(s, Inches(0.6 + i * 4.15), Inches(1.6), Inches(3.9), Inches(2.1), h, d, size=14)
card(s, Inches(0.6), Inches(4.1), Inches(12.2), Inches(2.5), fill=SOFT, line=SOFT)
textbox(s, Inches(0.9), Inches(4.25), Inches(11.7), Inches(2.3), [
    ("Ý tưởng: PhishLens Edu", {"size": 20, "bold": True, "color": ACCENT}),
    ("Không thay thế Gmail/Defender. Là lớp “ý kiến thứ hai có giải thích” cho email đã lọt vào hộp thư:", {"size": 16}),
    ("", {"bullet": True, "parts": [("phân tích đa kênh ", True), ("(người gửi, liên kết, nội dung, ảnh/QR, tệp)", False)], "size": 15}),
    ("", {"bullet": True, "parts": [("mức độ rủi ro 0–100 ", True), ("+ loại tấn công + kỹ thuật né tránh", False)], "size": 15}),
    ("", {"bullet": True, "parts": [("giải thích bằng tiếng Việt + chế độ luyện tập ", True), ("cho sinh viên, cán bộ", False)], "size": 15}),
])

# =============================================================== 11. architecture
s = new_slide("Kiến trúc PhishLens Edu", "4 · Ứng dụng")
flow = [("1. Tách email", ".eml (MIME): header, văn bản/HTML, liên kết, ảnh, tệp"),
        ("2. Phân tích đa kênh", "5 bộ phân tích độc lập, mỗi dấu hiệu có độ mạnh + lời giải thích"),
        ("3. Kết hợp bằng chứng", "Noisy-OR → điểm từng kênh + điểm tổng 0–100, loại tấn công"),
        ("4. Giải thích & hướng dẫn", "Lý do, bài học, tô sáng cụm từ, việc cần làm")]
for i, (h, d) in enumerate(flow):
    x = Inches(0.6 + i * 3.1)
    card_text(s, x, Inches(1.55), Inches(2.75), Inches(1.45), h, d, size=12)
    if i < 3:
        arrow(s, x + Inches(2.77), Inches(2.1), Inches(0.3))
rows = [("Kênh", "Phân tích")] + C.CHANNELS
table(s, Inches(0.6), Inches(3.3), Inches(12.2), rows, [1.6, 10.6], size=13, row_h=0.55, bold_col0=True)

# =============================================================== 12. inherit paper
s = new_slide("Kế thừa bài báo trong PhishLens", "4 · Ứng dụng")
bullets(s, Inches(0.6), Inches(1.6), Inches(6.4), Inches(5), [
    ("Mô hình nội dung = KD-BiLSTM của bài báo ", "(teacher MobileBERT → student 4,4M tham số, chạy CPU)"),
    ("Huấn luyện lại ", "trên email trường học tiếng Việt + email tiếng Anh, có cả bản viết lại kiểu LLM"),
    ("Attention → giải thích: ", "hiển thị các từ mô hình chú ý nhiều nhất (ánh xạ về chữ có dấu)"),
    ("Mô hình chỉ là 1 trong 5 kênh: ", "khi văn bản bị giấu vào ảnh/tệp, các kênh khác bù lại"),
    ("Có mô hình TF-IDF để đối chiếu ", "(chọn được trên giao diện)"),
], size=16)
picture(s, IMG("c_qr_evidence.png"), Inches(7.3), Inches(1.55), Inches(5.5), Inches(5.3))

# =============================================================== 13-15. demos
s = new_slide("Demo: email chỉ có ảnh + mã QR (quishing)", "4 · Ứng dụng · Demo")
picture(s, IMG("s04_qr_m365_top.png"), Inches(0.5), Inches(1.5), Inches(8.0), Inches(5.0))
picture(s, IMG("c_qr_figure.png"), Inches(8.8), Inches(1.5), Inches(4.0), Inches(4.3))
textbox(s, Inches(8.8), Inches(5.9), Inches(4.0), Inches(1.2),
        [("OCR đọc chữ tiếng Việt trong ảnh; QR giải mã ra link .click giả mạo → 98–100/100.",
          {"size": 13, "color": INK2})])

s = new_slide("Demo: tệp đính kèm & mạo danh thầy cô", "4 · Ứng dụng · Demo")
picture(s, IMG("c_zip_att.png"), Inches(0.5), Inches(1.5), Inches(6.2), Inches(3.6))
textbox(s, Inches(0.5), Inches(5.2), Inches(6.2), Inches(1.6),
        [("ZIP có mật khẩu (né diệt virus) chứa HoaDon_T10.pdf.exe: hệ thống vẫn đọc được tên tệp "
          "bên trong → phát hiện đuôi kép + tệp chạy được. Tệp không bao giờ được mở.", {"size": 13, "color": INK2})])
picture(s, IMG("s08_the_cao_top.png"), Inches(7.0), Inches(1.5), Inches(5.9), Inches(4.0))
textbox(s, Inches(7.0), Inches(5.2), Inches(5.9), Inches(1.6),
        [("“Thầy nhờ mua thẻ cào”: không link, không tệp. Mô hình văn bản chỉ cho 4%, nhưng hệ đa kênh "
          "chấm 78/100 nhờ tên hiển thị mạo danh + yêu cầu giữ bí mật + đòi mã thẻ.", {"size": 13, "color": INK2})])

s = new_slide("Demo: 12 email mẫu & chế độ luyện tập", "4 · Ứng dụng · Demo")
rows = [("Email mẫu", "Điểm", "Mức")] + [
    (a, b, (c, STATUS["good"] if c == "An toàn" else STATUS["critical"])) for a, b, c in C.SAMPLES]
table(s, Inches(0.5), Inches(1.45), Inches(6.0), rows, [4.2, 0.7, 1.4], size=11, row_h=0.39)
picture(s, IMG("quiz_a.png"), Inches(6.8), Inches(1.45), Inches(6.1), Inches(4.6))
textbox(s, Inches(6.8), Inches(6.15), Inches(6.1), Inches(0.9),
        [("Luyện tập: tự đoán trước → xem đáp án, phân tích và bài học; có bảng điểm, chuỗi đúng.",
          {"size": 13, "color": INK2})])

# =============================================================== 16. experiment design
s = new_slide("Đánh giá độ bền: thiết kế thí nghiệm", "5 · Đánh giá")
R = C.robustness()
textbox(s, Inches(0.6), Inches(1.45), Inches(12.2), Inches(0.9), [
    ("Câu hỏi: khi kẻ tấn công dùng AI viết lại email, hoặc chuyển thông điệp vào ảnh, mã QR, tệp đính "
     "kèm, bộ phát hiện còn bắt được bao nhiêu? Có báo nhầm email hợp lệ không?", {"size": 16, "color": INK2})])
rows = [("Kịch bản", "Mô tả")] + [(t["label"], t["desc"]) for t in R["transforms"]]
table(s, Inches(0.6), Inches(2.5), Inches(7.2), rows, [2.0, 5.2], size=13, row_h=0.48, bold_col0=True)
card_text(s, Inches(8.2), Inches(2.5), Inches(4.6), Inches(1.9), "Dữ liệu",
          f"{R['n_phish']} email lừa đảo + {R['n_legit']} email hợp lệ / kịch bản, lấy từ template held-out "
          "(chưa từng dùng để huấn luyện). Header người gửi giữ trung tính.", size=13)
card_text(s, Inches(8.2), Inches(4.6), Inches(4.6), Inches(1.75), "4 bộ phát hiện",
          "Chỉ văn bản: TF-IDF · KD-BiLSTM\nĐa kênh PhishLens: TF-IDF · KD-BiLSTM", size=13)

# =============================================================== 17. results chart (native)
s = new_slide("Kết quả: tỉ lệ phát hiện email lừa đảo", "5 · Đánh giá")
robust_chart(s, R, Inches(0.5), Inches(1.4), Inches(8.6), Inches(5.6))
fp = R["fpr"]
rows = [("Báo nhầm", "VB/TF", "VB/KD", "ĐK/TF", "ĐK/KD")] + [
    (t["label"], *[f"{100 * fp[t['key']][d['key']]['rate']:.0f}%" for d in R["detectors"]])
    for t in R["transforms"]]
textbox(s, Inches(9.3), Inches(1.45), Inches(3.6), Inches(0.4),
        [("Báo nhầm trên email hợp lệ", {"size": 14, "bold": True})])
table(s, Inches(9.3), Inches(1.9), Inches(3.6), rows, [1.9, 0.75, 0.75, 0.75, 0.75], size=10, row_h=0.36)
textbox(s, Inches(9.3), Inches(4.6), Inches(3.6), Inches(2.3), [
    ("VB = chỉ đọc văn bản thân thư; ĐK = PhishLens đa kênh. Ngưỡng: điểm ≥ 50 hoặc P ≥ 0,5.",
     {"size": 11, "color": MUTED}),
    ("Dữ liệu tổng hợp; 'LLM viết lại' là bộ luật mô phỏng - con số thể hiện xu hướng.",
     {"size": 11, "color": MUTED, "italic": True})])

# =============================================================== 18. findings
s = new_slide("Phát hiện chính", "5 · Đánh giá")
finds = [
    ("Chuyển kênh vô hiệu hóa mô hình chỉ đọc văn bản",
     "Ảnh / QR / Word / HTML: chỉ văn bản 0% → đa kênh 57–100%. Trả lời câu hỏi “email có ảnh + file thì sao”."),
    ("LLM viết lại làm giảm mô hình văn bản",
     "TF-IDF 80% → 67%, KD-BiLSTM 67% → 60%; hệ đa kênh giữ 80%."),
    ("BEC (mạo danh nhờ chuyển tiền/thẻ cào) khó nhất",
     "Không link, không tệp: bỏ sót 50% khi bỏ tín hiệu người gửi. Thực tế: người gửi là tín hiệu mạnh nhất (mẫu demo 78/100)."),
    ("Mô hình bài báo khi sang tiếng Việt",
     "KD-BiLSTM báo nhầm 14% so với 1% của TF-IDF trên email hợp lệ chưa thấy - tokenizer tiếng Anh xóa dấu → cần teacher đa ngôn ngữ."),
    ("Học đường tắt",
     "Bản đầu báo nhầm email thật có link trường vì dữ liệu tổng hợp lệch. Che URL + email hợp lệ 'khó' đã khắc phục."),
]
for i, (h, d) in enumerate(finds):
    col, row = i % 2, i // 2
    w = Inches(6.0) if i < 4 else Inches(12.2)
    card_text(s, Inches(0.6 + col * 6.2), Inches(1.5 + row * 1.8), w, Inches(1.6), h, d, size=13)

# =============================================================== 19. limits & next
s = new_slide("Hạn chế & hướng tiếp theo", "6 · Kết luận")
bullets(s, Inches(0.6), Inches(1.6), Inches(6.0), Inches(5), [
    ("Hạn chế", ""),
    "- Dữ liệu tổng hợp; chưa có email lừa đảo thật của trường",
    "- 'LLM viết lại' mới là bộ luật mô phỏng",
    "- Chưa tái hiện Table 7–8 (ModernBERT, DeBERTa, Qwen, Phi-4, XGBoost…)",
    "- Tokenizer MobileBERT không giữ dấu tiếng Việt",
    "- Chưa kiểm tra danh tiếng URL trực tuyến, chưa sandbox tệp",
    "- OCR trên CPU mất vài giây mỗi ảnh",
], size=16)
bullets(s, Inches(6.9), Inches(1.6), Inches(6.0), Inches(5), [
    ("Hướng tiếp theo", ""),
    "- Thu thập email lừa đảo thật (ẩn danh) qua hộp thư báo cáo của Phòng CNTT",
    "- Sinh biến thể bằng LLM thật chạy cục bộ (đã có chỗ cắm Ollama)",
    "- Teacher đa ngôn ngữ: PhoBERT / XLM-R",
    "- Khảo sát người dùng: kiểm tra trước/sau 2 tuần luyện tập",
    "- Tích hợp: add-in Outlook/Gmail hoặc hộp thư “chuyển tiếp để kiểm tra”",
], size=16)

# =============================================================== 20. conclusion
s = new_slide("Kết luận", "6 · Kết luận")
card_text(s, Inches(0.6), Inches(1.6), Inches(3.9), Inches(4.6), "Tái hiện",
          "Đã dựng lại đầy đủ phương pháp: dữ liệu, 4 baseline, teacher MobileBERT, KD-BiLSTM, "
          "5 kịch bản × 5-fold. Số tham số và xu hướng khớp bài báo; số liệu tuyệt đối chưa so được "
          "vì thiếu dữ liệu gốc.", size=14)
card_text(s, Inches(4.75), Inches(1.6), Inches(3.9), Inches(4.6), "Bổ sung",
          "Notebook Colab, sửa lỗi huấn luyện teacher, corpus tiếng Việt có template held-out, "
          "che URL chống học đường tắt, giải thích attention có dấu.", size=14)
card_text(s, Inches(8.9), Inches(1.6), Inches(3.9), Inches(4.6), "Ứng dụng",
          "PhishLens Edu: lớp phân tích đa kênh có giải thích cho trường học. Mô hình bài báo là "
          "kênh nội dung; ảnh/QR/tệp bù cho điểm yếu chuyển kênh (0% → 57–100%).",
          head_color=ACCENT, fill=SOFT, size=14)
textbox(s, Inches(0.6), Inches(6.4), Inches(12.2), Inches(0.6),
        [("Cảm ơn thầy và các bạn đã lắng nghe!", {"size": 20, "bold": True, "color": ACCENT})],
        align=PP_ALIGN.CENTER)

out = os.path.join(C.ROOT, "report", "TrinhBay_PhishLens.pptx")
prs.save(out)
print("saved", out, len(prs.slides), "slides")
