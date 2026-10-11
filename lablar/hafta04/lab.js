"use strict";
const lab = Number(document.body.dataset.lab);
const fixed = document.body.dataset.fixed === "true";
const byId = id => document.getElementById(id);
const encoder = new TextEncoder();
let packet, firstAttempt, errorPage;
const requests = {package: 0, check: 0};

function showRequests() {
  byId("package-requests").textContent = requests.package;
  byId("check-requests").textContent = requests.check;
}

function step(number) {
  byId(`step-${number}`).hidden = false;
  document.querySelectorAll(".step-list li").forEach((item, index) => {
    if (index + 1 === number) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
    item.classList.toggle("complete", index + 1 < number);
  });
  byId(`step-${number}`).scrollIntoView({behavior: "smooth", block: "start"});
}

function onClick(id, action) {
  byId(id).addEventListener("click", async () => {
    const button = byId(id);
    button.disabled = true;
    byId("page-error").hidden = true;
    try { await action(); }
    catch (error) {
      byId("page-error").textContent = `İşlem tamamlanamadı: ${error.message}. Lab sunucusunu kontrol edip yeniden dene.`;
      byId("page-error").hidden = false;
      button.disabled = false;
    }
  });
}

function fromHex(value) {
  if (!/^(?:[0-9a-f]{2})+$/i.test(value)) throw new Error("Geçersiz hex alanı");
  return Uint8Array.from(value.match(/../g), pair => parseInt(pair, 16));
}

async function decrypt(keyBytes) {
  const key = await crypto.subtle.importKey("raw", keyBytes, "AES-GCM", false, ["decrypt"]);
  const opened = await crypto.subtle.decrypt({name: "AES-GCM", iv: fromHex(packet.nonce_hex),
    tagLength: 128}, key, fromHex(packet.ciphertext_and_tag_hex));
  return new TextDecoder("utf-8", {fatal: true}).decode(opened);
}

async function tryPin(number) {
  const pin = String(number).padStart(4, "0");
  const key = await crypto.subtle.digest("SHA-256", encoder.encode(pin));
  const keyHex = Array.from(new Uint8Array(key), byte => byte.toString(16).padStart(2, "0")).join("");
  try { return {pin, keyHex, plaintext: await decrypt(key)}; }
  catch (error) {
    if (error.name !== "OperationError") throw error;
    return {pin, keyHex, plaintext: null};
  }
}

function keyFromError() {
  const parsed = new DOMParser().parseFromString(errorPage, "text/html");
  const config = parsed.querySelector("#debug-config")?.textContent || "";
  return /"AES_KEY_HEX":\s*"([0-9a-f]{64})"/.exec(config)?.[1] || null;
}

async function finish(plaintext, reason) {
  if (plaintext !== null) {
    requests.check++;
    showRequests();
    const response = await fetch("/api/check", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({lab, answer: plaintext})});
    if (!response.ok || !(await response.json()).accepted) throw new Error("Not doğrulanamadı; sunucu yeniden başlamış olabilir");
    byId("plaintext").textContent = plaintext;
    byId("plaintext").hidden = false;
  }
  byId("result").textContent = plaintext === null ? "Bu yöntemle not açılamadı." : "Not açıldı ve sunucudaki kayıtla doğrulandı.";
  byId("outcome-reason").textContent = reason;
  byId("outcome").hidden = false;
  byId("outcome").dataset.state = plaintext === null ? "blocked" : "opened";
}

async function bruteForce() {
  byId("progress-view").hidden = false;
  const sample = [];
  for (let number = 0; number < 10_000; number++) {
    const attempt = number === 0 ? firstAttempt : await tryPin(number);
    const attempts = number + 1;
    const line = `${attempt.pin} → ${attempt.plaintext === null ? "Paket doğrulanmadı" : "Not açıldı"}`;
    if (number < 3) sample.push(line);
    if (number < 3 || attempts % 100 === 0 || attempt.plaintext !== null || attempts === 10_000) {
      byId("progress").value = attempts;
      byId("attempt-count").textContent = `${attempts.toLocaleString("tr-TR")} / 10.000 aday denendi`;
      byId("attempt-log").textContent = [...sample, ...(number >= 3 ? ["…", line] : [])].join("\n");
      // Gerçek ilerlemeyi çiz; ekrandaki süre bir GPU benchmark'ı değildir.
      await new Promise(resolve => requestAnimationFrame(resolve));
    }
    if (attempt.plaintext !== null) {
      await finish(attempt.plaintext, `PIN: ${attempt.pin}. ${attempts.toLocaleString("tr-TR")} denemede bulundu. AES'in key'i yalnız 10.000 olasılıktan biriydi.`);
      return;
    }
  }
  await finish(null, "10.000 PIN adayı bitti. Bu paketi açan key, denediğimiz PIN adaylarından türemiyor.");
}

