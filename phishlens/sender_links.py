"""Sender (headers) and link analysis."""
import ipaddress
import re
from urllib.parse import urlparse

from . import config
from .evidence import Evidence, domain_of, impersonation, noisy_or, registered_domain

TRUSTED = {**{d: config.ORG_NAME for d in config.ORG_DOMAINS}, **config.BRANDS}

_AUTHORITY = re.compile(
    r"phòng|khoa|trường|ban |ban$|hiệu trưởng|trưởng|thầy|cô |giảng viên|đào tạo|công tác|"
    r"ctsv|tài vụ|kế toán|thư viện|admin|support|hỗ trợ|helpdesk|it\b|cntt|security|bảo mật|"
    r"ngân hàng|bank|microsoft|google|office|paypal|apple|zalo|momo|shopee|viettel|"
    + "|".join(re.escape(n.lower()) for n in set(config.BRANDS.values()) | {config.ORG_NAME}),
    re.I)


def _auth(results: str, mech: str):
    m = re.search(rf"\b{mech}\s*=\s*(\w+)", results or "", re.I)
    return m.group(1).lower() if m else None


def analyze_sender(doc):
    ev = []
    dom = domain_of(doc.from_addr)
    if not doc.from_addr:
        ev.append(Evidence("sender", "Không xác định được người gửi",
                           "Email không có địa chỉ người gửi hợp lệ.", 0.15))
        return ev

    fails = [m.upper() for m in ("spf", "dkim", "dmarc")
             if _auth(doc.auth_results, m) in ("fail", "softfail", "permerror")]
    passes = [m.upper() for m in ("spf", "dkim", "dmarc") if _auth(doc.auth_results, m) == "pass"]
    if fails:
        ev.append(Evidence(
            "sender", f"Xác thực tên miền thất bại ({', '.join(fails)})",
            f"Máy chủ nhận báo {', '.join(fails)} = fail cho tên miền {dom}: email có thể đã bị "
            "giả mạo địa chỉ người gửi.",
            0.25 + 0.15 * len(fails),
            "SPF/DKIM/DMARC là 'chữ ký' của tên miền. Thất bại nghĩa là không chắc email đến từ "
            "đúng tổ chức.", tags=["spoofing"]))

    imp = impersonation(dom, TRUSTED)
    if imp:
        t, kind = imp
        ev.append(Evidence(
            "sender", "Tên miền người gửi giả dạng tổ chức uy tín",
            f"'{dom}' trông giống '{t}' ({TRUSTED[t]}) nhưng không phải tên miền thật"
            + (" (sai khác vài ký tự)." if kind == "lookalike" else "."),
            0.65, "Đọc kỹ từng ký tự của tên miền sau dấu @, ví dụ dhdemo-edu.com ≠ dhdemo.edu.vn.",
            tags=["spoofing"]))

    name = doc.from_name or ""
    if dom in config.FREEMAIL and _AUTHORITY.search(name):
        ev.append(Evidence(
            "sender", "Tên hiển thị mạo danh đơn vị nhưng gửi từ email cá nhân",
            f"Tên hiển thị '{name}' nghe như một đơn vị/người có thẩm quyền, nhưng địa chỉ thật "
            f"là {doc.from_addr} (dịch vụ email miễn phí).",
            0.5, "Đơn vị trong trường gửi thư từ tên miền của trường, không dùng Gmail/Yahoo.",
            tags=["impersonation"]))
    m = re.search(r"[\w.+-]+@([\w-]+\.[\w.-]+)", name)
    if m and m.group(1).lower() != dom:
        ev.append(Evidence(
            "sender", "Tên hiển thị chứa một địa chỉ email khác",
            f"Tên hiển thị ghi '{m.group(0)}' nhưng thư thực sự gửi từ {doc.from_addr}.", 0.5,
            "Ứng dụng thư thường chỉ hiện tên hiển thị - hãy mở xem địa chỉ thật.",
            tags=["impersonation"]))

    rdom = domain_of(doc.reply_to)
    if rdom and registered_domain(rdom) != registered_domain(dom):
        ev.append(Evidence(
            "sender", "Địa chỉ trả lời (Reply-To) khác người gửi",
            f"Khi bấm Trả lời, thư sẽ đi tới {doc.reply_to} thay vì {doc.from_addr}.",
            0.35 if rdom in config.FREEMAIL else 0.25,
            "Kẻ gian dùng Reply-To để nhận phản hồi ở hộp thư của chúng.", tags=["impersonation"]))
    pdom = domain_of(doc.return_path)
    if pdom and registered_domain(pdom) != registered_domain(dom) and not fails:
        ev.append(Evidence("sender", "Return-Path khác tên miền người gửi",
                           f"Return-Path: {doc.return_path}.", 0.08))

    is_org = any(dom == d or dom.endswith("." + d) for d in config.ORG_DOMAINS)
    if is_org and passes and not fails:
        ev.append(Evidence("sender", "Người gửi thuộc tên miền của trường và đã xác thực",
                           f"{doc.from_addr} - {', '.join(passes)} = pass.", good=True))
    elif passes and not fails and not imp:
        ev.append(Evidence("sender", "Tên miền người gửi đã xác thực",
                           f"{dom}: {', '.join(passes)} = pass (chỉ xác nhận tên miền, không "
                           "xác nhận người gửi đáng tin).", good=True))
    return ev


