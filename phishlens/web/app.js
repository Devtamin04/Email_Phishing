"use strict";
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const md = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
const state = { model: "kd", ocr: true, quiz: { correct: 0, total: 0, streak: 0, seen: [] } };

const LEVEL_ICON = { good: "✓", warning: "!", serious: "▲", critical: "⛔" };
function sev(strength) {
  if (strength >= 0.6) return ["critical", "⛔", "Rất cao"];
  if (strength >= 0.35) return ["serious", "▲", "Cao"];
  if (strength >= 0.15) return ["warning", "!", "Trung bình"];
  return ["info", "i", "Thấp"];
}
function levelKey(score) {
  return score >= 75 ? "critical" : score >= 50 ? "serious" : score >= 25 ? "warning" : "good";
}
function meter(value, key) {
  return `<div class="meter" style="--c: var(--${key})" role="meter" aria-valuenow="${value}"
    aria-valuemin="0" aria-valuemax="100"><div style="width:${Math.max(value, 1)}%"></div></div>`;
}

// ---------------------------------------------------------------- tabs
function showTab() {
  const t = (location.hash || "#analyze").slice(1);
  document.querySelectorAll(".page").forEach((p) => (p.hidden = p.id !== "tab-" + t));
  document.querySelectorAll(".tab").forEach((a) => a.classList.toggle("active", a.dataset.tab === t));
  if (t === "quiz" && !$("#quiz-card").dataset.loaded) nextQuiz();
  if (t === "robust") loadRobustness();
}
window.addEventListener("hashchange", showTab);

// ---------------------------------------------------------------- api
async function api(url, opts = {}) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error((await r.text()) || r.statusText);
  return r.json();
}
function loading(el, msg) {
  el.innerHTML = `<div class="loading"><div class="spinner"></div>${esc(msg)}</div>`;
}
function analyzingMsg(hasImages = true) {
  return "Đang phân tích…" + (state.ocr && hasImages ? " (đọc chữ trong ảnh có thể mất 10–20 giây)" : "");
}

