importScripts("/simulasyon-md5.js");
// Brute force işçisi: karakter kümesindeki bütün adayları sırayla MD5'ler.
onmessage = (e) => {
  const { charset, length, target } = e.data;
  const cs = new TextEncoder().encode(charset), n = cs.length;
  const total = Math.pow(n, length);
  const idx = new Uint8Array(length), bytes = new Uint8Array(length);
  for (let i = 0; i < length; i++) bytes[i] = cs[0];
  const w = new Int32Array(16), out = new Int32Array(4);
  let tried = 0, last = performance.now();
  const t0 = last;
  while (tried < total) {
    fillBlock(bytes, length, w); md5Block(w, out); tried++;
    if (out[0] === target[0] && out[1] === target[1] && out[2] === target[2] && out[3] === target[3]) {
      postMessage({ done: true, found: new TextDecoder().decode(bytes), tried, total, ms: performance.now() - t0 }); return;
    }
    // Sağdan sola sayaç: aaaa → aaab → …
    let p = length - 1;
    while (p >= 0) { idx[p]++; if (idx[p] < n) { bytes[p] = cs[idx[p]]; break; } idx[p] = 0; bytes[p] = cs[0]; p--; }
    if ((tried & 0x3ffff) === 0) {
      const now = performance.now();
      if (now - last > 200) { last = now; postMessage({ tried, total, ms: now - t0, cur: new TextDecoder().decode(bytes) }); }
    }
  }
  postMessage({ done: true, found: null, tried, total, ms: performance.now() - t0 });
};
