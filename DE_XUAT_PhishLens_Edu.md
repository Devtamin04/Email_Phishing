# Đề xuất hướng nghiên cứu: PhishLens Edu

**Tên đề tài (dự kiến):** Phân tích rủi ro email lừa đảo đa kênh có giải thích, bền vững trước phishing do LLM tạo và biến đổi — ứng dụng trong môi trường giáo dục

*Multimodal, explainable phishing-risk analysis robust to LLM-generated and modality-shifted phishing, for educational institutions*

---

## 1. Vì sao không đi tiếp theo hướng của bài báo

Bài báo gốc (Eskandarian et al., JISA 2026) chưng cất MobileBERT thành một BiLSTM nhỏ để **phân loại văn bản email** thành lừa đảo hoặc không. Khi áp dụng thực tế, cách làm này vướng ba điểm:

1. **Các trường đã có bộ lọc.** Gmail và Microsoft 365 Defender đã chặn phần lớn thư rác và lừa đảo phổ biến. Thêm một bộ phân loại văn bản nữa không tạo ra nhiều giá trị.
2. **Email thật có ảnh và tệp.** Kẻ tấn công ngày càng giấu thông điệp vào ảnh, mã QR, PDF, tệp HTML hay tệp nén có mật khẩu. Mô hình chỉ đọc thân thư thì không thấy được những nội dung này.
3. **Chỉ trả lời "có/không".** Người dùng không biết *vì sao* email nguy hiểm, nên lần sau vẫn dễ bị lừa.

## 2. Ý tưởng

Không xây dựng hệ thống thay thế Gmail hay Defender. Thay vào đó, xây dựng **một lớp "ý kiến thứ hai có giải thích"** cho những email *đã lọt vào hộp thư*:

- **Phân tích đa kênh**: người gửi (SPF/DKIM/DMARC, mạo danh, tên miền giả), liên kết, nội dung, **hình ảnh (OCR + giải mã QR)** và **tệp đính kèm** (phân tích tĩnh, không bao giờ mở hay chạy tệp).
- **Đánh giá mức độ** thay vì chỉ nhị phân: điểm rủi ro 0–100, chia 4 mức (An toàn / Cần chú ý / Nguy hiểm / Rất nguy hiểm). Kèm theo là **loại tấn công** (đánh cắp tài khoản, lừa chuyển tiền, mã độc, QR, dụ dỗ) và **kỹ thuật né tránh** được dùng.
- **Giải thích bằng tiếng Việt**: mỗi dấu hiệu đi kèm lý do và một "bài học" ngắn. Chế độ **luyện tập nhận diện** giúp sinh viên và cán bộ tự rèn kỹ năng.
- **Kế thừa bài báo**: mô hình nội dung chính là KD-BiLSTM của bài báo. Trọng số attention của nó được tận dụng để chỉ ra những từ mà mô hình chú ý.

**Vị trí trong thực tế:** người dùng chuyển tiếp email nghi ngờ vào một hộp thư "kiểm tra giúp tôi" của trường (hoặc dùng add-in cho Outlook/Gmail), và nhận lại báo cáo giải thích. Bộ phận CNTT dùng chính báo cáo đó để xử lý sự cố. Mọi xử lý chạy trên máy chủ nội bộ, không gửi email ra dịch vụ bên ngoài.

## 3. Câu hỏi nghiên cứu

- **RQ1.** Bộ phát hiện chỉ dựa vào văn bản (như KD-BiLSTM của bài báo) suy giảm ra sao khi email lừa đảo được **LLM viết lại**, hoặc khi thông điệp bị **chuyển sang ảnh, mã QR, tệp đính kèm**?
- **RQ2.** Kết hợp bằng chứng đa kênh có khôi phục được khả năng phát hiện mà **không làm tăng báo nhầm** trên email hợp lệ (vốn cũng có ảnh, QR, tệp) không?
- **RQ3** *(giai đoạn sau).* Lời giải thích và chế độ luyện tập có giúp người dùng nhận diện tốt hơn không? Đo bằng bài kiểm tra trước và sau khi dùng.

## 4. Phương pháp

