// MD5 (tek blok, ≤ 55 bayt): sayfa ve brute force işçisi ortak kullanır.
const S = [7,12,17,22,7,12,17,22,7,12,17,22,7,12,17,22,5,9,14,20,5,9,14,20,5,9,14,20,5,9,14,20,4,11,16,23,4,11,16,23,4,11,16,23,4,11,16,23,6,10,15,21,6,10,15,21,6,10,15,21,6,10,15,21];
const K = new Int32Array(64);
for (let i = 0; i < 64; i++) K[i] = Math.floor(Math.abs(Math.sin(i + 1)) * 4294967296) | 0;
const G = new Uint8Array(64);
for (let i = 0; i < 64; i++) G[i] = i < 16 ? i : i < 32 ? (5 * i + 1) % 16 : i < 48 ? (3 * i + 5) % 16 : (7 * i) % 16;
// Tek blokluk mesaj (en fazla 55 bayt) için MD5; w: 16 kelimelik hazır blok.
function md5Block(w, out) {
  let a = 0x67452301, b = 0xefcdab89 | 0, c = 0x98badcfe | 0, d = 0x10325476;
  for (let i = 0; i < 64; i++) {
    let f;
    if (i < 16) f = (b & c) | (~b & d);
    else if (i < 32) f = (d & b) | (~d & c);
    else if (i < 48) f = b ^ c ^ d;
    else f = c ^ (b | ~d);
    f = (f + a + K[i] + w[G[i]]) | 0;
    a = d; d = c; c = b;
    b = (b + ((f << S[i]) | (f >>> (32 - S[i])))) | 0;
  }
  out[0] = (a + 0x67452301) | 0; out[1] = (b + (0xefcdab89 | 0)) | 0;
  out[2] = (c + (0x98badcfe | 0)) | 0; out[3] = (d + 0x10325476) | 0;
}
function fillBlock(bytes, len, w) {
  w.fill(0);
  for (let i = 0; i < len; i++) w[i >> 2] |= bytes[i] << ((i & 3) * 8);
  w[len >> 2] |= 0x80 << ((len & 3) * 8);
  w[14] = len * 8;
}
function md5Hex(str) {
  const bytes = new TextEncoder().encode(str);
  if (bytes.length > 55) return null;
  const w = new Int32Array(16), out = new Int32Array(4);
  fillBlock(bytes, bytes.length, w); md5Block(w, out);
  let hex = "";
  for (const v of out) for (let k = 0; k < 4; k++) hex += ((v >>> (k * 8)) & 255).toString(16).padStart(2, "0");
  return hex;
}
