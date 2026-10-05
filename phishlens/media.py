"""Images (QR decoding + OCR) and attachments (static analysis - files are never executed)."""
import base64
import hashlib
import io
import re
import zipfile

from . import config
from .evidence import Evidence
from .parser import Link, html_to_text, extract_urls

# ---------------------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------------------
_OCR = None


def _trusted_host(url):
    from urllib.parse import urlparse

    from .sender_links import TRUSTED
    h = (urlparse(url).hostname or "").lower()
    return any(h == d or h.endswith("." + d) for d in TRUSTED)


def ocr_reader():
    global _OCR
    if _OCR is None and config.OCR_ENABLED:
        try:
            import easyocr
            _OCR = easyocr.Reader(config.OCR_LANGS, gpu=False, verbose=False)
        except Exception as e:  # noqa: BLE001 - OCR is optional
            print("OCR disabled:", e)
            config.OCR_ENABLED = False
    return _OCR


def _decode_image(data):
    import cv2
    import numpy as np
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    return arr


def decode_qr(img):
    import cv2
    if img is None:
        return []
    det = cv2.QRCodeDetector()
    for scale in (1.0, 2.0, 0.5):
        im = img if scale == 1.0 else cv2.resize(img, None, fx=scale, fy=scale)
        try:
            ok, texts, _, _ = det.detectAndDecodeMulti(im)
        except cv2.error:
            ok, texts = False, []
        texts = [t for t in (texts or []) if t]
        if ok and texts:
            return texts
    return []


_OCR_CACHE = {}


def run_ocr(img, key=None):
    if key is not None and key in _OCR_CACHE:
        return _OCR_CACHE[key]
    r = ocr_reader()
    if r is None or img is None:
        return ""
    h, w = img.shape[:2]
    if max(h, w) > 1600:
        import cv2
        f = 1600 / max(h, w)
        img = cv2.resize(img, None, fx=f, fy=f)
    text = " ".join(t for _, t, conf in r.readtext(img) if conf > 0.2)
    if key is not None:
        _OCR_CACHE[key] = text
    return text


def thumbnail(data, max_side=480):
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:  # noqa: BLE001
        return None
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def analyze_images(images, use_ocr=True):
    """-> evidences, [(where, text)], [Link], info list"""
    ev, texts, links, info = [], [], [], []
    for im in images:
        where = f"ảnh {im.filename}"
        arr = _decode_image(im.data)
        item = {"name": im.filename, "size": len(im.data), "thumb": thumbnail(im.data),
                "qr": [], "ocr": ""}
        if arr is None:
            info.append(item)
            continue
        if min(arr.shape[:2]) < 8:
            info.append(item)
            continue
        for q in decode_qr(arr):
            item["qr"].append(q)
            urls = extract_urls(q, f"qr:{im.filename}") or (
                [Link(q, "", f"qr:{im.filename}")] if re.match(r"\w+://", q) else [])
            links += urls
            official = any(_trusted_host(u.href) for u in urls) and urls
            ev.append(Evidence(
                "image", "Mã QR dẫn tới tên miền chính thức" if official
                else "Email chứa mã QR dẫn tới một liên kết",
                f"Mã QR trong {im.filename} chứa: {q}", 0.05 if official else 0.3,
                "Mã QR che giấu liên kết khỏi bộ lọc và khỏi mắt người đọc; quét trên điện "
                "thoại cũng tránh được lớp bảo vệ của máy tính (quishing).", where,
                [] if official else ["quishing"]))
        if use_ocr:
            t = run_ocr(arr, hashlib.sha1(im.data).hexdigest())
            item["ocr"] = t
            if t:
                texts.append((where, t))
                links += extract_urls(t, f"ocr:{im.filename}")
        info.append(item)
    return ev, texts, links, info