// ---------------------------------------------------------------- result rendering
function renderResult(r, { compact = false } = {}) {
  const lk = r.level.key;
  const ev = r.evidence;
  const head = `
  <div class="panel verdict">
    <div class="hero">
      <div class="hero-value">${r.score}<small>/100</small></div>
      <div class="badge"><span class="ico ${lk}">${LEVEL_ICON[lk]}</span>${esc(r.level.label)}</div>
    </div>
    <div>
      ${meter(r.score, lk)}
      <p class="summary">${md(r.summary)}</p>
      ${r.attacks.length ? `<div class="chips"><span class="chip-label">Loại tấn công:</span>${r.attacks.map((a) => `<span class="chip attack">${esc(a.label)}</span>`).join("")}</div>` : ""}
      ${r.techniques.length && r.score >= 25 ? `<div class="chips"><span class="chip-label">Kỹ thuật:</span>${r.techniques.map((t) => `<span class="chip">${esc(t)}</span>`).join("")}</div>` : ""}
      ${r.model ? `<div class="model-line" style="margin-top:8px">Mô hình nội dung: ${esc(r.model.model)} · P(lừa đảo) = ${(100 * r.model.prob).toFixed(0)}% · ${r.elapsed_ms} ms</div>` : ""}
    </div>
  </div>`;
  const truth = r.sample && r.sample.truth ? `
  <div class="truth"><b>Đáp án của mẫu:</b> ${r.sample.truth === "phishing" ? "Lừa đảo" : "Email hợp lệ"} — ${esc(r.sample.lesson)}</div>` : "";

  const cats = `
  <div class="panel">
    <h3>Mức rủi ro theo kênh</h3>
    ${r.categories.map((c) => `<div class="cat-row"><span>${esc(c.label)}</span>${meter(c.score, levelKey(c.score))}<span class="v">${c.score}</span></div>`).join("")}
    <h3 style="margin-top:16px">Nên làm gì?</h3>
    <ul class="recs">${r.recommendations.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
  </div>`;

  const evid = `
  <div class="panel">
    <h3>Vì sao? (${ev.length} dấu hiệu)</h3>
    ${ev.length ? "" : `<p class="hint">Không phát hiện dấu hiệu rủi ro.</p>`}
    ${ev.slice(0, compact ? 4 : 50).map((e) => {
      const [k, ic, lbl] = sev(e.strength);
      return `<div class="ev"><span class="ico ${k}" title="Mức ${lbl}">${ic}</span><div>
        <div class="ev-title">${esc(e.title)}</div>
        <div class="ev-meta">Mức ${lbl} · ${esc(e.source)}</div>
        <div class="ev-detail">${esc(e.detail)}</div>
        ${e.tip && !compact ? `<div class="ev-tip"><b>Bài học:</b> ${esc(e.tip)}</div>` : ""}
      </div></div>`;
    }).join("")}
    ${r.good.length ? `<h3 style="margin-top:14px">Dấu hiệu tích cực</h3><ul class="good-list">${r.good.map((g) => `<li>${esc(g.title)}${g.detail ? " — " + esc(g.detail) : ""}</li>`).join("")}</ul>` : ""}
  </div>`;
  if (compact) return head + truth + evid;

  const m = r.email;
  const imgs = m.images.length ? `
    <h3 style="margin-top:16px">Hình ảnh (${m.images.length})</h3>
    <div class="media">${m.images.map((i) => `<figure>${i.thumb ? `<img src="${i.thumb}" alt="${esc(i.name)}">` : ""}
      <figcaption><b>${esc(i.name)}</b>
      ${i.qr.length ? `<br>Mã QR: <code>${esc(i.qr.join(", "))}</code>` : ""}
      ${i.ocr ? `<br>Chữ đọc được (OCR): “${esc(i.ocr.slice(0, 220))}${i.ocr.length > 220 ? "…" : ""}”` : ""}
      </figcaption></figure>`).join("")}</div>` : "";
  const atts = m.attachments.length ? `
    <h3 style="margin-top:16px">Tệp đính kèm (${m.attachments.length})</h3>
    <table><thead><tr><th>Tên tệp</th><th>Loại thực tế</th><th class="num">Kích thước</th><th>Phát hiện</th></tr></thead><tbody>
    ${m.attachments.flatMap((a) => [a, ...(a.inner || []).map((x) => ({ ...x, name: "↳ " + x.name }))]).map((a) => `<tr>
      <td>${esc(a.name)}</td><td>${esc(a.detected)}</td><td class="num">${(a.size / 1024).toFixed(1)} KB</td>
      <td>${(a.findings || []).map(esc).join("<br>") || "—"}</td></tr>`).join("")}
    </tbody></table>` : "";
  const links = m.links.length ? `
    <h3 style="margin-top:16px">Liên kết (${m.links.length})</h3>
    <table><thead><tr><th>Địa chỉ thật</th><th>Chữ hiển thị</th><th>Vị trí</th></tr></thead><tbody>
    ${m.links.map((l) => `<tr><td style="word-break:break-all">${l.suspicious ? "⚠ " : ""}${esc(l.href)}</td><td>${esc(l.text)}</td><td>${esc(l.where)}</td></tr>`).join("")}
    </tbody></table>` : "";
  const mail = `
  <div class="panel">
    <h3>Nội dung email</h3>
    <dl class="mail-head">
      <dt>Người gửi</dt><dd>${esc(m.from_name)} &lt;${esc(m.from_addr)}&gt;</dd>
      ${m.reply_to ? `<dt>Trả lời tới</dt><dd>${esc(m.reply_to)}</dd>` : ""}
      ${m.to ? `<dt>Người nhận</dt><dd>${esc(m.to)}</dd>` : ""}
      <dt>Tiêu đề</dt><dd>${esc(m.subject)}</dd>
    </dl>
    <div class="mail-body">${m.body_html || "<i>(không có nội dung văn bản)</i>"}</div>
    <div class="legend-inline"><span class="l-cue">Cụm từ thao túng tâm lý (di chuột để xem loại)</span><span class="l-url">Liên kết đáng ngờ</span></div>
    ${imgs}${atts}${links}
  </div>`;
  return head + truth + `<div class="grid2">${evid}<div style="display:grid;gap:16px;align-content:start">${cats}</div></div>` + mail;
}

