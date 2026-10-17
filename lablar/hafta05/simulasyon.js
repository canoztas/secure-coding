// Hafta 5 parola kırma simülatörü: lab.py çalışırken http://127.0.0.1:8086/simulasyon

/* ---------- Ortak yardımcılar ---------- */
const $ = (id) => document.getElementById(id);
const nf1 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 1 });
const nf0 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
const SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹";
const sup = (n) => String(n).split("").map((c) => SUP[+c] ?? c).join("");
function fmtN(n) {
  if (!isFinite(n)) return "∞";
  if (n < 1e6) return nf0.format(Math.round(n));
  const e = Math.floor(Math.log10(n)), m = n / 10 ** e;
  return `${nf1.format(m)} × 10${sup(e)}`;
}
const YIL = 31557600, EVREN = 13.8e9 * YIL;
function fmtSure(s) {
  if (!isFinite(s)) return "∞";
  if (s < 1e-3) return "anında";
  if (s < 1) return `${nf0.format(s * 1000)} ms`;
  if (s < 60) return `${nf1.format(s)} sn`;
  if (s < 3600) return `${nf1.format(s / 60)} dk`;
  if (s < 86400) return `${nf1.format(s / 3600)} saat`;
  if (s < YIL) return `${nf1.format(s / 86400)} gün`;
  const y = s / YIL;
  if (y < 1e3) return `${nf1.format(y)} yıl`;
  if (y < 1e6) return `${nf1.format(y / 1e3)} bin yıl`;
  if (y < 1e9) return `${nf1.format(y / 1e6)} milyon yıl`;
  if (s < EVREN) return `${nf1.format(y / 1e9)} milyar yıl`;
  return `evrenin yaşının ${fmtN(s / EVREN)} katı`;
}
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const hexOf = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
async function digest(alg, text) { return hexOf(await crypto.subtle.digest(alg, new TextEncoder().encode(text))); }
async function pbkdf2(text, saltBytes, iterations = 600000) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(text), "PBKDF2", false, ["deriveBits"]);
  return hexOf(await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: saltBytes, iterations }, key, 256));
}
const randBytes = (n) => crypto.getRandomValues(new Uint8Array(n));
const randToken = () => [...randBytes(9)].map((b) => "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!#-"[b % 59]).join("");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const RATES = [
  { id: "md5", label: "MD5 · 1 × RTX 5090", rate: 219.5e9 },
  { id: "sha", label: "SHA-256 · 1 × RTX 5090", rate: 27.6816e9 },
  { id: "bcrypt", label: "bcrypt cost 10 · 16 × RTX 5090", rate: 138675 },
  { id: "online", label: "Online · 10 deneme/sn", rate: 10 },
];

/* ---------- Sentetik veri (lablar/hafta05/veri.py) ---------- */
const COMMON = {
  "123456": 23174, "123456789": 7671, "qwerty": 3810, "password": 3645, "1111111": 3120, "12345678": 2938, "abc123": 2877,
  "parola": 1904, "sifre": 1655, "000000": 1590, "sifre123": 1377, "galatasaray": 1215, "fenerbahce": 1188, "asdasd": 1133,
  "besiktas": 1022, "trabzonspor": 811, "istanbul34": 767, "ankara06": 702, "galatasaray1905": 655, "fenerbahce1907": 640,
  "iloveyou": 612, "admin": 590, "letmein": 433, "welcome1": 401, "parola1!": 388, "qwerty123!": 356, "sonbahar2026!": 214,
  "ekim2026!": 187, "yaz2026!": 166, "kahve2019!": 92,
};
const COMMON_RANK = Object.keys(COMMON).sort((a, b) => COMMON[b] - COMMON[a]);
const WORDS = ["123456", "password", "qwerty", "parola", "sifre", "admin", "letmein", "iloveyou", "galatasaray", "fenerbahce", "besiktas",
  "trabzonspor", "istanbul", "ankara", "izmir", "sonbahar", "ilkbahar", "kis", "yaz", "ekim", "kasim", "kahve", "cay", "simit", "deniz",
  "gunes", "ayse", "mehmet", "fatma", "ahmet", "zeynep", "ali", "elif", "can", "kedi", "kopek", "aslan", "kartal", "karadeniz", "anadolu",
  "turkiye", "bilgisayar", "yazilim", "okul", "universite", "ogrenci", "merhaba", "sevgi", "ask", "hayat", "dunya", "mavi", "kirmizi",
  "yesil", "siyah", "beyaz", "futbol", "basket", "muzik", "oyun"];
