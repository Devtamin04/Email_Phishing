"""PhishLens Edu web app (local only).

    .venv/bin/python -m uvicorn phishlens.app:app --host 127.0.0.1 --port 8000
"""
import html
import json
import os
import random

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .content import KDTextModel, LinearTextModel
from .engine import analyze
from .media import thumbnail
from .parser import EmailDoc, extract_urls, from_manual, parse_eml
from .synth import LEGIT, PHISH, _fill, llm_rewrite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "samples")
MODELS_DIR = os.path.join(ROOT, "models")
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

app = FastAPI(title="PhishLens Edu")
MODELS = {}


def _load_models():
    kd = os.path.join(MODELS_DIR, "kd_bilstm")
    if os.path.exists(os.path.join(kd, "student.pt")):
        MODELS["kd"] = KDTextModel(kd)
    lin = os.path.join(MODELS_DIR, "linear.joblib")
    if os.path.exists(lin):
        MODELS["linear"] = LinearTextModel.load(lin)


def _model(key):
    if key in MODELS:
        return MODELS[key]
    return MODELS.get("kd") or MODELS.get("linear")


def _index():
    p = os.path.join(SAMPLES, "index.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


# ---------------------------------------------------------------------------------------
# Quiz pool: demo mailbox + synthetic emails (incl. LLM-style rewrites)
# ---------------------------------------------------------------------------------------
PHISH_SENDERS = [("Phòng Đào tạo", "phongdaotao.dhdemo@gmail.com", ""),
                 ("Phòng CNTT", "it-helpdesk@dhdemo-edu.com", "spf=fail; dmarc=fail"),
                 ("Ban Giám hiệu", "bgh.dhdemo@outlook.com", ""),
                 ("Thông báo sinh viên", "thongbao@portal-sinhvien.click", "spf=none; dmarc=none")]
LEGIT_SENDERS = [("Phòng Đào tạo", "daotao@dhdemo.edu.vn"), ("Văn phòng Khoa CNTT", "vpkcntt@dhdemo.edu.vn"),
                 ("Thư viện", "thuvien@dhdemo.edu.vn"), ("ThS. Lê Thị Hoa", "hoalt@dhdemo.edu.vn")]
QUIZ = {}


def _build_quiz(n=30, seed=11):
    rng = random.Random(seed)
    for s in _index():
        QUIZ[s["id"]] = {"kind": "sample", **s}
    for i in range(n):
        phish = rng.random() < 0.55
        if phish:
            atype, tpl = rng.choice(PHISH)
            text, rewritten = _fill(tpl, rng), rng.random() < 0.6
            subject = text.split(".")[0][:70]
            if rewritten:
                text, _ = llm_rewrite(text, rng)
            name, addr, auth = rng.choice(PHISH_SENDERS)
            lesson = ("Email lừa đảo (sinh tự động" + (", đã được viết lại kiểu LLM" if rewritten
                                                       else "") + "). Xem các dấu hiệu bên dưới.")
        else:
            text = _fill(rng.choice(LEGIT), rng)
            (name, addr), auth = rng.choice(LEGIT_SENDERS), "spf=pass; dkim=pass; dmarc=pass"
            atype, lesson = "legit", "Email hợp lệ của trường (sinh tự động)."
            subject = text.split(".")[0][:70]
        doc = EmailDoc(subject=subject, from_name=name, from_addr=addr,
                       auth_results=auth, text=text)
        doc.links = extract_urls(text, "body")
        QUIZ[f"q{i:02d}"] = {"kind": "synthetic", "id": f"q{i:02d}", "doc": doc,
                             "truth": "phishing" if phish else "legit", "attack": atype,
                             "lesson": lesson}


def _quiz_doc(item):
    if item["kind"] == "sample":
        return parse_eml(open(os.path.join(SAMPLES, item["id"] + ".eml"), "rb").read())
    return item["doc"]


@app.on_event("startup")
def _startup():
    _load_models()
    _build_quiz()


# ---------------------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------------------
@app.get("/api/status")
def status():
    return {"models": {k: m.name for k, m in MODELS.items()}, "ocr": config.OCR_ENABLED,
            "org": config.ORG_NAME, "org_domains": config.ORG_DOMAINS}


@app.get("/api/samples")
def samples():
    return [{k: s[k] for k in ("id", "title", "subject", "sender")} for s in _index()]


@app.get("/api/samples/{sid}/eml")
def sample_eml(sid: str):
    p = os.path.join(SAMPLES, os.path.basename(sid) + ".eml")
    if not os.path.exists(p):
        raise HTTPException(404)
    return FileResponse(p, media_type="message/rfc822", filename=os.path.basename(p))


@app.post("/api/analyze/sample/{sid}")
def analyze_sample(sid: str, model: str = "kd", ocr: bool = True):
    p = os.path.join(SAMPLES, os.path.basename(sid) + ".eml")
    if not os.path.exists(p):
        raise HTTPException(404)
    r = analyze(parse_eml(open(p, "rb").read()), _model(model), ocr)
    meta = next((s for s in _index() if s["id"] == sid), {})
    r["sample"] = {k: meta.get(k) for k in ("truth", "attack", "lesson", "title")}
    return r


@app.post("/api/analyze/eml")
async def analyze_eml(file: UploadFile = File(...), model: str = Form("kd"), ocr: bool = Form(True)):
    raw = await file.read()
    if len(raw) > 25_000_000:
        raise HTTPException(413, "Tệp quá lớn (tối đa 25MB)")
    return analyze(parse_eml(raw), _model(model), ocr)


@app.post("/api/analyze/manual")
async def analyze_manual(subject: str = Form(""), sender: str = Form(""), body: str = Form(""),
                         model: str = Form("kd"), ocr: bool = Form(True),
                         files: list[UploadFile] = File(default=[])):
    fs = [(f.filename, f.content_type or "", await f.read()) for f in files if f.filename]
    return analyze(from_manual(subject, sender, body, fs), _model(model), ocr)


@app.get("/api/quiz/next")
def quiz_next(exclude: str = ""):
    seen = set(exclude.split(",")) if exclude else set()
    pool = [k for k in QUIZ if k not in seen] or list(QUIZ)
    qid = random.choice(pool)
    doc = _quiz_doc(QUIZ[qid])
    return {"id": qid, "total": len(QUIZ), "email": {
        "subject": doc.subject, "from_name": doc.from_name, "from_addr": doc.from_addr,
        "reply_to": doc.reply_to,
        "body_html": html.escape(doc.text or "").replace("\n", "<br>"),
        "links": [{"href": l.href, "text": l.text} for l in doc.links],
        "images": [{"name": i.filename, "thumb": thumbnail(i.data)} for i in doc.images],
        "attachments": [{"name": a.filename, "size": len(a.data)} for a in doc.attachments]}}


class Answer(BaseModel):
    id: str
    answer: str
    model: str = "kd"


@app.post("/api/quiz/answer")
def quiz_answer(a: Answer):
    item = QUIZ.get(a.id)
    if not item:
        raise HTTPException(404)
    r = analyze(_quiz_doc(item), _model(a.model), True)
    return {"correct": a.answer == item["truth"], "truth": item["truth"],
            "lesson": item.get("lesson", ""), "analysis": r}


@app.get("/api/robustness")
def robustness():
    p = os.path.join(ROOT, "results", "robustness.json")
    if not os.path.exists(p):
        return JSONResponse({"available": False})
    return {"available": True, **json.load(open(p, encoding="utf-8"))}


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
