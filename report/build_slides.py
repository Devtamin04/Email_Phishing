"""Builds report/Slide_TimHieu_NoiDung_DongGop.pptx: tìm hiểu bài báo → nội dung thực hiện → đóng góp."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slide_kit import *  # noqa: E402,F401,F403

R = C.robustness()
GREEN, GREEN_SOFT = RGBColor(0x1B, 0x8A, 0x5A), RGBColor(0xDD, 0xF3, 0xE8)
PARTS = [("I", "Tìm hiểu", "Bối cảnh, bài báo KD-BiLSTM: dữ liệu, mô hình, kết quả, khoảng trống"),
         ("II", "Nội dung thực hiện", "Tái hiện bài báo · xây dựng PhishLens Edu · đánh giá độ bền"),
         ("III", "Đóng góp", "Những gì nhóm bổ sung so với bài báo, phát hiện, hướng phát triển")]


def section(num, title, sub):
    """Full-bleed divider slide between the three parts."""
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = ACCENT
    textbox(s, Inches(0.9), Inches(2.2), Inches(11.5), Inches(1.0),
            [(f"PHẦN {num}", {"size": 20, "bold": True, "color": SOFT})])
    textbox(s, Inches(0.9), Inches(2.9), Inches(11.5), Inches(1.3), [(title, {"size": 48, "bold": True, "color": CARD})])
    textbox(s, Inches(0.9), Inches(4.2), Inches(11.5), Inches(1.0), [(sub, {"size": 20, "color": SOFT})])
    N[0] += 1


def pill(slide, x, y, text, fill=ACCENT, w=Inches(0.55)):
    c = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, w, w)
    c.fill.solid(); c.fill.fore_color.rgb = fill; c.line.fill.background()
    c.text_frame.text = text
    p = c.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.runs[0].font.size, p.runs[0].font.bold, p.runs[0].font.color.rgb, p.runs[0].font.name = Pt(16), True, CARD, FONT


# =============================================================== title
s = prs.slides.add_slide(BLANK)
s.background.fill.solid()
s.background.fill.fore_color.rgb = PAGE
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(0.25))
band.fill.solid(); band.fill.fore_color.rgb = ACCENT; band.line.fill.background()
textbox(s, Inches(0.9), Inches(1.7), Inches(11.5), Inches(0.5),
        [("TỪ BÀI BÁO ĐẾN ỨNG DỤNG", {"size": 16, "bold": True, "color": ACCENT})])
textbox(s, Inches(0.9), Inches(2.2), Inches(11.5), Inches(1.2), [(C.TITLE, {"size": 42, "bold": True})])
textbox(s, Inches(0.9), Inches(3.3), Inches(11.5), Inches(1.0),
        [("Tìm hiểu KD-BiLSTM · Tái hiện · Xây dựng PhishLens Edu cho trường học", {"size": 22, "color": INK2})])
textbox(s, Inches(0.9), Inches(4.7), Inches(11.5), Inches(1.4),
        [("Bài báo: " + C.PAPER, {"size": 13, "color": MUTED, "italic": True}),
         ("Nhóm thực hiện: [Họ tên các thành viên]", {"size": 16})])
N[0] += 1

# =============================================================== roadmap
s = new_slide("Nội dung trình bày")
for i, (n, h, d) in enumerate(PARTS):
    x = Inches(0.6 + i * 4.15)
    card(s, x, Inches(1.7), Inches(3.9), Inches(2.6), fill=SOFT if i == 2 else CARD)
    pill(s, x + Inches(0.25), Inches(1.95), n, w=Inches(0.65))
    textbox(s, x + Inches(0.25), Inches(2.75), Inches(3.4), Inches(1.5),
            [(h, {"size": 22, "bold": True, "color": ACCENT if i == 2 else INK}), (d, {"size": 14, "color": INK2})])
    if i < 2:
        arrow(s, x + Inches(3.92), Inches(2.85), Inches(0.2))
textbox(s, Inches(0.6), Inches(4.75), Inches(12.2), Inches(0.4),
        [("Mạch trình bày", {"size": 16, "bold": True})])
flow = ["Bài báo gốc", "Tái hiện pipeline", "Tìm ra khoảng trống", "PhishLens Edu", "Đánh giá độ bền"]
for i, t in enumerate(flow):
    x = Inches(0.6 + i * 2.5)
    card_text(s, x, Inches(5.25), Inches(2.1), Inches(0.8), t, "", size=13,
              fill=SOFT if i >= 3 else CARD, head_color=ACCENT if i >= 3 else INK)
    if i < 4:
        arrow(s, x + Inches(2.12), Inches(5.5))

# =============================================================== PART I
section("I", "Tìm hiểu", PARTS[0][2])

s = new_slide("Bối cảnh: email lừa đảo trong thời LLM", "I · Tìm hiểu")
bullets(s, Inches(0.6), Inches(1.6), Inches(7.0), Inches(5.2), [
    ("LLM giúp kẻ tấn công ", "viết email trôi chảy, lịch sự, cá nhân hóa với chi phí gần bằng 0"),
    ("Ba hành vi né tránh tiêu biểu:", ""),
    "- Paraphrase: diễn đạt lại để né chữ ký từ khóa",
    "- Masking: làm mềm dấu hiệu lộ liễu thành giọng công sở",
    "- Personalization: chèn tên, chức danh, bối cảnh của người nhận",
    ("“Chuyển kênh”: ", "đặt thông điệp vào ảnh, mã QR (quishing), tệp HTML/PDF/ZIP có mật khẩu"),
    ("Trường học là mục tiêu dễ: ", "hàng chục nghìn tài khoản, thông báo thật cũng nói về học phí, học bổng, mật khẩu"),
], size=16)
card_text(s, Inches(8.0), Inches(1.7), Inches(4.8), Inches(2.3), "Giải pháp hiện có còn thiếu gì?",
          "Gmail / M365 Defender chặn phần lớn chiến dịch phổ biến, nhưng email lọt qua thường là email "
          "khéo nhất. Người dùng là lớp phòng thủ cuối mà lại không biết vì sao email đáng ngờ.", size=13)
card_text(s, Inches(8.0), Inches(4.2), Inches(4.8), Inches(2.3), "Mô hình lớn thì khó triển khai",
          "Transformer hàng trăm triệu – hàng tỷ tham số khó đặt ở gateway. Gửi email lên API LLM thương mại "
          "thì tốn chi phí, trễ và lộ dữ liệu cá nhân.", size=13)

s = new_slide("Bài báo chọn tìm hiểu", "I · Tìm hiểu")
textbox(s, Inches(0.6), Inches(1.45), Inches(12.2), Inches(0.9), [
    ("Eskandarian et al. (Viện An ninh mạng Canada – ĐH New Brunswick & Mastercard), JISA 101 (2026) 104552",
     {"size": 15, "color": INK2, "italic": True}),
    ("Mục tiêu: bộ phát hiện nhỏ, nhanh, chạy CPU, vẫn bền trước email do LLM viết lại", {"size": 17, "bold": True})])
picture(s, IMG("diag1.png"), Inches(0.6), Inches(2.45), Inches(7.6), Inches(4.4))
bullets(s, Inches(8.5), Inches(2.45), Inches(4.4), Inches(4.5), [
    ("Bốn đóng góp của bài báo", ""),
    "- Bộ dữ liệu “nhận biết LLM”: email thật + email LLM viết lại",
    "- BiLSTM + attention chưng cất từ MobileBERT, đủ nhẹ cho gateway",
    "- Phân tích đánh đổi độ chính xác – độ trễ – kích thước",
    "- Góc nhìn vận hành khi tích hợp vào hệ thống thư",
], size=15)

s = new_slide("Dữ liệu và quy trình sinh email bằng LLM", "I · Tìm hiểu")
table(s, Inches(0.6), Inches(1.5), Inches(5.6),
      [("Bộ dữ liệu", "Lừa đảo", "Hợp lệ"), ("Cambridge Phishing", "78.154", "–"), ("Nazario", "4.487", "–"),
       ("Chakraborty", "7.323", "11.283"), ("Phishing Pot", "4.351", "–"), ("Enron", "–", "517.402"),
       ("Tổng email thật", "94.315", "528.685"), (("Email do LLM sinh", ACCENT), "41.333", "6.242")],
      [2.8, 1.4, 1.4], size=13, row_h=0.42, bold_col0=True)
card_text(s, Inches(6.6), Inches(1.5), Inches(6.2), Inches(1.6), "Email LLM “khó” hơn thật không? (Fig. 2)",
          "Cosine TF-IDF với tập email hợp lệ: email LLM sinh dịch sang phải → giống email hợp lệ hơn "
          "email lừa đảo gốc.", size=13)
card_text(s, Inches(6.6), Inches(3.3), Inches(6.2), Inches(1.6), "Chấm “mức phishing” bằng bộ câu hỏi",
          "Hỏi LLM: có tạo khẩn cấp? link đáng ngờ? đòi cập nhật tài khoản?… → tín hiệu mềm để lọc mẫu "
          "sinh kém chất lượng.", size=13)
card_text(s, Inches(6.6), Inches(5.1), Inches(6.2), Inches(1.5), "Khử trùng lặp & 5 kịch bản",
          "Loại ~10K mẫu gần trùng. Đánh giá Orig-Orig, Gen-Gen, Orig-Gen, Gen-Orig, Mixture; "
          "5-fold, chia 72/8/20.", size=13)

s = new_slide("Mô hình: từ LSTM đến KD-BiLSTM", "I · Tìm hiểu")
steps = [("LSTM", "Word2Vec 100d"), ("BiLSTM", "ngữ cảnh 2 chiều"), ("+ Single-head", "chú ý cụm từ"),
         ("+ Multi-head", "H=4, D=64"), ("KD-BiLSTM", "học từ MobileBERT")]
for i, (h, d) in enumerate(steps):
    x = Inches(0.6 + i * 2.5)
    card_text(s, x, Inches(1.55), Inches(2.1), Inches(1.0), h, d,
              head_color=ACCENT if i == 4 else INK, fill=SOFT if i == 4 else CARD, size=13)
    if i < 4:
        arrow(s, x + Inches(2.12), Inches(1.9))
picture(s, IMG("diag2.png"), Inches(0.6), Inches(2.85), Inches(8.0), Inches(2.6))
card_text(s, Inches(8.9), Inches(2.85), Inches(3.9), Inches(3.75), "Chưng cất tri thức",
          "Teacher MobileBERT 25,3M → đóng băng.\nStudent ~4,5M; embedding khởi tạo từ teacher.\n\n"
          "L = α·CE + (1−α)·τ²·KL\nα = 0,5 · τ = 2 · lr 1e-4\n3 epoch · batch 32", size=13)
textbox(s, Inches(0.6), Inches(5.6), Inches(8.0), Inches(1.2), [
    ("Điểm mới: chưng cất khác kiến trúc (transformer → mạng hồi quy), teacher học cả email LLM, "
     "student được kiểm tra tổng quát hóa chéo phân phối Orig ↔ Gen.", {"size": 14, "color": INK2})])

s = new_slide("Kết quả của bài báo (kịch bản Mixture)", "I · Tìm hiểu")
rows = [("Mô hình", "Tham số", "F1 (%)", "Test (s)")] + [
    ((m, ACCENT) if "KD" in m else m, p, f, t) for m, p, f, t in C.PAPER_MIXTURE]
table(s, Inches(0.6), Inches(1.6), Inches(7.4), rows, [3.2, 1.2, 1.1, 1.1], size=13, row_h=0.42)
bullets(s, Inches(8.4), Inches(1.6), Inches(4.4), Inches(5), [
    ("Mỗi bước nâng cấp đều tăng F1: ", "91,3% → 95,3% → 96,7%"),
    ("KD-BiLSTM kém transformer tốt nhất ", "~1–2,5 điểm F1"),
    ("Đổi lại: ", "nhanh hơn 5–19×, nhỏ hơn 20–800×"),
    ("Gen-Orig: ", "recall BiLSTM chỉ 51% → KD-BiLSTM 98%"),
    ("LR + TF-IDF ", "chỉ kém mô hình đề xuất ~1,3 điểm accuracy"),
], size=16)

s = new_slide("Nhận xét: điểm mạnh và khoảng trống của bài báo", "I · Tìm hiểu")
card_text(s, Inches(0.6), Inches(1.6), Inches(5.9), Inches(2.4), "Điểm mạnh",
          "Đặt vấn đề đúng thời điểm (email LLM) · dữ liệu có tính tới hành vi né tránh · kịch bản chéo "
          "phân phối hợp lý · phân tích đầy đủ đánh đổi chính xác/chi phí.", head_color=GREEN, size=14)
card_text(s, Inches(6.9), Inches(1.6), Inches(5.9), Inches(2.4), "Hạn chế khi tái lập",
          "Dữ liệu & code “available on request” · số liệu chưa thống nhất (47.575 / ~14.000 / 13.692 mẫu) · "
          "thiếu chi tiết kiến trúc (nối attention, pooling).", head_color=STATUS["critical"], size=14)
textbox(s, Inches(0.6), Inches(4.25), Inches(12.2), Inches(0.4),
        [("Ba khoảng trống khi đưa vào thực tế → câu hỏi của nhóm", {"size": 17, "bold": True, "color": ACCENT})])
gaps = [("1", "Chỉ đọc văn bản", "Email thật có ảnh, mã QR, tệp đính kèm."),
        ("2", "Chỉ trả lời có/không", "Người dùng không biết mức độ nguy hiểm và lý do."),
        ("3", "Chỉ có tiếng Anh", "Chưa xét tiếng Việt và môi trường trường học.")]
for i, (n, h, d) in enumerate(gaps):
    x = Inches(0.6 + i * 4.15)
    card(s, x, Inches(4.8), Inches(3.9), Inches(1.75), fill=SOFT, line=SOFT)
    pill(s, x + Inches(0.2), Inches(5.0), n, w=Inches(0.5))
    textbox(s, x + Inches(0.85), Inches(4.95), Inches(2.95), Inches(1.5),
            [(h, {"size": 16, "bold": True}), (d, {"size": 13, "color": INK2})])

# =============================================================== PART II
section("II", "Nội dung thực hiện", PARTS[1][2])

s = new_slide("Hai mảng công việc", "II · Nội dung thực hiện")
card_text(s, Inches(0.6), Inches(1.6), Inches(5.9), Inches(2.3), "A. Tái hiện bài báo — gói phishkd",
          "Dữ liệu + sinh email kiểu LLM · 4 baseline · teacher MobileBERT · KD-BiLSTM (Algorithm 1) · "
          "5 kịch bản × 5-fold · notebook Colab chạy toàn bộ.", size=14)
card_text(s, Inches(6.9), Inches(1.6), Inches(5.9), Inches(2.3), "B. Ứng dụng — PhishLens Edu (gói phishlens)",
          "Phân tích rủi ro email đa kênh, có giải thích tiếng Việt, kèm chế độ luyện tập và thí nghiệm "
          "độ bền. Web app chạy cục bộ (FastAPI).", head_color=ACCENT, fill=SOFT, size=14)
rows = [("Bài báo", "Mã nguồn của nhóm")] + [
    ("3.2 · 3 hành vi né tránh, chấm mức phishing, khử trùng lặp", "phishkd/augment.py, analysis.py"),
    ("4.1–4.6 · Word2Vec, LSTM, BiLSTM, +SH, +MH", "phishkd/text.py, models.py"),
    ("4.7–4.8 · MobileBERT, KD student, loss (Eq. 20–23)", "phishkd/models.py: KDStudent, distillation_loss"),
    ("Algorithm 1 · vòng chưng cất", "phishkd/train.py: distill"),
    ("5.2 · 5 kịch bản, 5-fold, 72/8/20", "phishkd/data.py: scenario_folds"),
]
table(s, Inches(0.6), Inches(4.15), Inches(12.2), rows, [6.5, 5.7], size=12, row_h=0.42)

s = new_slide("A. Tái hiện: đã làm được đến đâu?", "II · Nội dung thực hiện")
rows = [("Thành phần", "Bài báo", "Bản tái hiện", "Trạng thái")] + [
    (a, b, c, (d, STATUS_COLOR[d])) for a, b, c, d in C.REPRO]
table(s, Inches(0.6), Inches(1.5), Inches(12.2), rows, [3.0, 3.3, 4.6, 1.1], size=11, row_h=0.43)

s = new_slide("A. Tái hiện: số liệu đo được", "II · Nội dung thực hiện")
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
          "Dữ liệu toy, 1 fold → chỉ kiểm tra pipeline. Xu hướng khớp bài báo: chéo phân phối làm giảm "
          "điểm; multi-head và KD giúp tổng quát hóa tốt hơn.", size=13)

s = new_slide("A. Tái hiện: vấn đề gặp phải và cách khắc phục", "II · Nội dung thực hiện")
rows = [("Hiện tượng", "Nguyên nhân", "Khắc phục")] + C.FIXES
table(s, Inches(0.6), Inches(1.5), Inches(12.2), rows, [3.2, 4.2, 4.2], size=13, row_h=0.75)
textbox(s, Inches(0.6), Inches(5.6), Inches(12.2), Inches(1),
        [("Các chỗ bài báo không mô tả rõ (pooling sau attention, chia fold chéo miền, ngưỡng lọc, prompt "
          "sinh dữ liệu) được nhóm tự quyết định và ghi lại trong README.", {"size": 14, "color": INK2, "italic": True})])

s = new_slide("B. Từ bài báo đến ứng dụng: PhishLens Edu", "II · Nội dung thực hiện")
rows = [("Khoảng trống của bài báo", "Định hướng của PhishLens Edu")] + [
    ("Chỉ đọc văn bản thân thư", "Phân tích 5 kênh: người gửi, liên kết, nội dung, ảnh & QR, tệp đính kèm"),
    ("Nhãn nhị phân có/không", "Điểm rủi ro 0–100, 4 mức, loại tấn công, kỹ thuật né tránh"),
    ("Không giải thích", "Lý do + bài học tiếng Việt, tô sáng cụm từ, chế độ luyện tập"),
    ("Dữ liệu tiếng Anh", "Corpus email trường học tiếng Việt, cấu hình theo tên miền trường"),
]
table(s, Inches(0.6), Inches(1.55), Inches(12.2), rows, [4.2, 8.0], size=14, row_h=0.55, bold_col0=True)
card(s, Inches(0.6), Inches(4.6), Inches(12.2), Inches(2.0), fill=SOFT, line=SOFT)
textbox(s, Inches(0.9), Inches(4.75), Inches(11.7), Inches(1.8), [
    ("Định vị: “ý kiến thứ hai có giải thích”", {"size": 19, "bold": True, "color": ACCENT}),
    ("Không thay Gmail/Defender. Người dùng chuyển tiếp hoặc tải .eml nghi ngờ lên → nhận điểm, lý do, "
     "việc cần làm. Chạy hoàn toàn cục bộ, chỉ phân tích tĩnh, không bao giờ mở hay thực thi tệp.", {"size": 15}),
])

s = new_slide("B. Kiến trúc PhishLens Edu", "II · Nội dung thực hiện")
picture(s, IMG("diag3.png"), Inches(0.6), Inches(1.5), Inches(8.2), Inches(4.5))
card_text(s, Inches(9.1), Inches(1.5), Inches(3.7), Inches(2.6), "Kết hợp bằng chứng (noisy-OR)",
          "S_c = 1 − Π (1 − s_i)\nScore = 100·[1 − Π_c (1 − S_c)]\n\nĐơn điệu, dễ giải thích, kênh này bù cho kênh kia.",
          size=13)
card_text(s, Inches(9.1), Inches(4.3), Inches(3.7), Inches(1.7), "4 mức rủi ro",
          "An toàn < 25 · Cần chú ý 25–49\nNguy hiểm 50–74 · Rất nguy hiểm ≥ 75", size=13)
textbox(s, Inches(0.6), Inches(6.15), Inches(12.2), Inches(0.8),
        [("Mỗi bằng chứng = tiêu đề + mô tả + độ mạnh s ∈ [0,1] + bài học + nhãn loại tấn công.",
          {"size": 14, "color": INK2})])

s = new_slide("B. Năm kênh phân tích", "II · Nội dung thực hiện")
rows = [("Kênh", "Phân tích")] + C.CHANNELS
table(s, Inches(0.6), Inches(1.5), Inches(12.2), rows, [1.6, 10.6], size=14, row_h=0.62, bold_col0=True)
textbox(s, Inches(0.6), Inches(5.5), Inches(12.2), Inches(1.2), [
    ("Văn bản lấy từ OCR ảnh và từ tệp đính kèm được đưa lại vào kênh nội dung; URL từ QR, ảnh, tệp được "
     "đưa vào kênh liên kết → thông điệp “chuyển kênh” vẫn bị phân tích.", {"size": 15, "color": INK2})])

s = new_slide("B. Kế thừa KD-BiLSTM của bài báo ở kênh nội dung", "II · Nội dung thực hiện")
bullets(s, Inches(0.6), Inches(1.6), Inches(6.4), Inches(5), [
    ("Huấn luyện lại đúng quy trình đã tái hiện ", "trên email trường học tiếng Việt + tiếng Anh, có bản viết lại kiểu LLM"),
    ("Attention → giải thích: ", "hiển thị từ được chú ý nhiều nhất, ánh xạ về chữ gốc có dấu qua offset mapping"),
    ("Che URL & địa chỉ email ", "trước mô hình → học ngôn ngữ, không học “có tên miền = lừa đảo”"),
    ("8 nhóm thủ đoạn tâm lý (vi/en) ", "rút từ bộ câu hỏi chấm mức phishing của bài báo"),
    ("Có mô hình TF-IDF để đối chiếu ", "(chọn trên giao diện)"),
], size=16)
picture(s, IMG("c_qr_evidence.png"), Inches(7.3), Inches(1.55), Inches(5.5), Inches(5.3))

s = new_slide("B. Corpus email trường học tiếng Việt", "II · Nội dung thực hiện")
bullets(s, Inches(0.6), Inches(1.6), Inches(7.2), Inches(5), [
    ("15 dạng tấn công: ", "khóa tài khoản, học bổng giả, học phí giả, tuyển CTV, thầy nhờ mua thẻ cào, macro, "
                          "hóa đơn điện tử, mã QR…"),
    ("21 dạng email hợp lệ, ", "kể cả email “khó”: có link chính thức, tệp, QR, hạn chót, chữ “mật khẩu”"),
    ("Phép biến đổi kiểu LLM cho tiếng Việt: ", "paraphrase / masking / personalization"),
    ("Email hợp lệ cũng được cá nhân hóa ", "để văn phong lịch sự không thành dấu hiệu"),
    ("12 email mẫu .eml ", "bao phủ các tình huống điển hình (tệp “độc” đều là tệp giả vô hại)"),
], size=16)
card_text(s, Inches(8.2), Inches(1.7), Inches(4.6), Inches(2.4), "Chia template train / held-out",
          "Cứ 3 template giữ lại 1 chỉ để đánh giá. Nếu train và test chung cách viết, mô hình đạt ~100% "
          "một cách giả tạo.", head_color=ACCENT, fill=SOFT, size=13)
card_text(s, Inches(8.2), Inches(4.3), Inches(4.6), Inches(2.2), "Cấu hình theo trường",
          "Tên trường, tên miền chính thức, thương hiệu hay bị giả mạo, bật/tắt OCR — trong phishlens/config.py.",
          size=13)

s = new_slide("Demo: email chỉ có ảnh + mã QR (quishing)", "II · Nội dung thực hiện · Demo")
picture(s, IMG("s04_qr_m365_top.png"), Inches(0.5), Inches(1.5), Inches(8.0), Inches(5.0))
picture(s, IMG("c_qr_figure.png"), Inches(8.8), Inches(1.5), Inches(4.0), Inches(4.3))
textbox(s, Inches(8.8), Inches(5.9), Inches(4.0), Inches(1.2),
        [("OCR đọc chữ tiếng Việt trong ảnh; QR giải mã ra link .click giả mạo tên trường → Rất nguy hiểm.",
          {"size": 13, "color": INK2})])

s = new_slide("Demo: tệp đính kèm & mạo danh thầy cô", "II · Nội dung thực hiện · Demo")
picture(s, IMG("c_zip_att.png"), Inches(0.5), Inches(1.5), Inches(6.2), Inches(3.6))
textbox(s, Inches(0.5), Inches(5.2), Inches(6.2), Inches(1.6),
        [("ZIP có mật khẩu chứa HoaDon_T10.pdf.exe: không giải nén được nhưng vẫn đọc tên tệp bên trong → "
          "đuôi kép + tệp chạy được. Tệp không bao giờ được mở.", {"size": 13, "color": INK2})])
picture(s, IMG("s08_the_cao_top.png"), Inches(7.0), Inches(1.5), Inches(5.9), Inches(4.0))
textbox(s, Inches(7.0), Inches(5.2), Inches(5.9), Inches(1.6),
        [("“Thầy nhờ mua thẻ cào”: không link, không tệp. Mô hình văn bản chỉ cho 4%, hệ đa kênh chấm 78/100 "
          "nhờ tên hiển thị mạo danh + yêu cầu giữ bí mật + đòi mã thẻ.", {"size": 13, "color": INK2})])

s = new_slide("Demo: 12 email mẫu & chế độ luyện tập", "II · Nội dung thực hiện · Demo")
rows = [("Email mẫu", "Điểm", "Mức")] + [
    (a, b, (c, STATUS["good"] if c == "An toàn" else STATUS["critical"])) for a, b, c in C.SAMPLES]
table(s, Inches(0.5), Inches(1.45), Inches(6.0), rows, [4.2, 0.7, 1.4], size=11, row_h=0.39)
picture(s, IMG("quiz_a.png"), Inches(6.8), Inches(1.45), Inches(6.1), Inches(4.6))
textbox(s, Inches(6.8), Inches(6.15), Inches(6.1), Inches(0.9),
        [("9/9 email lừa đảo ở mức Rất nguy hiểm, 3/3 email thật ở mức An toàn. Luyện tập: tự đoán trước "
          "→ xem đáp án, phân tích, bài học.", {"size": 13, "color": INK2})])

s = new_slide("Đánh giá độ bền: thiết kế thí nghiệm", "II · Nội dung thực hiện")
textbox(s, Inches(0.6), Inches(1.45), Inches(12.2), Inches(1.0), [
    ("", {"parts": [("RQ1: ", True), ("bộ phát hiện chỉ đọc văn bản (như bài báo) suy giảm thế nào khi email bị LLM "
                                       "viết lại hoặc chuyển vào ảnh / QR / tệp?", False)], "size": 15, "after": 4}),
    ("", {"parts": [("RQ2: ", True), ("kết hợp bằng chứng đa kênh có khôi phục được mà không tăng báo nhầm?", False)],
          "size": 15})])
rows = [("Kịch bản", "Mô tả")] + [(t["label"], t["desc"]) for t in R["transforms"]]
table(s, Inches(0.6), Inches(2.6), Inches(7.2), rows, [2.0, 5.2], size=12, row_h=0.47, bold_col0=True)
card_text(s, Inches(8.2), Inches(2.6), Inches(4.6), Inches(1.9), "Dữ liệu",
          f"{R['n_phish']} email lừa đảo + {R['n_legit']} email hợp lệ / kịch bản, từ template held-out. "
          "Email hợp lệ biến đổi tương ứng; người gửi giữ trung tính.", size=13)
card_text(s, Inches(8.2), Inches(4.7), Inches(4.6), Inches(1.7), "4 bộ phát hiện",
          "Chỉ văn bản: TF-IDF · KD-BiLSTM\nĐa kênh PhishLens: TF-IDF · KD-BiLSTM", size=13)

s = new_slide("Kết quả: tỉ lệ phát hiện email lừa đảo", "II · Nội dung thực hiện")
robust_chart(s, R, Inches(0.5), Inches(1.4), Inches(8.6), Inches(5.6))
fp = R["fpr"]
rows = [("Báo nhầm", "VB/TF", "VB/KD", "ĐK/TF", "ĐK/KD")] + [
    (t["label"], *[f"{100 * fp[t['key']][d['key']]['rate']:.0f}%" for d in R["detectors"]])
    for t in R["transforms"]]
textbox(s, Inches(9.3), Inches(1.45), Inches(3.6), Inches(0.4),
        [("Báo nhầm trên email hợp lệ", {"size": 14, "bold": True})])
table(s, Inches(9.3), Inches(1.9), Inches(3.6), rows, [1.9, 0.75, 0.75, 0.75, 0.75], size=10, row_h=0.36)
textbox(s, Inches(9.3), Inches(4.6), Inches(3.6), Inches(2.3), [
    ("VB = chỉ đọc thân thư; ĐK = PhishLens đa kênh. Ngưỡng: điểm ≥ 50 hoặc P ≥ 0,5.", {"size": 11, "color": MUTED}),
    ("Dữ liệu tổng hợp; “LLM viết lại” là bộ luật mô phỏng – con số thể hiện xu hướng.",
     {"size": 11, "color": MUTED, "italic": True})])

# =============================================================== PART III
section("III", "Đóng góp", PARTS[2][2])

s = new_slide("Bài báo làm gì — nhóm bổ sung gì", "III · Đóng góp")
rows = [("Khía cạnh", "Bài báo gốc", ("Nhóm thực hiện", ACCENT))] + [
    ("Kênh phân tích", "Chỉ văn bản thân thư", "5 kênh: người gửi, liên kết, nội dung, ảnh & QR, tệp"),
    ("Đầu ra", "Nhãn nhị phân", "Điểm 0–100, 4 mức, loại tấn công, kỹ thuật né tránh"),
    ("Giải thích", "Không", "Lý do + bài học tiếng Việt, tô sáng, attention có dấu"),
    ("Ngôn ngữ / bối cảnh", "Tiếng Anh, doanh nghiệp", "Tiếng Việt + Anh, môi trường trường học"),
    ("Đánh giá", "Chuyển phân phối Orig ↔ Gen", "Thêm chuyển kênh: ảnh, QR, Word, HTML + báo nhầm"),
    ("Tái lập", "Dữ liệu & code theo yêu cầu", "Code mở, notebook Colab, script .bat cho Windows"),
    ("Người dùng", "Gateway / hệ thống", "Sinh viên, cán bộ: web app + chế độ luyện tập"),
]
table(s, Inches(0.6), Inches(1.5), Inches(12.2), rows, [2.6, 3.8, 5.8], size=14, row_h=0.62, bold_col0=True)

s = new_slide("Năm đóng góp của nhóm", "III · Đóng góp")
contribs = [
    ("Bản tái hiện đầy đủ, chạy lại được",
     "Dữ liệu → 4 baseline → MobileBERT → KD-BiLSTM, 5 kịch bản × 5-fold; notebook Colab; tìm và sửa lỗi "
     "teacher MobileBERT bị sụp."),
    ("Corpus email trường học tiếng Việt",
     "15 dạng tấn công, 21 dạng hợp lệ, biến đổi kiểu LLM tiếng Việt, chia template held-out."),
    ("Hệ thống PhishLens Edu",
     "5 kênh, kết hợp noisy-OR, giải thích tiếng Việt, chế độ luyện tập; chạy cục bộ, phân tích tĩnh."),
    ("Thí nghiệm độ bền chuyển kênh",
     "Chỉ văn bản: 0% khi thông điệp vào ảnh/QR/tệp → đa kênh phục hồi 57–100%."),
    ("Phân tích lỗi có giá trị thực tiễn",
     "BEC khó nhất; mô hình bài báo cần teacher hợp tiếng Việt; tách kênh giảm học đường tắt."),
]
for i, (h, d) in enumerate(contribs):
    col, row = i % 2, i // 2
    x, y = Inches(0.6 + col * 6.2), Inches(1.5 + row * 1.75)
    w = Inches(6.0) if i < 4 else Inches(12.2)
    card(s, x, y, w, Inches(1.55), fill=SOFT if i == 2 else CARD)
    pill(s, x + Inches(0.2), y + Inches(0.2), str(i + 1), w=Inches(0.5))
    textbox(s, x + Inches(0.85), y + Inches(0.12), w - Inches(1.0), Inches(1.4),
            [(h, {"size": 16, "bold": True, "after": 3}), (d, {"size": 13, "color": INK2})])

s = new_slide("Phát hiện chính từ thực nghiệm", "III · Đóng góp")
tp = R["tpr"]
finds = [
    ("Chuyển kênh vô hiệu hóa mô hình chỉ đọc văn bản",
     "Ảnh / QR / Word / HTML: chỉ văn bản 0% → đa kênh 57–100%."),
    ("LLM viết lại làm giảm mô hình văn bản",
     f"TF-IDF {tp['orig']['text_linear']['rate']:.0%} → {tp['llm']['text_linear']['rate']:.0%}, "
     f"KD-BiLSTM {tp['orig']['text_kd']['rate']:.0%} → {tp['llm']['text_kd']['rate']:.0%}; "
     f"hệ đa kênh giữ {tp['llm']['full_linear']['rate']:.0%}. Khớp nhận định của bài báo."),
    ("BEC (mạo danh nhờ chuyển tiền/thẻ cào) khó nhất",
     "Không link, không tệp: bỏ sót 50% khi bỏ tín hiệu người gửi; có người gửi thật thì demo đạt 78/100."),
    ("Mô hình bài báo khi sang tiếng Việt",
     "KD-BiLSTM báo nhầm ~14% so với 1% của TF-IDF: tokenizer tiếng Anh xóa dấu → cần PhoBERT / XLM-R."),
    ("Học đường tắt",
     "Bản đầu báo nhầm email thật có link trường (96–100%). Che URL + email hợp lệ “khó” → dưới 0,3."),
]
for i, (h, d) in enumerate(finds):
    col, row = i % 2, i // 2
    w = Inches(6.0) if i < 4 else Inches(12.2)
    card_text(s, Inches(0.6 + col * 6.2), Inches(1.5 + row * 1.8), w, Inches(1.6), h, d, size=13)

s = new_slide("Hạn chế & hướng phát triển", "III · Đóng góp")
bullets(s, Inches(0.6), Inches(1.6), Inches(6.0), Inches(5), [
    ("Hạn chế", ""),
    "- Dữ liệu tổng hợp; chưa có email lừa đảo thật của trường",
    "- “LLM viết lại” mới là bộ luật mô phỏng",
    "- Chưa tái hiện Table 7–8 (ModernBERT, DeBERTa, XGBoost…)",
    "- Độ mạnh bằng chứng đặt thủ công, chưa hiệu chỉnh",
    "- Chưa kiểm tra danh tiếng URL, chưa sandbox tệp",
    "- OCR trên CPU mất vài giây mỗi ảnh",
], size=16)
bullets(s, Inches(6.9), Inches(1.6), Inches(6.0), Inches(5), [
    ("Hướng phát triển", ""),
    "- Thu thập email lừa đảo thật (ẩn danh) qua hộp thư báo cáo của Phòng CNTT",
    "- Sinh biến thể bằng LLM thật chạy cục bộ (đã có chỗ cắm Ollama)",
    "- Teacher đa ngôn ngữ: PhoBERT / XLM-R",
    "- Khảo sát người dùng: kiểm tra trước/sau 2 tuần luyện tập",
    "- Tích hợp add-in Outlook/Gmail hoặc hộp thư “chuyển tiếp để kiểm tra”",
], size=16)

s = new_slide("Kết luận", "III · Đóng góp")
cols = [("Tìm hiểu", "Nắm vững phương pháp KD-BiLSTM: dữ liệu nhận biết LLM, BiLSTM + attention, chưng cất "
                     "từ MobileBERT; chỉ ra 3 khoảng trống khi đưa vào thực tế.", INK, CARD),
        ("Nội dung thực hiện", "Tái hiện đầy đủ pipeline (số tham số & xu hướng khớp bài báo) và xây dựng "
                               "PhishLens Edu với KD-BiLSTM làm kênh nội dung.", INK, CARD),
        ("Đóng góp", "Từ bộ phân loại văn bản → hệ phân tích đa kênh có giải thích cho trường học; "
                     "chuyển kênh: 0% → 57–100%.", ACCENT, SOFT)]
for i, (h, d, hc, f) in enumerate(cols):
    card_text(s, Inches(0.6 + i * 4.15), Inches(1.9), Inches(3.9), Inches(3.4), h, d, head_color=hc, fill=f, size=17)
textbox(s, Inches(0.6), Inches(6.3), Inches(12.2), Inches(0.6),
        [("Cảm ơn thầy cô và các bạn đã lắng nghe!", {"size": 20, "bold": True, "color": ACCENT})],
        align=PP_ALIGN.CENTER)

out = os.path.join(C.ROOT, "report", "Slide_TimHieu_NoiDung_DongGop.pptx")
prs.save(out)
print("saved", out, len(prs.slides), "slides")
