"""Üç kasıtlı hatalı parola alıştırması; yalnız 127.0.0.1 üzerinde, sentetik verilerle çalışır.

python -X utf8 lablar/hafta05/lab.py                  # alıştırma sürümü  → http://127.0.0.1:8086
python -X utf8 lablar/hafta05/lab.py --fixed --port 8087   # düzeltilmiş sürüm
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import secrets
import sys
import threading
import time
from collections import Counter, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import veri  # noqa: E402

LOCK_AFTER = 5


def scrypt_record(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    # Online lab için küçük scrypt maliyeti (~ onlarca ms): her giriş gerçekten bir hash hesaplar.
    salt = salt or secrets.token_bytes(16)
    return salt, hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)


def wait_seconds(failures: int) -> int:
    if failures < LOCK_AFTER:
        return 0
    return min(30 * 2 ** (failures - LOCK_AFTER), 3600)


class State:
    def __init__(self, fixed: bool):
        self.fixed = fixed
        self.lock = threading.Lock()
        self.employee_pw = veri.employee_passwords(fixed)
        self.accounts = {user: scrypt_record(pw) for user, pw in self.employee_pw.items()}
        self.dummy = scrypt_record(secrets.token_urlsafe(24))
        self.failures = Counter()
        self.last_failure = {}
        forum = veri.forum_passwords()
        self.forum_pw = forum
        if fixed:
            self.dump = [{"user": user, **veri.pbkdf2_record(pw)} for user, pw in forum.items()]
        else:
            self.dump = [{"user": user, "sha256_hex": veri.sha256_hex(pw)} for user, pw in forum.items()]
        self.server_log = deque(maxlen=12)

    def reset_lab1(self):
        with self.lock:
            self.failures.clear()
            self.last_failure.clear()

    def login(self, username: str, password: str):
        """(status, body). Alıştırma sürümü farklı mesaj ve sert kilit; düzeltilmiş sürüm tek mesaj ve artan bekleme."""
        with self.lock:
            failures = self.failures[username]
            if username in self.accounts:
                if not self.fixed and failures >= LOCK_AFTER:
                    return 423, {"error": "Hesap kilitlendi"}
                remaining = self.last_failure.get(username, 0) + wait_seconds(failures) - time.time()
                if self.fixed and remaining > 0:
                    return 429, {"error": "Çok fazla deneme. Daha sonra tekrar deneyin.", "retry_after": int(remaining) + 1}
        record = self.accounts.get(username)
        if record is None and not self.fixed:
            # KASITLI HATA: kayıtsız kullanıcıda hash hesaplanmaz ve mesaj farklıdır.
            return 401, {"error": "Kullanıcı bulunamadı"}
        salt, stored = record or self.dummy
        ok = hmac.compare_digest(scrypt_record(password, salt)[1], stored) and record is not None
        if ok:
            with self.lock:
                self.failures[username] = 0
            return 200, {"ok": True, "message": f"Hoş geldin, {username}"}
        if record is not None:
            with self.lock:
                self.failures[username] += 1
                self.last_failure[username] = time.time()
        if self.fixed:
            return 401, {"error": "Kullanıcı adı veya parola hatalı"}
        return 401, {"error": "Parola yanlış"}


def create_server(port=8086, fixed=False):
    state = State(fixed)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Parola denemeleri terminal loguna düşmesin; Lab 3 kendi gösterim logunu tutar.

        def send(self, status, body, mime="text/html; charset=utf-8", headers=None):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, status, value, headers=None):
            self.send(status, json.dumps(value, ensure_ascii=False, indent=2), "application/json; charset=utf-8", headers)

        def read_json(self, limit=65536):
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= limit:
                raise ValueError("length")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("object")
            return data

        def do_GET(self):
            parsed = urlsplit(self.path)
            path = parsed.path
            if path in ("/", "/lab/1", "/lab/2", "/lab/3"):
                page = (ROOT / "lab.html").read_text(encoding="utf-8")
                page = page.replace("{{LAB}}", path[-1] if path != "/" else "0")
                page = page.replace("{{MODE}}", "Düzeltilmiş sürüm" if fixed else "Alıştırma sürümü")
                page = page.replace("{{FIXED}}", "true" if fixed else "false")
                self.send(200, page)
            elif path in ("/lab.css", "/lab.js", "/simulasyon.css", "/simulasyon.js", "/simulasyon-md5.js", "/simulasyon-worker.js"):
                mime = "text/css" if path.endswith(".css") else "text/javascript"
                self.send(200, (ROOT / path[1:]).read_bytes(), mime + "; charset=utf-8")
            elif path == "/simulasyon":
                self.send(200, (ROOT / "simulasyon.html").read_bytes())
            elif path == "/cozum.py":
                self.send(200, (ROOT / "cozum.py").read_bytes(), "text/plain; charset=utf-8")
            elif path == "/api/lab1/info":
                self.send_json(200, {"site": "ornek.test", "guessed_names": veri.GUESSED_NAMES,
                                     "spray_list": veri.SPRAY_LIST, "lock_after": LOCK_AFTER,
                                     "policy": "Tek mesaj + artan bekleme + kayıtta yaygın parola listesi" if fixed
                                     else "Farklı hata mesajları + 5 hatada hesap kilidi"})
            elif path == "/api/lab2/dump":
                self.send_json(200, {"site": "forum.ornek.test (eski yedek)",
                                     "format": ("pbkdf2_sha256 · 600.000 tur · kayıt başına 16 bayt salt" if fixed
                                                else "sha256(parola) · salt yok"),
                                     "records": state.dump})
            elif path == "/api/lab2/wordlist":
                self.send_json(200, {"words": veri.WORDS, "years": list(veri.YEARS),
                                     "rules": ["kelime", "Kelime", "kelime+yıl", "Kelime+yıl+!"]})
            elif path == "/api/lab3/check" and not fixed:
                # KASITLI HATA: parolanın kendisi URL'de; sunucu ve proxy loglarına yazılır.
                password = parse_qs(parsed.query).get("password", [""])[0]
                state.server_log.append(f"GET /api/lab3/check?password={quote(password, safe='')}")
                count = veri.COMMON.get(password.lower(), 0)
                self.send_json(200, {"found": count > 0, "count": count})
            elif re.fullmatch(r"/api/lab3/range/[0-9A-Fa-f]{5}", path):
                state.server_log.append(f"GET {path}")
                self.send(200, veri.range_body(path[-5:]), "text/plain; charset=utf-8")
            elif path == "/api/lab3/log":
                self.send_json(200, {"lines": list(state.server_log)})
            else:
                self.send_json(404, {"error": "Bulunamadı"})

        def do_POST(self):
            path = urlsplit(self.path).path
            try:
                data = self.read_json()
            except (ValueError, json.JSONDecodeError):
                self.send_json(400, {"error": "Geçersiz istek"})
                return
            if path == "/api/login":
                username, password = data.get("username"), data.get("password")
                if not isinstance(username, str) or not isinstance(password, str) or len(password) > 256:
                    self.send_json(400, {"error": "Geçersiz istek"})
                    return
                status, body = state.login(username.strip().lower(), password)
                headers = {"Retry-After": str(body["retry_after"])} if status == 429 else None
                self.send_json(status, body, headers)
            elif path == "/api/lab1/reset":
                state.reset_lab1()
                self.send_json(200, {"reset": True})
            elif path == "/api/lab3/reset-log":
                state.server_log.clear()
                self.send_json(200, {"reset": True})
            elif path == "/api/check":
                pairs = data.get("pairs")
                source = {1: state.employee_pw, 2: state.forum_pw}.get(data.get("lab"))
                if source is None or not isinstance(pairs, list) or len(pairs) > 100:
                    self.send_json(400, {"error": "Geçersiz istek"})
                    return
                correct = sum(1 for pair in pairs if isinstance(pair, list) and len(pair) == 2
                              and all(isinstance(x, str) for x in pair)
                              and secrets.compare_digest(source.get(pair[0], "\0").encode(), pair[1].encode()))
                self.send_json(200, {"checked": len(pairs), "correct": correct})
            else:
                self.send_json(404, {"error": "Bulunamadı"})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.state = state
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8086)
    parser.add_argument("--fixed", action="store_true", help="Tek hata mesajı, artan bekleme, yaygın parola listesi, salt + PBKDF2, k-anonymity")
    args = parser.parse_args()
    print("Sentetik kullanıcılar hazırlanıyor (PBKDF2/scrypt birkaç saniye sürebilir)...", flush=True)
    with create_server(args.port, args.fixed) as server:
        print(f"Parola lab: http://127.0.0.1:{server.server_port} ({'duzeltilmis' if args.fixed else 'alistirma'})", flush=True)
        print("Durdurmak: Ctrl+C. Yeniden baslatinca rastgele parolalar ve salt'lar degisir.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