const YEARS = ["2024", "2025", "2026"];
function* mutate(w) { yield w; yield w[0].toUpperCase() + w.slice(1); for (const y of YEARS) { yield w + y; yield w[0].toUpperCase() + w.slice(1) + y + "!"; } }
const CANDIDATES = [...new Set(WORDS.flatMap((w) => [...mutate(w)]))];

/* ---------- Sekmeler ---------- */
const tabs = [...document.querySelectorAll('[role="tab"]')];
function showTab(id, focus) {
  tabs.forEach((t) => {
    const on = t.getAttribute("aria-controls") === id;
    t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1;
    $(t.getAttribute("aria-controls")).hidden = !on;
    if (on && focus) t.focus();
  });
  try { localStorage.setItem("pks-tab", id); } catch (e) {}
  if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
}
tabs.forEach((t, i) => {
  t.addEventListener("click", () => showTab(t.getAttribute("aria-controls")));
  t.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const n = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    showTab(n.getAttribute("aria-controls"), true);
  });
});
{
  let start = location.hash.slice(1);
  if (!$(start) || $(start).getAttribute("role") !== "tabpanel") { try { start = localStorage.getItem("pks-tab") || "hash"; } catch (e) { start = "hash"; } }
  if ($(start)) showTab(start);
}

/* ---------- 1 · Hash ---------- */
const twinSalts = [randBytes(16), randBytes(16)];
let hashSeq = 0;
function prefixHtml(hex, n = 5) { return `<b>${hex.slice(0, n).toUpperCase()}</b>${hex.slice(n).toUpperCase()}`; }
async function updateHash() {
  const pw = $("hash-in").value, seq = ++hashSeq;
  const md5 = md5Hex(pw);
  $("h-md5").textContent = md5 ?? "(55 bayttan uzun: bu demo kısa parolalar içindir)";
  $("h-sha1").innerHTML = prefixHtml(await digest("SHA-1", pw));
  const sha = await digest("SHA-256", pw);
  $("h-sha256").textContent = sha;
  await sleep(150);
  if (seq !== hashSeq) return;
  const salt = twinSalts[0], t0 = performance.now();
  const pb = await pbkdf2(pw, salt);
  if (seq !== hashSeq) return;
  const ms = performance.now() - t0;
  window.PBKDF2_MS = ms;
  $("h-pbkdf2").innerHTML = `salt ${hexOf(salt).slice(0, 16)}… → ${pb}`;
  $("h-pbkdf2-ms").textContent = `Bu tarayıcıda tek hash ${nf0.format(ms)} ms sürdü: saniyede yaklaşık ${nf1.format(1000 / ms)} deneme.`;
  renderTwins(pw, sha);
}
async function renderTwins(pw, sha) {
  const rows = [];
  for (const [i, user] of ["alice", "bob"].entries()) rows.push({ user, salt: twinSalts[i], pb: await pbkdf2(pw, twinSalts[i]) });
  $("twin-body").innerHTML = rows.map((r) => `<tr><td class="mono">${r.user}</td><td class="mono">${esc(pw)}</td>
    <td class="hash same">${sha.slice(0, 24)}…</td><td class="hash">${hexOf(r.salt).slice(0, 12)}…</td><td class="hash">${r.pb.slice(0, 24)}…</td></tr>`).join("");
}
$("hash-in").addEventListener("input", updateHash);
document.querySelectorAll("[data-hash-preset]").forEach((b) => b.addEventListener("click", () => { $("hash-in").value = b.dataset.hashPreset; updateHash(); }));
$("twin-salt").addEventListener("click", () => { twinSalts[0] = randBytes(16); twinSalts[1] = randBytes(16); updateHash(); });
updateHash();

