# Dự án: phát hiện email lừa đảo thế hệ LLM

Thư mục này có hai phần:

| Phần | Thư mục | Nội dung |
|---|---|---|
| **1. Tái hiện bài báo** | `phishkd/`, `scripts/run_experiments.py`, `phishing_kd_bilstm.ipynb` | KD-BiLSTM của Eskandarian et al. (JISA 2026) |
| **2. Hướng mới: PhishLens Edu** | `phishlens/`, `scripts/build_samples.py`, `scripts/train_text_models.py`, `scripts/robustness_eval.py` | Hệ thống phân tích rủi ro email **đa kênh, có giải thích**, kèm giao diện web cho trường học |

## PhishLens Edu — chạy nhanh

```bash
# cài thêm (ngoài phần của phishkd)
.venv/bin/pip install fastapi "uvicorn[standard]" python-multipart pillow opencv-python-headless qrcode pypdf easyocr
.venv/bin/pip install --force-reinstall --no-deps torch torchvision --index-url https://download.pytorch.org/whl/cpu

.venv/bin/python scripts/build_samples.py            # 12 email mẫu -> samples/
.venv/bin/python scripts/train_text_models.py --kd   # TF-IDF + KD-BiLSTM -> models/
.venv/bin/python scripts/robustness_eval.py --n 30   # thí nghiệm độ bền -> results/robustness.json
.venv/bin/python -m uvicorn phishlens.app:app --host 127.0.0.1 --port 8765
# mở http://127.0.0.1:8765   (mở thẳng một mẫu: http://127.0.0.1:8765/?sample=s04_qr_m365)
```

- **Cấu hình theo trường**: tên trường, tên miền chính thức, danh sách thương hiệu hay bị giả mạo, bật/tắt OCR đều nằm trong [phishlens/config.py](phishlens/config.py).
- **OCR** dùng EasyOCR (vi + en). Lần chạy đầu sẽ tải trọng số khoảng 100MB về máy. Mọi phân tích đều chạy cục bộ.
- **Tệp "độc hại" trong `samples/`** đều là tệp giả vô hại (không có mã thật), chỉ dùng để minh họa cách phát hiện.

| Module | Vai trò |
|---|---|
| `parser.py` | Đọc .eml (MIME): header, văn bản/HTML, liên kết, ảnh, tệp đính kèm |
| `sender_links.py` | SPF/DKIM/DMARC, tên hiển thị mạo danh, Reply-To, tên miền giả (typo, homoglyph, chèn tên thương hiệu); phân tích từng URL |
| `content.py` | 8 nhóm dấu hiệu thao túng tâm lý (vi/en) + mô hình văn bản (KD-BiLSTM của bài báo, giải thích bằng attention; hoặc TF-IDF+LR) |
| `media.py` | Ảnh: giải mã QR, OCR; tệp đính kèm: magic bytes, đuôi kép, macro, PDF JavaScript, HTML đăng nhập giả / smuggling, ZIP có mật khẩu |
| `engine.py` | Kết hợp bằng chứng (noisy-OR) → điểm 0–100, mức độ, loại tấn công, kỹ thuật né tránh, lời khuyên |
| `synth.py` | Corpus email trường học tiếng Việt và các phép biến đổi kiểu LLM; template được chia train / held-out |
| `app.py`, `web/` | Giao diện: phân tích email, luyện tập nhận diện, đánh giá độ bền, giới thiệu |

---

# Phần 1 — phishkd: tái hiện bài báo KD-BiLSTM

Bài báo: *Eskandarian et al., "A lightweight defense mechanism against next-generation of phishing
emails using distilled attention-augmented BiLSTM", JISA 101 (2026) 104552.*

Mục tiêu: dựng lại pipeline để học hỏi (chưa nhằm tái lập số liệu).

## Cài đặt (venv cô lập)

```bash
python3 -m venv .venv
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install transformers gensim scikit-learn pandas tqdm
```

## Chạy

