# Báo cáo: phát hiện email phishing do LLM viết bằng BiLSTM chưng cất từ MobileBERT

**Paper:** Eskandarian et al., *A lightweight defense mechanism against next-generation of phishing emails using distilled attention-augmented BiLSTM*, Journal of Information Security and Applications 101 (2026) 104552. Nhóm tác giả: Canadian Institute for Cybersecurity (UNB) và Mastercard.

---

## 1. Bài toán

- LLM giúp kẻ tấn công viết email phishing trôi chảy, lịch sự, giống hệt email công việc. Các bộ lọc dựa vào từ khóa ("urgent", "verify your account", …) hay danh tiếng URL/người gửi vì vậy bị qua mặt.
- Các mô hình transformer lớn (BERT, LLM) phát hiện tốt nhưng chậm và nặng, khó đặt trực tiếp ở mail gateway hay thiết bị đầu cuối. Gọi LLM qua API thì thêm độ trễ và rủi ro lộ dữ liệu email.
- **Mục tiêu:** một bộ phát hiện **nhỏ, nhanh, chạy được trên CPU/thiết bị**, nhưng vẫn **chịu được email phishing do LLM viết lại**.

## 2. Cách tiếp cận

### 2.1 Dữ liệu "nhận biết LLM"

- **Dữ liệu thật**: gộp 5 nguồn gồm Cambridge Phishing, Nazario, Chakraborty, Phishing Pot (phishing) và Enron (email hợp lệ), tổng khoảng 623.000 email.
- **Dữ liệu sinh**: dùng LLM thương mại (OpenAI, DeepSeek) viết lại email phishing theo 3 hành vi né tránh:
  - **Paraphrase**: diễn đạt lại để tránh khớp từ khóa.
  - **Masking**: làm mềm các dấu hiệu lộ liễu, chuyển sang giọng văn công sở.
  - **Personalization**: chèn tên, chức danh, dự án của người nhận cho giống email nội bộ.
- **Kiểm chứng rằng email sinh "khó" hơn**: tác giả đo độ tương đồng cosine TF‑IDF giữa email phishing và email hợp lệ. Email do LLM sinh gần email hợp lệ hơn email phishing gốc (Fig. 2).
- **Chấm điểm "mức phishing" bằng câu hỏi**: hỏi LLM một loạt câu cho mỗi email, chẳng hạn "có tạo cảm giác khẩn cấp không?", "link có đáng ngờ không?", "có giả danh quyền lực không?". Câu trả lời được gộp thành một điểm tổng, dùng để lọc mẫu sinh kém chất lượng và điều khiển việc sinh mẫu.
- **Khử trùng lặp**: từ khoảng 25.000 mẫu, loại khoảng 10.000 mẫu gần giống nhau, còn khoảng 14.000 mẫu.

### 2.2 Mô hình: đi từng bước, từ đơn giản đến phức tạp

| Bước | Mô hình | Ý tưởng |
|---|---|---|
| 1 | LSTM | Đọc email tuần tự, input là vector Word2Vec 100 chiều |
| 2 | BiLSTM | Đọc hai chiều để hiểu ngữ cảnh trước và sau mỗi từ |
| 3 | BiLSTM + single-head attention | Tập trung vào cụm từ "nguy hiểm" như *verify your account* |
| 4 | BiLSTM + multi-head attention (4 head) | Mỗi head bắt một loại tín hiệu khác nhau, ví dụ khẩn cấp, giả danh, xin mật khẩu |
| 5 | **KD-BiLSTM** (đề xuất) | Mô hình bước 4 học thêm từ một "thầy" MobileBERT |

### 2.3 Giải pháp chính: knowledge distillation

- **Teacher**: MobileBERT (25,3M tham số), fine-tune trên dữ liệu hỗn hợp gồm email thật và email do LLM sinh.
- **Student**: BiLSTM + multi-head attention (khoảng 4,5M tham số):
  - Dùng chung tokenizer WordPiece với teacher.
  - Lớp embedding được **khởi tạo bằng embedding của teacher**.
