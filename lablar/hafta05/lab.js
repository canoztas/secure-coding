"use strict";
// Ders 5 parola labı: hazır düğmeler, gerçek HTTP istekleri ve Web Crypto. Sunucu yalnız 127.0.0.1.
const LAB = Number(document.body.dataset.lab);
const FIXED = document.body.dataset.fixed === "true";
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value).replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const fmt = (n) => Number(n).toLocaleString("tr-TR");
const hex = (buffer) => [...new Uint8Array(buffer)].map((b) => b.toString(16).padStart(2, "0")).join("");
const fromHex = (text) => new Uint8Array(text.match(/../g).map((h) => parseInt(h, 16)));
const enc = new TextEncoder();
const sha = async (algo, text) => hex(await crypto.subtle.digest(algo, enc.encode(text)));

async function api(path, options = {}) {
  const started = performance.now();
  const response = await fetch(path, {cache: "no-store", ...options});
  const type = response.headers.get("Content-Type") || "";
  const body = type.includes("json") ? await response.json() : await response.text();
  return {status: response.status, body, ms: performance.now() - started};
}
const post = (path, value) => api(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(value)});
const login = (username, password) => post("/api/login", {username, password});

function table(headers, rows, hit = () => false) {
  return `<table><thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>` +
    rows.map((row, i) => `<tr${hit(row, i) ? ' class="hit"' : ""}>${row.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("") +
    "</tbody></table>";
}
const counts = (items) => `<div class="counts">${items.map(([label, value]) => `<span>${esc(label)}: <strong>${esc(value)}</strong></span>`).join("")}</div>`;
const status = (text, kind = "") => `<p class="status ${kind}" role="status">${esc(text)}</p>`;

// Sözlük kuralları: veri.py mutate() ile aynı sıra.
function* mutate(word, years) {
  const cap = word.charAt(0).toUpperCase() + word.slice(1);
  yield word; yield cap;
  for (const year of years) { yield word + year; yield cap + year + "!"; }
}
function candidates(words, years) {
  const seen = new Set();
  for (const word of words) for (const guess of mutate(word, years)) seen.add(guess);
  return [...seen];
}

const shared = {};

const LABS = {
  1: {
    label: "LAB 1 · ONLINE SALDIRI",
    title: "Kilit var, yine de girdik",
    task: "ornek.test'in giriş sayfası 5 hatalı denemede hesabı kilitliyor. Önce hata mesajlarına, sonra kilide, en son password spraying'e bakalım. Bütün denemeler bu sunucuya giden gerçek HTTP istekleridir.",
    steps: [
      {
        short: "Hata mesajları",
        title: "1. Hata mesajları hangi hesabın var olduğunu söylüyor mu?",
        help: "Saldırgan şirketin ekip sayfasından 48 olası kullanıcı adı çıkarmış. Her birine yanlış bir parola gönderiyoruz ve yanıtı ve süreyi kaydediyoruz.",
        button: "48 kullanıcı adını dene",
        async run() {
          await post("/api/lab1/reset", {reset: true});
          const info = (await api("/api/lab1/info")).body;
          shared.info = info;
          const rows = [];
          for (const name of info.guessed_names) {
            const r = await login(name, "yanlis-parola");
            rows.push({name, status: r.status, message: r.body.error || r.body.message, ms: r.ms});
          }
          const groups = {};
          for (const row of rows) (groups[row.message] ||= []).push(row);
          shared.existing = FIXED ? rows.map((r) => r.name) : rows.filter((r) => r.message !== "Kullanıcı bulunamadı").map((r) => r.name);
          const summary = Object.entries(groups).map(([message, list]) =>
            [esc(message), fmt(list.length), fmt(Math.round(list.reduce((a, r) => a + r.ms, 0) / list.length)) + " ms"]);
          const sample = rows.filter((r) => ["alice", "selim.acar", "ece.kurt", "test"].includes(r.name));
          return table(["Yanıt", "Ad sayısı", "Ortalama süre"], summary) +
            table(["Kullanıcı adı", "HTTP", "Mesaj", "Süre"], sample.map((r) => [`<code>${esc(r.name)}</code>`, r.status, esc(r.message), Math.round(r.ms) + " ms"])) +
            (FIXED
              ? status("Bütün yanıtlar aynı: hangi adların kayıtlı olduğu anlaşılmıyor.", "good") +
                `<p>Kayıtsız adlarda da sahte bir hash hesaplanıyor; süreler de birbirine yakın.</p>`
              : status(`${shared.existing.length} kullanıcı adı kayıtlı çıktı. Mesaj ve süre bunu söyledi.`, "bad") +
                `<p>"Kullanıcı bulunamadı" yanıtında parola hash'i hiç hesaplanmadığı için o yanıt daha hızlı geliyor.</p>`);
        },
      },
      {
        short: "Tek hesap",
        title: "2. Tek hesaba brute force: kilit işe yarıyor mu?",
        help: "Saldırgan yalnız <code>alice</code> hesabına art arda 8 yaygın parola deniyor. 1. adımda alice'e zaten bir hatalı deneme yapılmıştı.",
        button: "alice için 8 parola dene",
        async run() {
          const guesses = ["123456", "password", "qwerty", "alice2026", "Alice2026!", "Sonbahar2026!", "Parola1!", "alice123"];
          const rows = [];
          for (const guess of guesses) {
            const r = await login("alice", guess);
            rows.push([`<code>${esc(guess)}</code>`, r.status, esc(r.body.error || r.body.message) + (r.body.retry_after ? ` · Retry-After: ${r.body.retry_after} sn` : "")]);
          }
          const stopped = rows.filter((r) => r[1] === 423 || r[1] === 429).length;
          return table(["Denenen parola", "HTTP", "Yanıt"], rows, (r) => r[1] === 423 || r[1] === 429) +
            status(`${stopped} deneme sunucuda durduruldu.`, "good") +
            `<p>${FIXED ? "5. hatadan sonra 429 + Retry-After: bekleme süresi her hatada ikiye katlanır (30 sn → 1 saat)." :
              "5. hatadan sonra hesap kilitlendi (423). Tek hesaba brute force bu hızla ilerleyemez."}</p>`;
        },
      },
      {
        short: "Spraying",
        title: "3. Password spraying: her hesaba yalnız 3 deneme",
        help: "Bu kez tek hesaba çok parola yerine çok hesaba az parola deniyoruz: mevsimlik ve yaygın 3 parola × 1. adımda bulunan hesaplar. Hiçbir hesap 5 hataya ulaşmıyor.",
        button: "3 parola × hesapları dene",
        async run(out) {
          const users = shared.existing || shared.info.guessed_names;
          const sprays = shared.info.spray_list;
          const total = users.length * sprays.length;
          out.innerHTML = `<progress max="${total}" value="0"></progress><p class="muted" role="status">0 / ${total}</p>`;
          const bar = out.querySelector("progress"), label = out.querySelector("p");
          const found = [], codes = {};
          let done = 0;
          for (const password of sprays) {
            for (const user of users) {
              const r = await login(user, password);
              codes[r.status] = (codes[r.status] || 0) + 1;
              if (r.status === 200) found.push([user, password]);
              bar.value = ++done; label.textContent = `${done} / ${total} istek`;
            }
          }
          const check = (await post("/api/check", {lab: 1, pairs: found})).body;
          return counts([["Toplam istek", fmt(total)], ...Object.entries(codes).map(([c, n]) => [`HTTP ${c}`, fmt(n)]), ["Giriş yapılan hesap", fmt(found.length)]]) +
            (found.length ? table(["Hesap", "Parola"], found.map(([u, p]) => [`<code>${esc(u)}</code>`, `<code>${esc(p)}</code>`]), () => true) : "") +
            (found.length
              ? status(`${found.length} hesaba girildi; sunucu ${check.correct} / ${check.checked} çifti doğruladı. Yeni kilitlenen hesap yok.`, "bad")
              : status("Hiçbir hesaba girilemedi. Bu parolalar kayıt sırasında reddedilmişti.", "good")) +
            (codes[423] || codes[429] ? `<p class="muted">${fmt((codes[423] || 0) + (codes[429] || 0))} durdurulan istek, 2. adımda zaten ${FIXED ? "bekletilen" : "kilitlenen"} alice hesabına gitti.</p>` : "");
        },
      },
    ],
    solution: () => FIXED ? [
      "Hata mesajı tek: “Kullanıcı adı veya parola hatalı”. Kayıtsız adda da sahte hash hesaplanır; mesaj ve süre hesabın varlığını söylemez.",
      "Sert kilit yerine artan bekleme (429 + Retry-After): brute force yavaşlar, saldırgan da gerçek kullanıcıyı uzun süre dışarıda bırakamaz.",
      "Kayıt ve parola değişiminde yaygın / sızmış parola listesi kontrol edildi. Sonbahar2026! gibi parolalar hiç kabul edilmedi; spraying bu yüzden boş döndü.",
      "Gerçek sistemde ek katmanlar: IP / istemci bazlı sınır, bot tespiti, giriş anomalisi izleme ve en önemlisi MFA. Dağıtık proxy kullanan saldırgan IP sınırını aşabilir.",
    ] : [
      "İki farklı hata mesajı (ve süre farkı) kayıtlı hesapları ortaya çıkardı: user enumeration.",
      "Hesap başına 5 hata kilidi tek hesaba brute force'u durdurdu.",
      "Spraying her hesaba 3 deneme yaptı; kilit hiç tetiklenmedi. Mevsimlik parola kullanan 4 hesap bulundu.",
      "Düzeltme: tek hata mesajı + sahte hash, artan bekleme, kayıtta yaygın / sızmış parola listesi, MFA. Kilit tek başına spraying'e karşı yetmez.",
    ],
  },
  2: {
    label: "LAB 2 · OFFLINE SALDIRI",
    title: "Sızan forum yedeği",
    task: "forum.ornek.test'in eski bir veritabanı yedeği sızdı. Saldırgan artık giriş sayfasıyla uğraşmıyor: hash'ler elinde, kilit veya bekleme yok. Denemeler bu tarayıcıda yapılır; sunucuya parola adayı gönderilmez.",
    steps: [
      {
        short: "Yedek",
        title: "1. Yedekte ne var?",
        help: "Yedeği indirip ilk kayıtlara ve aynı hash'i paylaşan kayıtlara bakıyoruz.",
        button: "Sızan yedeği göster",
        async run() {
          const dump = (await api("/api/lab2/dump")).body;
          shared.dump = dump;
          const records = dump.records;
          const key = (r) => r.sha256_hex || r.hash_hex;
          const groups = {};
          for (const r of records) (groups[key(r)] ||= []).push(r.user);
          const dupes = Object.entries(groups).filter(([, users]) => users.length > 1);
          const rows = records.slice(0, 8).map((r) => FIXED
            ? [`<code>${esc(r.user)}</code>`, `<code>${esc(r.salt_hex.slice(0, 12))}…</code>`, `<code>${esc(r.hash_hex.slice(0, 20))}…</code>`]
            : [`<code>${esc(r.user)}</code>`, `<code>${esc(r.sha256_hex.slice(0, 32))}…</code>`]);
          const dupeSet = new Set(dupes.flatMap(([, u]) => u));
          return `<p>Biçim: <strong>${esc(dump.format)}</strong> · ${fmt(records.length)} kayıt</p>` +
            table(FIXED ? ["Kullanıcı", "Salt", "Hash"] : ["Kullanıcı", "SHA-256"], rows, (row) => dupeSet.has(row[0].replace(/<[^>]+>/g, ""))) +
            (dupes.length
              ? status(`${dupes.length} hash birden çok kayıtta tekrar ediyor: ${dupes.map(([, u]) => u.join(" = ")).join(" · ")}`, "bad") +
                "<p>Salt olmadığı için aynı parola aynı hash'i üretir. Birini kırmak hepsini kırmaktır.</p>"
              : status("Tekrar eden hash yok: aynı parola bile farklı salt ile farklı kayıt üretir.", "good"));
        },
      },
      {
        short: "Sözlük",
        title: "2. Sözlük ve kurallar",
        help: "Rastgele brute force yerine insanların gerçekten seçtiği kelimelerle başlıyoruz. Her kelimeye politikaya uyduran kurallar uygulanır: büyük harf, yıl ve ünlem.",
        button: "Aday listesini hazırla",
        async run() {
          const list = (await api("/api/lab2/wordlist")).body;
          shared.candidates = candidates(list.words, list.years);
          const kahve = [...mutate("kahve", list.years)];
          return counts([["Taban kelime", fmt(list.words.length)], ["Kural", list.rules.length + " biçim × yıl"], ["Benzersiz aday", fmt(shared.candidates.length)]]) +
            `<p>Örnek: <code>kahve</code> → ${kahve.map((k) => `<code>${esc(k)}</code>`).join(" ")}</p>` +
            `<p class="muted">Gerçek saldırılarda milyonlarca kelimelik sızıntı listeleri ve binlerce kural kullanılır. Bu liste sınıf için küçültülmüştür.</p>`;
        },
      },
      {
        short: "Kırma",
        title: "3. Kırmayı başlat",
        help: FIXED
          ? "Her kayıt kendi salt'ıyla PBKDF2-HMAC-SHA256 (600.000 tur) kullanıyor. Aynı adayı her kullanıcı için ayrı hesaplamamız gerekir. Gösterim 12 saniyeyle sınırlı."
          : "Salt yok: her adayın SHA-256'sını bir kez hesaplayıp bütün kayıtlarla karşılaştırıyoruz.",
        button: FIXED ? "12 saniye dene ve ölç" : "Bütün adayları dene",
        async run(out) {
          const records = shared.dump.records, cands = shared.candidates;
          const found = [];
          const started = performance.now();
          let guesses = 0;
          if (!FIXED) {
            const lookup = new Map();
            for (const guess of cands) { lookup.set(await sha("SHA-256", guess), guess); guesses++; }
            for (const r of records) if (lookup.has(r.sha256_hex)) found.push([r.user, lookup.get(r.sha256_hex)]);
          } else {
            out.innerHTML = `<progress max="12000" value="0"></progress><p class="muted" role="status">Başlıyor…</p>`;
            const bar = out.querySelector("progress"), label = out.querySelector("p");
            const keys = new Map();
            const open = new Set(records.map((r) => r.user));
            outer: for (const guess of cands) {
              let base = keys.get(guess);
              if (!base) { base = await crypto.subtle.importKey("raw", enc.encode(guess), "PBKDF2", false, ["deriveBits"]); keys.clear(); keys.set(guess, base); }
              for (const r of records) {
                if (!open.has(r.user)) continue;
                if (performance.now() - started > 12000) break outer;
                const bits = await crypto.subtle.deriveBits({name: "PBKDF2", hash: "SHA-256", salt: fromHex(r.salt_hex), iterations: r.iterations}, base, 256);
                guesses++;
                if (hex(bits) === r.hash_hex) { found.push([r.user, guess]); open.delete(r.user); }
                bar.value = performance.now() - started;
                label.textContent = `${fmt(guesses)} deneme · aday: ${guess} · bulunan: ${found.length}`;
              }
            }
          }
          const seconds = (performance.now() - started) / 1000;
          const rate = guesses / seconds;
          const check = found.length ? (await post("/api/check", {lab: 2, pairs: found})).body : {correct: 0, checked: 0};
          const full = FIXED ? cands.length * records.length : cands.length;
          return counts([["Hesaplanan hash", fmt(guesses)], ["Süre", seconds.toFixed(2) + " sn"], ["Bu tarayıcıda hız", fmt(Math.round(rate)) + " / sn"], ["Kırılan kayıt", `${found.length} / ${records.length}`]]) +
            (found.length ? table(["Kullanıcı", "Parola"], found.map(([u, p]) => [`<code>${esc(u)}</code>`, `<code>${esc(p)}</code>`]), () => true) : "") +
            status(`Sunucu ${check.correct} / ${check.checked} parolayı doğruladı.`, FIXED ? "" : "bad") +
            (FIXED
              ? `<p>Bütün sözlük için gereken hesap: ${fmt(cands.length)} aday × ${fmt(records.length)} kullanıcı = <strong>${fmt(full)}</strong> PBKDF2. Bu hızla yaklaşık <strong>${fmt(Math.round(full / rate / 60))} dakika</strong>. Yine de en yaygın parolalar ilk saniyelerde düşebilir: maliyet zayıf parolayı güçlü yapmaz.</p>`
              : `<p>${fmt(cands.length)} SHA-256 hesabı bütün kullanıcılar için yetti. Bir GPU saniyede milyarlarca SHA-256 hesaplar (Hafta 4).</p>`);
        },
      },
    ],
    solution: () => FIXED ? [
      "Kayıt başına rastgele salt: aynı parola farklı hash üretti; hazır tablo ve 'birini kır, hepsini kır' etkisi kalmadı.",
      "PBKDF2 600.000 tur: her aday her kullanıcı için ayrı ve pahalı. Bütün sözlüğü denemek dakikalar/saatler sürer; GPU'da da oran korunur.",
      "Ama 123456 gibi parolalar ilk denemelerde yine bulunur. Maliyet + kayıtta yaygın parola listesi birlikte gerekir.",
      "Yeni sistemde Argon2id (bellek gerektirir, GPU'da daha pahalı) tercih edilir. Tarayıcıda Argon2 olmadığı için bu lab PBKDF2 gösterir.",
    ] : [
      "Salt olmadığı için aynı parolalar aynı hash'te göründü ve tek bir arama tablosu bütün kayıtlara uygulandı.",
      "SHA-256 hızlı bir genel hash: 479 aday milisaniyeler içinde hesaplandı. Kural uygulanmış sözlük politikaya uyan parolaları da buldu.",
      "Kilit, CAPTCHA, IP sınırı offline saldırıda devrede değildir: saldırgan sunucuya hiç sormaz.",
      "Düzeltme: Argon2id (veya scrypt / PBKDF2) + kayıt başına salt; kayıtta yaygın parola listesi; sızıntı sonrası parolaları sıfırla ve oturumları sonlandır.",
    ],
  },
  3: {
    label: "LAB 3 · SIZINTI KONTROLÜ",
    title: "Parolayı göndermeden sor",
    task: "Kayıt formu yeni parolanın sızıntı listelerinde olup olmadığını bir servise soruyor. Soru nasıl soruluyor ve servis ne öğreniyor? Servis bu labda yerel bir taklittir; gerçek Have I Been Pwned API'si çağrılmaz.",
    steps: [
      {
        short: "Parola",
        title: "1. Kontrol edilecek parolayı seç",
        help: "Hazır örneklerden birini seçin. Gerçek parolanızı yazmayın.",
        button: "Seçili parolayı hazırla",
        setup(panel) {
          const words = ["kirmizi", "bisiklet", "sabah", "cayi", "deniz", "kalem", "bulut", "limon", "kopru", "orman", "pencere", "kum"];
          const pick = new Uint32Array(4); crypto.getRandomValues(pick);
          const phrase = [...pick].map((n) => words[n % words.length]).join(" ");
          const box = document.createElement("div");
          box.className = "presets";
          for (const value of ["Sonbahar2026!", "123456", phrase]) {
            const b = document.createElement("button");
            b.type = "button"; b.className = "secondary"; b.textContent = value;
            b.addEventListener("click", () => { shared.password = value; box.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b))); });
            box.appendChild(b);
          }
          shared.password = "Sonbahar2026!";
          box.firstChild.setAttribute("aria-pressed", "true");
          panel.querySelector(".help").after(box);
        },
        async run() {
          await post("/api/lab3/reset-log", {reset: true});
          const pw = shared.password;
          if (!FIXED) {
            shared.url = "/api/lab3/check?password=" + encodeURIComponent(pw);
            return `<p>Gönderilecek istek:</p><pre>GET ${esc(shared.url)}</pre>` + status("Parolanın kendisi URL'de, sunucuya gidiyor.", "bad");
          }
          const digest = (await sha("SHA-1", pw)).toUpperCase();
          shared.prefix = digest.slice(0, 5); shared.suffix = digest.slice(5);
          return `<p>SHA-1(<code>${esc(pw)}</code>):</p><p class="hash"><span class="pre">${esc(shared.prefix)}</span><span class="suf">${esc(shared.suffix)}</span></p>` +
            `<p>Sunucuya yalnız ilk <strong>5</strong> hex karakter gidecek: <code>GET /api/lab3/range/${esc(shared.prefix)}</code>. Kalan 35 karakter bu tarayıcıda kalır.</p>` +
            `<p class="muted">Buradaki SHA-1 parola saklamak için değil, listede arama anahtarı olarak kullanılır.</p>`;
        },
      },
      {
        short: "Sunucuya sor",
        title: "2. Sunucuya sor",
        help: FIXED ? "Sunucu bu prefix ile başlayan bütün suffix'leri ve dolgu satırlarını döndürür. Karşılaştırmayı tarayıcı yapar." : "Sunucu parolayı alır ve listede olup olmadığını söyler.",
        button: "İsteği gönder",
        async run() {
          if (!FIXED) {
            const r = await api(shared.url);
            return `<pre>${esc(JSON.stringify(r.body, null, 2))}</pre>` + status(r.body.found ? `Listede: ${fmt(r.body.count)} kez görülmüş (sentetik sayı).` : "Listede yok.", r.body.found ? "bad" : "good");
          }
          const r = await api(`/api/lab3/range/${shared.prefix}`);
          const lines = r.body.trim().split("\n");
          const map = new Map(lines.map((l) => l.split(":")));
          const seen = Number(map.get(shared.suffix) || 0);
          const padding = lines.filter((l) => l.endsWith(":0")).length;
          return counts([["Dönen satır", fmt(lines.length)], ["Dolgu (sayı 0)", fmt(padding)], ["Eşleşme", seen ? fmt(seen) + " kez" : "yok"]]) +
            `<pre>${esc(lines.slice(0, 5).join("\n"))}\n…</pre>` +
            status(seen ? `Bu parola listede ${fmt(seen)} kez görülmüş (sentetik sayı). Kayıt reddedilmeli.` : "Listede yok. Bu kontrol tek başına parolanın güçlü olduğunu kanıtlamaz.", seen ? "bad" : "good");
        },
      },
      {
        short: "Log",
        title: "3. Sunucu ne gördü?",
        help: "Sunucunun istek logunu açıyoruz. Gerçek hayatta bu satırlar proxy, CDN ve izleme sistemlerine de düşebilir.",
        button: "Sunucu logunu göster",
        async run() {
          const log = (await api("/api/lab3/log")).body.lines;
          const decoded = log.map((line) => { try { return decodeURIComponent(line); } catch { return line; } });
          return `<pre>${esc(decoded.join("\n") || "(boş)")}</pre>` + (FIXED
            ? status("Logda yalnız 5 hex karakter var. Aynı prefix'i yüzlerce farklı hash paylaşıyor.", "good")
            : status("Logda parolanın kendisi duruyor.", "bad"));
        },
      },
    ],
    solution: () => FIXED ? [
      "Parolanın SHA-1 özeti tarayıcıda hesaplandı; sunucuya yalnız ilk 5 hex karakter gitti (k-anonymity).",
      "Sunucu o prefix'le başlayan bütün suffix'leri ve 0 sayılı dolgu satırlarını döndürdü; hangi satırın aradığımız olduğunu bilmiyor.",
      "Eşleşme yerelde yapıldı. Have I Been Pwned Pwned Passwords range API'si aynı yöntemi kullanır (Add-Padding başlığı ile 800–1000 satır).",
      "Bu sonuç kayıt kontrolünün bir parçasıdır: liste dışı olmak parolayı güçlü yapmaz; uzunluk ve yavaş hash yine gerekir.",
    ] : [
      "Parola URL'nin query kısmında gönderildi; sunucu logunda açıkça göründü (Hafta 3: query loglara düşer).",
      "Kontrol servisi, ona soran herkesin parolasını öğrenmiş oldu. Servis veya logları sızarsa yeni bir parola listesi oluşur.",
      "Düzeltme: parolayı gönderme; özetin yalnız ilk 5 karakteriyle sor, gelen listeyle yerelde karşılaştır (k-anonymity).",
      "Düzeltilmiş sürümde aynı adımları tekrarlayın ve logu karşılaştırın.",
    ],
  },
};

