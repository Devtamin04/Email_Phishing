"""Turns a raw .eml (or a manually entered message) into an EmailDoc."""
import email
import re
from dataclasses import dataclass, field
from email import policy
from email.utils import getaddresses, parseaddr
from html.parser import HTMLParser

URL_RE = re.compile(r"""(?:https?://|www\.)[^\s<>"'()\[\]{}]+""", re.I)


@dataclass
class Part:
    filename: str
    content_type: str
    data: bytes


@dataclass
class Link:
    href: str
    text: str = ""
    source: str = "body"          # body | html | qr:<img> | ocr:<img> | att:<file>


@dataclass
class EmailDoc:
    subject: str = ""
    from_name: str = ""
    from_addr: str = ""
    reply_to: str = ""
    return_path: str = ""
    to: str = ""
    date: str = ""
    auth_results: str = ""
    text: str = ""
    html: str = ""
    links: list = field(default_factory=list)
    images: list = field(default_factory=list)
    attachments: list = field(default_factory=list)


class _HTMLText(HTMLParser):
    """Visible text + <a href> anchors + <img src> of an HTML body."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.links, self.imgs = [], [], []
        self._a, self._skip = None, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
        elif tag == "a" and a.get("href"):
            self._a = [a["href"], []]
        elif tag == "img" and a.get("src"):
            self.imgs.append(a["src"])
        elif tag in ("br", "p", "div", "tr", "li", "h1", "h2", "h3"):
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag == "a" and self._a:
            self.links.append(Link(self._a[0], "".join(self._a[1]).strip(), "html"))
            self._a = None

    def handle_data(self, data):
        if self._skip:
            return
        self.out.append(data)
        if self._a:
            self._a[1].append(data)


def html_to_text(html: str):
    p = _HTMLText()
    p.feed(html)
    text = re.sub(r"[ \t]+", " ", "".join(p.out))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip(), p.links, p.imgs


def extract_urls(text: str, source: str):
    out = []
    for u in URL_RE.findall(text or ""):
        u = u.rstrip(".,;:!?")
        out.append(Link(u if "://" in u else "http://" + u, u, source))
    return out


def _dedup_links(links):
    seen, out = set(), []
    for l in links:
        k = (l.href, l.text, l.source)
        if k not in seen:
            seen.add(k)
            out.append(l)
    return out


def parse_eml(raw: bytes) -> EmailDoc:
    msg = email.message_from_bytes(raw, policy=policy.default)
    name, addr = parseaddr(str(msg.get("From", "")))
    doc = EmailDoc(
        subject=str(msg.get("Subject", "")), from_name=name, from_addr=addr.lower(),
        reply_to=parseaddr(str(msg.get("Reply-To", "")))[1].lower(),
        return_path=parseaddr(str(msg.get("Return-Path", "")))[1].lower(),
        to=", ".join(a for _, a in getaddresses([str(msg.get("To", ""))])),
        date=str(msg.get("Date", "")),
        auth_results=" ".join(str(v) for v in msg.get_all("Authentication-Results", []) or []),
    )
    texts, htmls = [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        fname = part.get_filename()
        disp = part.get_content_disposition()
        if ctype == "text/plain" and disp != "attachment" and not fname:
            texts.append(part.get_content())
        elif ctype == "text/html" and disp != "attachment" and not fname:
            htmls.append(part.get_content())
        else:
            data = part.get_payload(decode=True) or b""
            fname = fname or f"part.{ctype.split('/')[-1]}"
            target = doc.images if ctype.startswith("image/") else doc.attachments
            target.append(Part(fname, ctype, data))
    doc.html = "\n".join(htmls)
    links = []
    if htmls:
        h_text, h_links, _ = html_to_text(doc.html)
        links += h_links
        doc.text = "\n".join(texts) if texts else h_text
    else:
        doc.text = "\n".join(texts)
    links += extract_urls(doc.text, "body")
    doc.links = _dedup_links(links)
    return doc


def from_manual(subject="", sender="", body="", files=()) -> EmailDoc:
    """files: iterable of (filename, content_type, bytes)."""
    name, addr = parseaddr(sender)
    is_html = bool(re.search(r"<(html|a|p|div|br)\b", body or "", re.I))
    doc = EmailDoc(subject=subject, from_name=name, from_addr=addr.lower())
    if is_html:
        doc.html = body
        doc.text, links, _ = html_to_text(body)
    else:
        doc.text, links = body, []
    doc.links = _dedup_links(links + extract_urls(doc.text, "body"))
    for fn, ct, data in files:
        (doc.images if (ct or "").startswith("image/") else doc.attachments).append(Part(fn, ct, data))
    return doc