| Bước | Nội dung |
|---|---|
| 1. Tách email | Đọc tệp .eml (MIME): header, văn bản/HTML, liên kết (cả chữ hiển thị và địa chỉ thật), ảnh, tệp đính kèm |
| 2. Phân tích đa kênh | **Người gửi**: SPF/DKIM/DMARC, tên hiển thị mạo danh đơn vị nhưng gửi từ Gmail, Reply-To khác người gửi, tên miền nhái (gõ sai, ký tự giống nhau, chèn tên trường vào tên miền khác)<br>**Liên kết**: chữ hiển thị khác địa chỉ thật, link rút gọn, IP, đuôi tên miền hay bị lạm dụng, đường dẫn đăng nhập<br>**Nội dung**: KD-BiLSTM, cùng 8 nhóm thủ đoạn tâm lý (áp lực thời gian, đe dọa, dụ dỗ, đòi mật khẩu/OTP, đòi chuyển tiền, yêu cầu giữ bí mật, hướng dẫn thao tác nguy hiểm, lời chào chung chung)<br>**Ảnh**: OCR tiếng Việt, giải mã QR; chữ đọc được trong ảnh lại được phân tích như nội dung<br>**Tệp**: nhận dạng loại thật bằng magic bytes, đuôi kép (.pdf.exe), macro Office, PDF có JavaScript hoặc lệnh tự chạy, HTML có ô mật khẩu hoặc HTML smuggling, ZIP có mật khẩu (vẫn đọc được tên tệp bên trong) |
| 3. Kết hợp | Mỗi dấu hiệu có một độ mạnh. Gộp theo kiểu noisy-OR thành điểm từng kênh và điểm tổng; suy ra loại tấn công và kỹ thuật né tránh |
| 4. Giải thích | Danh sách lý do kèm bài học, tô sáng cụm từ đáng ngờ, liệt kê liên kết thật, lời khuyên theo mức độ và loại tấn công |

**Dữ liệu:**
- Một corpus email trường học tiếng Việt (tổng hợp) gồm 15 dạng tấn công và 21 dạng email hợp lệ. Trong số email hợp lệ có cả những email "khó", chẳng hạn email thật có link, QR, tệp đính kèm, hoặc nhắc tới "mật khẩu" hay "học bổng".
- Thêm phần dữ liệu tiếng Anh từ bản tái hiện bài báo.
- Các phép biến đổi kiểu LLM (paraphrase / masking / personalization) giống bài báo.
- **Template được chia thành nhóm train và nhóm held-out**, để thí nghiệm đo khả năng tổng quát hóa sang những cách viết mà mô hình chưa từng thấy.

## 5. Thí nghiệm độ bền (RQ1–RQ2)

Mỗi email lừa đảo lấy từ template held-out được biến đổi theo 6 kịch bản. Email hợp lệ được biến đổi theo đúng các kịch bản đó, để đo báo nhầm. Header người gửi được giữ trung tính, để chỉ còn "cách mang thông điệp" thay đổi.

| Kịch bản | Mô tả |
|---|---|
| Gốc | Thông điệp nằm trong thân thư |
| LLM viết lại | paraphrase + masking + personalization |
| Chuyển vào ảnh | Thông điệp (đã viết lại) nằm trong ảnh, thân thư gần như trống |
| Ảnh + mã QR | Như trên; liên kết được giấu trong mã QR |
| Tệp Word | Thông điệp nằm trong tệp .docx |
| Tệp HTML | Thông điệp nằm trong tệp .html |

So sánh bốn bộ phát hiện:
- chỉ đọc văn bản, dùng TF-IDF;
- chỉ đọc văn bản, dùng KD-BiLSTM (mô hình của bài báo);
- PhishLens đa kênh, dùng TF-IDF;
- PhishLens đa kênh, dùng KD-BiLSTM.

### Kết quả sơ bộ

30 email lừa đảo và 30 email hợp lệ cho mỗi kịch bản, lấy từ template held-out. Ngưỡng: điểm ≥ 50 với hệ đa kênh, P ≥ 0,5 với mô hình chỉ đọc văn bản.

| Kịch bản | Phát hiện: chỉ văn bản (TF-IDF / KD-BiLSTM) | Phát hiện: đa kênh (TF-IDF / KD-BiLSTM) | Báo nhầm: đa kênh (TF-IDF / KD-BiLSTM) |
|---|---|---|---|
| Gốc | 80% / 67% | 80% / 80% | 0% / 10% |
| LLM viết lại | 67% / 60% | 80% / 80% | 0% / 10% |
| Chuyển vào ảnh | 0% / 0% | 90% / 97% | 0% / 17% |
| Ảnh + mã QR | 0% / 0% | 100% / 100% | 7% / 20% |
| Tệp Word | 0% / 0% | 70% / 57% | 0% / 10% |
| Tệp HTML | 0% / 0% | 100% / 100% | 0% / 17% |

**Nhận xét:**