function render() {
  if (!LABS[LAB]) { $("home").hidden = false; return; }
  const lab = LABS[LAB];
  $("exercise").hidden = false;
  $("label").textContent = lab.label + (FIXED ? " · DÜZELTİLMİŞ" : "");
  $("title").textContent = lab.title;
  $("task").textContent = lab.task;
  document.title = `${lab.title} · Ders 5`;
  const names = [...lab.steps.map((s, i) => `${i + 1} · ${s.short}`), "4 · Çözüm"];
  $("step-list").innerHTML = names.map((n, i) => `<li${i === 0 ? ' aria-current="step"' : ""}>${esc(n)}</li>`).join("");
  const host = $("steps");
  host.innerHTML = "";
  const panels = [];
  const mark = (index) => $("step-list").querySelectorAll("li").forEach((li, i) => {
    li.toggleAttribute("aria-current", i === index); li.classList.toggle("complete", i < index);
  });
  const show = (index) => { panels[index].hidden = false; mark(index); panels[index].scrollIntoView({behavior: "smooth", block: "start"}); };
  lab.steps.forEach((step, index) => {
    const panel = document.createElement("section");
    panel.className = "panel demo-step"; panel.id = `step-${index + 1}`; panel.hidden = index > 0;
    panel.innerHTML = `<h2>${esc(step.title)}</h2><p class="help">${step.help}</p><button type="button" class="run">${esc(step.button)}</button><div class="out" aria-live="polite"></div>` +
      `<button type="button" class="secondary next" hidden>${index + 2 === 4 ? "4. Çözümü açıkla →" : `${index + 2}. adıma geç →`}</button>`;
    host.appendChild(panel); panels.push(panel);
    if (step.setup) step.setup(panel);
    const run = panel.querySelector(".run"), out = panel.querySelector(".out"), next = panel.querySelector(".next");
    run.addEventListener("click", async () => {
      run.disabled = true; $("page-error").hidden = true;
      try { out.innerHTML = await step.run(out); next.hidden = false; }
      catch (error) { $("page-error").textContent = "Hata: " + error.message; $("page-error").hidden = false; run.disabled = false; }
    });
    next.addEventListener("click", () => { next.hidden = true; show(index + 1); });
  });
  const solution = document.createElement("section");
  solution.className = "panel demo-step"; solution.id = "step-4"; solution.hidden = true;
  const other = `http://127.0.0.1:${Number(location.port) + (FIXED ? -1 : 1)}/lab/${LAB}`;
  solution.innerHTML = `<h2>4. Çözüm: ne oldu, nasıl düzelir?</h2><ol>${lab.solution().map((s) => `<li>${esc(s)}</li>`).join("")}</ol>` +
    `<p><a href="${esc(other)}" id="compare">Aynı gösterimi ${FIXED ? "alıştırma" : "düzeltilmiş"} sürümde aç →</a> <span class="muted">(İki lab sunucusu da açık olmalı.)</span></p>` +
    `<details id="source-code"><summary>Hazır çözüm kodu · isteğe bağlı</summary><pre id="solution-command">python -X utf8 lablar/hafta05/cozum.py ${LAB} --port ${esc(location.port)}</pre>` +
    `<a href="/cozum.py" download="cozum.py">Çözüm kodunu indir · cozum.py</a><pre id="solution-code">Yükleniyor…</pre></details>`;
  host.appendChild(solution); panels.push(solution);
  solution.querySelector("details").addEventListener("toggle", async () => {
    const pre = $("solution-code");
    if (pre.dataset.loaded) return;
    pre.textContent = (await api("/cozum.py")).body; pre.dataset.loaded = "1";
  }, {once: true});
  $("restart").hidden = false;
}

$("restart").addEventListener("click", () => location.reload());
render();
