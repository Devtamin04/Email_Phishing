"""Nội dung báo cáo (khoảng 30 trang). Mỗi khối:
("h1", tên chương) · ("h2", tên mục) · ("p", đoạn; hỗ trợ **đậm**) · ("eq", công thức; _{} ^{})
("tab", chú thích, rows, độ rộng cột cm, cỡ chữ) · ("fig", ảnh, chú thích, rộng cm)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "results", "robustness.json"), encoding="utf-8"))


def pct(v):
    return f"{100 * v:.0f}%"


def rob_rows():
    rows = [("Kịch bản", "VB TF-IDF", "VB KD", "ĐK TF-IDF", "ĐK KD")]
    for t in R["transforms"]:
        k = t["key"]
        rows.append((t["label"], *[pct(R["tpr"][k][d][  "rate"]) for d in
                                    ("text_linear", "text_kd", "full_linear", "full_kd")]))
    return rows


def fpr_rows():
    rows = [("Kịch bản", "VB TF-IDF", "VB KD", "ĐK TF-IDF", "ĐK KD")]
    for t in R["transforms"]:
        k = t["key"]
        rows.append((t["label"], *[pct(R["fpr"][k][d]["rate"]) for d in
                                    ("text_linear", "text_kd", "full_linear", "full_kd")]))
    return rows


BLOCKS = [
    # =====================================================================================
    ("h1", "BỐI CẢNH VÀ VẤN ĐỀ NGHIÊN CỨU"),
    ("h2", "Email lừa đảo – mối đe dọa thường trực đối với các tổ chức"),
    ("p", "Thư điện tử vẫn là kênh liên lạc chính thức trong hầu hết các cơ quan, doanh nghiệp và cơ sở "
          "giáo dục. Chính vì mức độ phổ biến và tính “chính thức” đó, email cũng là con đường được kẻ tấn "
          "công ưa chuộng nhất để thực hiện lừa đảo (phishing): giả danh một đơn vị đáng tin cậy nhằm dụ "
          "người nhận cung cấp mật khẩu, mã OTP, thông tin tài chính, chuyển tiền, hoặc mở một tệp đính kèm "
          "chứa mã độc. Khác với các cuộc tấn công khai thác lỗ hổng phần mềm, phishing nhắm vào yếu tố con "
          "người – mắt xích khó vá nhất trong mọi hệ thống an toàn thông tin."),
    ("p", "Trong môi trường trường học, rủi ro này càng rõ nét. Một trường đại học có hàng chục nghìn tài "
          "khoản email của sinh viên và cán bộ, phần lớn người dùng chưa được đào tạo bài bản về an toàn "
          "thông tin, trong khi các thông báo hợp lệ của nhà trường lại thường xuyên chứa những chủ đề nhạy "
          "cảm như học phí, học bổng, lịch thi, cảnh báo học vụ hay yêu cầu cập nhật thông tin. Kẻ tấn công "
          "chỉ cần mô phỏng đúng giọng văn của Phòng Đào tạo hay Phòng Công tác Sinh viên là có thể đánh lừa "
          "người nhận. Một tài khoản email trường bị chiếm đoạt lại tiếp tục bị dùng để gửi thư lừa đảo nội "
          "bộ, khiến thiệt hại lan rộng."),
    ("h2", "Mô hình ngôn ngữ lớn và thế hệ email lừa đảo mới"),
    ("p", "Sự xuất hiện của các mô hình ngôn ngữ lớn (Large Language Model – LLM) như GPT hay DeepSeek đã "
          "làm thay đổi căn bản bức tranh này. Trước đây, email lừa đảo thường dễ nhận ra nhờ lỗi chính tả, "
          "câu chữ vụng về, lời chào chung chung và những từ khóa lộ liễu như “khẩn cấp”, “tài khoản sẽ bị "
          "khóa”, “nhấn vào đây”. Với LLM, kẻ tấn công có thể sinh ra hàng loạt email trôi chảy, lịch sự, "
          "được cá nhân hóa theo tên, chức danh và bối cảnh công việc của từng người nhận với chi phí gần như "
          "bằng không. Các nghiên cứu gần đây cho thấy email lừa đảo do LLM tạo ra đạt hiệu quả tương đương "
          "email do con người soạn thảo công phu [4], [5]."),
    ("p", "Ba hành vi né tránh tiêu biểu khi dùng LLM là: diễn đạt lại (paraphrasing) để tránh các chữ ký "
          "từ khóa đã biết; làm mềm (masking) các dấu hiệu lộ liễu thành giọng văn công sở bình thường; và cá "
          "nhân hóa (personalization) bằng cách chèn thông tin cụ thể của người nhận để email trông giống thư "
          "nội bộ. Bên cạnh đó, kẻ tấn công còn chủ động “chuyển kênh” thông điệp: đặt toàn bộ nội dung vào "
          "một hình ảnh, giấu liên kết trong mã QR (quishing), hoặc đưa trang đăng nhập giả vào một tệp HTML, "
          "PDF hay tệp nén có mật khẩu đính kèm. Những kỹ thuật này nhắm thẳng vào điểm yếu của các bộ lọc chỉ "
          "đọc phần văn bản của email."),
    ("h2", "Hạn chế của các giải pháp hiện tại"),
    ("p", "Các nhà cung cấp lớn như Google Workspace hay Microsoft 365 Defender đã tích hợp sẵn bộ lọc thư "
          "rác và lừa đảo với khả năng chặn phần lớn các chiến dịch phổ biến. Tuy nhiên, những email còn lọt "
          "qua bộ lọc thường chính là những email nguy hiểm nhất: được viết khéo léo, nhắm mục tiêu cụ thể, "
          "hoặc dùng kỹ thuật chuyển kênh. Khi đó, người dùng là lớp phòng thủ cuối cùng, nhưng họ lại thiếu "
          "công cụ để hiểu vì sao một email đáng ngờ và cần làm gì tiếp theo."),
    ("p", "Ở phía nghiên cứu, các mô hình học sâu dựa trên Transformer cho độ chính xác cao trong phân loại "
          "email, nhưng kích thước hàng trăm triệu đến hàng tỷ tham số khiến chúng khó triển khai trực tiếp "
          "tại máy chủ thư hay thiết bị đầu cuối. Việc gửi email tới API của các LLM thương mại để phân tích "
          "lại phát sinh độ trễ, chi phí và rủi ro lộ dữ liệu cá nhân. Đây chính là khoảng trống mà bài báo "
          "của Eskandarian và cộng sự [1] hướng tới: một bộ phát hiện nhỏ gọn, nhanh, nhưng vẫn bền vững trước "
          "email lừa đảo do LLM viết lại."),
    ("p", "Dù vậy, khi đặt bài báo vào bối cảnh triển khai thực tế, có thể nhận thấy ba vấn đề còn bỏ ngỏ. "
          "Thứ nhất, mô hình chỉ phân loại phần văn bản, trong khi email thực tế có hình ảnh và tệp đính kèm. "
          "Thứ hai, đầu ra là nhãn nhị phân “lừa đảo/không lừa đảo”, không cho người dùng biết mức độ nguy "
          "hiểm và lý do. Thứ ba, bài báo được đánh giá trên dữ liệu tiếng Anh, chưa xem xét ngữ cảnh tiếng "
          "Việt và môi trường trường học."),
    ("h2", "Mục tiêu và phạm vi của đề tài"),
    ("p", "Đề tài đặt ra ba mục tiêu nối tiếp nhau. **Mục tiêu thứ nhất** là nghiên cứu và trình bày cơ sở lý "
          "thuyết cùng phương pháp của bài báo gốc: các mô hình LSTM, BiLSTM, cơ chế attention, MobileBERT và "
          "kỹ thuật chưng cất tri thức (knowledge distillation). **Mục tiêu thứ hai** là tái hiện lại toàn bộ "
          "pipeline của bài báo bằng mã nguồn của nhóm, đánh giá mức độ tái hiện và ghi nhận các vấn đề thực "
          "tế phát sinh. **Mục tiêu thứ ba**, cũng là đóng góp chính, là vận dụng bài báo để xây dựng PhishLens "
          "Edu – một hệ thống phân tích rủi ro email đa kênh, có giải thích bằng tiếng Việt, dành cho môi "
          "trường giáo dục, kèm theo một thí nghiệm đánh giá độ bền của bộ phát hiện trước email lừa đảo do "
          "LLM tạo ra và các kỹ thuật chuyển kênh."),
    ("p", "Về phạm vi, đề tài không nhằm xây dựng một hệ thống thay thế Gmail hay Microsoft Defender. "
          "PhishLens Edu được định vị là lớp “ý kiến thứ hai có giải thích” cho những email đã lọt vào hộp "
          "thư. Hệ thống chạy hoàn toàn cục bộ, chỉ phân tích tĩnh tệp đính kèm và không bao giờ mở hay thực "
          "thi tệp. Do không có quyền truy cập dữ liệu gốc của bài báo, các thực nghiệm sử dụng dữ liệu tổng "
          "hợp; vì vậy các con số trong báo cáo thể hiện xu hướng, cần được kiểm chứng thêm trên dữ liệu thật."),

    # =====================================================================================
    ("h1", "CƠ SỞ LÝ THUYẾT"),
    ("h2", "Bài toán phát hiện email lừa đảo"),
    ("p", "Về hình thức, phát hiện email lừa đảo có thể được phát biểu như một bài toán phân loại: cho một "
          "email x, cần xác định nhãn y ∈ {0, 1}, trong đó 1 là lừa đảo và 0 là hợp lệ, hoặc tổng quát hơn là "
          "ước lượng xác suất p(y = 1 | x). Một email không chỉ là một đoạn văn bản mà là một đối tượng có cấu "
          "trúc theo chuẩn MIME, gồm phần tiêu đề (header) chứa thông tin người gửi, người nhận, kết quả xác "
          "thực; phần thân ở dạng văn bản thuần hoặc HTML; các liên kết; các hình ảnh nhúng và các tệp đính "
          "kèm. Mỗi thành phần mang những tín hiệu khác nhau về khả năng lừa đảo."),
    ("p", "Các hướng tiếp cận truyền thống gồm danh sách đen URL và tên miền, luật dựa trên từ khóa, và các "
          "bộ phân loại học máy trên đặc trưng thủ công. Các hướng hiện đại dùng mô hình học sâu đọc trực "
          "tiếp nội dung văn bản. Điểm chung của phần lớn nghiên cứu học sâu, trong đó có bài báo gốc, là chỉ "
          "khai thác kênh văn bản. Đề tài sẽ chỉ ra rằng đây là giới hạn quan trọng khi kẻ tấn công chủ động "
          "chuyển thông điệp sang các kênh khác."),
    ("h2", "Biểu diễn văn bản: TF-IDF, Word2Vec và WordPiece"),
    ("p", "Để đưa văn bản vào mô hình, trước hết cần biểu diễn nó dưới dạng số. Mô hình không gian vector với "
          "trọng số TF-IDF gán cho mỗi từ t trong văn bản d một trọng số tỉ lệ thuận với tần suất của từ trong "
          "văn bản và tỉ lệ nghịch với số văn bản chứa từ đó:"),
    ("eq", "tfidf(t, d) = tf(t, d) × log( N / df(t) )"),
    ("p", "trong đó N là tổng số văn bản và df(t) là số văn bản chứa t. Độ tương đồng giữa hai văn bản được "
          "đo bằng cosine giữa hai vector TF-IDF. Bài báo gốc dùng chính độ đo này để chứng minh email do LLM "
          "sinh ra gần với email hợp lệ hơn so với email lừa đảo gốc."),
    ("p", "Word2Vec [8] học một vector dày đặc cho mỗi từ sao cho các từ xuất hiện trong ngữ cảnh tương tự có "
          "vector gần nhau. Với kiến trúc CBOW, mô hình dự đoán từ ở giữa từ các từ xung quanh. Các mô hình "
          "LSTM cơ sở trong bài báo dùng vector Word2Vec 100 chiều làm đầu vào. Trong khi đó, các mô hình "
          "Transformer như BERT và MobileBERT dùng bộ tách từ WordPiece, chia từ hiếm thành các mảnh nhỏ hơn "
          "để có bộ từ vựng hữu hạn (khoảng 30.000 mảnh) mà vẫn biểu diễn được mọi từ."),
    ("h2", "Mạng LSTM và BiLSTM"),
    ("p", "Mạng nơ-ron hồi quy (RNN) xử lý chuỗi bằng cách cập nhật một trạng thái ẩn tại mỗi bước thời gian, "
          "nhưng gặp khó khăn với phụ thuộc xa do hiện tượng tiêu biến gradient. Mạng LSTM (Long Short-Term "
          "Memory) [6] khắc phục điều này bằng một ô nhớ C_{t} và ba cổng điều khiển luồng thông tin. Cổng "
          "quên quyết định phần nào của bộ nhớ cũ được giữ lại:"),
    ("eq", "f_{t} = σ(W_{f} · [h_{t−1}, x_{t}] + b_{f})"),
    ("p", "Cổng vào chọn thông tin mới cần ghi vào bộ nhớ thông qua giá trị ứng viên C̃_{t}:"),
    ("eq", "i_{t} = σ(W_{i} · [h_{t−1}, x_{t}] + b_{i}),    C̃_{t} = tanh(W_{C} · [h_{t−1}, x_{t}] + b_{C})"),
    ("p", "Bộ nhớ được cập nhật bằng cách kết hợp phần cũ được giữ lại và phần mới, sau đó cổng ra quyết định "
          "trạng thái ẩn h_{t} được truyền sang bước tiếp theo:"),
    ("eq", "C_{t} = f_{t} ⊙ C_{t−1} + i_{t} ⊙ C̃_{t},    o_{t} = σ(W_{o} · [h_{t−1}, x_{t}] + b_{o}),    h_{t} = o_{t} ⊙ tanh(C_{t})"),
    ("p", "Trong email lừa đảo, ý nghĩa của một cụm từ phụ thuộc vào cả phần trước lẫn phần sau. Mạng BiLSTM "
          "chạy hai LSTM theo hai chiều ngược nhau và ghép trạng thái ẩn của chúng, nhờ đó mỗi vị trí có thông "
          "tin từ toàn bộ câu:"),
    ("eq", "h_{t} = [ h→_{t} ‖ h←_{t} ]"),
    ("h2", "Cơ chế attention và multi-head attention"),
    ("p", "BiLSTM đối xử như nhau với mọi từ khi tổng hợp biểu diễn của câu, trong khi trong email lừa đảo một "
          "số cụm từ như “xác minh tài khoản” hay “tài khoản sẽ bị khóa” mang trọng số ngữ nghĩa lớn hơn hẳn. "
          "Cơ chế attention [7] chiếu chuỗi trạng thái ẩn thành ba không gian truy vấn Q, khóa K và giá trị V, "
          "rồi tính trọng số chú ý bằng tích vô hướng có chia tỉ lệ:"),
    ("eq", "Attention(Q, K, V) = softmax( Q·K^{T} / √d_{k} ) · V"),
    ("p", "Multi-head attention thực hiện nhiều phép attention song song trên các không gian chiếu khác nhau, "
          "mỗi “đầu” có thể học một loại tín hiệu riêng (ví dụ một đầu chú ý vào sự khẩn cấp, một đầu chú ý "
          "vào yêu cầu cung cấp mật khẩu), sau đó ghép kết quả và chiếu về không gian chung:"),
    ("eq", "MultiHead(X) = Concat(head_{1}, …, head_{h}) · W^{O},    head_{i} = Attention(X·W_{i}^{Q}, X·W_{i}^{K}, X·W_{i}^{V})"),
    ("p", "Một lợi ích phụ quan trọng của attention là khả năng diễn giải: trọng số chú ý cho biết mô hình đã "
          "“nhìn” vào những từ nào khi đưa ra quyết định. PhishLens Edu tận dụng chính đặc điểm này để hiển "
          "thị lời giải thích cho người dùng."),
    ("h2", "Transformer và MobileBERT"),
    ("p", "Kiến trúc Transformer [7] thay hoàn toàn cơ chế hồi quy bằng các lớp self-attention xếp chồng, cho "
          "phép học biểu diễn ngữ cảnh sâu và huấn luyện song song hiệu quả. BERT [9] tiền huấn luyện "
          "Transformer trên lượng văn bản rất lớn rồi tinh chỉnh (fine-tune) cho từng bài toán cụ thể. "
          "MobileBERT [10] là phiên bản thu gọn của BERT dành cho thiết bị hạn chế tài nguyên: giữ độ sâu 24 "
          "lớp nhưng dùng cấu trúc “thắt cổ chai” để giảm số tham số xuống khoảng 25 triệu. Trong bài báo, "
          "MobileBERT đóng vai trò mô hình thầy (teacher)."),
    ("h2", "Chưng cất tri thức (Knowledge Distillation)"),
    ("p", "Chưng cất tri thức, do Hinton và cộng sự đề xuất [2], là kỹ thuật huấn luyện một mô hình nhỏ (học "
          "trò – student) bắt chước một mô hình lớn đã huấn luyện (thầy – teacher). Ngoài nhãn đúng, học trò "
          "còn học từ phân phối xác suất “làm mềm” của thầy. Phân phối này chứa thông tin phong phú hơn nhãn "
          "cứng, ví dụ một email hợp lệ nhưng có vài nét giống lừa đảo sẽ được thầy gán xác suất trung gian. "
          "Độ mềm được điều khiển bởi nhiệt độ τ:"),
    ("eq", "p_{i} = exp(z_{i} / τ) / Σ_{j} exp(z_{j} / τ)"),
    ("p", "Hàm mất mát tổng hợp là tổ hợp giữa entropy chéo với nhãn đúng và phân kỳ Kullback–Leibler giữa "
          "phân phối của thầy và trò, trong đó hệ số τ² giữ cho độ lớn gradient của hai thành phần cân bằng:"),
    ("eq", "L_{distill} = α · CE(y, z_{S}) + (1 − α) · τ^{2} · KL( σ(z_{T}/τ) ‖ σ(z_{S}/τ) )"),
    ("p", "Bài báo gốc chọn α = 0,5 và τ = 2. Điểm đặc biệt là việc chưng cất diễn ra giữa hai kiến trúc khác "
          "nhau: từ Transformer sang mạng hồi quy BiLSTM, thay vì từ một Transformer lớn sang một Transformer "
          "nhỏ như thường thấy."),
    ("h2", "Các cơ chế xác thực email và kỹ thuật né tránh"),
    ("p", "Giao thức SMTP cho phép bất kỳ ai ghi tùy ý địa chỉ người gửi, vì vậy các cơ chế xác thực đã được "
          "bổ sung. SPF [11] cho phép chủ tên miền công bố các máy chủ được phép gửi thư; DKIM [12] gắn chữ ký "
          "số vào thư; DMARC [13] kết hợp hai cơ chế trên và quy định cách xử lý khi xác thực thất bại. Kết "
          "quả kiểm tra được máy chủ nhận ghi vào trường Authentication-Results. Một email mang địa chỉ của "
          "trường nhưng SPF và DMARC thất bại là dấu hiệu mạnh của giả mạo."),
    ("p", "Kẻ tấn công cũng dùng nhiều kỹ thuật né tránh khác: tên miền nhái gõ sai một vài ký tự hoặc dùng ký "
          "tự giống nhau (homoglyph, ví dụ micros0ft); chèn tên tổ chức vào một tên miền khác "
          "(dhdemo.edu.vn.account-verify.top); dùng tên hiển thị “Phòng Đào tạo” cho một địa chỉ Gmail; chữ "
          "hiển thị của liên kết khác địa chỉ thật; tệp có đuôi kép như hoadon.pdf.exe; tài liệu Office chứa "
          "macro; PDF chứa JavaScript tự chạy; tệp HTML chứa biểu mẫu đăng nhập giả hoặc dùng JavaScript để "
          "dựng tệp độc ngay trong trình duyệt (HTML smuggling); tệp nén có mật khẩu để phần mềm diệt virus "
          "không quét được. Đây là cơ sở để thiết kế các bộ phân tích của PhishLens Edu ở Chương 5."),
    ("h2", "Các chỉ số đánh giá"),
    ("p", "Hiệu năng phân loại được đánh giá qua ma trận nhầm lẫn gồm TP, TN, FP, FN. Độ chính xác "
          "(Accuracy) là tỉ lệ dự đoán đúng; Precision đo tỉ lệ email bị cảnh báo thực sự là lừa đảo; Recall "
          "(trong báo cáo gọi là tỉ lệ phát hiện) đo tỉ lệ email lừa đảo được phát hiện; F1 là trung bình điều "
          "hòa của Precision và Recall. Bài báo dùng weighted-F1 để giảm ảnh hưởng của mất cân bằng lớp. Với "
          "bài toán triển khai thực tế, tỉ lệ báo nhầm (False Positive Rate) trên email hợp lệ đặc biệt quan "
          "trọng, vì báo nhầm nhiều sẽ khiến người dùng mất niềm tin và bỏ qua cảnh báo."),
    ("eq", "Precision = TP / (TP + FP),    Recall = TP / (TP + FN),    F1 = 2 · P · R / (P + R)"),

    # =====================================================================================
    ("h1", "PHÂN TÍCH BÀI BÁO NGHIÊN CỨU"),
    ("h2", "Thông tin chung và đóng góp của bài báo"),
    ("p", "Bài báo “A lightweight defense mechanism against next-generation of phishing emails using distilled "
          "attention-augmented BiLSTM” của Eskandarian và cộng sự thuộc Viện An ninh mạng Canada (Đại học New "
          "Brunswick) và Mastercard, đăng trên tạp chí Journal of Information Security and Applications, tập "
          "101, năm 2026 [1]. Bài báo nêu bốn đóng góp: (1) một bộ dữ liệu “nhận biết LLM” kết hợp email thật "
          "và email do LLM viết lại; (2) một kiến trúc BiLSTM có attention được chưng cất từ MobileBERT, đủ nhẹ "
          "để triển khai ở gateway và thiết bị đầu cuối; (3) phân tích đánh đổi giữa độ chính xác, độ trễ và "
          "kích thước mô hình; (4) góc nhìn vận hành về cách tích hợp vào hệ thống thư điện tử."),
    ("fig", "diag1.png", "Quy trình đề xuất của bài báo gốc", 16),
    ("h2", "Dữ liệu và quy trình sinh email bằng LLM"),
    ("p", "Tác giả tổng hợp năm bộ dữ liệu công khai hoặc được cấp quyền truy cập, tổng cộng khoảng 623.000 "
          "email, trong đó 94.315 email lừa đảo và 528.685 email hợp lệ. Bảng 3.1 tóm tắt các nguồn dữ liệu. "
          "Từ khoảng 25.000 email được chọn, tác giả dùng các dịch vụ LLM thương mại để sinh thêm 47.575 email "
          "(41.333 lừa đảo, 6.242 hợp lệ) theo ba hành vi paraphrasing, masking và personalization."),
    ("tab", "Các bộ dữ liệu được sử dụng trong bài báo gốc",
     [("Bộ dữ liệu", "Lừa đảo", "Hợp lệ", "Năm"),
      ("Cambridge Phishing", "78.154", "–", "2024"), ("Nazario Phishing Corpus", "4.487", "–", "2005"),
      ("Chakraborty", "7.323", "11.283", "2023"), ("Phishing Pot", "4.351", "–", "2024"),
      ("Enron", "–", "517.402", "2004"), ("Tổng email thật", "94.315", "528.685", "–"),
      ("Email do LLM sinh", "41.333", "6.242", "2025")], [6.5, 3, 3, 2.5], 12),
    ("p", "Để kiểm chứng rằng email sinh ra thực sự “khó” hơn, tác giả tính độ tương đồng cosine TF-IDF trung "
          "bình giữa mỗi email lừa đảo và tập email hợp lệ. Phân phối của email do LLM sinh dịch sang phải so "
          "với email lừa đảo gốc, nghĩa là chúng giống email hợp lệ hơn và do đó khó phát hiện hơn. Ngoài ra, "
          "tác giả đề xuất cơ chế chấm “mức độ phishing” bằng một bộ câu hỏi gửi tới LLM, chẳng hạn “Email có "
          "tạo cảm giác khẩn cấp không?”, “Liên kết có đáng ngờ không?”, “Email có yêu cầu cập nhật tài khoản "
          "qua liên kết không?”. Câu trả lời của từng câu hỏi được coi là một tín hiệu mềm, được tổng hợp "
          "thành điểm dùng để lọc mẫu sinh kém chất lượng. Cuối cùng, khoảng 10.000 mẫu gần trùng lặp bị loại, "
          "còn lại khoảng 14.000 email."),
    ("h2", "Kiến trúc mô hình theo từng bước"),
    ("p", "Các mô hình được nâng cấp dần để đo đóng góp của từng thành phần. Mô hình cơ sở LSTM và BiLSTM nhận "
          "chuỗi vector Word2Vec 100 chiều. Bước tiếp theo bổ sung single-head attention trên đầu ra BiLSTM, "
          "rồi thay bằng multi-head attention với 4 đầu, mỗi đầu 64 chiều (tổng 256 chiều). Bảng 3.2 trình "
          "bày các thành phần và siêu tham số theo Bảng 2 của bài báo."),
    ("tab", "Thành phần và siêu tham số của BiLSTM + multi-head attention",
     [("Thành phần", "Cấu hình"), ("Đầu vào", "Chuỗi vector Word2Vec, F = 100"),
      ("BiLSTM", "128 chiều đầu ra, hàm kích hoạt tanh"),
      ("Multi-head attention", "H = 4 đầu, D = 64; chiếu Q/K/V lên 256 chiều, chiếu đầu ra"),
      ("Dropout", "0,5"), ("Lớp phân loại", "Dense 1 nơ-ron, sigmoid"),
      ("Hàm mất mát", "Binary cross-entropy"), ("Tối ưu", "Adam, lr = 0,001; batch 32; 5 epoch")], [5, 11], 12),
    ("h2", "Quy trình chưng cất tri thức"),
    ("p", "Ở giai đoạn chưng cất, MobileBERT được fine-tune trên tập dữ liệu hỗn hợp rồi đóng băng. Mô hình "
          "học trò dùng cùng bộ tách từ WordPiece với thầy, lớp embedding được khởi tạo trực tiếp từ ma trận "
          "embedding của MobileBERT, sau đó là BiLSTM, multi-head attention, chuẩn hóa residual, gộp trung "
          "bình toàn cục, dropout và lớp đầu ra hai logit. Khác với các mô hình cơ sở dùng một nơ-ron sigmoid, "
          "đầu ra hai logit cho phép so khớp phân phối softmax giữa thầy và trò. Thuật toán 1 của bài báo lặp "
          "qua từng batch: tính logit của thầy và trò, tính phân phối làm mềm với nhiệt độ τ, tính mất mát "
          "cứng và mềm, kết hợp theo công thức (2.9) rồi cập nhật tham số của trò bằng Adam với tốc độ học "
          "1e-4 trong 3 epoch, batch 32."),
    ("fig", "diag2.png", "Kiến trúc chưng cất tri thức từ MobileBERT sang BiLSTM + multi-head attention", 16),
    ("h2", "Thiết kế thực nghiệm của bài báo"),
    ("p", "Mỗi mô hình được đánh giá trên năm kịch bản: Orig-Orig (huấn luyện và kiểm thử trên email thật), "
          "Gen-Gen (trên email LLM), Orig-Gen (học email thật, kiểm thử email LLM), Gen-Orig (học email LLM, "
          "kiểm thử email thật) và Mixture (trộn cả hai). Hai kịch bản chéo đo khả năng tổng quát hóa giữa "
          "email người viết và email máy viết. Mỗi kịch bản dùng kiểm định chéo phân tầng 5-fold, chia "
          "train/validation/test theo tỉ lệ 72/8/20, chạy trên Google Colab với GPU L4. Ngoài các mô hình của "
          "chính mình, tác giả so sánh với ModernBERT, DeBERTaV3, T5, DeepSeek-R1-Distill-Qwen-1.5B, Phi-4-mini "
          "và các mô hình nhẹ như Logistic Regression, XGBoost, fastText, TinyBERT, DistilBERT."),
    ("h2", "Kết quả của bài báo"),
    ("p", "Bảng 3.3 tóm tắt kết quả ở kịch bản Mixture. Mỗi bước nâng cấp đều cải thiện F1, từ 91,32% của "
          "LSTM lên 95,25% của BiLSTM + multi-head attention và 96,67% của mô hình chưng cất. Mô hình KD-BiLSTM "
          "chỉ kém các Transformer tốt nhất khoảng 1–2,5 điểm F1 nhưng có thời gian suy luận nhanh hơn 5–19 "
          "lần và kích thước nhỏ hơn 20–800 lần."),
    ("tab", "Kết quả của bài báo gốc ở kịch bản Mixture",
     [("Mô hình", "Tham số", "F1 (%)", "Test (s)"),
      ("LSTM", "17K", "91,32", "0,83"), ("BiLSTM", "34K", "91,65", "1,30"),
      ("BiLSTM + single-head", "67K", "93,48", "1,37"), ("BiLSTM + multi-head", "495K", "95,25", "1,51"),
      ("KD-BiLSTM (đề xuất)", "4,5M", "96,67", "6,06"), ("MobileBERT (teacher)", "25,3M", "98,56", "42,00"),
      ("ModernBERT-base", "149M", "98,98", "37,26"), ("DeBERTaV3-base", "86M", "98,75", "38,34"),
      ("T5-base", "109,6M", "98,73", "31,43"), ("DeepSeek-R1-Distill-Qwen-1.5B", "1.780M", "98,83", "56,40"),
      ("Phi-4-mini", "3.840M", "96,45", "116,65")], [7.5, 2.8, 2.6, 2.6], 12),
    ("p", "Ở các kịch bản chéo, kết quả cho thấy rõ thách thức của email do LLM sinh. Khi chỉ học trên email "
          "LLM rồi kiểm thử trên email thật (Gen-Orig), recall của LSTM chỉ còn 45,10% và của BiLSTM là 51,19%. "
          "Multi-head attention nâng recall lên 62,97%, và mô hình chưng cất đạt recall 98,24% với F1 90,02%. "
          "Ở chiều ngược lại (Orig-Gen), F1 của BiLSTM là 79,93%, của multi-head là 92,40% và của KD-BiLSTM là "
          "89,60%. Trong so sánh với các mô hình nhẹ, Logistic Regression trên TF-IDF đạt độ chính xác 95,67% "
          "ở kịch bản Mixture, chỉ thấp hơn mô hình đề xuất (97,01%) khoảng 1,3 điểm."),
    ("h2", "Nhận xét về bài báo"),
    ("p", "Điểm mạnh của bài báo là đặt vấn đề đúng thời điểm, xây dựng dữ liệu có tính đến email do LLM viết "
          "lại, thiết kế các kịch bản chéo phân phối hợp lý và phân tích đầy đủ đánh đổi giữa độ chính xác với "
          "chi phí triển khai. Tuy nhiên, khi đọc kỹ có thể nhận thấy một số hạn chế. Dữ liệu và mã nguồn chưa "
          "được công bố (“available on request”), gây khó khăn cho việc tái lập. Một số số liệu không thống "
          "nhất: Bảng 1 ghi 47.575 email LLM, mục 3.2.2 ghi tập cuối khoảng 14.000 email, còn mỗi kịch bản "
          "dùng 13.692 mẫu. Nhiều chi tiết kiến trúc không được mô tả đủ, như cách nối attention với lớp phân "
          "loại hay cách gộp chuỗi. Quan trọng hơn với ứng dụng thực tế, bài báo chỉ xét kênh văn bản và đầu "
          "ra nhị phân, chưa xét hình ảnh, mã QR, tệp đính kèm hay khả năng giải thích cho người dùng. Đây là "
          "những điểm mà đề tài kế thừa và phát triển ở các chương sau."),

    # =====================================================================================
    ("h1", "TÁI HIỆN BÀI BÁO"),
    ("h2", "Môi trường và tổ chức mã nguồn"),
    ("p", "Toàn bộ thực nghiệm được thực hiện trên máy tính cá nhân không có GPU, trong một môi trường Python "
          "ảo (virtual environment) độc lập để không ảnh hưởng đến hệ thống. Bảng 4.1 trình bày cấu hình môi "
          "trường. Nhóm cũng xây dựng một notebook tự chứa để chạy lại toàn bộ pipeline trên Google Colab khi "
          "cần GPU."),
    ("tab", "Cấu hình môi trường thực nghiệm",
     [("Thành phần", "Thông số"), ("Phần cứng", "CPU 16 luồng, RAM 15 GB, không GPU"),
      ("Ngôn ngữ", "Python 3.12 (virtual environment riêng)"),
      ("Học sâu", "PyTorch 2.14 (bản CPU), Hugging Face Transformers 5.18"),
      ("Biểu diễn từ", "gensim 4.4 (Word2Vec), scikit-learn (TF-IDF, đánh giá)"),
      ("Mô hình thầy", "google/mobilebert-uncased"),
      ("Notebook", "phishing_kd_bilstm.ipynb – chạy được trên Google Colab")], [4.5, 11.5], 12),
    ("p", "Mã nguồn tái hiện được tổ chức thành gói phishkd gồm bốn mô-đun. Mô-đun text thực hiện tiền xử lý "
          "theo mục 4.1 của bài báo (chuyển chữ thường, bỏ chữ số, dấu câu, từ dừng) và huấn luyện Word2Vec "
          "CBOW 100 chiều. Mô-đun data quản lý corpus thống nhất với ba cột văn bản, nhãn và nguồn (orig/gen), "
          "đồng thời sinh năm kịch bản đánh giá với kiểm định chéo 5-fold. Mô-đun models cài đặt các mô hình "
          "LSTM, BiLSTM, BiLSTM + single-head, BiLSTM + multi-head, mô hình thầy và mô hình trò. Mô-đun train "
          "chứa vòng huấn luyện cho từng loại mô hình và hàm mất mát chưng cất. Ngoài ra, mô-đun analysis cài "
          "đặt các công cụ phân tích dữ liệu: độ tương đồng TF-IDF, chấm điểm mức phishing bằng bộ câu hỏi và "
          "khử trùng lặp."),
    ("h2", "Dữ liệu thay thế và mô phỏng hành vi LLM"),
    ("p", "Do không có dữ liệu gốc và không gửi dữ liệu ra dịch vụ LLM bên ngoài, nhóm xây dựng một corpus "
          "tổng hợp từ các mẫu câu (template) điền ngẫu nhiên tên dịch vụ, số tiền, đường dẫn, thời hạn. Ba "
          "hành vi của LLM được mô phỏng bằng bộ luật: paraphrase thay thế cụm từ bằng các cách nói tương "
          "đương và đảo thứ tự câu; masking thay các dấu hiệu lộ liễu như “urgent”, “final warning”, dấu chấm "
          "than liên tiếp bằng cách diễn đạt mềm mỏng; personalization chèn lời chào theo tên, chức danh, dự "
          "án và chữ ký của người gửi. Các prompt dành cho LLM thật cũng được chuẩn bị sẵn và có thể cắm một "
          "LLM chạy cục bộ (qua Ollama) để thay cho bộ luật mà không phải gửi dữ liệu ra ngoài."),
    ("p", "Phân tích độ tương đồng TF-IDF trên corpus tổng hợp cho kết quả cùng xu hướng với Hình 2 của bài "
          "báo: độ tương đồng trung bình của email lừa đảo “đã viết lại” với tập email hợp lệ là 0,026, cao "
          "hơn nhiều so với 0,002 của email lừa đảo gốc. Cơ chế chấm mức phishing dùng cùng 9 câu hỏi của bài "
          "báo; vì không gọi LLM, câu trả lời được ước lượng bằng từ khóa, và trọng số của mỗi câu hỏi được "
          "tính theo mức độ phân biệt với nhãn thật (AUC − 0,5). Kết quả xếp hạng hợp lý: câu hỏi về liên kết "
          "đáng ngờ, sự khẩn cấp và yêu cầu cập nhật tài khoản có trọng số cao nhất, tương tự Hình 3 của bài báo."),
    ("h2", "Cài đặt các mô hình"),
    ("p", "Các mô hình cơ sở dùng Word2Vec huấn luyện trên tập train của từng fold làm lớp embedding đóng băng. "
          "LSTM và BiLSTM dùng 32 chiều ẩn để số tham số huấn luyện xấp xỉ Bảng 4 của bài báo. Hai mô hình "
          "attention dùng BiLSTM 64 chiều mỗi hướng (128 chiều đầu ra theo Bảng 2), multi-head attention 4 đầu "
          "× 64 chiều, gộp trung bình có mặt nạ, dropout 0,5 và một nơ-ron đầu ra. Huấn luyện dùng Adam với "
          "tốc độ học 0,001, batch 32, 5 epoch, chọn checkpoint có weighted-F1 tốt nhất trên tập validation."),
    ("p", "Mô hình thầy là MobileBERT với đầu phân loại hai lớp, fine-tune bằng AdamW, tốc độ học 5e-5 và lịch "
          "khởi động tuyến tính. Mô hình trò có embedding WordPiece 30.522 × 128 sao chép từ thầy, BiLSTM 128 "
          "chiều mỗi hướng, multi-head attention 4 × 64, kết nối residual và LayerNorm, gộp trung bình, dropout "
          "và lớp đầu ra hai logit, tổng cộng 4,44 triệu tham số. Hàm mất mát và quy trình huấn luyện tuân "
          "thủ đúng công thức (2.9) và Thuật toán 1 với α = 0,5, τ = 2, Adam lr = 1e-4, 3 epoch, batch 32. Do "
          "thầy đã đóng băng và chạy ở chế độ suy luận, logit của thầy được tính một lần cho toàn bộ tập train "
          "rồi dùng lại; cách làm này cho kết quả tương đương bước 5 của Thuật toán 1 nhưng giảm đáng kể thời "
          "gian huấn luyện trên CPU."),
    ("h2", "Kết quả tái hiện"),
    ("p", "Bảng 4.2 so sánh số tham số của các mô hình. LSTM, BiLSTM, mô hình thầy và mô hình trò có số tham "
          "số rất sát với bài báo. Hai mô hình attention có sai khác lớn hơn vì bài báo không mô tả đủ cách "
          "nối lớp attention với lớp phân loại; đây là một trong các điểm tự quyết định khi tái hiện."),
    ("tab", "So sánh số tham số giữa bài báo và bản tái hiện",
     [("Mô hình", "Bài báo", "Tái hiện"), ("LSTM", "16.961", "17.185"), ("BiLSTM", "33.921", "34.369"),
      ("BiLSTM + single-head", "66.561", "151.169"), ("BiLSTM + multi-head", "494.977", "217.089"),
      ("MobileBERT (teacher)", "25,3M", "24,58M"), ("KD-BiLSTM (student)", "4,5M", "4,44M")], [7, 4.5, 4.5], 12),
    ("p", "Trên corpus tổng hợp, các kịch bản cùng phân phối (Orig-Orig, Gen-Gen, Mixture) đều đạt khoảng "
          "100% vì dữ liệu sinh từ template quá dễ; các con số này chỉ xác nhận pipeline hoạt động đúng. Kịch "
          "bản chéo Orig-Gen mới cho thấy sự khác biệt có ý nghĩa, được trình bày ở Bảng 4.3. Xu hướng khớp "
          "với bài báo: chuyển từ email người viết sang email “máy viết” làm giảm điểm, và multi-head "
          "attention cho kết quả tốt nhất trong nhóm mô hình cơ sở. Mô hình trò đạt F1 92,55%, cao hơn hẳn "
          "thầy (51,66%) trong lần chạy này; nguyên nhân là thầy được fine-tune trên tập train nhỏ nên nhạy "
          "với độ lệch phân phối, trong khi trò được hưởng lợi từ việc học cả nhãn cứng lẫn phân phối mềm."),
    ("tab", "F1 (%) ở kịch bản chéo Orig-Gen (bản tái hiện: dữ liệu tổng hợp, 1 fold)",
     [("Mô hình", "Bài báo", "Tái hiện"), ("LSTM", "82,17", "81,75"), ("BiLSTM", "79,93", "88,81"),
      ("BiLSTM + single-head", "85,03", "80,04"), ("BiLSTM + multi-head", "92,40", "90,90"),
      ("MobileBERT (teacher)", "91,80", "51,66"), ("KD-BiLSTM", "89,60", "92,55")], [7, 4.5, 4.5], 12),
    ("p", "Về tốc độ, trên tập kiểm thử của kịch bản Mixture, mô hình trò suy luận trong 0,35 giây so với "
          "11,83 giây của thầy, tức nhanh hơn khoảng 34 lần trên CPU. Bài báo báo cáo 6,06 giây so với 42 giây "
          "(khoảng 7 lần) trên GPU. Tỉ lệ lớn hơn trên CPU là hợp lý vì GPU tăng tốc Transformer hiệu quả hơn "
          "nhiều so với mạng hồi quy. Kết quả này khẳng định luận điểm cốt lõi của bài báo: mô hình chưng cất "
          "phù hợp cho triển khai không cần phần cứng tăng tốc."),
    ("h2", "Các vấn đề gặp phải và cách khắc phục"),
    ("p", "Vấn đề đáng chú ý nhất là mô hình thầy MobileBERT bị “sụp” khi fine-tune: sau huấn luyện, nó luôn "
          "dự đoán một lớp duy nhất. Phân tích đường cong mất mát cho thấy giá trị mất mát ở những bước đầu "
          "lên tới khoảng 10⁷. Nguyên nhân là bộ gộp (pooler) của MobileBERT trả về trực tiếp trạng thái ẩn "
          "của token [CLS] mà không qua hàm tanh, nên logit ban đầu có độ lớn rất cao. Nhóm khắc phục bằng "
          "cách cắt gradient (gradient clipping) với chuẩn tối đa 1,0 – giá trị mặc định của Hugging Face "
          "Trainer – và đặt số bước cập nhật tối thiểu là 120, giúp mô hình đủ thời gian vượt qua giai đoạn "
          "mất mát lớn khi tập dữ liệu nhỏ. Bảng 4.4 tổng hợp các vấn đề và cách xử lý."),
    ("tab", "Các vấn đề gặp phải khi tái hiện và cách khắc phục",
     [("Hiện tượng", "Nguyên nhân", "Khắc phục"),
      ("Teacher luôn dự đoán một lớp", "Pooler lấy thẳng [CLS] chưa qua tanh, mất mát ban đầu ~10⁷",
       "Gradient clipping (chuẩn 1,0) và tối thiểu 120 bước"),
      ("Mô hình văn bản báo nhầm email có link", "Dữ liệu tổng hợp: chỉ email lừa đảo chứa tên miền",
       "Che URL trước mô hình văn bản, thêm email hợp lệ “khó”"),
      ("Giải thích attention mất dấu tiếng Việt", "Tokenizer MobileBERT uncased bỏ dấu",
       "Ánh xạ attention về chữ gốc qua offset mapping"),
      ("Tiêu đề tiếng Việt bị dính chữ", "Lỗi gập header của thư viện email Python",
       "Tăng độ dài dòng tối đa của header")], [4.3, 5.8, 5.9], 11),
    ("h2", "Đánh giá mức độ tái hiện"),
    ("p", "Bảng 4.5 tổng hợp mức độ tái hiện từng thành phần. Phần phương pháp – các mô hình, hàm mất mát, quy "
          "trình chưng cất và thiết kế đánh giá – được tái hiện đầy đủ. Phần dữ liệu và sinh email bằng LLM "
          "được thay thế hoặc mô phỏng do giới hạn về quyền truy cập dữ liệu và nguyên tắc không gửi dữ liệu "
          "ra ngoài. Các so sánh với những mô hình lớn ở Bảng 7 và 8 của bài báo chưa được thực hiện. Vì vậy, "
          "bản tái hiện xác nhận được tính đúng đắn và các xu hướng của phương pháp, nhưng chưa so sánh được "
          "số liệu tuyệt đối với bài báo."),
    ("tab", "Mức độ tái hiện các thành phần của bài báo",
     [("Thành phần", "Bản tái hiện", "Mức độ"),
      ("Dữ liệu thật 5 bộ (~623K email)", "Corpus tổng hợp từ template", "Thay thế"),
      ("Sinh email bằng LLM", "Prompt sẵn sàng; bộ luật mô phỏng 3 hành vi", "Mô phỏng"),
      ("Độ tương đồng TF-IDF", "Có, cùng xu hướng", "Đạt"),
      ("Chấm mức phishing bằng câu hỏi", "9 câu hỏi, trả lời bằng từ khóa", "Mô phỏng"),
      ("Khử trùng lặp", "Cosine TF-IDF", "Đạt"),
      ("LSTM / BiLSTM / +SH / +MH", "Đủ 4 mô hình theo Bảng 2", "Đạt"),
      ("Teacher MobileBERT", "24,6M tham số, thêm gradient clipping", "Đạt"),
      ("KD-BiLSTM (Thuật toán 1)", "Đúng hàm mất mát, 4,44M tham số", "Đạt"),
      ("5 kịch bản × 5-fold, 72/8/20", "Có", "Đạt"),
      ("So sánh Transformer lớn (Bảng 7)", "Chưa thực hiện", "Chưa"),
      ("So sánh mô hình nhẹ (Bảng 8)", "Chưa thực hiện", "Chưa")], [6, 7.3, 2.7], 11),

    # =====================================================================================
    ("h1", "ĐÓNG GÓP CỦA ĐỀ TÀI: HỆ THỐNG PHISHLENS EDU"),
    ("h2", "Từ bài báo đến ứng dụng"),
    ("p", "Sau khi tái hiện, câu hỏi đặt ra là làm thế nào để kết quả của bài báo trở nên hữu ích trong thực "
          "tế. Như đã phân tích ở Chương 1, các trường đã có bộ lọc của nhà cung cấp, nên một bộ phân loại văn "
          "bản nữa không tạo ra nhiều giá trị. Điều thực sự còn thiếu là khả năng xử lý những email đã lọt qua "
          "bộ lọc – vốn thường có hình ảnh, mã QR, tệp đính kèm – và khả năng giải thích để người dùng tự nhận "
          "diện được trong những lần sau. Từ đó, nhóm đề xuất PhishLens Edu với ba định hướng: phân tích đa "
          "kênh thay vì chỉ văn bản; đánh giá mức độ rủi ro thay vì nhãn nhị phân; và giải thích, giáo dục người "
          "dùng thay vì chỉ cảnh báo."),
    ("p", "Trong quy trình sử dụng dự kiến, người dùng chuyển tiếp email nghi ngờ tới một hộp thư “kiểm tra "
          "giúp tôi” của trường, hoặc tải tệp .eml lên giao diện web. Hệ thống trả về điểm rủi ro, danh sách lý "
          "do kèm bài học và lời khuyên. Bộ phận công nghệ thông tin có thể dùng chính báo cáo này để xử lý "
          "sự cố. Toàn bộ xử lý diễn ra trên máy chủ nội bộ, phù hợp với yêu cầu bảo vệ dữ liệu cá nhân."),
    ("h2", "Kiến trúc tổng thể"),
    ("p", "Hình 5.1 mô tả kiến trúc của hệ thống gồm bốn bước. Bộ tách email đọc tệp theo chuẩn MIME và tách ra "
          "các thành phần: thông tin người gửi và kết quả xác thực, văn bản và HTML, danh sách liên kết (gồm cả "
          "chữ hiển thị và địa chỉ thật), hình ảnh nhúng và tệp đính kèm. Năm bộ phân tích độc lập xử lý từng "
          "kênh và sinh ra các “bằng chứng”, mỗi bằng chứng gồm tiêu đề, mô tả, độ mạnh trong khoảng [0, 1], "
          "bài học dành cho người dùng và nhãn loại tấn công. Bộ kết hợp gộp các bằng chứng thành điểm rủi ro, "
          "và lớp giải thích trình bày kết quả cho người dùng."),
    ("fig", "diag3.png", "Kiến trúc hệ thống PhishLens Edu", 16),
    ("h2", "Phân tích người gửi và liên kết"),
    ("p", "Bộ phân tích người gửi đọc trường Authentication-Results để kiểm tra SPF, DKIM, DMARC; mỗi cơ chế "
          "thất bại làm tăng độ mạnh của bằng chứng. Hệ thống phát hiện tên hiển thị mạo danh – tên nghe như "
          "một đơn vị hay người có thẩm quyền (“Phòng Đào tạo”, “Trưởng khoa”, “Microsoft”) nhưng địa chỉ thật "
          "thuộc dịch vụ email miễn phí – và trường Reply-To dẫn tới một tên miền khác. Để phát hiện tên miền "
          "nhái, hệ thống so sánh tên miền người gửi với danh sách tên miền tin cậy (tên miền của trường và "
          "các thương hiệu hay bị giả mạo) bằng ba phép kiểm tra: khoảng cách chỉnh sửa Levenshtein từ 1 đến "
          "2 ký tự; so khớp sau khi chuẩn hóa ký tự giống nhau (0→o, 1→l, rn→m); và phát hiện tên thương hiệu "
          "bị chèn vào một tên miền đăng ký khác."),
    ("p", "Bộ phân tích liên kết xét từng URL thu được từ thân thư, từ mã QR, từ chữ trong ảnh và từ tệp đính "
          "kèm. Các dấu hiệu gồm: chữ hiển thị là một tên miền nhưng địa chỉ thật trỏ tới tên miền khác; dùng "
          "địa chỉ IP thay cho tên miền; dùng dịch vụ rút gọn liên kết; tên miền punycode; đuôi tên miền hay bị "
          "lạm dụng như .top, .click, .xyz; ký tự @ trong phần máy chủ; quá nhiều cấp tên miền con; đường dẫn "
          "gợi ý trang đăng nhập hoặc xác minh. Các dấu hiệu của một liên kết được kết hợp thành một bằng chứng "
          "duy nhất, kèm danh sách lý do cụ thể."),
    ("h2", "Phân tích nội dung: kế thừa KD-BiLSTM của bài báo"),
    ("p", "Kênh nội dung là nơi kế thừa trực tiếp bài báo. Mô hình KD-BiLSTM được huấn luyện lại theo đúng quy "
          "trình đã tái hiện ở Chương 4, trên dữ liệu gồm email trường học tiếng Việt và email tiếng Anh, có "
          "cả các bản viết lại kiểu LLM. Xác suất lừa đảo do mô hình đưa ra được chuyển thành một bằng chứng có "
          "độ mạnh tăng dần khi xác suất vượt 0,5. Để giải thích, hệ thống lấy trọng số attention mà mỗi từ "
          "nhận được (trung bình qua các đầu và các vị trí truy vấn) và hiển thị những từ được chú ý nhiều "
          "nhất. Do tokenizer của MobileBERT xóa dấu tiếng Việt, các mảnh WordPiece được ánh xạ ngược về chữ "
          "gốc có dấu thông qua offset mapping."),
    ("p", "Một quyết định thiết kế quan trọng là che URL và địa chỉ email trước khi đưa văn bản vào mô hình. "
          "Liên kết và người gửi đã có bộ phân tích riêng; việc che đi buộc mô hình học ngôn ngữ thay vì học "
          "các đường tắt như “có tên miền thì là lừa đảo” (xem mục 6.4). Bên cạnh mô hình học máy, hệ thống "
          "dùng một từ điển song ngữ Việt–Anh gồm tám nhóm thủ đoạn tâm lý, được tổng hợp từ bộ câu hỏi chấm "
          "mức phishing của bài báo: tạo áp lực thời gian, đe dọa hậu quả, dụ dỗ bằng lợi ích, yêu cầu đăng "
          "nhập hoặc cung cấp thông tin, yêu cầu chuyển tiền, yêu cầu giữ bí mật hoặc né xác minh, hướng dẫn "
          "thao tác nguy hiểm và lời chào chung chung. Các cụm từ khớp được tô sáng trong nội dung email. "
          "Nếu email có lời nhắc an toàn như “nhà trường không bao giờ yêu cầu cung cấp mật khẩu qua email”, độ "
          "mạnh của nhóm dấu hiệu liên quan được giảm để tránh báo nhầm."),
    ("h2", "Phân tích hình ảnh và mã QR"),
    ("p", "Đây là phần trả lời trực tiếp câu hỏi “email có hình ảnh thì phát hiện thế nào”. Mỗi ảnh nhúng hoặc "
          "đính kèm được giải mã bằng OpenCV để tìm mã QR, thử ở nhiều tỉ lệ phóng khác nhau. Nội dung mã QR "
          "nếu là liên kết sẽ được đưa vào bộ phân tích liên kết; bản thân việc email chứa mã QR dẫn tới một "
          "liên kết lạ cũng là một bằng chứng (quishing), trong khi QR dẫn về tên miền chính thức của trường "
          "chỉ được ghi nhận ở mức rất thấp. Tiếp theo, chữ trong ảnh được nhận dạng bằng EasyOCR với mô hình "
          "tiếng Việt và tiếng Anh; văn bản thu được đi qua toàn bộ kênh nội dung như văn bản thông thường. "
          "Khi phần chữ của email rất ít còn thông điệp chính nằm trong ảnh, hệ thống ghi nhận thêm bằng chứng "
          "“nội dung chính nằm trong ảnh” – một kỹ thuật né tránh điển hình."),
    ("h2", "Phân tích tệp đính kèm"),
    ("p", "Tệp đính kèm chỉ được phân tích tĩnh, không bao giờ được mở hay thực thi. Đầu tiên, loại tệp thật "
          "được nhận diện qua magic bytes (PDF, ZIP, Office OOXML, OLE, PE, HTML, ISO, LNK…) và so sánh với phần "
          "mở rộng để phát hiện tệp đổi đuôi. Tên tệp được kiểm tra đuôi kép (hoadon.pdf.exe), ký tự đảo chiều "
          "RLO và các đuôi thực thi. Với tài liệu Office, hệ thống tìm vbaProject.bin (macro) và các tham chiếu "
          "mẫu từ Internet; với PDF, tìm các khóa /JavaScript, /OpenAction, /Launch, /EmbeddedFile, /SubmitForm "
          "và trích xuất văn bản, liên kết; với tệp HTML, tìm ô nhập mật khẩu, biểu mẫu gửi dữ liệu ra máy chủ "
          "ngoài, dấu hiệu HTML smuggling (atob, Blob) và chuyển hướng tự động. Với tệp ZIP, hệ thống kiểm tra "
          "cờ mã hóa: dù không giải nén được nội dung, tên các tệp bên trong vẫn đọc được, nhờ đó vẫn phát "
          "hiện được tệp chạy được có đuôi kép. Văn bản trích xuất từ tệp tiếp tục được phân tích ở kênh nội "
          "dung."),
    ("h2", "Kết hợp bằng chứng và tính điểm rủi ro"),
    ("p", "Mỗi bằng chứng i có độ mạnh s_{i} ∈ [0, 1], có thể hiểu như xác suất bằng chứng đó tự nó cho thấy "
          "email là lừa đảo. Các bằng chứng được kết hợp theo mô hình noisy-OR: email chỉ an toàn khi không "
          "bằng chứng nào “kích hoạt”. Điểm của từng kênh c và điểm tổng được tính như sau:"),
    ("eq", "S_{c} = 1 − Π_{i ∈ c} (1 − s_{i}),    Score = 100 · [ 1 − Π_{c} (1 − S_{c}) ]"),
    ("p", "Cách kết hợp này có ba ưu điểm: đơn điệu (thêm bằng chứng không bao giờ làm giảm điểm), dễ giải "
          "thích (mỗi bằng chứng đóng góp độc lập) và cho phép mỗi kênh bù cho kênh khác. Điểm 0–100 được chia "
          "thành bốn mức: An toàn (dưới 25), Cần chú ý (25–49), Nguy hiểm (50–74) và Rất nguy hiểm (từ 75). "
          "Các nhãn của bằng chứng được cộng dồn theo độ mạnh để suy ra loại tấn công nổi bật (đánh cắp tài "
          "khoản, lừa chuyển tiền, phát tán mã độc, quishing, dụ dỗ) và các kỹ thuật né tránh được sử dụng. "
          "Lời khuyên được sinh theo mức độ và loại tấn công, ví dụ với email đánh cắp tài khoản: “Nếu lỡ "
          "nhập mật khẩu, hãy đổi mật khẩu ngay, bật xác thực hai lớp và báo Phòng CNTT”."),
    ("h2", "Bộ dữ liệu email trường học tiếng Việt"),
    ("p", "Để phù hợp bối cảnh, nhóm xây dựng một corpus email trường học tiếng Việt gồm 15 dạng tấn công (đánh "
          "cắp tài khoản, học bổng giả, tuyển cộng tác viên, học phí giả, mạo danh thầy cô nhờ mua thẻ cào, "
          "macro, hóa đơn điện tử, mã QR…) và 21 dạng email hợp lệ. Trong số email hợp lệ có các email “khó” – "
          "email thật nhưng chứa liên kết chính thức, nhắc tới tệp đính kèm, mã QR, hạn chót, học bổng hay "
          "mật khẩu – để tránh mô hình học rằng mọi email nhắc tới những chủ đề này đều là lừa đảo. Các phép "
          "biến đổi kiểu LLM được cài đặt riêng cho tiếng Việt; email hợp lệ cũng được áp dụng phong cách cá "
          "nhân hóa để văn phong lịch sự không trở thành dấu hiệu nhận biết."),
    ("p", "Điểm quan trọng về phương pháp là các mẫu được chia theo template: cứ ba template thì một template "
          "được giữ lại (held-out), không dùng để huấn luyện mà chỉ dùng để đánh giá. Nếu huấn luyện và kiểm "
          "thử dùng chung cách viết, mô hình dễ dàng đạt gần 100% một cách giả tạo; việc giữ lại các dạng email "
          "chưa từng thấy mới đo được khả năng tổng quát hóa thật sự."),
    ("h2", "Giao diện và chức năng"),
    ("p", "Hệ thống được triển khai dưới dạng ứng dụng web chạy cục bộ (FastAPI ở phía máy chủ, HTML/JavaScript "
          "ở phía người dùng), gồm bốn chức năng: phân tích email, luyện tập nhận diện, xem kết quả đánh giá độ "
          "bền và giới thiệu. Người dùng có thể tải lên tệp .eml, dán nội dung, hoặc chọn một trong 12 email "
          "mẫu. Hình 5.2 là kết quả phân tích một email chỉ chứa ảnh và mã QR: điểm 100/100 ở mức Rất nguy "
          "hiểm, loại tấn công đánh cắp tài khoản, các kỹ thuật né tránh được nhận diện và mức rủi ro theo từng "
          "kênh."),
    ("fig", "s04_qr_m365_top.png", "Kết quả phân tích email chỉ chứa ảnh và mã QR", 16),
    ("p", "Hình 5.3 cho thấy cách hệ thống “đọc” được ảnh: OCR nhận dạng chính xác đoạn chữ tiếng Việt yêu cầu "
          "xác thực Microsoft 365 trước 17 giờ, và mã QR được giải mã thành một liên kết tới tên miền .click "
          "giả dạng tên trường. Những thông tin này hoàn toàn vô hình với một mô hình chỉ đọc thân thư."),
    ("fig", "c_qr_figure.png", "OCR và giải mã mã QR trong ảnh nhúng", 8),
    ("p", "Hình 5.4 minh họa phân tích tệp đính kèm với một tệp ZIP có mật khẩu. Hệ thống không giải nén được "
          "nội dung nhưng vẫn đọc tên tệp bên trong là HoaDon_T10.pdf.exe, từ đó phát hiện đuôi kép và tệp chạy "
          "được. Hình 5.5 là trường hợp mạo danh thầy nhờ mua thẻ cào: email không có liên kết hay tệp, mô hình "
          "văn bản chỉ cho xác suất 4% vì đây là dạng email chưa từng thấy, nhưng hệ thống vẫn chấm 78/100 nhờ "
          "phát hiện tên hiển thị mạo danh gửi từ Gmail, yêu cầu giữ bí mật và yêu cầu gửi mã thẻ."),
    ("fig", "c_zip_att.png", "Phân tích tệp ZIP có mật khẩu chứa tệp đuôi kép", 15),
    ("fig", "s08_the_cao_top.png", "Phân tích email mạo danh thầy nhờ mua thẻ cào", 16),
    ("p", "Chức năng luyện tập (Hình 5.6) trộn email mẫu với email sinh tự động, kể cả các bản viết lại kiểu "
          "LLM. Người dùng tự quyết định email an toàn hay lừa đảo trước, sau đó mới xem đáp án, bài học và phân "
          "tích chi tiết; hệ thống ghi nhận số câu đúng và chuỗi trả lời đúng liên tiếp. Đây là thành phần giáo "
          "dục, hướng tới mục tiêu nâng cao năng lực tự nhận diện của sinh viên và cán bộ."),
    ("fig", "quiz_a.png", "Chế độ luyện tập nhận diện email lừa đảo", 16),

    # =====================================================================================
    ("h1", "THỰC NGHIỆM VÀ ĐÁNH GIÁ"),
    ("h2", "Đánh giá trên bộ email mẫu"),
    ("p", "Bộ 12 email mẫu được thiết kế bao phủ các tình huống điển hình trong trường học, gồm ba email hợp lệ "
          "và chín email lừa đảo với các kỹ thuật khác nhau. Mọi tệp “độc hại” trong bộ mẫu đều là tệp giả vô "
          "hại. Bảng 6.1 trình bày kết quả với mô hình nội dung KD-BiLSTM. Tất cả email lừa đảo đều được xếp "
          "mức Rất nguy hiểm (78–100 điểm), và cả ba email hợp lệ đều ở mức An toàn (0–7 điểm), kể cả email "
          "bảo trì hệ thống có nhắc tới “mật khẩu” và email sự kiện có ảnh poster kèm mã QR."),
    ("tab", "Kết quả phân tích trên 12 email mẫu",
     [("Email mẫu", "Kỹ thuật chính", "Điểm", "Mức"),
      ("Lịch thi cuối kỳ", "Email thật, có PDF", "0", "An toàn"),
      ("Tài khoản sẽ bị khóa", "Tên miền nhái, link hiển thị sai", "100", "Rất nguy hiểm"),
      ("Học bổng viết trau chuốt", "Gmail mạo danh, Reply-To, link rút gọn", "94", "Rất nguy hiểm"),
      ("Chỉ có ảnh + mã QR", "Nội dung trong ảnh, link trong QR", "98", "Rất nguy hiểm"),
      ("Biên lai học phí", "Tệp HTML đăng nhập giả", "100", "Rất nguy hiểm"),
      ("Danh sách cảnh cáo", "Tài liệu Word có macro", "100", "Rất nguy hiểm"),
      ("Hóa đơn điện tử", "ZIP có mật khẩu, .pdf.exe", "100", "Rất nguy hiểm"),
      ("Thầy nhờ mua thẻ cào", "Mạo danh, không link, không tệp", "78", "Rất nguy hiểm"),
      ("Workshop CLB", "Email thật, poster + QR chính thức", "5", "An toàn"),
      ("Điều chỉnh học phí", "Giả mạo tên miền trường, PDF JavaScript", "97", "Rất nguy hiểm"),
      ("Microsoft 365 (tiếng Anh)", "Văn phong LLM, link hiển thị sai", "99", "Rất nguy hiểm"),
      ("Bảo trì hệ thống email", "Email thật, có chữ “mật khẩu”", "7", "An toàn")], [4.6, 6.4, 1.6, 3.4], 11),
    ("h2", "Thiết kế thí nghiệm đánh giá độ bền"),
    ("p", "Thí nghiệm nhằm trả lời hai câu hỏi nghiên cứu. Câu hỏi thứ nhất (RQ1): bộ phát hiện chỉ dựa trên "
          "văn bản, như mô hình của bài báo, suy giảm thế nào khi email lừa đảo được LLM viết lại hoặc thông "
          "điệp bị chuyển sang ảnh, mã QR, tệp đính kèm? Câu hỏi thứ hai (RQ2): kết hợp bằng chứng đa kênh có "
          "khôi phục được khả năng phát hiện mà không làm tăng báo nhầm trên email hợp lệ hay không?"),
    ("p", f"Mỗi kịch bản dùng {R['n_phish']} email lừa đảo và {R['n_legit']} email hợp lệ lấy từ các template "
          "held-out. Mỗi email lừa đảo được biến đổi theo sáu kịch bản: giữ nguyên; LLM viết lại (kết hợp cả "
          "ba hành vi); chuyển nội dung đã viết lại vào ảnh; chuyển vào ảnh và giấu liên kết trong mã QR; đặt "
          "nội dung trong tệp Word; đặt nội dung trong tệp HTML. Email hợp lệ được biến đổi theo đúng các kịch "
          "bản tương ứng để đo báo nhầm một cách công bằng, vì trong thực tế email hợp lệ cũng có ảnh, QR và tệp. "
          "Thông tin người gửi được giữ trung tính để chỉ còn “cách mang thông điệp” thay đổi. Bốn bộ phát hiện "
          "được so sánh: hai mô hình chỉ đọc văn bản thân thư (TF-IDF với hồi quy logistic, và KD-BiLSTM của "
          "bài báo) và hai cấu hình đa kênh của PhishLens dùng tương ứng hai mô hình đó. Ngưỡng cảnh báo là xác "
          "suất từ 0,5 với mô hình văn bản và điểm từ 50 với hệ đa kênh."),
    ("fig", "diag4.png", "Thiết kế thí nghiệm đánh giá độ bền", 16),
    ("h2", "Kết quả thí nghiệm"),
    ("p", "Bảng 6.2 trình bày tỉ lệ phát hiện email lừa đảo; Hình 6.2 biểu diễn cùng số liệu dưới dạng biểu đồ. "
          "Bảng 6.3 trình bày tỉ lệ báo nhầm trên email hợp lệ. Trong các bảng, VB là bộ phát hiện chỉ đọc văn "
          "bản, ĐK là hệ thống đa kênh, KD là mô hình KD-BiLSTM của bài báo."),
    ("tab", "Tỉ lệ phát hiện email lừa đảo theo kịch bản", rob_rows(), [4.8, 2.8, 2.8, 2.8, 2.8], 12),
    ("fig", "c_robust_chart.png", "Tỉ lệ phát hiện email lừa đảo theo kịch bản và bộ phát hiện", 16),
    ("tab", "Tỉ lệ báo nhầm trên email hợp lệ theo kịch bản", fpr_rows(), [4.8, 2.8, 2.8, 2.8, 2.8], 12),
    ("h2", "Phân tích kết quả"),
    ("p", "**Về RQ1**, kết quả cho thấy hai mức suy giảm rõ rệt của bộ phát hiện chỉ đọc văn bản. Khi email "
          "được LLM viết lại, tỉ lệ phát hiện của TF-IDF giảm từ 80% xuống 67%, của KD-BiLSTM giảm từ 67% xuống "
          "60%, khẳng định quan sát của bài báo rằng email do LLM viết lại khó phát hiện hơn. Nghiêm trọng hơn, "
          "khi thông điệp bị chuyển vào ảnh, mã QR, tệp Word hay tệp HTML, cả hai mô hình chỉ đọc thân thư đều "
          "phát hiện được 0%. Nói cách khác, chỉ một thao tác chuyển kênh đơn giản là đủ vô hiệu hóa hoàn toàn "
          "mọi bộ phân loại văn bản, bất kể mô hình tốt đến đâu."),
    ("p", "**Về RQ2**, hệ thống đa kênh giữ tỉ lệ phát hiện 80% khi email được viết lại và phục hồi 90–97% với "
          "nội dung trong ảnh, 100% với ảnh kèm mã QR, 57–70% với tệp Word và 100% với tệp HTML. Tệp Word có tỉ "
          "lệ thấp nhất vì không có tín hiệu bổ sung nào ngoài văn bản bên trong; tệp HTML và mã QR có thêm "
          "tín hiệu từ liên kết và cấu trúc tệp. Về báo nhầm, cấu hình đa kênh dùng TF-IDF gần như không báo "
          "nhầm (0–7%), trong khi cấu hình dùng KD-BiLSTM báo nhầm 10–20%."),
    ("h2", "Phân tích lỗi và bài học rút ra"),
    ("p", "**Mạo danh nhờ chuyển tiền (BEC) là dạng khó nhất.** Phân tích theo từng template cho thấy email "
          "mạo danh thầy nhờ mua thẻ cào bị mô hình văn bản bỏ sót hoàn toàn và hệ đa kênh vẫn bỏ sót 50%. Dạng "
          "này không có liên kết hay tệp, còn thí nghiệm lại cố ý giữ người gửi trung tính, tức là loại bỏ tín "
          "hiệu mạnh nhất của chính nó. Trong email mẫu thực tế, khi người gửi là một địa chỉ Gmail đặt tên "
          "“Trưởng khoa”, hệ thống chấm 78/100. Điều này cho thấy giá trị của việc kết hợp kênh người gửi với "
          "kênh nội dung."),
    ("p", "**Giới hạn của mô hình bài báo khi chuyển sang tiếng Việt.** Trên email hợp lệ chưa từng thấy, "
          "KD-BiLSTM báo nhầm khoảng 14% so với 1% của TF-IDF khi cùng đặt trong hệ đa kênh. Phân tích các ca "
          "báo nhầm cho thấy chúng tập trung ở thông báo họp khoa và thông báo hạn nộp hồ sơ học bổng. Nguyên "
          "nhân có thể là tokenizer tiếng Anh của MobileBERT xóa dấu tiếng Việt, làm mất thông tin phân biệt "
          "nghĩa, cộng với lượng dữ liệu huấn luyện nhỏ. Hướng khắc phục là chưng cất từ một mô hình thầy đa "
          "ngôn ngữ hoặc chuyên tiếng Việt như PhoBERT [14] hay XLM-R [15], hoặc hiệu chỉnh ngưỡng."),
    ("p", "**Hiện tượng học đường tắt.** Phiên bản đầu tiên của mô hình văn bản báo nhầm cả email thật có liên "
          "kết chính thức của trường với xác suất lên tới 96–100%; từ được mô hình chú ý nhiều nhất lại là tên "
          "miền của trường. Nguyên nhân là trong dữ liệu tổng hợp ban đầu, chỉ email lừa đảo mới chứa tên miền, "
          "nên mô hình học quy tắc sai “có tên miền thì là lừa đảo”. Đây là ví dụ điển hình của hiện tượng học "
          "đường tắt (shortcut learning) trong học sâu [16]. Sau khi che URL trước mô hình văn bản và bổ sung "
          "email hợp lệ “khó”, xác suất trên các email này giảm xuống dưới 0,3. Bài học rút ra là mô hình chỉ "
          "đọc văn bản rất dễ học mẹo từ dữ liệu, và việc tách bạch trách nhiệm giữa các kênh không chỉ giúp "
          "phát hiện các kỹ thuật chuyển kênh mà còn làm hệ thống bền vững hơn trước sai lệch dữ liệu."),
    ("h2", "Ưu điểm và hạn chế"),
    ("p", "Về ưu điểm, PhishLens Edu bổ sung đúng những gì bài báo còn thiếu khi đưa vào thực tế: xử lý được "
          "ảnh, mã QR và tệp đính kèm; đánh giá mức độ thay vì nhãn nhị phân; giải thích bằng tiếng Việt với "
          "bài học cụ thể; có chế độ luyện tập phục vụ giáo dục; chạy hoàn toàn cục bộ và không thực thi tệp. "
          "Kiến trúc theo bằng chứng giúp dễ bổ sung bộ phân tích mới mà không phải huấn luyện lại mô hình."),
    ("p", "Về hạn chế, dữ liệu huấn luyện và đánh giá là dữ liệu tổng hợp, phép “LLM viết lại” mới là bộ luật "
          "mô phỏng, nên các con số chỉ thể hiện xu hướng. Độ mạnh của từng bằng chứng hiện được đặt thủ công "
          "dựa trên hiểu biết chuyên môn, chưa được hiệu chỉnh trên dữ liệu thật. Hệ thống chưa kiểm tra danh "
          "tiếng URL trực tuyến, chưa chạy tệp trong môi trường cách ly (sandbox), và OCR trên CPU mất vài giây "
          "cho mỗi ảnh. Mô hình KD-BiLSTM kế thừa từ bài báo có tỉ lệ báo nhầm cao hơn mô hình TF-IDF trên "
          "tiếng Việt."),

    # =====================================================================================
    ("h1", "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN"),
    ("h2", "Kết luận"),
    ("p", "Đề tài đã nghiên cứu bài báo của Eskandarian và cộng sự về phát hiện email lừa đảo thế hệ LLM bằng "
          "BiLSTM có attention được chưng cất từ MobileBERT, trình bày cơ sở lý thuyết của các thành phần LSTM, "
          "BiLSTM, attention, Transformer và chưng cất tri thức. Phương pháp của bài báo đã được tái hiện đầy đủ "
          "về mặt kỹ thuật: dữ liệu, bốn mô hình cơ sở, mô hình thầy, mô hình chưng cất và quy trình năm kịch "
          "bản với kiểm định chéo. Số tham số và các xu hướng chính khớp với bài báo – chuyển phân phối làm giảm "
          "hiệu năng, multi-head attention và chưng cất giúp tổng quát hóa tốt hơn, mô hình trò nhanh hơn thầy "
          "nhiều lần – dù chưa so được số liệu tuyệt đối do thiếu dữ liệu gốc."),
    ("p", "Trên cơ sở đó, đề tài vận dụng bài báo để xây dựng PhishLens Edu, đặt mô hình KD-BiLSTM làm kênh nội "
          "dung trong một hệ thống phân tích rủi ro email đa kênh có giải thích dành cho môi trường giáo dục. "
          "Thí nghiệm độ bền cho thấy chỉ đọc văn bản là không đủ: các kỹ thuật chuyển kênh làm tỉ lệ phát hiện "
          "của mô hình văn bản giảm về 0%, trong khi kết hợp bằng chứng đa kênh phục hồi 57–100%."),
    ("h2", "Đóng góp của đề tài"),
    ("p", "Đóng góp của đề tài gồm năm điểm. Thứ nhất, một bản tái hiện đầy đủ, có thể chạy lại của phương "
          "pháp trong bài báo, kèm notebook chạy trên Google Colab và phân tích các vấn đề thực tế khi tái hiện, "
          "đặc biệt là hiện tượng sụp của MobileBERT và cách khắc phục. Thứ hai, một corpus email trường học "
          "tiếng Việt với các phép biến đổi kiểu LLM và cách chia template held-out để đánh giá khả năng tổng "
          "quát hóa. Thứ ba, hệ thống PhishLens Edu với năm kênh phân tích, cơ chế kết hợp bằng chứng noisy-OR, "
          "giải thích bằng tiếng Việt và chế độ luyện tập. Thứ tư, một thí nghiệm đánh giá độ bền cho thấy giới "
          "hạn của các bộ phát hiện chỉ dựa trên văn bản trước các kỹ thuật chuyển kênh. Thứ năm, các phân tích "
          "lỗi có giá trị thực tiễn: dạng BEC là khó nhất, mô hình của bài báo cần mô hình thầy phù hợp tiếng "
          "Việt, và hiện tượng học đường tắt có thể được giảm bằng cách tách bạch trách nhiệm giữa các kênh."),
    ("h2", "Hướng phát triển"),
    ("p", "Trong thời gian tới, đề tài có thể phát triển theo các hướng sau. Về dữ liệu, cần thu thập email lừa "
          "đảo thật (đã ẩn danh) mà trường nhận được thông qua hộp thư báo cáo của Phòng CNTT, đồng thời sinh "
          "biến thể bằng LLM thật chạy cục bộ để có dữ liệu đa dạng hơn. Về mô hình, cần chưng cất từ mô hình "
          "thầy đa ngôn ngữ như PhoBERT hay XLM-R và hiệu chỉnh độ mạnh của các bằng chứng trên dữ liệu thật. Về "
          "đánh giá, cần thực hiện khảo sát người dùng với sinh viên – làm bài kiểm tra nhận diện trước và sau "
          "hai tuần dùng chế độ luyện tập – để đo hiệu quả giáo dục. Về triển khai, hệ thống có thể được tích "
          "hợp dưới dạng add-in cho Outlook/Gmail hoặc một hộp thư “chuyển tiếp để kiểm tra”, và mở rộng với "
          "kiểm tra danh tiếng URL, phân tích tệp trong sandbox."),
]

REFERENCES = [
    "M. Eskandarian, M. Rabbani, A. Kaniyamattam, F. Nejati, M. Mirani, G. Piya, I. Opushnyev, A. A. Ghorbani, "
    "S. Dadkhah, “A lightweight defense mechanism against next-generation of phishing emails using distilled "
    "attention-augmented BiLSTM,” Journal of Information Security and Applications, vol. 101, 104552, 2026.",
    "G. Hinton, O. Vinyals, J. Dean, “Distilling the knowledge in a neural network,” arXiv:1503.02531, 2015.",
    "J. Kim, J. Oh, N. Kim, S. Cho, S.-Y. Yun, “Comparing Kullback-Leibler divergence and mean squared error "
    "loss in knowledge distillation,” arXiv:2105.08919, 2021.",
    "J. Hazell, “Spear phishing with large language models,” arXiv:2305.06972, 2023.",
    "F. Heiding, B. Schneier, A. Vishwanath, J. Bernstein, P. S. Park, “Devising and detecting phishing emails "
    "using large language models,” IEEE Access, 2024.",
    "S. Hochreiter, J. Schmidhuber, “Long short-term memory,” Neural Computation, vol. 9, no. 8, pp. 1735–1780, 1997.",
    "A. Vaswani et al., “Attention is all you need,” in Advances in Neural Information Processing Systems, 2017.",
    "T. Mikolov, K. Chen, G. Corrado, J. Dean, “Efficient estimation of word representations in vector space,” "
    "arXiv:1301.3781, 2013.",
    "J. Devlin, M.-W. Chang, K. Lee, K. Toutanova, “BERT: Pre-training of deep bidirectional transformers for "
    "language understanding,” in Proc. NAACL-HLT, 2019.",
    "Z. Sun, H. Yu, X. Song, R. Liu, Y. Yang, D. Zhou, “MobileBERT: a compact task-agnostic BERT for "
    "resource-limited devices,” in Proc. ACL, 2020.",
    "S. Kitterman, “Sender Policy Framework (SPF) for authorizing use of domains in email,” RFC 7208, IETF, 2014.",
    "D. Crocker, T. Hansen, M. Kucherawy, “DomainKeys Identified Mail (DKIM) signatures,” RFC 6376, IETF, 2011.",
    "M. Kucherawy, E. Zwicky, “Domain-based Message Authentication, Reporting, and Conformance (DMARC),” "
    "RFC 7489, IETF, 2015.",
    "D. Q. Nguyen, A. T. Nguyen, “PhoBERT: Pre-trained language models for Vietnamese,” in Findings of EMNLP, 2020.",
    "A. Conneau et al., “Unsupervised cross-lingual representation learning at scale,” in Proc. ACL, 2020.",
    "R. Geirhos et al., “Shortcut learning in deep neural networks,” Nature Machine Intelligence, vol. 2, "
    "pp. 665–673, 2020.",
]