function setupSolution() {
  const steps = lab === 1 ? [
    "Alice'in Bob'a gönderdiği paket indirildi. Secret key pakette yoktu.",
    "Her dört rakamlı PIN'in SHA-256 özeti bir aday key olarak denendi. Denemeler bu tarayıcıda yapıldı.",
    fixed ? "Rastgele key kullanılan bu sürümde 10.000 adayın hiçbiri paketi açmadı." : "Doğru PIN'den üretilen key, AES-GCM doğrulamasını geçti ve not açıldı.",
    "256 bit hash çıktısı, 10.000 farklı PIN'i daha geniş bir aday alanına dönüştürmez."
  ] : [
    "Alice'in Bob'a gönderdiği şifreli paket alındı; nonce zaten açıktı.",
    fixed ? "XML isteği genel bir 400 yanıtı verdi; key veya traceback görünmedi." : "Desteklenmeyen XML isteği 500 yanıtı üretti; debug ayarlarında AES_KEY_HEX göründü.",
    fixed ? "Hata yanıtından key elde edilemediği için bu yöntemle not açılamadı." : "Hex gösterimi key baytlarına çevrildi; paketin nonce ve ciphertext/tag alanlarıyla not çözüldü.",
    "Hex çözmek bir gösterim dönüşümüdür. Notun açılmasını sağlayan bilgi secret key'dir."
  ];
  steps.forEach(text => { const item = document.createElement("li"); item.textContent = text; byId("solution-steps").append(item); });
  byId("solution-fix").textContent = lab === 1
    ? "Düzeltme: AES key'ini yeterli uzunlukta güvenli rastgele baytlardan üret. İnsan parolası kullanılacaksa uygun parola KDF'si gerekir."
    : "Düzeltme: hata yanıtına key veya uygulama ayarlarını ekleme. Daha önce sızmış key'i yenile ve etkilenen veriyi değerlendir.";
  byId("solution-command").textContent = `python lablar/hafta04/cozum.py ${lab}` + (location.port !== "8084" ? ` --port ${location.port}` : "");
  byId("compare").href = `http://127.0.0.1:${fixed ? 8084 : 8085}/lab/${lab}`;
  byId("compare").textContent = fixed ? "Hatalı sürümde aynı adımları göster →" : "Düzeltilmiş sürümde aynı adımları göster →";
  byId("source-code").addEventListener("toggle", async () => {
    if (!byId("source-code").open || byId("solution-code").dataset.loaded) return;
    try {
      const response = await fetch("/cozum.py");
      if (!response.ok) throw new Error("Çözüm kodu alınamadı");
      byId("solution-code").textContent = await response.text();
      byId("solution-code").dataset.loaded = "true";
    } catch (error) { byId("solution-code").textContent = error.message; }
  });
}

