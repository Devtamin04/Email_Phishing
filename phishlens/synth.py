"""Synthetic Vietnamese school-email corpus + "LLM-style" rewrites (paraphrase / masking /
personalization, as in Sec. 3.2 of the paper).

Templates are split by id: every 3rd template is *held out* from training and only used to
evaluate robustness, so the detectors are tested on phrasings they have never seen.
"""
import random
import re

import pandas as pd

PHISH = [  # (attack type, template)
    ("credential", "Kính gửi sinh viên, hệ thống email sinh viên đang được nâng cấp. Tài khoản của "
     "bạn sẽ bị khóa trong vòng {n} giờ nếu không xác minh. Vui lòng nhấn vào đường link sau để "
     "xác minh tài khoản ngay: {url}"),
    ("credential", "Thông báo từ Phòng CNTT: mật khẩu tài khoản {svc} của bạn sẽ hết hạn hôm nay. "
     "Đăng nhập tại {url} để giữ nguyên mật khẩu hiện tại, nếu không bạn sẽ mất quyền truy cập."),
    ("credential", "Cổng thông tin đào tạo ghi nhận đăng nhập bất thường từ {country}. Để bảo vệ "
     "tài khoản, bạn cần xác thực lại thông tin trước {hour} hôm nay tại {url}."),
    ("credential", "Bạn có 1 tài liệu được chia sẻ qua {svc}: \"{doc}\". Đăng nhập bằng tài khoản "
     "email trường để xem tài liệu: {url}"),
    ("scam", "Chúc mừng {name}! Bạn đã được chọn nhận học bổng {sch} trị giá {amt} đồng. Vui lòng "
     "cập nhật số tài khoản ngân hàng và số CCCD tại {url} trước {day} để nhận học bổng."),
    ("scam", "Chương trình tri ân sinh viên: tặng {amt} đồng cho 100 sinh viên đăng ký đầu tiên. "
     "Đăng ký nhanh tại {url}, số lượng có hạn!"),
    ("scam", "Tuyển cộng tác viên online làm tại nhà, thu nhập {amt} đồng/ngày. Chỉ cần đóng phí "
     "giữ chỗ 200.000 đồng qua số tài khoản {acct} là được nhận việc ngay."),
    ("payment", "Phòng Kế hoạch - Tài chính thông báo: sinh viên chưa hoàn thành học phí sẽ bị cấm "
     "thi. Vui lòng chuyển khoản {amt} đồng vào số tài khoản {acct} trước {day} và gửi lại biên lai."),
    ("payment", "Em {name} ơi, thầy đang họp không nghe máy được. Em mua giúp thầy {k} thẻ cào "
     "Viettel mệnh giá 500.000 rồi gửi mã thẻ qua email này nhé, chiều thầy gửi lại tiền. Việc này "
     "em giữ kín giúp thầy."),
    ("payment", "Kính gửi anh/chị, Ban Giám hiệu yêu cầu chuyển gấp khoản tạm ứng {amt} đồng cho "
     "đối tác theo số tài khoản mới {acct}. Vui lòng xử lý ngay và không trao đổi qua điện thoại vì "
     "tôi đang đi công tác."),
    ("malware", "Danh sách sinh viên bị cảnh cáo học vụ học kỳ này được đính kèm. Vui lòng mở tệp "
     "và bật Enable Content để xem đầy đủ nội dung."),
    ("malware", "Hóa đơn điện tử tháng {mon} của bạn đã được phát hành. Tải hóa đơn tại {url} và "
     "giải nén bằng mật khẩu {k}{k}{k}{k}."),
    ("quishing", "Hệ thống xác thực hai lớp Microsoft 365 của trường được cập nhật. Vui lòng quét "
     "mã QR trong thư bằng điện thoại để kích hoạt lại trước {hour} hôm nay, quá hạn tài khoản sẽ "
     "bị tạm khóa."),
    ("credential", "Thư viện thông báo bạn đang có {k} cuốn sách quá hạn và bị tính phí phạt. Đăng "
     "nhập tài khoản thư viện tại {url} để gia hạn và tránh bị khóa thẻ."),
    ("scam", "Bạn là sinh viên may mắn trúng thưởng laptop trong chương trình khảo sát của trường. "
     "Nhận quà tại {url} và thanh toán phí vận chuyển {amt} đồng."),
]
LEGIT = [
    "Thân gửi các bạn sinh viên lớp {cls}, lịch thi cuối kỳ môn {course} đã được cập nhật trên cổng "
    "đào tạo của trường. Các bạn kiểm tra phòng thi và mang theo thẻ sinh viên. Trân trọng, {sender}",
    "Chào {name}, cô đã nhận bài tập lớn môn {course} của nhóm em. Nhóm chú ý bổ sung phần tài liệu "
    "tham khảo trước buổi bảo vệ ngày {day}. Thân mến, {sender}",
    "Câu lạc bộ {club} trân trọng mời các bạn tham gia workshop \"{topic}\" vào {day} lúc {hour} "
    "tại hội trường {room}. Thông tin chi tiết có trên trang sự kiện của trường.",
    "Thư viện thông báo: thư viện mở cửa đến 21h trong tuần ôn thi. Sinh viên vui lòng trả sách "
    "đúng hạn để các bạn khác có thể mượn.",
    "Phòng Công tác sinh viên thông báo danh sách sinh viên nhận học bổng khuyến khích học tập đã "
    "được công bố trên website của trường. Học bổng được chuyển vào tài khoản đã đăng ký với nhà "
    "trường, sinh viên không cần thực hiện thêm thao tác nào.",
    "Kính gửi quý thầy cô, cuộc họp khoa {dept} sẽ diễn ra vào {day} lúc {hour} tại phòng {room}. "
    "Nội dung: rà soát đề cương môn học năm học mới. Trân trọng.",
    "Chào các bạn, nhắc nhở hạn nộp báo cáo thực tập là {day}. Báo cáo nộp qua hệ thống LMS của "
    "trường, định dạng PDF. Mọi thắc mắc liên hệ văn phòng khoa.",
    "Phòng CNTT thông báo hệ thống email sẽ bảo trì từ 22h đến 23h ngày {day}, có thể gián đoạn gửi "
    "nhận thư. Nhà trường không bao giờ yêu cầu bạn cung cấp mật khẩu qua email.",
    "Chào {name}, bảng điểm giữa kỳ môn {course} đã có trên LMS. Em xem và phản hồi nếu có sai sót "
    "trước {day} nhé.",
    "Đoàn trường thông báo kế hoạch tình nguyện Mùa hè xanh. Sinh viên quan tâm đăng ký với bí thư "
    "chi đoàn lớp trước {day}.",
    "Nhắc nhở: hạn đóng học phí học kỳ này là {day}. Sinh viên đóng qua ứng dụng ngân hàng theo "
    "hướng dẫn trên cổng thông tin chính thức, không chuyển khoản cho cá nhân.",
    "Chào {name}, nhóm mình họp online lúc {hour} {day} để chia việc cho đồ án môn {course}. Link "
    "phòng họp mình gửi trong nhóm chat lớp nhé.",
    "Ký túc xá thông báo lịch cắt điện để bảo trì vào sáng {day}. Sinh viên chủ động sạc thiết bị "
    "và bảo quản đồ dùng cá nhân.",
    "Trung tâm Hỗ trợ việc làm giới thiệu ngày hội việc làm vào {day} với hơn 50 doanh nghiệp. "
    "Sinh viên mang theo CV bản in để phỏng vấn trực tiếp.",
    "Chào {name}, cảm ơn em đã tham gia khảo sát chất lượng môn học. Kết quả khảo sát giúp khoa cải "
    "thiện chương trình đào tạo.",
    # "hard" legitimate emails: official links, attachments, QR, deadlines, account wording
    "Thân gửi các bạn, Phòng Đào tạo gửi kế hoạch đăng ký học phần học kỳ 2 trong tệp đính kèm. Các "
    "bạn đăng ký trên cổng đào tạo https://dhdemo.edu.vn/dang-ky-hoc-phan trước {day}. Trân trọng.",
    "Chào {name}, slide bài giảng tuần này môn {course} cô đã đưa lên LMS tại "
    "https://lms.dhdemo.edu.vn. Em xem trước khi lên lớp nhé.",
    "Hạn chót nộp hồ sơ xét học bổng khuyến khích học tập là {day}. Sinh viên xem điều kiện và mẫu "
    "đơn tại https://dhdemo.edu.vn/hoc-bong, nộp bản giấy tại văn phòng khoa.",
    "Phòng CNTT hướng dẫn bật xác thực hai lớp cho email sinh viên. Bạn tự gõ địa chỉ trang chính "
    "thức của trường và làm theo hướng dẫn trong tệp đính kèm; nhà trường không gửi link đăng nhập "
    "qua email.",
    "Câu lạc bộ {club} gửi poster sự kiện trong tệp đính kèm. Các bạn quét mã QR trên poster để xem "
    "chi tiết trên trang sự kiện https://dhdemo.edu.vn/su-kien của trường.",
    "Chào {name}, em vui lòng xác nhận tham dự lễ tốt nghiệp bằng cách trả lời email này trước "
    "{day}. Văn phòng khoa {dept}.",
]