# ---------------------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------------------
def sniff(data: bytes, name: str = ""):
    head = data[:2048]
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"PK\x03\x04"):
        try:
            names = zipfile.ZipFile(io.BytesIO(data)).namelist()
        except zipfile.BadZipFile:
            return "zip"
        if "[Content_Types].xml" in names:
            for pre, kind in (("word/", "docx"), ("xl/", "xlsx"), ("ppt/", "pptx")):
                if any(n.startswith(pre) for n in names):
                    return kind
        return "zip"
    if head.startswith(b"\xD0\xCF\x11\xE0"):
        return "ole"
    if head.startswith(b"MZ"):
        return "exe"
    if head.startswith(b"\x89PNG"):
        return "png"
    if head.startswith(b"\xFF\xD8"):
        return "jpg"
    if head.startswith(b"GIF8"):
        return "gif"
    if head.startswith(b"Rar!"):
        return "rar"
    if head.startswith(b"7z\xBC\xAF"):
        return "7z"
    if head.startswith(b"L\x00\x00\x00\x01\x14\x02\x00"):
        return "lnk"
    if len(data) > 0x8006 and data[0x8001:0x8006] == b"CD001":
        return "iso"
    low = head.lower()
    if re.search(rb"<!doctype html|<html|<script|<form|<body", low):
        return "html"
    try:
        head.decode("utf-8")
        return "text"
    except UnicodeDecodeError:
        return "binary"


_FAMILY = {"pdf": {"pdf"}, "docx": {"docx", "docm", "dotx", "dotm"}, "xlsx": {"xlsx", "xlsm", "xltm", "xlam"},
           "pptx": {"pptx", "pptm", "ppsm"}, "ole": {"doc", "xls", "ppt", "msg", "msi"},
           "zip": {"zip", "jar", "apk"}, "exe": {"exe", "dll", "scr", "com", "cpl"},
           "png": {"png"}, "jpg": {"jpg", "jpeg"}, "gif": {"gif"}, "rar": {"rar"}, "7z": {"7z"},
           "html": {"html", "htm", "shtml", "xhtml", "svg"}, "lnk": {"lnk"}, "iso": {"iso", "img"},
           "text": {"txt", "csv", "log", "md", "json", "xml", "eml", "ics", "svg", "html", "htm"}}


def _ext(name):
    return name.rsplit(".", 1)[-1].lower().strip() if "." in name else ""


def _pdf(data, name, where):
    ev, links, text = [], [], ""
    checks = [(rb"/JavaScript|/JS\b", 0.5, "PDF chứa mã JavaScript"),
              (rb"/Launch", 0.7, "PDF có lệnh /Launch để chạy chương trình"),
              (rb"/EmbeddedFile", 0.4, "PDF nhúng tệp khác bên trong"),
              (rb"/SubmitForm", 0.4, "PDF có biểu mẫu gửi dữ liệu ra ngoài")]
    hits = [(s, m) for rx, s, m in checks if re.search(rx, data)]
    auto = re.search(rb"/OpenAction|/AA\b", data)
    for s, m in hits:
        ev.append(Evidence("attachment", m + (" (tự chạy khi mở)" if auto and "JavaScript" in m else ""),
                           f"Tệp {name}.", s + (0.15 if auto else 0),
                           "PDF bình thường (thông báo, biểu mẫu) hiếm khi cần chạy mã.", where,
                           ["malware"]))
    for u in re.findall(rb"/URI\s*\(([^)]+)\)", data):
        links.append(Link(u.decode("latin-1"), "", f"att:{name}"))
    try:
        from pypdf import PdfReader
        text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages[:10])
    except Exception:  # noqa: BLE001
        pass
    if links and len(text.strip()) < 200:
        ev.append(Evidence("attachment", "PDF gần như chỉ chứa một liên kết/nút bấm",
                           f"{name}: ít nội dung nhưng có {len(links)} liên kết.", 0.25,
                           "PDF 'mồi' chỉ để dẫn bạn tới trang đăng nhập giả.", where,
                           ["credential_harvest"]))
    if not hits:
        ev.append(Evidence("attachment", f"{name}: không thấy mã thực thi trong PDF",
                           "Không có JavaScript/Launch/tệp nhúng.", good=True, source=where))
    return ev, links, text