// ---------------------------------------------------------------- analyze tab
async function runAnalysis(promise, hasImages) {
  const el = $("#result");
  loading(el, analyzingMsg(hasImages));
  try {
    el.innerHTML = renderResult(await promise);
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    el.innerHTML = `<div class="empty"><h2>Lỗi</h2><p>${esc(e.message)}</p></div>`;
  }
}
async function loadSamples() {
  const list = await api("/api/samples");
  $("#sample-list").innerHTML = list.map((s) => `
    <button class="sample" data-id="${esc(s.id)}"><div class="t">${esc(s.title)}</div>
    <div class="s">${esc(s.sender)}</div></button>`).join("");
  $("#sample-list").addEventListener("click", (ev) => {
    const b = ev.target.closest(".sample");
    if (!b) return;
    document.querySelectorAll(".sample").forEach((x) => x.classList.toggle("active", x === b));
    runAnalysis(api(`/api/analyze/sample/${b.dataset.id}?model=${state.model}&ocr=${state.ocr}`, { method: "POST" }), true);
  });
}
function uploadEml(file) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("model", state.model);
  fd.append("ocr", state.ocr);
  runAnalysis(api("/api/analyze/eml", { method: "POST", body: fd }), true);
}
function setupInputs() {
  const drop = $("#drop");
  $("#eml-input").addEventListener("change", (e) => e.target.files[0] && uploadEml(e.target.files[0]));
  ["dragover", "dragenter"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, () => drop.classList.remove("over")));
  drop.addEventListener("drop", (e) => { e.preventDefault(); e.dataTransfer.files[0] && uploadEml(e.dataTransfer.files[0]); });
  $("#manual-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    fd.append("model", state.model);
    fd.append("ocr", state.ocr);
    runAnalysis(api("/api/analyze/manual", { method: "POST", body: fd }), true);
  });
  $("#model-select").addEventListener("change", (e) => (state.model = e.target.value));
  $("#ocr-toggle").addEventListener("change", (e) => (state.ocr = e.target.checked));
}