1. **LLM viết lại làm giảm khả năng phát hiện của mô hình chỉ đọc văn bản**: TF-IDF giảm từ 80% xuống 67%, KD-BiLSTM từ 67% xuống 60%. Hệ đa kênh giữ nguyên ở 80%.
2. **Chỉ cần chuyển thông điệp sang ảnh, QR hay tệp đính kèm là mô hình chỉ đọc thân thư mất khả năng phát hiện hoàn toàn (0%).** Hệ đa kênh phục hồi được 57–100%, nhờ OCR, giải mã QR và trích xuất văn bản từ tệp. Đây là câu trả lời trực tiếp cho câu hỏi "email có ảnh và file thì phát hiện thế nào".
3. **Loại khó nhất là lừa chuyển tiền hoặc mạo danh thầy cô nhờ mua thẻ cào (BEC).** Thí nghiệm cố ý giữ header người gửi trung tính, và trong điều kiện đó hệ đa kênh vẫn bỏ sót 50%. Lý do là loại này không có link hay tệp, nên tín hiệu mạnh nhất nằm ở người gửi. Trong email mẫu thật (gửi từ Gmail, đặt tên hiển thị "Trưởng khoa"), hệ thống chấm 78/100, dù mô hình văn bản chỉ cho P = 4%.
4. **Giới hạn của mô hình bài báo khi chuyển sang tiếng Việt:**
   - Trên email hợp lệ chưa từng thấy, KD-BiLSTM báo nhầm 14%, trong khi TF-IDF chỉ báo nhầm 1% (cùng nằm trong hệ đa kênh).
   - Nguyên nhân có thể là tokenizer MobileBERT (tiếng Anh) xóa dấu tiếng Việt.
   - Cần một teacher đa ngôn ngữ (PhoBERT, XLM-R), hoặc hiệu chỉnh lại ngưỡng.
5. **Bài học về "học đường tắt".** Phiên bản đầu của mô hình văn bản báo nhầm cả email hợp lệ có link chính thức của trường. Nguyên nhân là trong dữ liệu tổng hợp, chỉ email lừa đảo mới chứa tên miền. Cách khắc phục là che URL và địa chỉ email trước khi đưa vào mô hình văn bản (đã có bộ phân tích liên kết riêng), đồng thời bổ sung email hợp lệ "khó". Điều này cho thấy mô hình chỉ đọc văn bản rất dễ học mẹo từ dữ liệu. Tách bạch từng kênh phân tích giúp hệ thống bền vững hơn.

*Lưu ý: đây là dữ liệu tổng hợp, và "LLM viết lại" mới là bộ luật mô phỏng. Các con số chỉ thể hiện xu hướng, cần kiểm chứng lại trên dữ liệu thật.*

## 5b. Prototype

Giao diện web chạy cục bộ, gồm 4 tab:

- **Phân tích email**: tải tệp .eml lên, dán nội dung, hoặc chọn từ 12 email mẫu (thật, cổ điển, viết lại kiểu LLM, ảnh + QR, HTML đăng nhập giả, macro, ZIP có mật khẩu chứa .pdf.exe, mạo danh thầy nhờ mua thẻ cào, PDF có JavaScript). Kết quả gồm điểm rủi ro, mức rủi ro theo từng kênh, danh sách lý do kèm bài học, cụm từ đáng ngờ được tô sáng, địa chỉ thật của từng liên kết, chữ OCR và nội dung QR trong ảnh, phân tích tệp đính kèm, và lời khuyên.
- **Luyện tập nhận diện**: người dùng tự đoán trước, sau đó xem đáp án và phân tích. Có bảng điểm và chuỗi trả lời đúng.
- **Đánh giá độ bền**: biểu đồ và bảng số liệu của thí nghiệm ở mục 5.
- **Giới thiệu**: ý tưởng, quy trình xử lý, quyền riêng tư và giới hạn.

## 6. Đóng góp dự kiến

1. **Bộ dữ liệu thử nghiệm** email trường học tiếng Việt, kèm các phép biến đổi kiểu LLM và chuyển kênh (ảnh, QR, tệp). Template được chia train/held-out.
2. **Đánh giá độ bền** của mô hình trong bài báo trước phishing do LLM tạo ra và phishing chuyển kênh. Kèm phân tích lỗi "học đường tắt" của mô hình văn bản (mục 5).
3. **Prototype PhishLens Edu**: phân tích đa kênh, có giải thích bằng tiếng Việt, có chế độ luyện tập. Chạy hoàn toàn cục bộ, cấu hình được theo từng trường.

## 7. Hạn chế và kế hoạch tiếp theo

- **Dữ liệu tổng hợp**: cần thu thập email lừa đảo thật mà trường đã nhận (ẩn danh hóa). Nguồn có thể là hộp thư báo cáo phishing của Phòng CNTT.
- **"LLM viết lại" hiện mới là bộ luật mô phỏng**: cần thay bằng LLM thật chạy cục bộ (ví dụ qua Ollama, code đã có sẵn chỗ cắm) để tạo biến thể đa dạng hơn.
- **Tokenizer**: MobileBERT không giữ dấu tiếng Việt, nên cân nhắc chưng cất từ một teacher đa ngôn ngữ (PhoBERT, XLM-R).
- **RQ3**: khảo sát người dùng với sinh viên (bài kiểm tra nhận diện trước và sau 2 tuần dùng chế độ luyện tập).
- **Tích hợp**: add-in Outlook/Gmail, hoặc hộp thư "chuyển tiếp để kiểm tra".
- **Phạm vi**: chưa kiểm tra danh tiếng URL trực tuyến, chưa chạy tệp trong sandbox; đây là các hướng có thể mở rộng.