def _ooxml(data, name, where):
    ev, links, text = [], [], ""
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    if any(n.lower().endswith("vbaproject.bin") for n in names):
        ev.append(Evidence("attachment", "Tài liệu Office chứa macro (VBA)",
                           f"{name} có vbaProject.bin - macro có thể tải và chạy mã độc khi bạn "
                           "bấm 'Enable Content'.", 0.7,
                           "Không bật macro cho tài liệu nhận qua email.", where, ["malware"]))
    for n in names:
        if n.endswith(".rels"):
            rel = z.read(n).decode("utf-8", "ignore")
            for tgt in re.findall(r'Target="(https?://[^"]+)"[^>]*TargetMode="External"', rel):
                links.append(Link(tgt, "", f"att:{name}"))
                if "attachedTemplate" in rel or "oleObject" in rel:
                    ev.append(Evidence("attachment", "Tài liệu tải mẫu/đối tượng từ Internet",
                                       f"{name} tham chiếu {tgt} (template injection).", 0.6,
                                       source=where, tags=["malware"]))
    parts = [n for n in names if re.match(r"(word/document|xl/sharedStrings|ppt/slides/slide\d+)\.xml$", n)]
    text = " ".join(re.sub(r"<[^>]+>", " ", z.read(n).decode("utf-8", "ignore")) for n in parts)
    return ev, links, re.sub(r"\s+", " ", text)


def _html_att(data, name, where):
    ev = []
    src = data.decode("utf-8", "ignore")
    ev.append(Evidence("attachment", "Tệp HTML đính kèm",
                       f"{name} sẽ mở trong trình duyệt như một trang web cục bộ.", 0.25,
                       "Trang đăng nhập giả gửi dưới dạng tệp .html né được bộ lọc URL.", where,
                       ["credential_harvest"]))
    if re.search(r'type\s*=\s*["\']?password', src, re.I):
        ev.append(Evidence("attachment", "Tệp HTML có ô nhập mật khẩu",
                           f"{name} chứa biểu mẫu yêu cầu mật khẩu.", 0.6,
                           "Không nhập mật khẩu vào trang mở từ tệp đính kèm.", where,
                           ["credential_harvest"]))
    for act in re.findall(r'<form[^>]+action\s*=\s*["\']([^"\']+)', src, re.I):
        if act.startswith("http"):
            ev.append(Evidence("attachment", "Biểu mẫu gửi dữ liệu tới máy chủ bên ngoài",
                               f"action = {act}", 0.3, source=where, tags=["credential_harvest"]))
    if re.search(r"atob\(|new Blob\(|msSaveOrOpenBlob|String\.fromCharCode|unescape\(", src):
        ev.append(Evidence("attachment", "Dấu hiệu HTML smuggling (giải mã dữ liệu ẩn bằng JS)",
                           f"{name} dùng atob/Blob để dựng tệp hoặc trang ngay trong trình duyệt.",
                           0.5, "Kỹ thuật này giấu mã độc khỏi bộ quét tệp đính kèm.", where,
                           ["malware", "evasion"]))
    if re.search(r'http-equiv\s*=\s*["\']?refresh|window\.location|location\.href', src, re.I):
        ev.append(Evidence("attachment", "Tệp HTML tự chuyển hướng sang trang khác",
                           f"{name} tự động mở một địa chỉ web.", 0.3, source=where,
                           tags=["credential_harvest"]))
    text, links, _ = html_to_text(src)
    for l in links:
        l.source = f"att:{name}"
    links += extract_urls(src, f"att:{name}")
    return ev, links, text