```bash
# 1) Dữ liệu (Sec. 3): toy corpus + sinh "LLM" rule-based + chấm điểm + khử trùng lặp
.venv/bin/python scripts/prepare_data.py
#    dùng dữ liệu thật:   --input my.csv   (cột text,label,source; source ∈ {orig, gen})
#    dùng LLM local:      --ollama llama3  (Ollama chạy trên máy, không gửi dữ liệu ra ngoài)

# 2) Baselines (Tables 4-5)
.venv/bin/python scripts/run_experiments.py --models lstm,bilstm,bilstm_sh,bilstm_mh

# 3) Teacher MobileBERT + KD student (Table 6) — trên CPU nên giảm độ dài
.venv/bin/python scripts/run_experiments.py --models teacher,kd --bert-max-len 128
```

Kết quả theo từng fold được ghi vào `results/results.csv`, còn kết quả trung bình (như các bảng 4–7) ở `results/results_summary.csv`.

## Bài báo ↔ code

| Bài báo | Code |
|---|---|
| 3.2: 3 hành vi né tránh (paraphrase / masking / personalization) | [phishkd/augment.py](phishkd/augment.py): `PROMPTS`, `LLMAugmenter`, `RuleAugmenter` |
| Fig. 2: cosine TF-IDF giữa email phishing và email hợp lệ | [phishkd/analysis.py](phishkd/analysis.py): `similarity_to_legit` |
| 3.2.1: chấm "mức phishing" bằng bộ câu hỏi, trọng số theo mức khớp với nhãn | `QUESTIONS`, `phishing_level`, `filter_low_confidence` |
| 3.2.2: khử trùng lặp | `deduplicate` |
| 4.1: tiền xử lý + Word2Vec CBOW 100d | [phishkd/text.py](phishkd/text.py) |
| 4.2–4.6: LSTM, BiLSTM, +single-head, +multi-head (H=4, D=64; Table 2) | [phishkd/models.py](phishkd/models.py) |
| 4.7: teacher MobileBERT | `build_teacher`, `train_teacher` |
| 4.8.1: student, embedding khởi tạo từ teacher (Eq. 24), residual + LayerNorm, avg pool, 2 logit | `KDStudent` |
| Eqs. 20–23: α·CE + (1−α)·τ²·KL | `distillation_loss` |
| Algorithm 1 | [phishkd/train.py](phishkd/train.py): `distill` |
| 5.2: 5 kịch bản, 5-fold, chia 72/8/20 | [phishkd/data.py](phishkd/data.py): `scenario_folds` |

## Những chỗ tự quyết định vì bài báo không nói rõ

- **Dữ liệu**: không có sẵn các bộ Cambridge, Nazario, Enron, … ở đây. Script dùng corpus toy sinh từ template, nên các mô hình đạt điểm gần tuyệt đối. Con số này chỉ để kiểm tra pipeline, không có ý nghĩa đánh giá.
- **Kịch bản chéo (Orig-Gen / Gen-Orig)**: chạy K-fold song song trên cả hai miền. Mỗi fold huấn luyện trên tập train của miền này và kiểm thử trên fold tương ứng của miền kia.
- **Chọn epoch**: giữ checkpoint có weighted‑F1 tốt nhất trên tập validation 8%.
- **Pooling sau attention**: dùng masked average pooling.
- **Kích thước baseline**: LSTM/BiLSTM dùng hidden=32 để số tham số gần với Table 4 (~17k / ~34k). Các mô hình attention dùng hidden=64 mỗi chiều, tức 128 ở đầu ra BiLSTM (Table 2).
- **Logit của teacher trong KD**: tính một lần rồi cache. Teacher đã đóng băng và chạy ở chế độ eval nên kết quả tương đương bước 5 của Algorithm 1 (muốn chạy đúng từng batch thì đặt `cache_teacher_logits=False`).
- **Số tham số của student** ≈ 4.4M, trong đó embedding WordPiece 30522×128 chiếm khoảng 3.9M. Con số này khớp với mức 4.5M trong bài.
- **Fine-tune MobileBERT**: pooler của MobileBERT lấy thẳng hidden state [CLS] mà không qua tanh, nên giá trị rất lớn và loss lúc đầu lên tới khoảng 10⁷. Code xử lý bằng gradient clipping (`max_grad_norm=1.0`, giống mặc định của HF Trainer) và `teacher_min_steps=120`. Nếu thiếu hai điều này, teacher sẽ sụp về dự đoán một lớp khi tập train nhỏ.
# Email_Phishing