function start() {
  if (!lab) { byId("home").hidden = false; return; }
  byId("exercise").hidden = false;
  byId("label").textContent = `ALICE → BOB / LAB ${lab} / ${fixed ? "DÜZELTİLMİŞ SÜRÜM" : "ADIM ADIM GÖSTERİM"}`;
  byId("title").textContent = lab === 1 ? "4 rakam ne kadar secret?" : "Hata sayfası neyi ele veriyor?";
  byId("task").textContent = fixed
    ? "Bu sürümde aynı adımları yeniden göstereceğiz. Uygulamanın düzeltmesi, önceki yöntemin sonucunu nasıl değiştiriyor?"
    : "Alice'in Bob'a gönderdiği not şifreli. Her düğme gösterimin bir adımını çalıştırır; ardından sonucu birlikte yorumlayabiliriz.";
  byId("observe-title").textContent = lab === 1 ? "2. Tek bir adayı deneyelim" : "2. Hata sayfasını inceleyelim";
  byId("observe-help").textContent = lab === 1
    ? "İlk PIN: 0000. Bu PIN'in SHA-256 özetiyle bir key üretip paketi açmayı deniyoruz."
    : "Uygulama yalnız JSON önizleme destekliyor. XML istersek hata yanıtında ne göreceğiz?";
  byId("observe").textContent = lab === 1 ? "0000 PIN'ini dene" : "XML önizlemeyi aç";
  byId("run-title").textContent = lab === 1 ? "3. Kalan PIN adaylarını tarayalım" : "3. Hata yanıtındaki key ile deneyelim";
  byId("run-help").textContent = lab === 1
    ? "0000–9999 aralığını sırayla tarıyoruz. Her deneme yerelde yapılır; ekrandaki sayaç gerçek deneme sayısıdır."
    : "Hazır çözüm, bu hata yanıtındaki key'i bulup aynı şifreli pakette kullanacak.";
  byId("run").textContent = lab === 1 ? "Adayları tara" : "Key'i bul ve notu çöz";
  if (lab === 1) {
    for (const id of ["application-code", "pin-examples", "bruteforce-target"]) byId(id).hidden = false;
    byId("application-code-help").textContent = fixed
      ? "Bu sürümde key doğrudan rastgele üretiliyor. Artık dört haneli bir PIN'den türemiyor."
      : "Zayıflık şu satırda: key = SHA-256(PIN). PIN yalnız dört rakam olduğu için key de yalnız 10.000 adaydan biri.";
    byId("application-snippet").textContent = (fixed
      ? "key = AESGCM.generate_key(bit_length=256)\n"
      : 'pin = f"{secrets.randbelow(10_000):04d}"\nkey = hashlib.sha256(pin.encode("ascii")).digest()  # HATA\n')
      + 'nonce = secrets.token_bytes(12)\nsealed = AESGCM(key).encrypt(nonce, message, None)';
  }
  setupSolution();
  onClick("inspect", async () => {
    requests.package++;
    showRequests();
    const response = await fetch(`/api/lab/${lab}`);
    if (!response.ok) throw new Error("Paket alınamadı");
    packet = await response.json();
    byId("package").textContent = JSON.stringify(packet, null, 2);
    byId("ciphertext").textContent = packet.ciphertext_and_tag_hex;
    byId("target-packet").textContent = "Hedef: " + packet.ciphertext_and_tag_hex.slice(0, 24) + "… (hex kesiti)";
    byId("key-source").textContent = `Şifreleme: ${packet.algorithm} · Key üretimi: ${packet.key_source}`;
    byId("download").href = `/api/lab/${lab}`;
    byId("download").download = `lab${lab}.json`;
    byId("packet-view").hidden = false;
  });
  onClick("next-observe", () => step(2));
  onClick("observe", async () => {
    if (lab === 1) {
      firstAttempt = await tryPin(0);
      byId("observation-status").textContent = firstAttempt.plaintext === null ? "0000 bu paketi açmadı." : "İlk adayda bulundu: PIN 0000.";
      byId("observation-output").textContent = "PIN: 0000\nSHA-256(0000) → aday key (hex):\n" + firstAttempt.keyHex
        + "\n\nHedef: indirdiğimiz aynı şifreli paket\n"
        + (firstAttempt.plaintext === null ? "AES-GCM: tag doğrulanmadı → sonraki PIN" : "AES-GCM: tag doğrulandı → not açıldı");
    } else {
      const response = await fetch("/lab/2/preview?format=xml");
      errorPage = await response.text();
      if (![400, 500].includes(response.status)) throw new Error("Beklenen hata yanıtı gelmedi");
      const parsed = new DOMParser().parseFromString(errorPage, "text/html");
      byId("observation-status").textContent = `HTTP ${response.status} · ${keyFromError() ? "Key, hata yanıtında görünüyor." : "Hata yanıtında key yok."}`;
      byId("observation-output").textContent = [...parsed.querySelectorAll("main .eyebrow, main h1, main h2, main pre")]
        .map(item => item.textContent.trim()).join("\n\n") || "Hata içeriği okunamadı";
      byId("preview-row").hidden = false;
    }
    byId("observation").hidden = false;
  });
  onClick("next-run", () => step(3));
  onClick("run", async () => {
    if (lab === 1) { await bruteForce(); return; }
    const keyHex = keyFromError();
    if (!keyHex) { await finish(null, "Hata yanıtında secret key yok. Nonce tek başına şifreli notu açmaya yetmiyor."); return; }
    await finish(await decrypt(fromHex(keyHex)), "Hata yanıtında görünen AES_KEY_HEX kullanıldı. Secret key sızdığı için Alice'in Bob'a gönderdiği not okunabildi.");
  });
  onClick("next-solution", () => step(4));
  onClick("restart", () => location.reload());
}
start();