/* ---------- 2 · Süre ---------- */
const TR = "çğıöşüÇĞİÖŞÜ";
function pools(pw) {
  const p = { lower: /[a-z]/.test(pw), upper: /[A-Z]/.test(pw), digit: /[0-9]/.test(pw), sym: /[^A-Za-z0-9çğıöşüÇĞİÖŞÜ]/.test(pw), tr: new RegExp(`[${TR}]`).test(pw) };
  const size = (p.lower ? 26 : 0) + (p.upper ? 26 : 0) + (p.digit ? 10 : 0) + (p.sym ? 33 : 0) + (p.tr ? 12 : 0);
  const names = [p.lower && "küçük harf", p.upper && "büyük harf", p.digit && "rakam", p.sym && "sembol", p.tr && "Türkçe harf"].filter(Boolean);
  return { size, names };
}
function classSize(ch) {
  if (/[a-z]/.test(ch)) return 26; if (/[A-Z]/.test(ch)) return 26; if (/[0-9]/.test(ch)) return 10;
  if (TR.includes(ch)) return 12; return 33;
}
function models(pw) {
  const len = [...pw].length, out = [];
  const pool = pools(pw);
  const brute = Math.pow(pool.size, len);
  out.push({ id: "brute", name: "Kör brute force", n: brute, why: `${len} karakter, ${pool.size} sembollük küme (${pool.names.join(", ") || "—"}): ${pool.size}${sup(len)}` });
  const low = pw.toLowerCase();
  const rank = COMMON_RANK.indexOf(low);
  if (rank >= 0) out.push({ id: "common", name: "Yaygın parola listesi", n: rank + 1, why: `Sızıntılarda en sık görülenler listesinde ${rank + 1}. sırada` });
  const ci = CANDIDATES.indexOf(pw);
  if (ci >= 0) out.push({ id: "lab", name: "Lab sözlüğü + kurallar", n: ci + 1, why: `60 kelime × kurallar = ${CANDIDATES.length} aday; ${ci + 1}. aday` });
  const m = pw.match(/^([A-Za-zçğıöşüÇĞİÖŞÜ]{3,15})(\d{0,4})([!.?*]?)$/);
  if (m && (m[2] || m[3] || /^[A-ZÇĞİÖŞÜ]/.test(pw))) out.push({ id: "dict", name: "Sözlük kelimesi + yıl + sembol", n: 100000 * 80 * 4 * 5, why: "100 bin kelime × 80 yıl × 4 yazım × 5 sembol" });
  else if (m && !m[2] && !m[3]) out.push({ id: "dict", name: "Sözlük kelimesi", n: 100000 * 4, why: "100 bin kelime × 4 yazım (küçük, Büyük, BÜYÜK, ters)" });
  const words = pw.split(/[\s\-_.]+/).filter(Boolean);
  if (words.length >= 3 && words.every((w) => /^[a-zçğıöşü]+$/i.test(w))) out.push({ id: "phrase", name: `${words.length} kelimelik cümle`, n: Math.pow(7776, words.length), why: `7.776 kelimelik zar listesi (EFF): 7776${sup(words.length)}` });
  else if (/^[A-ZÇĞİÖŞÜ]?[a-zçğıöşü]+[0-9]*[^A-Za-z0-9çğıöşüÇĞİÖŞÜ]?$/.test(pw)) {
    const mask = [...pw].reduce((a, ch) => a * classSize(ch), 1);
    if (mask < brute) out.push({ id: "mask", name: "Şablon (mask)", n: mask, why: "Politika şablonu (Büyük harf + küçükler + rakam + sembol): " + [...pw].map((ch) => /[a-z]/.test(ch) ? "?l" : /[A-Z]/.test(ch) ? "?u" : /[0-9]/.test(ch) ? "?d" : "?s").join("") });
  }
  return out;
}
const SURE_PRESETS = ["123456", "Sonbahar2026!", "Kahve2024!", "galatasaray1905", "Ahmetk12", "x7#Qp9!zR2", "kirmizi bisiklet sabah cayi", "Mavi.Kedi.Sabah.42"];
$("sure-presets").innerHTML = SURE_PRESETS.map((p) => `<button class="chip" data-sure="${esc(p)}">${esc(p)}</button>`).join("");
document.querySelectorAll("[data-sure]").forEach((b) => b.addEventListener("click", () => { $("sure-in").value = b.dataset.sure; updateSure(); }));
const LOG_MIN = -3, LOG_MAX = 18;
// CSP satır içi style özniteliğine izin vermez; konumlar CSSOM ile verilir.
function place(root) {
  root.querySelectorAll("[data-w]").forEach((e) => (e.style.width = `calc(${e.dataset.w}% - 6px)`));
  root.querySelectorAll("[data-l]").forEach((e) => (e.style.left = `${e.dataset.l}%`));
}
const pos = (s) => Math.max(0, Math.min(1, (Math.log10(Math.max(s, 1e-3)) - LOG_MIN) / (LOG_MAX - LOG_MIN))) * 100;
$("sure-ticks").innerHTML = [[1e-3, "1 ms"], [1, "1 sn"], [3600, "1 saat"], [YIL, "1 yıl"], [1e3 * YIL, "bin yıl"], [1e6 * YIL, "milyon yıl"], [1e9 * YIL, "milyar yıl"], [EVREN, "evren"]]
  .map(([s, t]) => `<span data-l="${pos(s)}">${t}</span>`).join("");
