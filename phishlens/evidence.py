"""Evidence = one explainable finding. Strength in [0, 1] is combined by noisy-OR."""
import re
from dataclasses import asdict, dataclass, field

CATEGORIES = {
    "sender": "Người gửi",
    "links": "Liên kết",
    "content": "Nội dung",
    "image": "Hình ảnh & mã QR",
    "attachment": "Tệp đính kèm",
}


@dataclass
class Evidence:
    category: str
    title: str
    detail: str
    strength: float = 0.0          # 0 for positive ("good") findings
    tip: str = ""                  # what the reader should learn from it
    source: str = "email"
    tags: list = field(default_factory=list)   # attack types / techniques
    good: bool = False

    def to_dict(self):
        return asdict(self)


def noisy_or(strengths):
    p = 1.0
    for s in strengths:
        p *= 1.0 - max(0.0, min(1.0, s))
    return 1.0 - p


# ---------------------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------------------
_SLD = {"com", "edu", "gov", "org", "net", "ac", "co", "info", "biz", "health", "int"}


def registered_domain(host: str) -> str:
    host = (host or "").lower().strip(".")
    labels = host.split(".")
    if len(labels) >= 3 and labels[-2] in _SLD and len(labels[-1]) == 2:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def domain_of(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower() if "@" in (addr or "") else ""


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


_HOMO = [("rn", "m"), ("vv", "w"), ("0", "o"), ("1", "l"), ("3", "e"), ("5", "s"), ("@", "a")]


def _skeleton(s: str) -> str:
    for a, b in _HOMO:
        s = s.replace(a, b)
    return s.replace("-", "")


def _name(reg: str) -> str:
    return reg.split(".")[0]


def impersonation(host: str, trusted: dict):
    """Returns (trusted_domain, kind) if `host` imitates a trusted domain, else None.
    kind: 'lookalike' (typo / homoglyph) or 'embedded' (brand placed in another domain)."""
    host = (host or "").lower()
    reg = registered_domain(host)
    for t in trusted:
        if host == t or host.endswith("." + t):
            return None
    for t in trusted:
        tn, rn = _name(t), _name(reg)
        if len(tn) >= 5 and (_skeleton(rn) == _skeleton(tn) or 1 <= levenshtein(rn, tn) <= 2):
            return t, "lookalike"
        if len(tn) >= 5 and re.search(rf"(^|[.\-]){re.escape(tn)}([.\-]|$)", host) and reg != t:
            return t, "embedded"
    return None