// ---------------------------------------------------------------- quiz
async function nextQuiz() {
  const card = $("#quiz-card");
  card.dataset.loaded = "1";
  $("#quiz-feedback").innerHTML = "";
  card.innerHTML = `<div class="spinner"></div>`;
  const q = await api("/api/quiz/next?exclude=" + state.quiz.seen.join(","));
  state.quiz.current = q.id;
  const m = q.email;
  card.innerHTML = `
    <dl class="mail-head">
      <dt>Người gửi</dt><dd>${esc(m.from_name)} &lt;${esc(m.from_addr)}&gt;</dd>
      ${m.reply_to ? `<dt>Trả lời tới</dt><dd>${esc(m.reply_to)}</dd>` : ""}
      <dt>Tiêu đề</dt><dd>${esc(m.subject)}</dd>
    </dl>
    <div class="mail-body">${m.body_html || "<i>(không có nội dung văn bản)</i>"}</div>
    ${m.links.length ? `<p class="hint" style="margin-top:8px">Liên kết trong thư: ${m.links.map((l) => `<code>${esc(l.text || l.href)}</code>`).join(", ")} <i>(trong thư thật, hãy di chuột để xem địa chỉ thật)</i></p>` : ""}
    ${m.images.length ? `<div class="media">${m.images.map((i) => `<figure>${i.thumb ? `<img src="${i.thumb}" alt="">` : ""}<figcaption>${esc(i.name)}</figcaption></figure>`).join("")}</div>` : ""}
    ${m.attachments.length ? `<p style="margin-top:10px">📎 ${m.attachments.map((a) => esc(a.name)).join(", ")}</p>` : ""}
    <div class="quiz-actions">
      <button class="btn safe" data-a="legit">✓ Email an toàn</button>
      <button class="btn phish" data-a="phishing">⚠ Email lừa đảo</button>
    </div>`;
  card.querySelectorAll("[data-a]").forEach((b) => b.addEventListener("click", () => answerQuiz(b.dataset.a)));
}
async function answerQuiz(answer) {
  $("#quiz-card").querySelectorAll("button").forEach((b) => (b.disabled = true));
  const fb = $("#quiz-feedback");
  loading(fb, "Đang chấm và phân tích…");
  const r = await api("/api/quiz/answer", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: state.quiz.current, answer, model: state.model }),
  });
  const s = state.quiz;
  s.total++; s.seen.push(state.quiz.current);
  if (r.correct) { s.correct++; s.streak++; } else s.streak = 0;
  $("#q-correct").textContent = s.correct;
  $("#q-total").textContent = s.total;
  $("#q-streak").textContent = s.streak;
  const verdict = r.truth === "phishing" ? "Đây là email lừa đảo." : "Đây là email hợp lệ.";
  fb.innerHTML = `<div class="feedback">
    <div class="panel feedback-head"><span class="badge"><span class="ico ${r.correct ? "good" : "critical"}">${r.correct ? "✓" : "✕"}</span>${r.correct ? "Chính xác!" : "Chưa đúng"}</span>
      <span>${verdict}</span><span style="flex:1"></span><button class="btn primary" id="q-next">Câu tiếp theo →</button></div>
    ${r.lesson ? `<div class="truth">${esc(r.lesson)}</div>` : ""}
    ${renderResult(r.analysis, { compact: true })}
  </div>`;
  $("#q-next").addEventListener("click", nextQuiz);
}

