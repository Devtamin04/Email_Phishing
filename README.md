# Email_Phishing — Phát hiện email lừa đảo thế hệ LLM

Dự án gồm hai phần:

| Phần | Thư mục | Nội dung |
|---|---|---|
| **1. Tái hiện bài báo** | `phishkd/`, `phishing_kd_bilstm.ipynb` | Mô hình KD-BiLSTM của *Eskandarian et al., JISA 101 (2026) 104552* |
| **2. PhishLens Edu** | `phishlens/` | Hệ thống phân tích rủi ro email **đa kênh, có giải thích**, có giao diện web, dùng cho trường học |

**Mục lục**
- [1. Cài đặt và chạy trên Windows (từng bước)](#1-cài-đặt-và-chạy-trên-windows-từng-bước)
- [2. Sử dụng giao diện](#2-sử-dụng-giao-diện)
- [3. Các tác vụ khác: train lại, tái hiện bài báo, thí nghiệm](#3-các-tác-vụ-khác)
- [4. Cài đặt thủ công bằng dòng lệnh](#4-cài-đặt-thủ-công-bằng-dòng-lệnh-cmd--powershell)
- [5. Xử lý lỗi thường gặp trên Windows](#5-xử-lý-lỗi-thường-gặp-trên-windows)
- [6. Linux / macOS](#6-linux--macos)
- [7. Cấu trúc dự án và chi tiết kỹ thuật](#7-cấu-trúc-dự-án-và-chi-tiết-kỹ-thuật)

---

## 1. Cài đặt và chạy trên Windows (từng bước)

### Yêu cầu

| Thành phần | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10 hoặc 11, bản 64-bit |
| Python | **3.10, 3.11 hoặc 3.12**, khuyến nghị 3.12 |
| RAM | Tối thiểu 8 GB; khuyến nghị 16 GB nếu muốn train lại KD-BiLSTM |
| Ổ đĩa | Khoảng 6 GB trống |
| Mạng | Cần Internet ở lần cài đầu tiên |
| GPU | **Không cần**: mọi thứ chạy được trên CPU |

### Bước 0 — Cài Python (bỏ qua nếu máy đã có Python 3.10–3.12)

1. Tải bộ cài **Windows installer (64-bit)** của Python 3.12 tại https://www.python.org/downloads/windows/
2. Chạy bộ cài. Ở màn hình đầu tiên, **tick ô "Add python.exe to PATH"**, rồi bấm *Install Now*.
3. Mở **Command Prompt** (nhấn `Win + R`, gõ `cmd`, Enter) và kiểm tra:
   ```bat
   py -3 --version
   ```
   Nếu kết quả là `Python 3.12.x` (hoặc 3.10/3.11) thì đã cài đúng.

### Bước 1 — Tải mã nguồn

**Cách 1: dùng Git**
```bat
cd /d D:\Projects
git clone https://github.com/Devtamin04/Email_Phishing.git
cd Email_Phishing
```

**Cách 2: không dùng Git.** Trên trang GitHub, bấm **Code → Download ZIP**, rồi giải nén vào một thư mục, ví dụ `D:\Projects\Email_Phishing`.

> **Lưu ý:** đặt dự án ở đường dẫn **không có dấu tiếng Việt và không có khoảng trắng**, ví dụ `D:\Projects\Email_Phishing`. Không nên đặt ở `C:\Users\Tên Có Dấu\Tài liệu\...`, vì một số thư viện có thể lỗi khi tạo môi trường ảo ở những đường dẫn như vậy.

### Bước 2 — Cài đặt thư viện: `setup.bat`

Mở thư mục dự án trong File Explorer, vào `scripts\windows\` và **nhấp đúp `setup.bat`**.

Script sẽ tự làm các việc sau, mất khoảng 5–15 phút tuỳ tốc độ mạng:
1. Tạo môi trường ảo `.venv` ngay trong thư mục dự án. Python của máy không bị ảnh hưởng.
2. Cài PyTorch bản CPU.
3. Cài các thư viện trong `requirements.txt`.
4. Kiểm tra cài đặt.

Cài thành công khi cửa sổ hiện:
```
OK - torch 2.x.x+cpu
Hoan tat! Buoc tiep theo: scripts\windows\run_app.bat
```

### Bước 3 — Chạy giao diện: `run_app.bat`

Repo **đã có sẵn** 12 email mẫu (`samples\`), mô hình đã train (`models\`) và kết quả thí nghiệm (`results\`). Vì vậy **không cần train lại**: nhấp đúp ngay **`scripts\windows\run_app.bat`**.

- Sau vài giây, trình duyệt tự mở **http://127.0.0.1:8765**.
- Cửa sổ đen (máy chủ) phải **để mở** trong lúc dùng. Muốn tắt thì đóng cửa sổ hoặc nhấn `Ctrl + C`.
- Máy chủ chỉ chạy trên máy của bạn (`127.0.0.1`), máy khác trong mạng không truy cập được. Email không được gửi đi đâu.
- Lần đầu phân tích một email có ảnh, EasyOCR sẽ tải mô hình nhận dạng chữ (khoảng 100 MB) nên hơi lâu. Các lần sau chỉ mất vài giây.

> `prepare.bat` chỉ cần chạy khi muốn **tạo lại** email mẫu hoặc **train lại** mô hình (xem mục 3).

---

## 2. Sử dụng giao diện

| Tab | Chức năng |
|---|---|
| **Phân tích email** | Chọn một trong 12 email mẫu ở cột trái, tải lên tệp `.eml`, hoặc dán nội dung thủ công. Kết quả gồm: điểm rủi ro 0–100, mức độ, loại tấn công, lý do kèm "bài học", mức rủi ro từng kênh (người gửi, liên kết, nội dung, ảnh/QR, tệp đính kèm), chữ đọc được trong ảnh, nội dung mã QR, phân tích tệp đính kèm |
| **Luyện tập nhận diện** | Tự đoán email an toàn hay lừa đảo, sau đó xem đáp án và phân tích; có bảng điểm |
| **Đánh giá độ bền** | Biểu đồ và bảng kết quả thí nghiệm khi email bị LLM viết lại, hoặc bị chuyển vào ảnh, QR, tệp đính kèm |
| **Giới thiệu** | Ý tưởng, quy trình xử lý, quyền riêng tư, giới hạn |

Ở góc phải trên có thể chọn **mô hình nội dung** (KD-BiLSTM của bài báo, hoặc TF-IDF) và bật/tắt **OCR ảnh**. Muốn mở thẳng một email mẫu, dùng đường dẫn dạng http://127.0.0.1:8765/?sample=s04_qr_m365

**Lấy tệp `.eml` từ hộp thư của bạn:**
- **Gmail (web):** mở email → bấm `⋮` (Thêm) → **Tải thư xuống** (*Download message*).
- **Outlook web / Outlook mới:** mở email → `⋯` → chọn lưu hoặc tải xuống dưới dạng `.eml`.
- **Thunderbird:** chuột phải vào email → **Lưu thành…** (*Save As*).
- Outlook bản cổ điển lưu email ra tệp `.msg`; hệ thống **chưa hỗ trợ** định dạng này.

> Các tệp "độc hại" trong `samples\` (macro, `.pdf.exe`, PDF có JavaScript, HTML đăng nhập giả) đều là **tệp giả vô hại**, chỉ dùng để minh hoạ. Hệ thống chỉ phân tích tĩnh và **không bao giờ mở hay chạy** tệp đính kèm.

---

## 3. Các tác vụ khác

Mỗi tác vụ có một file `.bat` tương ứng trong `scripts\windows\`. File không cần tham số thì nhấp đúp được. File có tham số thì chạy từ Command Prompt: mở thư mục dự án trong File Explorer, gõ `cmd` vào thanh địa chỉ, nhấn Enter, rồi gõ lệnh.

| Tác vụ | Lệnh | Thời gian (CPU) | Kết quả |
|---|---|---|---|
| Tạo lại email mẫu và train lại mô hình TF-IDF | `scripts\windows\prepare.bat` | < 1 phút | `samples\`, `models\linear.joblib` |
| Như trên, train thêm **KD-BiLSTM** (MobileBERT → BiLSTM) | `scripts\windows\prepare.bat kd` | 15–30 phút | `models\kd_bilstm\` |
| Tái hiện bài báo: dữ liệu + 4 baseline (1 fold) | `scripts\windows\run_paper.bat` | 2–5 phút | `results\results_summary.csv` |
| Tái hiện đầy đủ, có MobileBERT + KD-BiLSTM | `scripts\windows\run_paper.bat full` | vài giờ | `results\results_summary.csv` |
| Thí nghiệm độ bền (6 kịch bản × 4 bộ phát hiện) | `scripts\windows\run_robustness.bat` | 10–20 phút | `results\robustness.json` (hiện ở tab *Đánh giá độ bền*) |

> `prepare.bat` sẽ **ghi đè** mô hình có sẵn trong `models\`. Nếu chỉ chạy `prepare.bat` (không có `kd`), mô hình KD-BiLSTM có sẵn vẫn được giữ nguyên.

**Máy yếu?** Có thể chạy phần tái hiện bài báo trên **Google Colab**: tải `phishing_kd_bilstm.ipynb` lên https://colab.research.google.com, chọn *Runtime → Change runtime type → GPU*, rồi *Runtime → Run all*.

---

## 4. Cài đặt thủ công bằng dòng lệnh (CMD / PowerShell)

Phần này dành cho trường hợp muốn tự gõ lệnh thay vì dùng file `.bat`, ví dụ để xem chi tiết lỗi. Không cần "activate" môi trường ảo: chỉ cần gọi trực tiếp `.venv\Scripts\python`.

**Command Prompt (cmd):**
```bat
cd /d D:\Projects\Email_Phishing

:: 1. Tạo môi trường ảo
py -3 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip

:: 2. Cài PyTorch bản CPU trước, rồi các thư viện còn lại
.venv\Scripts\python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python -m pip install -r requirements.txt

:: 3. Cho phép in tiếng Việt ra console
set PYTHONUTF8=1

:: 4. (tuỳ chọn) tạo lại email mẫu và train lại mô hình; thêm --kd để train KD-BiLSTM
.venv\Scripts\python scripts\build_samples.py
.venv\Scripts\python scripts\train_text_models.py

:: 5. Chạy giao diện, rồi mở http://127.0.0.1:8765
.venv\Scripts\python -m uvicorn phishlens.app:app --host 127.0.0.1 --port 8765
```

**PowerShell:** dùng đúng các lệnh trên, chỉ khác hai điểm: dòng chú thích bắt đầu bằng `#` thay cho `::`, và biến môi trường đặt bằng lệnh sau thay cho `set PYTHONUTF8=1`:
```powershell
$env:PYTHONUTF8 = "1"
```

**Tái hiện bài báo và thí nghiệm bằng lệnh:**
```bat
.venv\Scripts\python scripts\prepare_data.py
.venv\Scripts\python scripts\run_experiments.py --models lstm,bilstm,bilstm_sh,bilstm_mh --max-folds 1
.venv\Scripts\python scripts\run_experiments.py --models teacher,kd --bert-max-len 128 --max-folds 1
.venv\Scripts\python scripts\robustness_eval.py --n 30
```

**Có GPU NVIDIA?** Ở bước 2, thay `.../whl/cpu` bằng bản CUDA phù hợp với máy (ví dụ `.../whl/cu121`). Code tự dùng GPU nếu có.

---

## 5. Xử lý lỗi thường gặp trên Windows

| Hiện tượng | Nguyên nhân / cách xử lý |
|---|---|
| `'python' is not recognized…` hoặc `'py' is not recognized…` | Python chưa có trong PATH. Cài lại Python và tick **Add python.exe to PATH** |
| `setup.bat` báo lỗi ngay khi tạo `.venv` | Kiểm tra lại `py -3 --version`. Nếu bản Python là 3.13 trở lên, cài thêm Python 3.12 rồi chạy lại `setup.bat` |
| `UnicodeEncodeError` khi in tiếng Việt | Chưa đặt mã hoá UTF-8. Chạy `set PYTHONUTF8=1` (CMD) hoặc `$env:PYTHONUTF8="1"` (PowerShell). Các file `.bat` đã tự đặt sẵn |
| `DLL load failed while importing _C` (khi import torch) | Thiếu Microsoft Visual C++ Redistributable. Cài bản **x64** tại https://aka.ms/vs/17/release/vc_redist.x64.exe rồi mở lại cửa sổ lệnh |
| `operator torchvision::nms does not exist` | torch và torchvision lệch phiên bản. Chạy lại lệnh sau: `.venv\Scripts\python -m pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cpu` |
| Windows Defender cảnh báo hoặc xoá tệp trong `samples\` | Các email mẫu có chứa tệp giả mô phỏng mã độc (vô hại). Khôi phục tệp trong *Windows Security → Protection history*, hoặc chạy `prepare.bat` để tạo lại |
| `[Errno 10048]` / *address already in use* | Cổng 8765 đang bị chiếm (có thể bởi một cửa sổ `run_app.bat` khác). Đóng cửa sổ đó, hoặc sửa `8765` trong `run_app.bat` thành cổng khác, ví dụ `8800` |
| Trình duyệt mở ra nhưng báo *không kết nối được* | Máy chủ chưa khởi động xong. Đợi thêm vài giây rồi bấm F5 |
| Windows Firewall hỏi quyền truy cập mạng | Có thể bấm *Cancel*: máy chủ chỉ chạy trên `127.0.0.1`, không cần mở ra mạng ngoài |
| Phân tích email có ảnh lần đầu rất lâu hoặc bị lỗi tải | EasyOCR đang tải mô hình (cần Internet). Nếu mạng chặn, bỏ tick **OCR ảnh** trên giao diện, hoặc đặt `OCR_ENABLED = False` trong `phishlens\config.py` |
| `pip` báo lỗi mạng hoặc timeout | Chạy lại `setup.bat`. Nếu dùng mạng trường hoặc công ty có proxy, đặt biến `HTTPS_PROXY` trước khi chạy |
| Chép dự án sang máy khác thì không chạy | Thư mục `.venv` không chép được giữa các máy. Xoá `.venv` rồi chạy lại `setup.bat` |

---

## 6. Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn phishlens.app:app --host 127.0.0.1 --port 8765
```
Các script trong `scripts/` dùng như trên Windows, chỉ cần thay `.venv\Scripts\python` bằng `.venv/bin/python`.

---

## 7. Cấu trúc dự án và chi tiết kỹ thuật

```
Email_Phishing/
├── phishkd/                 # Phần 1: tái hiện bài báo (dữ liệu, LSTM/BiLSTM/attention, MobileBERT, KD)
├── phishlens/               # Phần 2: PhishLens Edu
│   ├── config.py            #   cấu hình theo trường: tên trường, tên miền chính thức, bật/tắt OCR
│   └── web/                 #   giao diện (HTML/CSS/JS)
├── scripts/                 # script tạo dữ liệu, train, thí nghiệm
│   └── windows/             #   setup.bat, prepare.bat, run_app.bat, run_paper.bat, run_robustness.bat
├── samples/                 # 12 email mẫu (.eml)
├── models/                  # mô hình đã train: linear.joblib, kd_bilstm/
├── results/                 # kết quả thí nghiệm
├── report/                  # báo cáo và slide
├── phishing_kd_bilstm.ipynb # notebook chạy trên Google Colab
└── requirements.txt
```

### Phần 2 — PhishLens Edu: các module

| Module | Vai trò |
|---|---|
| `parser.py` | Đọc .eml (MIME): header, văn bản/HTML, liên kết, ảnh, tệp đính kèm |
| `sender_links.py` | SPF/DKIM/DMARC, tên hiển thị mạo danh, Reply-To, tên miền giả (typo, homoglyph, chèn tên thương hiệu); phân tích từng URL |
| `content.py` | 8 nhóm dấu hiệu thao túng tâm lý (vi/en) và mô hình văn bản (KD-BiLSTM của bài báo, giải thích bằng attention; hoặc TF-IDF+LR) |
| `media.py` | Ảnh: giải mã QR, OCR. Tệp đính kèm: magic bytes, đuôi kép, macro, PDF JavaScript, HTML đăng nhập giả / smuggling, ZIP có mật khẩu |
| `engine.py` | Kết hợp bằng chứng (noisy-OR) → điểm 0–100, mức độ, loại tấn công, kỹ thuật né tránh, lời khuyên |
| `synth.py` | Corpus email trường học tiếng Việt và các phép biến đổi kiểu LLM; template được chia train / held-out |
| `app.py`, `web/` | Giao diện: phân tích email, luyện tập nhận diện, đánh giá độ bền, giới thiệu |

### Phần 1 — phishkd: tái hiện bài báo KD-BiLSTM

Bài báo: *Eskandarian et al., "A lightweight defense mechanism against next-generation of phishing
emails using distilled attention-augmented BiLSTM", JISA 101 (2026) 104552.*

Mục tiêu: dựng lại pipeline để học hỏi (chưa nhằm tái lập số liệu).

#### Chạy (Linux/macOS; trên Windows dùng `run_paper.bat` hoặc thay `.venv/bin/python` bằng `.venv\Scripts\python`)

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

#### Bài báo ↔ code

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

#### Những chỗ tự quyết định vì bài báo không nói rõ

- **Dữ liệu**: không có sẵn các bộ Cambridge, Nazario, Enron, … ở đây. Script dùng corpus toy sinh từ template, nên các mô hình đạt điểm gần tuyệt đối. Con số này chỉ để kiểm tra pipeline, không có ý nghĩa đánh giá.
- **Kịch bản chéo (Orig-Gen / Gen-Orig)**: chạy K-fold song song trên cả hai miền. Mỗi fold huấn luyện trên tập train của miền này và kiểm thử trên fold tương ứng của miền kia.
- **Chọn epoch**: giữ checkpoint có weighted‑F1 tốt nhất trên tập validation 8%.
- **Pooling sau attention**: dùng masked average pooling.
- **Kích thước baseline**: LSTM/BiLSTM dùng hidden=32 để số tham số gần với Table 4 (~17k / ~34k). Các mô hình attention dùng hidden=64 mỗi chiều, tức 128 ở đầu ra BiLSTM (Table 2).
- **Logit của teacher trong KD**: tính một lần rồi cache. Teacher đã đóng băng và chạy ở chế độ eval nên kết quả tương đương bước 5 của Algorithm 1 (muốn chạy đúng từng batch thì đặt `cache_teacher_logits=False`).
- **Số tham số của student** ≈ 4.4M, trong đó embedding WordPiece 30522×128 chiếm khoảng 3.9M. Con số này khớp với mức 4.5M trong bài.
- **Fine-tune MobileBERT**: pooler của MobileBERT lấy thẳng hidden state [CLS] mà không qua tanh, nên giá trị rất lớn và loss lúc đầu lên tới khoảng 10⁷. Code xử lý bằng gradient clipping (`max_grad_norm=1.0`, giống mặc định của HF Trainer) và `teacher_min_steps=120`. Nếu thiếu hai điều này, teacher sẽ sụp về dự đoán một lớp khi tập train nhỏ.