- **Hàm loss** gồm hai phần, mỗi phần chiếm 50%:
  - Học theo nhãn thật (cross-entropy).
  - Bắt chước phân phối xác suất "làm mềm" của teacher (KL divergence, nhiệt độ τ = 2).
- **Điểm khác so với distillation thông thường:**
  1. Teacher được fine-tune trên dữ liệu có cả email do LLM viết.
  2. Chưng cất **khác kiến trúc**: từ transformer sang mạng hồi quy.
  3. Student được kiểm tra cả khả năng **tổng quát hóa chéo phân phối**.

### 2.4 Cách đánh giá

5 kịch bản huấn luyện/kiểm thử, mỗi kịch bản chạy 5-fold, chia train/val/test = 72/8/20:

| Kịch bản | Ý nghĩa |
|---|---|
| Orig‑Orig | Train và test trên email thật |
| Gen‑Gen | Train và test trên email do LLM sinh |
| **Orig‑Gen** | Train trên email thật, test trên email LLM, tức là gặp kiểu tấn công mới |
| **Gen‑Orig** | Train trên email LLM, test trên email thật |
| Mixture | Trộn cả hai, gần với thực tế triển khai nhất |

So sánh với: MobileBERT, ModernBERT, DeBERTaV3, T5, DeepSeek‑R1‑Distill‑Qwen‑1.5B, Phi‑4‑mini, cùng các baseline nhẹ (Logistic Regression, XGBoost, fastText, TinyBERT, DistilBERT).

## 3. Kết quả của paper

**Tiến bộ qua từng bước (kịch bản Mixture, weighted F1 %):**

| Mô hình | Tham số | F1 | Thời gian test |
|---|---|---|---|
| LSTM | 17K | 91,32 | 0,83 s |
| BiLSTM | 34K | 91,65 | 1,30 s |
| + single-head | 67K | 93,48 | 1,37 s |
| + multi-head | 495K | 95,25 | 1,51 s |
| **KD-BiLSTM** | **4,5M** | **96,67** | **6,06 s** |
| MobileBERT (teacher) | 25,3M | 98,56 | 42 s |

**So với các transformer lớn (Mixture):**

| Mô hình | Tham số | F1 | Thời gian test |
|---|---|---|---|
| ModernBERT-base | 149M | 98,98 | 37,26 s |
| DeepSeek-R1 Distill Qwen-1.5B | 1.780M | 98,83 | 56,40 s |
| DeBERTaV3-base | 86M | 98,75 | 38,34 s |
| T5-base | 110M | 98,73 | 31,43 s |
| Phi-4-mini | 3.840M | 96,45 | 116,65 s |
| **KD-BiLSTM** | **4,5M** | **96,67** | **6,06 s** |

**Các kết luận chính:**
- KD-BiLSTM thấp hơn các transformer tốt nhất khoảng **1–2,5 điểm F1**. Đổi lại, nó **nhanh hơn 5–19 lần** khi suy luận và **nhỏ hơn 20–800 lần**.
- **Cách hiểu đúng về dữ liệu LLM:**
  - Mô hình chỉ học trên email thật, rồi gặp email LLM (Orig‑Gen), thì giảm mạnh độ chính xác: LSTM 82,17 F1, BiLSTM 79,93.
  - Mô hình chỉ học trên email LLM, rồi gặp email thật (Gen‑Orig), thì **bỏ sót phishing rất nhiều**: recall LSTM chỉ 45,10%, BiLSTM 51,19%.
  - Trộn hai nguồn dữ liệu (Mixture) cho kết quả ổn định nhất.
- **Multi-head attention** cải thiện rõ khả năng tổng quát hóa: recall Gen‑Orig tăng từ 51,19% lên 62,97%, F1 Orig‑Gen tăng từ 79,93 lên 92,40.
- **Distillation** nâng recall Gen‑Orig lên 98,24%. Tuy vậy precision ở hai kịch bản chéo vẫn thấp (82–90%), nghĩa là có nhiều cảnh báo nhầm hơn.
- **Baselines cổ điển** khá mạnh trên tập trộn: Logistic Regression + TF‑IDF đạt 95,67% accuracy. Đổi lại, các mô hình này được cho là dễ bị qua mặt bởi email LLM.