# ---------------------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------------------
_CRED_PATH = re.compile(r"login|log-in|signin|sign-in|verify|verification|account|password|"
                        r"passwd|auth|update|secure|wallet|dang-?nhap|xac-?(thuc|minh)|mat-?khau|"
                        r"tai-?khoan|otp|banking", re.I)
_DOMAINISH = re.compile(r"((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host(url):
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def analyze_link(link, where="nội dung email"):
    url, reasons, tags = link.href.strip(), [], set()
    scheme = url.split(":", 1)[0].lower()
    if scheme in ("javascript", "data", "vbscript"):
        return Evidence("links", f"Liên kết thực thi mã ({scheme}:)",
                        f"Liên kết dạng {scheme}: có thể chạy mã khi bấm.", 0.5,
                        source=where, tags=["malware"])
    if scheme in ("mailto", "tel", "cid"):
        return None
    host = _host(url)
    if not host:
        return None
    reg = registered_domain(host)
    trusted = any(host == d or host.endswith("." + d) for d in TRUSTED)

    def add(s, msg, *t):
        reasons.append((s, msg))
        tags.update(t)

    shown = _DOMAINISH.search(link.text or "")
    if shown and "." in shown.group(1):
        shown_reg = registered_domain(shown.group(1))
        if shown_reg != reg and not shown.group(1).lower().endswith(reg):
            add(0.6, f"chữ hiển thị là '{shown.group(1)}' nhưng thực tế dẫn tới '{host}'",
                "credential_harvest")
    try:
        ipaddress.ip_address(host)
        add(0.5, "dùng địa chỉ IP thay vì tên miền")
    except ValueError:
        pass
    if reg in config.SHORTENERS:
        add(0.3, f"dùng dịch vụ rút gọn link ({reg}) để che đích đến thật")
    if "xn--" in host:
        add(0.5, "tên miền punycode (ký tự quốc tế giả dạng chữ Latin)")
    imp = impersonation(host, TRUSTED)
    if imp:
        t, kind = imp
        add(0.6, f"tên miền giả dạng {TRUSTED[t]} ({t})" +
            (" - sai khác vài ký tự" if kind == "lookalike" else " - chèn tên thương hiệu vào "
             "một tên miền khác"), "credential_harvest")
    if reg.rsplit(".", 1)[-1] in config.SUSPICIOUS_TLDS:
        add(0.3, f"đuôi tên miền .{reg.rsplit('.', 1)[-1]} thường bị lạm dụng")
    if "@" in url.split("//", 1)[-1].split("/", 1)[0]:
        add(0.4, "URL chứa ký tự @ để đánh lừa phần tên miền")
    if host.count(".") >= 4:
        add(0.15, "tên miền có quá nhiều cấp con")
    if not trusted and _CRED_PATH.search(url):
        add(0.25 if scheme == "http" else 0.15,
            "đường dẫn gợi ý trang đăng nhập/xác minh tài khoản", "credential_harvest")
    if not trusted and scheme == "http" and reasons:
        add(0.1, "không dùng HTTPS")
    if not reasons:
        return None
    s = noisy_or(r[0] for r in reasons)
    return Evidence(
        "links", f"Liên kết đáng ngờ: {host}",
        f"{url}\n" + "\n".join(f"• {m}" for _, m in reasons), s,
        "Di chuột lên liên kết để xem địa chỉ thật trước khi bấm; tự gõ địa chỉ trang chính "
        "thức thay vì bấm link trong email.", source=where, tags=sorted(tags) or ["link"])


def analyze_links(links, where_map=None):
    ev = []
    for l in links:
        e = analyze_link(l, (where_map or {}).get(l.source, l.source))
        if e:
            ev.append(e)
    return ev
