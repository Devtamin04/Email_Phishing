"""Deployment-specific knowledge. Edit for your institution."""

ORG_NAME = "Trường Đại học Demo"
ORG_DOMAINS = ["dhdemo.edu.vn"]          # official domains of the institution

# Brands commonly impersonated (domain -> display name)
BRANDS = {
    "microsoft.com": "Microsoft", "office.com": "Microsoft 365", "live.com": "Microsoft",
    "google.com": "Google", "gmail.com": "Gmail", "apple.com": "Apple", "paypal.com": "PayPal",
    "facebook.com": "Facebook", "zalo.me": "Zalo", "vietcombank.com.vn": "Vietcombank",
    "techcombank.com.vn": "Techcombank", "momo.vn": "MoMo", "shopee.vn": "Shopee",
    "viettel.vn": "Viettel", "dhl.com": "DHL", "netflix.com": "Netflix",
}
FREEMAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "proton.me",
            "protonmail.com", "yandex.com", "mail.ru", "gmx.com", "aol.com", "zoho.com"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "rb.gy", "is.gd", "cutt.ly",
              "shorturl.at", "ow.ly", "tiny.cc", "s.id", "rebrand.ly", "bitly.com"}
SUSPICIOUS_TLDS = {"top", "xyz", "zip", "click", "tk", "ml", "gq", "cf", "ga", "icu", "buzz",
                   "rest", "monster", "cam", "work", "support", "live", "sbs", "cfd", "mov"}
RISKY_EXT = {"exe", "scr", "js", "jse", "vbs", "vbe", "bat", "cmd", "ps1", "hta", "lnk", "iso",
             "img", "vhd", "msi", "jar", "wsf", "one", "apk", "cpl", "dll", "com", "pif", "reg"}
MACRO_EXT = {"docm", "xlsm", "pptm", "dotm", "xltm", "xlam", "ppsm"}
ARCHIVE_EXT = {"zip", "rar", "7z", "gz", "tar", "cab", "ace"}

# Risk levels (score 0-100) -> key, Vietnamese label, icon. Colours live in the UI.
LEVELS = [(75, "critical", "Rất nguy hiểm", "⛔"), (50, "serious", "Nguy hiểm", "▲"),
          (25, "warning", "Cần chú ý", "!"), (0, "good", "An toàn", "✓")]

OCR_ENABLED = True          # EasyOCR (vi + en); downloads ~100MB of weights on first use
OCR_LANGS = ["vi", "en"]
