"""Ders 4 lab çözümleri. Yalnız 127.0.0.1'deki sentetik labı okur.

python lab/hafta04/cozum.py 1
python lab/hafta04/cozum.py 2
Düzeltilmiş sürüm için aynı komutlara --port 8085 ekleyin.
"""
import argparse
import hashlib
import html
import json
import re
from urllib.error import HTTPError
from urllib.request import urlopen

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def fetch(port, path):
    try:
        response = urlopen(f"http://127.0.0.1:{port}{path}", timeout=5)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.read().decode("utf-8")


def decrypt_package(package, key):
    return AESGCM(key).decrypt(bytes.fromhex(package["nonce_hex"]),
                               bytes.fromhex(package["ciphertext_and_tag_hex"]),
                               None).decode()


def brute_force(package):
    # Paketi bir kez indiririz; adaylar sunucuya gönderilmez.
    for number in range(10_000):
        pin = f"{number:04d}"
        key = hashlib.sha256(pin.encode("ascii")).digest()
        try:
            return {"pin": pin, "attempts": number + 1, "plaintext": decrypt_package(package, key)}
        except InvalidTag:
            # Bu aday paketi doğrulamadı; diğer hataları gizlemiyoruz.
            continue
    return {"pin": None, "attempts": 10_000, "plaintext": None}


def leaked_key(error_page):
    match = re.search(r'"AES_KEY_HEX":\s*"([0-9a-f]{64})"', html.unescape(error_page))
    return bytes.fromhex(match[1]) if match else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lab", type=int, choices=(1, 2))
    parser.add_argument("--port", type=int, default=8084)
    args = parser.parse_args()
    status, body = fetch(args.port, f"/api/lab/{args.lab}")
    if status != 200:
        parser.error("Lab paketi alınamadı.")
    package = json.loads(body)
    if args.lab == 1:
        result = brute_force(package)
        print(f"Denenen aday: {result['attempts']} | PIN: {result['pin']}")
        print(result["plaintext"] or "10.000 adayın hiçbiri notu açmadı.")
    else:
        _, page = fetch(args.port, "/lab/2/preview?format=xml")
        key = leaked_key(page)
        print(decrypt_package(package, key) if key else "Hata yanıtında key yok; bu yoldan çözülemiyor.")