PHISH_URLS = ["http://dhdemo-edu.com/xac-thuc", "http://dhdemo.edu.vn.account-verify.top/login",
              "https://bit.ly/hb-dhdemo", "http://portal-sinhvien.click/dang-nhap",
              "http://103.45.12.8/m365/login", "https://dhdemo.edu.vn-secure.live/auth",
              "http://micros0ft-365.xyz/verify", "https://forms-dhdemo.icu/hoc-bong"]
FILL = dict(
    svc=["Microsoft 365", "Outlook", "Google Drive", "LMS", "OneDrive"],
    country=["Nga", "Brazil", "Nigeria", "Trung Quốc"],
    doc=["Danh sách học bổng HK1.xlsx", "Kế hoạch thi.pdf", "Điểm rèn luyện.docx"],
    name=["Minh Anh", "Quốc Bảo", "Thu Hà", "Gia Huy", "Ngọc Trâm", "Đức Long", "Khánh Linh"],
    sender=["ThS. Lê Thị Hoa", "Văn phòng Khoa CNTT", "Phòng Đào tạo", "TS. Phạm Minh Tuấn",
            "Ban chủ nhiệm CLB"],
    sch=["Khuyến khích học tập", "Vượt khó", "Doanh nghiệp tài trợ", "Tài năng trẻ"],
    day=["thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "ngày 15/10", "ngày 20/11"],
    hour=["8h00", "9h30", "14h00", "17h00"],
    cls=["CNTT01", "KT02", "QTKD03", "NNA04"],
    course=["Cấu trúc dữ liệu", "Kinh tế vi mô", "Mạng máy tính", "Tiếng Anh 2", "Học máy"],
    club=["Tin học", "Tiếng Anh", "Khởi nghiệp", "Bóng rổ"],
    topic=["Viết CV ấn tượng", "Nhập môn AI", "An toàn thông tin cho sinh viên"],
    room=["A1", "B2.03", "C1.01"], dept=["CNTT", "Kinh tế", "Ngoại ngữ"],
    acct=["0123456789 - Vietcombank - NGUYEN VAN A", "1903 4567 8910 - Techcombank - TRAN THI B"],
    mon=["9", "10", "11"],
)


def _fill(tpl, rng):
    vals = {k: rng.choice(v) for k, v in FILL.items()}
    vals.update(url=rng.choice(PHISH_URLS), n=rng.choice([12, 24, 48]), k=rng.randint(2, 5),
                amt=f"{rng.choice([2, 3, 5, 10, 15])}.000.000")
    return tpl.format(**vals)


# ---------------------------------------------------------------------------------------
# "LLM-style" rewrites in Vietnamese (rule-based stand-in; plug a real LLM for research)
# ---------------------------------------------------------------------------------------
_PARA = {
    "nhấn vào": ["bấm vào", "truy cập", "mở"], "xác minh": ["xác nhận", "kiểm tra lại"],
    "vui lòng": ["bạn vui lòng", "mong bạn", "phiền bạn"], "ngay": ["sớm", "kịp thời"],
    "đường link": ["liên kết", "cổng"], "bị khóa": ["tạm ngưng", "bị gián đoạn"],
    "hết hạn": ["hết hiệu lực", "không còn hiệu lực"], "đăng nhập": ["truy cập", "đăng nhập lại"],
    "chuyển khoản": ["chuyển tiền", "thanh toán"], "thông báo": ["xin thông tin", "cập nhật"],
}
_MASK = [(r"\bkhẩn( cấp)?\b", "cần lưu ý"), (r"!+", "."), (r"\bgấp\b", "sớm"),
         (r"\bngay\b", "khi thuận tiện"), (r"bị khóa", "cần được rà soát"),
         (r"cấm thi", "chưa đủ điều kiện dự thi"), (r"Kính gửi sinh viên,?", "Chào bạn,"),
         (r"nếu không[^.]*\.", "."), (r"quá hạn[^.,]*", "")]
_OPEN = ["Hy vọng bạn có một tuần học tập hiệu quả.", "Cảm ơn bạn đã luôn đồng hành cùng nhà trường.",
         "Chúc bạn một ngày tốt lành."]


def paraphrase(t, rng):
    for k, alts in _PARA.items():
        t = re.sub(rf"\b{k}\b", lambda m: rng.choice(alts), t, flags=re.I)
    return t


def masking(t, rng):
    for p, r in _MASK:
        t = re.sub(p, r, t, flags=re.I)
    return re.sub(r"\s+\.", ".", t)


def personalization(t, rng):
    name, sender = rng.choice(FILL["name"]), rng.choice(FILL["sender"])
    cls = rng.choice(FILL["cls"])
    return (f"Chào {name}, mình là {sender}. Như đã trao đổi trong buổi sinh hoạt lớp {cls}, "
            f"mình gửi bạn thông tin sau. {t} {rng.choice(_OPEN)} Thân mến, {sender}")


REWRITES = {"paraphrase": paraphrase, "masking": masking, "personalization": personalization}


def llm_rewrite(t, rng, chain=None):
    chain = chain or rng.sample(list(REWRITES), rng.randint(1, 3))
    for c in chain:
        t = REWRITES[c](t, rng)
    return t, "+".join(chain)


def is_heldout(idx):
    return idx % 3 == 2


def make_vi_corpus(n_per_template=40, seed=7, split="train"):
    """split: 'train' (non-held-out templates), 'heldout', or 'all'."""
    rng = random.Random(seed)
    keep = (lambda i: not is_heldout(i)) if split == "train" else \
        (is_heldout if split == "heldout" else (lambda i: True))
    rows = []
    for i, (atype, tpl) in enumerate(PHISH):
        if not keep(i):
            continue
        for _ in range(n_per_template):
            t = _fill(tpl, rng)
            rows.append((t, 1, "orig", atype, i, ""))
            g, chain = llm_rewrite(t, rng)
            rows.append((g, 1, "gen", atype, i, chain))
    for i, tpl in enumerate(LEGIT):
        if not keep(i):
            continue
        for _ in range(2 * n_per_template):
            t = _fill(tpl, rng)
            gen = rng.random() < 0.5
            if gen:  # benign emails get the polite/personal style too, so style alone is no cue
                t = personalization(t, rng) if rng.random() < 0.5 else paraphrase(t, rng)
            rows.append((t, 0, "gen" if gen else "orig", "legit", i, ""))
    df = pd.DataFrame(rows, columns=["text", "label", "source", "attack", "template", "rewrite"])
    return df.drop_duplicates("text").sample(frac=1, random_state=seed).reset_index(drop=True)
