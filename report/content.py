"""Shared facts & numbers for the report and the slides (single source of truth)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "report", "img")

TITLE = "Phát hiện email lừa đảo thế hệ LLM"
SUBTITLE = "Tái hiện KD-BiLSTM (Eskandarian et al., JISA 2026) và ứng dụng: PhishLens Edu"
PAPER = ("M. Eskandarian et al., \"A lightweight defense mechanism against next-generation of "
         "phishing emails using distilled attention-augmented BiLSTM\", Journal of Information "
         "Security and Applications 101 (2026) 104552.")
AUTHOR = "[Họ tên sinh viên]"

# ---------------------------------------------------------------- paper (Tables 4-7)
PAPER_MIXTURE = [  # model, params, F1 (mixture), test time (s)
    ("LSTM", "17K", "91,32", "0,83"),
    ("BiLSTM", "34K", "91,65", "1,30"),
    ("BiLSTM + single-head", "67K", "93,48", "1,37"),
    ("BiLSTM + multi-head", "495K", "95,25", "1,51"),
    ("KD-BiLSTM (đề xuất)", "4,5M", "96,67", "6,06"),
    ("MobileBERT (teacher)", "25,3M", "98,56", "42,0"),
    ("ModernBERT-base", "149M", "98,98", "37,26"),
    ("DeepSeek-R1-Distill-Qwen-1.5B", "1.780M", "98,83", "56,40"),
]

# ---------------------------------------------------------------- reproduction status
REPRO = [  # component, paper, ours, status
    ("Dữ liệu thật (5 bộ, ~623K email)", "Cambridge, Nazario, Chakraborty, Phishing Pot, Enron",
     "Corpus toy sinh từ template (không có dữ liệu gốc)", "Thay thế"),
    ("Sinh email bằng LLM", "OpenAI / DeepSeek: paraphrase, masking, personalization",
     "Prompt sẵn sàng + bộ luật mô phỏng 3 hành vi; có chỗ cắm LLM cục bộ (Ollama)", "Mô phỏng"),
    ("Phân tích tương đồng TF-IDF (Fig. 2)", "Có", "Có - cùng xu hướng (0,026 so với 0,002)", "Đạt"),
    ("Chấm điểm mức phishing bằng câu hỏi", "Hỏi LLM", "Cùng 9 câu hỏi, trả lời bằng từ khóa; trọng số theo AUC", "Mô phỏng"),
    ("Khử trùng lặp", "Có", "Có (cosine TF-IDF)", "Đạt"),
    ("LSTM / BiLSTM / +SH / +MH", "Word2Vec 100d, H=4, D=64", "Đủ 4 mô hình, đúng siêu tham số Table 2", "Đạt"),
    ("Teacher MobileBERT", "25,3M tham số", "24,6M; thêm gradient clipping để huấn luyện ổn định", "Đạt"),
    ("KD-BiLSTM (Algorithm 1)", "α=0,5, τ=2, lr 1e-4, 3 epoch", "Đúng công thức loss & Algorithm 1; 4,4M tham số", "Đạt"),
    ("5 kịch bản × 5-fold, 72/8/20", "Có", "Có (cách chia fold chéo miền tự đề xuất)", "Đạt"),
    ("So sánh ModernBERT, DeBERTa, T5, Qwen, Phi-4", "Có (Table 7)", "Chưa làm", "Chưa"),
    ("Baseline LR, XGBoost, fastText, TinyBERT, DistilBERT", "Có (Table 8)", "Chưa làm", "Chưa"),
]

PARAMS = [  # model, paper, ours
    ("LSTM", "16.961", "17.185"),
    ("BiLSTM", "33.921", "34.369"),
    ("BiLSTM + single-head", "66.561", "151.169"),
    ("BiLSTM + multi-head", "494.977", "217.089"),
    ("MobileBERT (teacher)", "25,3M", "24,58M"),
    ("KD-BiLSTM (student)", "4,5M", "4,44M"),
]
ORIG_GEN = [  # model, paper F1, ours F1 (toy, 1 fold)
    ("LSTM", "82,17", "81,75"),
    ("BiLSTM", "79,93", "88,81"),
    ("BiLSTM + single-head", "85,03", "80,04"),
    ("BiLSTM + multi-head", "92,40", "90,90"),
    ("MobileBERT (teacher)", "91,80", "51,66"),
    ("KD-BiLSTM", "89,60", "92,55"),
]
SPEED = {"paper": ("6,06 s", "42 s", "≈ 7×"), "ours": ("0,35 s", "11,83 s", "≈ 34×")}

FIXES = [
    ("Teacher MobileBERT bị sụp (luôn đoán 1 lớp)",
     "Pooler lấy thẳng [CLS] chưa qua tanh → loss ban đầu ~10⁷",
     "Gradient clipping (max_grad_norm = 1) + số bước tối thiểu 120"),
    ("Mô hình văn bản 'học đường tắt' theo tên miền",
     "Dữ liệu tổng hợp: chỉ email lừa đảo mới chứa URL → báo nhầm email thật có link",
     "Che URL/địa chỉ email trước mô hình văn bản + bổ sung email hợp lệ 'khó'"),
    ("Giải thích attention ra từ mất dấu ('khoan', 'đinh')",
     "Tokenizer MobileBERT uncased xóa dấu tiếng Việt",
     "Ánh xạ attention về chữ gốc qua offset mapping"),
    ("Tiêu đề tiếng Việt bị dính chữ khi ghi .eml",
     "Lỗi gập header (encoded-word) của thư viện email Python",
     "Tăng max_line_length để không gập header"),
]

EXTRAS = [
    "Notebook Colab tự chứa (phishing_kd_bilstm.ipynb) chạy toàn bộ pipeline tái hiện",
    "Corpus email trường học tiếng Việt: 15 dạng tấn công, 21 dạng email hợp lệ (kể cả email 'khó')",
    "Chia template train / held-out → đo khả năng tổng quát hóa sang cách viết chưa từng thấy",
    "Phép biến đổi kiểu LLM bằng tiếng Việt (paraphrase / masking / personalization)",
    "Che URL trước mô hình văn bản để tránh học đường tắt; tách bạch trách nhiệm từng kênh",
    "Giải thích bằng attention ánh xạ về từ gốc có dấu",
]

# ---------------------------------------------------------------- PhishLens
CHANNELS = [
    ("Người gửi", "SPF/DKIM/DMARC, tên hiển thị mạo danh (Gmail giả 'Phòng Đào tạo'), Reply-To khác, "
                  "tên miền nhái (typo, homoglyph, chèn tên trường)"),
    ("Liên kết", "Chữ hiển thị ≠ địa chỉ thật, link rút gọn, IP, đuôi .top/.click/.xyz, đường dẫn đăng nhập"),
    ("Nội dung", "KD-BiLSTM của bài báo (giải thích bằng attention) + 8 nhóm thủ đoạn tâm lý (vi/en)"),
    ("Ảnh & QR", "OCR tiếng Việt (EasyOCR), giải mã QR (OpenCV); chữ trong ảnh được phân tích như nội dung"),
    ("Tệp đính kèm", "Phân tích tĩnh: magic bytes, đuôi kép .pdf.exe, macro Office, PDF JavaScript, "
                     "HTML đăng nhập giả / smuggling, ZIP có mật khẩu"),
]
SAMPLES = [
    ("Lịch thi cuối kỳ (thật)", "0", "An toàn"),
    ("Tài khoản sẽ bị khóa (cổ điển)", "100", "Rất nguy hiểm"),
    ("Học bổng - viết trau chuốt kiểu LLM", "94", "Rất nguy hiểm"),
    ("Chỉ có ảnh + mã QR", "98", "Rất nguy hiểm"),
    ("Biên lai học phí (tệp HTML)", "100", "Rất nguy hiểm"),
    ("Danh sách cảnh cáo (Word macro)", "100", "Rất nguy hiểm"),
    ("Hóa đơn (ZIP mật khẩu, .pdf.exe)", "100", "Rất nguy hiểm"),
    ("Thầy nhờ mua thẻ cào (BEC)", "78", "Rất nguy hiểm"),
    ("Workshop CLB (poster + QR, thật)", "5", "An toàn"),
    ("Điều chỉnh học phí (giả mạo tên miền trường, PDF JS)", "97", "Rất nguy hiểm"),
    ("Microsoft 365 password (English)", "99", "Rất nguy hiểm"),
    ("Bảo trì email (thật, có chữ 'mật khẩu')", "7", "An toàn"),
]


def robustness():
    return json.load(open(os.path.join(ROOT, "results", "robustness.json"), encoding="utf-8"))