**Một số điểm cần lưu ý khi đọc paper:**
- **Số liệu kích thước dữ liệu không thống nhất**: Table 1 ghi 47.575 mẫu LLM, mục 3.2.2 ghi corpus cuối khoảng 14.000 mẫu, còn mỗi kịch bản dùng 13.692 mẫu.
- **Thiếu nhiều chi tiết** để tái lập chính xác: kiến trúc attention, cách pooling, ngưỡng lọc và khử trùng lặp, cách chia fold cho các kịch bản chéo, nội dung prompt sinh dữ liệu.
- **Dữ liệu và code chưa công bố** ("available on request").

## 4. Bản tái hiện của chúng ta đang ở đâu

| Thành phần | Paper | Bản tái hiện (notebook) | Trạng thái |
|---|---|---|---|
| Dữ liệu thật | 5 bộ, khoảng 623K email | Corpus "toy" tự sinh từ template | ⚠️ Thay thế tạm |
| Sinh email bằng LLM | OpenAI / DeepSeek | Đã có prompt cho 3 hành vi; mặc định dùng **luật giả lập** (thay từ đồng nghĩa, làm mềm câu chữ, chèn tên người nhận) | ⚠️ Giả lập |
| Phân tích tương đồng (Fig. 2) | TF‑IDF cosine | Đã làm, **cùng xu hướng**: email sinh gần email hợp lệ hơn (0,026 so với 0,002) | ✅ |
| Chấm điểm mức phishing | Hỏi LLM | Cùng bộ 9 câu hỏi, nhưng "trả lời" bằng đếm từ khóa; trọng số theo mức tương quan với nhãn | ⚠️ Giả lập |
| Khử trùng lặp | Có | Có, ngưỡng cosine tự chọn | ✅ |
| LSTM / BiLSTM / +SH / +MH | Có | Đủ cả 4 mô hình. LSTM và BiLSTM có số tham số gần như paper; 2 mô hình attention lệch do paper mô tả không đủ | ✅ |
| Teacher MobileBERT | 25,3M | 24,6M; cần thêm gradient clipping mới huấn luyện ổn định | ✅ |
| KD-BiLSTM | 4,5M, α = 0,5, τ = 2 | 4,4M, đúng công thức loss và Algorithm 1 | ✅ |
| 5 kịch bản × 5-fold, 72/8/20 | Có | Có (cách chia fold cho kịch bản chéo là cách hiểu của nhóm) | ✅ |
| So sánh ModernBERT, DeBERTa, T5, DeepSeek, Phi‑4 | Có | Chưa làm | ❌ |
| Baseline LR, XGBoost, fastText, TinyBERT, DistilBERT | Có | Chưa làm | ❌ |
| Biểu đồ radar độ chính xác, độ trễ, kích thước | Có | Chưa làm | ❌ |

**Tóm lại:**
- **Đã có:** toàn bộ "xương sống" phương pháp, từ dữ liệu đến 4 mô hình baseline, teacher, distillation và quy trình đánh giá 5 kịch bản. Notebook chạy thông trên Colab.
- **Chưa có ý nghĩa đánh giá:** dữ liệu toy quá dễ nên hầu hết mô hình đạt khoảng 96–100%. Chỉ có kịch bản Orig‑Gen cho thấy sụt giảm, khớp với nhận định của paper. Kết quả hiện tại **chưa so sánh được** với số liệu của paper.

## 5. Bước tiếp theo đề xuất

1. **Thu thập dữ liệu thật:** Nazario, Enron và Chakraborty có thể tải công khai. Cambridge phải xin quyền truy cập.
2. **Sinh email phishing bằng LLM thật**, ưu tiên LLM chạy cục bộ để không lộ dữ liệu, dùng prompt đã chuẩn bị sẵn. Sau đó thay bộ chấm điểm từ khóa bằng việc hỏi LLM.
3. **Chạy đủ 5-fold trên GPU** với độ dài 512 token như paper, rồi so với Tables 4–6.
4. **Bổ sung các baseline** ở Table 7 và Table 8, cùng biểu đồ đánh đổi độ chính xác, độ trễ và kích thước.