// ---------------------------------------------------------------- robustness
let robustLoaded = false;
async function loadRobustness() {
  if (robustLoaded) return;
  const body = $("#robust-body");
  const d = await api("/api/robustness");
  if (!d.available) {
    body.innerHTML = `<p class="hint">Chưa có kết quả. Chạy: <code>.venv/bin/python scripts/robustness_eval.py</code></p>`;
    return;
  }
  robustLoaded = true;
  const dets = d.detectors, trs = d.transforms;
  const colors = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)"];
  const legend = `<div class="chart-legend">${dets.map((x, i) => `<span><i style="background:${colors[i]}"></i>${esc(x.label)}</span>`).join("")}</div>`;
  body.innerHTML = `
    <h3>Tỉ lệ phát hiện email lừa đảo theo kịch bản tấn công</h3>
    <p class="hint">VB = chỉ đọc văn bản thân thư · ĐK = PhishLens đa kênh. ${d.n_phish} email lừa đảo và ${d.n_legit} email hợp lệ cho mỗi kịch bản · ngưỡng: điểm ≥ 50 (hệ thống đa kênh) hoặc P ≥ 0,5 (chỉ văn bản).</p>
    ${legend}
    <div class="chart" id="robust-chart"></div>
    <h3 style="margin-top:20px">Bảng số liệu</h3>
    <table><thead>
      <tr><th></th><th colspan="${dets.length}" class="num grp">Tỉ lệ phát hiện (email lừa đảo) ↑</th><th colspan="${dets.length}" class="num grp">Báo nhầm (email hợp lệ) ↓</th></tr>
      <tr><th>Kịch bản</th>${[...dets, ...dets].map((x) => `<th class="num">${esc(x.short)}</th>`).join("")}</tr></thead>
    <tbody>${trs.map((t) => `<tr><td><b>${esc(t.label)}</b><br><span class="hint">${esc(t.desc)}</span></td>
      ${dets.map((x) => `<td class="num">${(100 * d.tpr[t.key][x.key].rate).toFixed(0)}%</td>`).join("")}
      ${dets.map((x) => `<td class="num">${(100 * d.fpr[t.key][x.key].rate).toFixed(0)}%</td>`).join("")}</tr>`).join("")}</tbody></table>
    ${d.findings && d.findings.length ? `<div class="findings"><b>Nhận xét</b><ul>${d.findings.map((f) => `<li>${esc(f)}</li>`).join("")}</ul></div>` : ""}
    ${d.notes ? `<p class="hint" style="margin-top:12px">${d.notes.map(esc).join(" ")}</p>` : ""}`;
  drawChart($("#robust-chart"), d, colors);
}
function drawChart(el, d, colors) {
  const dets = d.detectors, trs = d.transforms;
  const W = Math.min(el.clientWidth || 900, 980), labelW = 230, padR = 46, barH = 11, gap = 2, groupGap = 18;
  const groupH = dets.length * (barH + gap) - gap;
  const H = 24 + trs.length * (groupH + groupGap);
  const x = (v) => labelW + v * (W - labelW - padR);
  let s = `<svg width="${W}" height="${H}" role="img" aria-label="Tỉ lệ phát hiện theo kịch bản">`;
  [0, 0.25, 0.5, 0.75, 1].forEach((v) => {
    s += `<line class="${v === 0 ? "baseline" : "gridline"}" x1="${x(v)}" x2="${x(v)}" y1="18" y2="${H}"/>`;
    s += `<text x="${x(v)}" y="12" text-anchor="middle">${v * 100}%</text>`;
  });
  trs.forEach((t, gi) => {
    const y0 = 24 + gi * (groupH + groupGap);
    s += `<text class="lbl" x="${labelW - 12}" y="${y0 + groupH / 2 + 4}" text-anchor="end">${esc(t.label)}</text>`;
    dets.forEach((det, di) => {
      const c = d.tpr[t.key][det.key], y = y0 + di * (barH + gap), w = Math.max(x(c.rate) - x(0), 2);
      const tip = `${esc(det.label)}<br>${esc(t.label)}: <b>${(100 * c.rate).toFixed(0)}%</b> (${c.hit}/${c.n})`;
      s += `<path d="M${x(0)},${y} h${w - 4} a4,4 0 0 1 4,4 v${barH - 8} a4,4 0 0 1 -4,4 h${-(w - 4)} z" fill="${colors[di]}" data-tip="${tip.replace(/"/g, "&quot;")}"/>`;
      s += `<rect x="${x(0)}" y="${y - 1}" width="${W - labelW - padR}" height="${barH + 2}" fill="transparent" data-tip="${tip.replace(/"/g, "&quot;")}"/>`;
      s += `<text class="val" x="${x(0) + w + 5}" y="${y + barH - 2}">${(100 * c.rate).toFixed(0)}%</text>`;
    });
  });
  el.innerHTML = s + "</svg>";
  const tt = $("#tooltip");
  el.addEventListener("mousemove", (e) => {
    const t = e.target.closest("[data-tip]");
    if (!t) { tt.hidden = true; return; }
    tt.innerHTML = t.dataset.tip; tt.hidden = false;
    tt.style.left = e.clientX + 14 + "px"; tt.style.top = e.clientY + 14 + "px";
  });
  el.addEventListener("mouseleave", () => (tt.hidden = true));
}

// ---------------------------------------------------------------- init
(async function init() {
  setupInputs();
  const st = await api("/api/status");
  const sel = $("#model-select");
  const names = { kd: "KD-BiLSTM (bài báo)", linear: "TF-IDF + LR" };
  sel.innerHTML = Object.keys(st.models).map((k) => `<option value="${k}">${names[k] || k}</option>`).join("")
    || `<option value="">(chưa có mô hình)</option>`;
  state.model = Object.keys(st.models)[0] || "";
  $("#org-name").textContent = "Trợ lý nhận diện email lừa đảo · " + st.org;
  await loadSamples();
  showTab();
  const sid = new URLSearchParams(location.search).get("sample");  // ?sample=s04_qr_m365
  if (sid) document.querySelector(`.sample[data-id="${CSS.escape(sid)}"]`)?.click();
})();