place($("sure-ticks"));
function updateSure() {
  const pw = $("sure-in").value;
  document.querySelectorAll("[data-sure]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.sure === pw));
  if (!pw) { $("sure-brute-n").textContent = "—"; $("sure-smart-n").textContent = "—"; return; }
  const ms = models(pw), brute = ms[0], smart = ms.reduce((a, b) => (b.n < a.n ? b : a));
  $("sure-brute-n").textContent = fmtN(brute.n) + " aday";
  $("sure-brute-why").textContent = brute.why;
  $("sure-smart-n").textContent = fmtN(smart.n) + " aday";
  $("sure-smart-why").textContent = smart === brute ? "Bilinen bir kalıba uymuyor: saldırganın elinde kör brute force kalıyor." : `${smart.name}: ${smart.why}`;
  $("sure-scale").innerHTML = RATES.map((r) => {
    const ts = smart.n / r.rate, tb = brute.n / r.rate;
    return `<div class="bar-row"><span>${r.label}</span><div class="track" role="img" aria-label="${r.label}: akıllı saldırgan ${fmtSure(ts)}, kör brute force ${fmtSure(tb)}">
      <div class="fill" data-w="${pos(ts)}"></div><div class="ghost" data-l="${pos(tb)}"></div></div>
      <strong class="mono">${fmtSure(ts)}</strong></div>`;
  }).join("");
  place($("sure-scale"));
  $("sure-table").innerHTML = `<thead><tr><th>Model</th><th>Aday sayısı</th>${RATES.map((r) => `<th>${r.label}</th>`).join("")}</tr></thead><tbody>` +
    ms.map((m) => `<tr class="${m === smart ? "best" : ""}"><td><strong>${m.name}</strong><br><span class="note">${esc(m.why)}</span></td><td class="mono">${fmtN(m.n)}</td>${RATES.map((r) => `<td class="mono">${fmtSure(m.n / r.rate)}</td>`).join("")}</tr>`).join("") + "</tbody>";
}
$("sure-in").addEventListener("input", updateSure);
updateSure();

/* ---------- 3 · Canlı brute force ---------- */
const workerUrl = "/simulasyon-worker.js";
let worker = null, lastRate = 0;
const BF_PRESETS = { "0123456789": ["7319", "482913", "1975"], "abcdefghijklmnopqrstuvwxyz": ["kedi", "simit", "parola", "zzzzz"], "abcdefghijklmnopqrstuvwxyz0123456789": ["ab12", "kedi7", "x9y8z"] };
function bfTarget() {
  const set = $("bf-set").value, pw = $("bf-in").value;
  const ok = pw.length >= 1 && pw.length <= 7 && [...pw].every((c) => set.includes(c));
  $("bf-err").textContent = ok ? "" : "Hedef yalnız seçili kümedeki karakterlerden oluşmalı (1–7 karakter).";
  $("bf-start").disabled = !ok || !!worker;
  const hex = ok ? md5Hex(pw) : "";
  $("bf-target").textContent = hex || "—";
  const total = ok ? Math.pow(set.length, pw.length) : 0;
  $("bf-total").textContent = fmtN(total);
  renderCompare(total, lastRate, null);
  return { ok, set, pw, hex, total };
}
function renderPresets() {
  $("bf-presets").innerHTML = BF_PRESETS[$("bf-set").value].map((p) => `<button class="chip" data-bf="${p}">${p}</button>`).join("");
  document.querySelectorAll("[data-bf]").forEach((b) => b.addEventListener("click", () => { $("bf-in").value = b.dataset.bf; bfTarget(); }));
}
function renderCompare(total, rate, tried) {
  const rows = [{ label: "Bu tarayıcı · MD5 · tek çekirdek", rate }, { label: "MD5 · 1 × RTX 5090", rate: 219.5e9 }, { label: "bcrypt cost 10 · 16 × RTX 5090", rate: 138675 }, { label: "Online giriş · 10 deneme/sn", rate: 10 }];
  $("bf-compare").innerHTML = `<thead><tr><th>Kim deniyor?</th><th>Deneme / sn</th><th>Bütün adaylar</th>${tried ? "<th>Bu parolaya kadar</th>" : ""}</tr></thead><tbody>` +
    rows.map((r) => `<tr><td>${r.label}</td><td class="mono">${r.rate ? fmtN(r.rate) : "başlatınca ölçülür"}</td><td class="mono">${r.rate ? fmtSure(total / r.rate) : "—"}</td>${tried ? `<td class="mono">${r.rate ? fmtSure(tried / r.rate) : "—"}</td>` : ""}</tr>`).join("") + "</tbody>";
}
function hexToWords(hex) { const out = new Int32Array(4); for (let i = 0; i < 4; i++) { let v = 0; for (let k = 3; k >= 0; k--) v = (v << 8) | parseInt(hex.substr(i * 8 + k * 2, 2), 16); out[i] = v | 0; } return out; }
function stopWorker(msg) {
  if (worker) { worker.terminate(); worker = null; }
  $("bf-stop").disabled = true; $("bf-set").disabled = false; $("bf-in").disabled = false;
  if (msg) $("bf-status").textContent = msg;
  bfTarget();
}
$("bf-start").addEventListener("click", () => {
  const t = bfTarget(); if (!t.ok) return;
  worker = new Worker(workerUrl);
  $("bf-start").disabled = true; $("bf-stop").disabled = false; $("bf-set").disabled = true; $("bf-in").disabled = true;
  $("bf-status").textContent = `${fmtN(t.total)} aday sırayla deneniyor…`;
  $("bf-prog").value = 0;
  worker.onmessage = (e) => {
    const d = e.data, rate = d.ms > 0 ? (d.tried / d.ms) * 1000 : 0;
    if (rate) lastRate = rate;
    $("bf-tried").textContent = fmtN(d.tried); $("bf-rate").textContent = rate ? fmtN(rate) + "/sn" : "—";
    $("bf-time").textContent = fmtSure(d.ms / 1000); $("bf-prog").value = d.tried / d.total;
    if (d.cur) $("bf-cur").textContent = d.cur;
    if (d.done) {
      $("bf-cur").textContent = d.found ?? "bulunamadı";
      renderCompare(d.total, lastRate, d.found ? d.tried : null);
      stopWorker(d.found ? `Bulundu: “${d.found}”. ${fmtN(d.tried)} deneme, ${fmtSure(d.ms / 1000)}. Aynı hash bcrypt ile saklansaydı her deneme milyonlarca kat yavaş olurdu.` : "Bütün adaylar denendi.");
    } else renderCompare(d.total, lastRate, null);
  };
  worker.postMessage({ charset: t.set, length: t.pw.length, target: hexToWords(t.hex) });
});
$("bf-stop").addEventListener("click", () => stopWorker("Durduruldu."));
$("bf-set").addEventListener("change", () => { renderPresets(); $("bf-in").value = BF_PRESETS[$("bf-set").value][0]; bfTarget(); });
$("bf-in").addEventListener("input", bfTarget);
renderPresets(); bfTarget();

/* ---------- 4 · Sızan veritabanı ---------- */
const FORUM = [["forum_alice", null], ["kartal34", "Kartal2025!"], ["sari_kanarya", "fenerbahce"], ["cimbom1905", "galatasaray"], ["aslan_kral", "galatasaray"],
  ["deniz_k", "Deniz2026!"], ["bob_forum", null], ["ogr_elif", "123456"], ["ogr_can", "123456"], ["ogr_ali", "123456"], ["kahvesever", "Kahve2024!"],
  ["mavi_gok", null], ["admin_eski", "admin"], ["yazilimci", "yazilim2025"], ["kara_kartal", "besiktas"], ["ekim_ruzgari", null], ["simitci", "Simit"],
  ["cay_ocagi", null], ["sonbahar_k", "Sonbahar2026!"], ["ilkbahar", null], ["misafir", "qwerty"], ["gezgin", null], ["oyuncu", "oyun2024"], ["anadolu_k", null]];
let forum = [], fzRunning = false, fzAbort = false;
async function forumInit() {
  forum = await Promise.all(FORUM.map(async ([u, p]) => { const pw = p ?? randToken(); return { u, pw, random: !p, hash: await digest("SHA-256", pw), cracked: null }; }));
  const counts = {}; forum.forEach((r) => (counts[r.hash] = (counts[r.hash] || 0) + 1));
  forum.forEach((r) => (r.dup = counts[r.hash]));
  renderForum();
}
function renderForum() {
  $("fz-body").innerHTML = forum.map((r) => `<tr class="${r.cracked ? "cracked" : ""}"><td class="mono">${r.u}</td>
    <td class="hash ${r.dup > 1 ? "same" : ""}">${r.hash.slice(0, 20)}…${r.dup > 1 ? ` <span class="tag bad">×${r.dup}</span>` : ""}</td>
    <td>${r.cracked ? `<span class="tag bad">kırıldı</span> <span class="mono">${esc(r.cracked)}</span>` : r.random && fzDone ? `<span class="tag good">sözlükte yok</span>` : `<span class="tag muted">bekliyor</span>`}</td></tr>`).join("");
  const c = forum.filter((r) => r.cracked).length;
  $("fz-cracked").textContent = `${c} / ${forum.length}`;
}
let fzDone = false;
$("fz-start").addEventListener("click", async () => {
  if (fzRunning) return;
  fzRunning = true; fzAbort = false; fzDone = false; $("fz-start").disabled = true;
  const byHash = new Map(); forum.forEach((r) => { if (!byHash.has(r.hash)) byHash.set(r.hash, []); byHash.get(r.hash).push(r); });
  const t0 = performance.now(); let tried = 0;
  for (const cand of CANDIDATES) {
    if (fzAbort) break;
    const h = await digest("SHA-256", cand); tried++;
    $("fz-cur").textContent = cand;
    const hit = byHash.get(h);
    if (hit) { hit.forEach((r) => (r.cracked = cand)); renderForum(); await sleep(hit.length > 1 ? 650 : 320); }
    else if (tried % 6 === 0) await sleep(16);
    $("fz-tried").textContent = nf0.format(tried);
    $("fz-time").textContent = fmtSure((performance.now() - t0) / 1000);
  }
  const elapsed = (performance.now() - t0) / 1000;
  fzDone = !fzAbort; fzRunning = false; $("fz-start").disabled = false; renderForum();
  if (fzAbort) return;
  $("fz-cur").textContent = `${forum.filter((r) => r.cracked).length} kayıt kırıldı`;
  const msPb = window.PBKDF2_MS || 300;
  const salted = (CANDIDATES.length * forum.length * msPb) / 1000;
  $("fz-salted-text").innerHTML = `Salt'sız: ${nf0.format(CANDIDATES.length)} aday × 1 hash = ${nf0.format(CANDIDATES.length)} hesap (animasyon hariç birkaç ms).<br>
    Salt'lı: her kullanıcının salt'ı farklı, her aday her kullanıcı için ayrı hesaplanır: ${nf0.format(CANDIDATES.length)} × ${forum.length} = ${nf0.format(CANDIDATES.length * forum.length)} PBKDF2.
    Bu tarayıcıda tek PBKDF2 ${nf0.format(msPb)} ms → <strong>${fmtSure(salted)}</strong>. Sözlük 1 milyon kelime olsaydı: <strong>${fmtSure((1e6 * 8 * forum.length * msPb) / 1000)}</strong>.`;
});
$("fz-reset").addEventListener("click", () => { fzAbort = true; fzDone = false; forum.forEach((r) => (r.cracked = null)); $("fz-tried").textContent = "0"; $("fz-time").textContent = "0 sn"; $("fz-cur").textContent = "—"; renderForum(); });
forumInit();

/* ---------- 5 · Giriş sayfasına saldırı ---------- */
const ACCOUNTS = [
  { u: "alice", pw: "r!Xv7-mQ2p-Lk9z" }, { u: "bob", pw: "Kahve2019!", leaked: true }, { u: "ayse.kaya", pw: "tY8#pW-3nq-Zr1c" },
  { u: "mehmet.demir", pw: "Mehmet!2024x" }, { u: "zeynep.celik", pw: "Galatasaray1905", leaked: true }, { u: "ece.kurt", pw: "Sonbahar2026!", weak: true },
  { u: "tolga.bulut", pw: "Sonbahar2026!", weak: true }, { u: "irem.akin", pw: "Ekim2026!", weak: true }, { u: "okan.aktas", pw: "Sonbahar2026!", weak: true },
  { u: "deniz.koc", pw: "Deniz2026!", leaked: true }, { u: "can.ozdemir", pw: "q4V!e9-Hs2b-Nw7k" }, { u: "elif.yildiz", pw: "Mavi.Kedi.Sabah.42" },
];
const BRUTE_TARGET = "ece.kurt";
const BRUTE_LIST = ["123456", "password", "qwerty", "Parola1!", "123456789", "Galatasaray1905", "Ekim2026!", "Yaz2026!", "Sonbahar2026!", "Kis2027!"];
const SPRAY = ["Sonbahar2026!", "Ekim2026!", "Parola1!"];
const COMBO = [["bob", "Kahve2019!"], ["mehmet.demir", "Mehmet123"], ["zeynep.celik", "Galatasaray1905"], ["selim.acar", "Selim2020!"], ["deniz.koc", "Deniz2026!"], ["alice", "Alice2018!"], ["elif.yildiz", "Elif1990"]];
const MODES = {
  brute: { desc: `Tek hesap (${BRUTE_TARGET}), en olası ${BRUTE_LIST.length} parola sırayla. Doğru parola 9. sırada.`, queue: () => BRUTE_LIST.map((p) => [BRUTE_TARGET, p]), scale: (n) => `1 milyon adaylık listeyle tek hesap: ${fmtSure(1e6)} (kilit yoksa).` },
  spray: { desc: `${SPRAY.length} yaygın parola × ${ACCOUNTS.length} hesap. Her hesapta en fazla ${SPRAY.length} hatalı deneme.`, queue: () => SPRAY.flatMap((p) => ACCOUNTS.map((a) => [a.u, p])), scale: () => `10.000 hesaplı bir kurumda ${SPRAY.length} parola: ${nf0.format(30000)} istek → ${fmtSure(30000)}.` },
  stuff: { desc: `Başka bir siteden sızan ${COMBO.length} e-posta:parola çifti, her biri bir kez. Kullanıcılardan üçü aynı parolayı burada da kullanıyor.`, queue: () => COMBO.slice(), scale: () => `1 milyon satırlık combo listesi, 1 istek/sn: ${fmtSure(1e6)}; 100 IP'ye dağıtılırsa ${fmtSure(1e4)}.` },
};
let mode = "brute", st = null, timer = null;
function resetOnline() {
  clearTimeout(timer); timer = null; $("on-run").textContent = "Başlat";
  st = { queue: MODES[mode].queue(), i: 0, fails: 0, alarm: false, done: false, acc: Object.fromEntries(ACCOUNTS.map((a) => [a.u, { dots: [], fails: 0, state: "" }])) };
  $("on-log").innerHTML = ""; $("on-mode-desc").textContent = MODES[mode].desc;
  renderOnline(); summary();
}
function effectivePw(a) { return $("d-block").checked && (a.weak || a.leaked) ? "(kayıtta reddedildi, başka parola)" : a.pw; }
function logLine(cls, text) { const div = document.createElement("div"); div.className = cls; div.textContent = text; $("on-log").appendChild(div); $("on-log").scrollTop = $("on-log").scrollHeight; }
function step() {
  if (!st || st.done) return false;
  if (st.i >= st.queue.length) { finish("Liste bitti."); return false; }
  if (st.alarm) { finish("Toplam hata alarmı saldırıyı engelledi; kalan istekler gönderilemedi."); return false; }
  const [u, p] = st.queue[st.i++];
  const acct = ACCOUNTS.find((a) => a.u === u), s = st.acc[u];
  const t = String(st.i).padStart(2, "0");
  if (!acct) { st.fails++; logLine("fail", `${t} POST /login ${u.padEnd(13)} ${p.padEnd(16)} → 401 bilgiler hatalı (hesap yok)`); checkAlarm(); renderOnline(); return true; }
  if (s.state === "lock") { s.dots.push("lock"); logLine("lock", `${t} POST /login ${u.padEnd(13)} ${p.padEnd(16)} → 423 hesap kilitli`); renderOnline(); return true; }
  if (s.state === "ok" || s.state === "mfa") { renderOnline(); return true; }
  if (p === effectivePw(acct)) {
    if ($("d-mfa").checked) { s.state = "mfa"; s.dots.push("mfa"); logLine("mfa", `${t} POST /login ${u.padEnd(13)} ${p.padEnd(16)} → parola doğru · MFA istendi, saldırgan geçemedi`); }
    else { s.state = "ok"; s.dots.push("ok"); logLine("ok", `${t} POST /login ${u.padEnd(13)} ${p.padEnd(16)} → 200 GİRİŞ BAŞARILI`); }
    if (mode === "brute") { renderOnline(); finish(s.state === "ok" ? "Hedef hesap ele geçti." : "Parola bulundu ama MFA girişi durdurdu."); return false; }
  } else {
    s.fails++; st.fails++; s.dots.push("fail");
    logLine("fail", `${t} POST /login ${u.padEnd(13)} ${p.padEnd(16)} → 401 bilgiler hatalı`);
    if ($("d-lock").checked && s.fails >= 5) { s.state = "lock"; s.dots[s.dots.length - 1] = "lock"; logLine("lock", `   ${u} 5 hatalı deneme → hesap kilitlendi`); if (mode === "brute") { renderOnline(); finish("Hedef hesap kilitlendi; brute force durdu. Not: saldırgan aynı yolla meşru kullanıcıyı da dışarıda bırakabilir."); return false; } }
    checkAlarm();
  }
  renderOnline();
  return true;
}
function checkAlarm() { if ($("d-alarm").checked && st.fails >= 12 && !st.alarm) { st.alarm = true; logLine("sys", `   ALARM: bütün hesaplarda ${st.fails} hatalı deneme → kaynak engellendi`); } }
function finish(msg) { st.done = true; clearTimeout(timer); timer = null; $("on-run").textContent = "Başlat"; logLine("sys", "— " + msg); summary(msg); }
function renderOnline() {
  $("on-accts").innerHTML = ACCOUNTS.map((a) => {
    const s = st.acc[a.u];
    const tag = s.state === "ok" ? '<span class="tag bad">ele geçti</span>' : s.state === "mfa" ? '<span class="tag good">MFA durdurdu</span>' : s.state === "lock" ? '<span class="tag warm">kilitli</span>' : '<span class="tag muted">güvende</span>';
    return `<div class="acct"><span class="u">${a.u}</span><span class="dots">${s.dots.map((d) => `<i class="dot ${d}"></i>`).join("")}</span>${tag}</div>`;
  }).join("");
  const v = Object.values(st.acc);
  $("on-req").textContent = st.i;
  $("on-open").textContent = v.filter((s) => s.state === "ok").length;
  $("on-mfa").textContent = v.filter((s) => s.state === "mfa").length;
  $("on-lock").textContent = v.filter((s) => s.state === "lock").length;
  $("on-clock").textContent = fmtSure(st.i);
}
function summary(end) {
  const v = Object.values(st.acc), open = v.filter((s) => s.state === "ok").length, locked = v.filter((s) => s.state === "lock").length;
  const lines = [];
  if (end) lines.push(`${st.i} istek, ${fmtSure(st.i)}: ${open} hesap ele geçti, ${locked} hesap kilitlendi.`);
  lines.push(MODES[mode].scale(st.i));
  $("on-summary").textContent = lines.join(" ");
}
function run() {
  if (!st || st.done) resetOnline();
  if (timer) { clearTimeout(timer); timer = null; $("on-run").textContent = "Devam et"; return; }
  $("on-run").textContent = "Duraklat";
  const tick = () => { if (step()) timer = setTimeout(tick, 960 - $("on-speed").value); else { timer = null; if (!st.done) $("on-run").textContent = "Başlat"; } };
  tick();
}
document.querySelectorAll("#on-mode button").forEach((b) => b.addEventListener("click", () => {
  mode = b.dataset.mode; document.querySelectorAll("#on-mode button").forEach((x) => x.setAttribute("aria-pressed", x === b)); resetOnline();
}));
["d-lock", "d-alarm", "d-block", "d-mfa"].forEach((id) => $(id).addEventListener("change", resetOnline));
$("on-run").addEventListener("click", run);
$("on-step").addEventListener("click", () => { if (!st) resetOnline(); if (st.done) return; clearTimeout(timer); timer = null; $("on-run").textContent = "Devam et"; step(); });
$("on-reset").addEventListener("click", resetOnline);
resetOnline();