def analyze_attachment(name, data, depth=0):
    """-> evidences, [(where, text)], [Link], info dict"""
    where = f"tệp {name}"
    ev, texts, links = [], [], []
    ext, kind = _ext(name), sniff(data, name)
    info = {"name": name, "size": len(data), "ext": ext, "detected": kind, "findings": []}

    if "\u202e" in name:
        ev.append(Evidence("attachment", "Tên tệp dùng ký tự đảo chiều (RLO)",
                           f"Tên thật: {name!r}", 0.8, "Ký tự RLO làm 'exe.pdf' hiển thị như "
                           "'fdp.exe'…", where, ["malware"]))
    m = re.search(r"\.(pdf|docx?|xlsx?|pptx?|jpe?g|png|txt|mp4)\s*\.(\w+)$", name, re.I)
    if m and m.group(2).lower() in config.RISKY_EXT | {"html", "htm"}:
        ev.append(Evidence("attachment", "Tệp có đuôi kép",
                           f"'{name}' giả làm .{m.group(1)} nhưng thực chất là .{m.group(2)}.",
                           0.9, "Windows thường ẩn đuôi tệp - bật 'File name extensions' để thấy "
                           "đuôi thật.", where, ["malware"]))
    if ext in config.RISKY_EXT or kind in ("exe", "lnk", "iso"):
        ev.append(Evidence("attachment", "Tệp có thể chạy được (chương trình/script)",
                           f"{name} (loại thực tế: {kind if data else 'không đọc được - bị mã hóa'}).", 0.85,
                           "Không mở tệp chương trình nhận qua email.", where, ["malware"]))
    if ext in config.MACRO_EXT:
        ev.append(Evidence("attachment", "Định dạng Office cho phép macro",
                           f"Đuôi .{ext} được thiết kế để chứa macro.", 0.45, source=where,
                           tags=["malware"]))
    fam = next((f for f, exts in _FAMILY.items() if ext in exts), None)
    if ext and kind not in ("text", "binary") and fam and kind != fam and ext not in _FAMILY.get(kind, ()):
        ev.append(Evidence("attachment", "Đuôi tệp không khớp nội dung thật",
                           f"{name} có đuôi .{ext} nhưng nội dung thực là {kind}.",
                           0.8 if kind in ("exe", "html", "lnk") else 0.4,
                           "Kẻ gian đổi đuôi tệp để vượt bộ lọc.", where, ["malware", "evasion"]))

    if kind == "pdf":
        e, l, t = _pdf(data, name, where)
        ev, links = ev + e, links + l
        texts.append((where, t))
    elif kind in ("docx", "xlsx", "pptx"):
        e, l, t = _ooxml(data, name, where)
        ev, links = ev + e, links + l
        texts.append((where, t))
    elif kind == "ole":
        if re.search(rb"_VBA_PROJECT|VBA\x00|Macros", data):
            ev.append(Evidence("attachment", "Tài liệu Office cũ chứa macro",
                               f"{name} (định dạng OLE) có luồng VBA.", 0.65, source=where,
                               tags=["malware"]))
    elif kind == "html":
        e, l, t = _html_att(data, name, where)
        ev, links = ev + e, links + l
        texts.append((where, t))
    elif kind == "zip" and depth == 0:
        z = zipfile.ZipFile(io.BytesIO(data))
        infos = z.infolist()[:30]
        if any(i.flag_bits & 0x1 for i in infos):
            ev.append(Evidence("attachment", "Tệp nén có mật khẩu",
                               f"{name}: nội dung bị mã hóa nên phần mềm diệt virus không quét "
                               "được.", 0.5, "Mật khẩu gửi kèm trong thư là chiêu né quét virus.",
                               where, ["malware", "evasion"]))
        info["inner"] = []
        for i in infos:
            if i.is_dir():
                continue
            locked = i.flag_bits & 0x1 or i.file_size > 10_000_000
            # encrypted entries cannot be read, but their *names* are still visible
            data_i = b"" if locked else z.read(i)
            e, t, l, sub = analyze_attachment(i.filename, data_i, depth + 1)
            if locked:
                sub["detected"] = "không đọc được (mã hóa)"
            for x in e:
                x.source = f"{where} → {i.filename}"
            ev, texts, links = ev + e, texts + t, links + l
            info["inner"].append(sub)
    elif kind in ("rar", "7z"):
        ev.append(Evidence("attachment", f"Tệp nén .{kind} không quét được bên trong",
                           f"{name}", 0.2, source=where, tags=["evasion"]))
    elif kind == "text":
        texts.append((where, data[:20000].decode("utf-8", "ignore")))
        links += extract_urls(data[:20000].decode("utf-8", "ignore"), f"att:{name}")
    info["findings"] = [x.title for x in ev if not x.good and "→" not in x.source]
    return ev, texts, links, info
