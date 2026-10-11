"""İki kasıtlı hatalı, yalnız 127.0.0.1 üzerinde çalışan kripto alıştırması."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import secrets
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent


def pin_key(pin: str) -> bytes:
    # KASITLI HATA: hızlı hash, 10.000 olasılığı güçlü bir secret yapmaz.
    return hashlib.sha256(pin.encode("ascii")).digest()


class Challenge:
    def __init__(self, number: int, fixed: bool):
        self.number = number
        self.pin = f"{secrets.randbelow(10_000):04d}" if number == 1 and not fixed else None
        self.key = pin_key(self.pin) if self.pin is not None else AESGCM.generate_key(bit_length=256)
        self.message = f"Bulusma: 14.30 | LAB{number}{{{secrets.token_hex(4)}}}"
        self.nonce = secrets.token_bytes(12)
        self.sealed = AESGCM(self.key).encrypt(self.nonce, self.message.encode(), None)

    def package(self):
        return {
            "algorithm": "AES-256-GCM",
            "key_source": "SHA-256(4 ASCII rakam)" if self.pin is not None else "256 bit rastgele key",
            "nonce_hex": self.nonce.hex(),
            "ciphertext_and_tag_hex": self.sealed.hex(),
        }


def create_server(port=8084, fixed=False):
    challenges = {n: Challenge(n, fixed) for n in (1, 2)}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Sentetik key veya çözülen not terminal loguna düşmesin.

        def send(self, status, body, mime="text/html; charset=utf-8"):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, status, value):
            self.send(status, json.dumps(value, ensure_ascii=False, indent=2), "application/json; charset=utf-8")

        def do_GET(self):
            parsed = urlsplit(self.path)
            path = parsed.path
            if path in ("/", "/lab/1", "/lab/2"):
                page = (ROOT / "lab.html").read_text(encoding="utf-8")
                page = page.replace("{{LAB}}", path[-1] if path != "/" else "0")
                page = page.replace("{{MODE}}", "Düzeltilmiş sürüm" if fixed else "Alıştırma sürümü")
                page = page.replace("{{FIXED}}", "true" if fixed else "false")
                self.send(200, page)
            elif path in ("/lab.css", "/lab.js"):
                mime = "text/css" if path.endswith(".css") else "text/javascript"
                self.send(200, (ROOT / path[1:]).read_bytes(), mime + "; charset=utf-8")
            elif path == "/cozum.py":
                self.send(200, (ROOT / "cozum.py").read_bytes(), "text/plain; charset=utf-8")
            elif path in ("/api/lab/1", "/api/lab/2"):
                self.send_json(200, challenges[int(path[-1])].package())
            elif path == "/lab/2/preview":
                format_name = parse_qs(parsed.query).get("format", ["json"])[0]
                try:
                    if format_name != "json":
                        raise ValueError("Desteklenmeyen onizleme formati")
                    self.send_json(200, challenges[2].package())
                except ValueError:
                    if fixed:
                        self.send(400, '<!doctype html><html lang="tr"><meta charset="utf-8">'
                                  '<link rel="stylesheet" href="/lab.css"><main><a href="/lab/2">← Lab 2</a>'
                                  '<p class="eyebrow">400 · İSTEK HATASI</p><h1>Önizleme oluşturulamadı.</h1>'
                                  '<p>Desteklenen biçim: json.</p></main></html>')
                    else:
                        # Öğrenciye gösterilen debug verisi sadece BU LABIN sentetik key'idir.
                        # Gerçek ortam değişkenlerini veya uygulama dosyalarını okumaz.
                        debug = {"AES_KEY_HEX": challenges[2].key.hex(), "algorithm": "AES-256-GCM"}
                        details = html.escape(traceback.format_exc(limit=1))
                        config = html.escape(json.dumps(debug, indent=2))
                        self.send(500, '<!doctype html><html lang="tr"><meta charset="utf-8">'
                                  '<link rel="stylesheet" href="/lab.css"><main><a href="/lab/2">← Lab 2</a>'
                                  '<p class="eyebrow">500 · DEBUG HATA SAYFASI</p><h1>ValueError</h1>'
                                  f'<pre>{details}</pre><section id="leak"><h2>Uygulama ayarları</h2><pre id="debug-config">{config}</pre></section>'
                                  '<p>Bu sayfadaki hangi değer şifreli notu açmaya yarar?</p></main></html>')
            else:
                self.send_json(404, {"error": "Bulunamadı"})

        def do_POST(self):
            if self.path != "/api/check":
                self.send_json(404, {"error": "Bulunamadı"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError()
                data = json.loads(self.rfile.read(length))
                number, answer = data.get("lab"), data.get("answer")
                if type(number) is not int or number not in challenges or not isinstance(answer, str):
                    raise ValueError()
                accepted = secrets.compare_digest(answer.strip().encode(), challenges[number].message.encode())
            except (ValueError, AttributeError, TypeError):
                self.send_json(400, {"error": "Geçersiz cevap biçimi"})
                return
            self.send_json(200, {"accepted": accepted})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8084)
    parser.add_argument("--fixed", action="store_true", help="Güçlü key ve genel hata yanıtı kullan")
    args = parser.parse_args()
    with create_server(args.port, args.fixed) as server:
        print(f"Kripto lab: http://127.0.0.1:{server.server_port} ({'duzeltilmis' if args.fixed else 'alistirma'})", flush=True)
        print("Durdurmak: Ctrl+C. Yeniden baslatinca paketler ve key'ler degisir.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
