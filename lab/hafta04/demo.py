"""Yerel kriptografi dersi: yalnızca sentetik veri, ağ/dosya erişimi yok.

python -X utf8 lab/hafta04/demo.py --json varliklar/hafta04/lab-dogrulama.json
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import platform
import random
import secrets
from datetime import datetime, timezone
from pathlib import Path

import cryptography
from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Bu bloklar slaytlara aynı kaynaktan alınır ve aşağıda doğrudan çalıştırılır.
SNIPPETS = {
    "tiny_dh": '''p, g = 23, 5  # teaching only; too small for security
alice_private, bob_private = 6, 15
alice_public = pow(g, alice_private, p)
bob_public = pow(g, bob_private, p)
alice_shared = pow(bob_public, alice_private, p)
bob_shared = pow(alice_public, bob_private, p)''',
    "predictable_reset": '''import random
server = random.Random(42)  # deliberately known seed
alice_token = server.randrange(100_000, 1_000_000)
bob_token = server.randrange(100_000, 1_000_000)
attacker = random.Random(42)
attacker.randrange(100_000, 1_000_000)  # same known order
predicted = attacker.randrange(100_000, 1_000_000)
token_owners = {alice_token: "Alice", bob_token: "Bob"}
reset_target = token_owners.get(predicted)''',
    "simple_encrypt": '''import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = AESGCM.generate_key(bit_length=256)
nonce = secrets.token_bytes(12)
message = b"Bulusma: 14.30"
sealed = AESGCM(key).encrypt(nonce, message, None)''',
    "simple_decrypt": '''opened = AESGCM(key).decrypt(nonce, sealed, None)
print(opened.decode())  # Bulusma: 14.30''',
    "rsa_example": '''from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
scheme = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),
                      algorithm=hashes.SHA256(), label=None)
sealed = public_key.encrypt(b"Bulusma: 14.30", scheme)
opened = private_key.decrypt(sealed, scheme)''',
    "key_exchange": '''from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
alice = X25519PrivateKey.generate()
bob = X25519PrivateKey.generate()
alice_secret = alice.exchange(bob.public_key())
bob_secret = bob.exchange(alice.public_key())
same_secret = alice_secret == bob_secret''',
    "derive_key": '''from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
def make_key(shared_secret):
    return HKDF(algorithm=hashes.SHA256(), length=32,
                salt=None, info=b"ders4-demo").derive(shared_secret)
alice_key = make_key(alice_secret)
bob_key = make_key(bob_secret)''',
    "caesar": '''alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def caesar(text, key):
    return "".join(alphabet[(alphabet.index(c) + key) % 26]
                   if c in alphabet else c for c in text)
ciphertext = caesar("MERHABA", 3)
plaintext = caesar(ciphertext, -3)''',
    "prng": '''import random
alice = random.Random(42)
bob = random.Random(42)
first = [alice.randrange(100) for _ in range(5)]
again = [bob.randrange(100) for _ in range(5)]
next_alice = alice.randrange(100)
next_bob = bob.randrange(100)''',
    "base64": '''import base64
message = b"amount=100&to=alice"
encoded = base64.b64encode(message)
decoded = base64.b64decode(encoded)''',
    "hash": '''import hashlib
message = b"amount=100&to=alice"
changed = b"amount=900&to=alice"
digest = hashlib.sha256(message).hexdigest()
forged_digest = hashlib.sha256(changed).hexdigest()
accepted = hashlib.sha256(changed).hexdigest() == forged_digest''',
    "hmac": '''import hmac, secrets
key = secrets.token_bytes(32)  # demo için bir kez
message = b"amount=100&to=alice"
tag = hmac.digest(key, message, "sha256")

def valid(body, received_tag):
    expected = hmac.digest(key, body, "sha256")
    return hmac.compare_digest(expected, received_tag)''',
    "encrypt": '''import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = AESGCM.generate_key(bit_length=256)  # demo için bir kez
nonce = secrets.token_bytes(12)  # her şifrelemede yeni
aad = b"record:42|schema:1"
message = b"amount=100&to=alice"
sealed = AESGCM(key).encrypt(nonce, message, aad)''',
    "decrypt": '''from cryptography.exceptions import InvalidTag

def open_record(key, nonce, sealed, expected_aad):
    try:
        return AESGCM(key).decrypt(nonce, sealed, expected_aad)
    except InvalidTag:
        return None  # kaydı kullanma; işlemi reddet''',
    "sign": '''from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
private_key = Ed25519PrivateKey.generate()  # demo anahtarı
public_key = private_key.public_key()
message = b"release=1.2;sha256=example"
signature = private_key.sign(message)
public_key.verify(signature, message)  # başarı: None''',
    "random": '''import random, secrets
first = random.Random(42).getrandbits(128)
again = random.Random(42).getrandbits(128)
token = secrets.token_urlsafe(32)  # 32 bayt rastgelelik''',
}


def xor_bytes(left: bytes, right: bytes) -> bytes:
    assert len(left) == len(right)
    return bytes(a ^ b for a, b in zip(left, right))


def run_demo() -> dict:
    checks = []
    def check(name, actual, expected):
        checks.append({"id": name, "actual": actual, "expected": expected, "passed": actual == expected})
        if actual != expected:
            raise AssertionError(checks[-1])

    contexts = {}
    for name, code in SNIPPETS.items():
        parent = {"decrypt": "encrypt", "simple_decrypt": "simple_encrypt", "derive_key": "key_exchange"}.get(name)
        context = contexts[parent] if parent else {}
        exec(compile(code, f"slide:{name}", "exec"), context)
        contexts[name] = context

    tiny = contexts["tiny_dh"]
    check("tiny_dh_public_values", [tiny["alice_public"], tiny["bob_public"]], [8, 19])
    check("tiny_dh_shared_secret", [tiny["alice_shared"], tiny["bob_shared"]], [2, 2])
    reset = contexts["predictable_reset"]
    check("known_seed_and_order_predict_reset", reset["predicted"], reset["bob_token"])
    check("predicted_token_targets_other_user", reset["reset_target"], "Bob")
    simple = contexts["simple_encrypt"]
    check("simple_encryption_roundtrip", simple["opened"], simple["message"])
    rsa_demo = contexts["rsa_example"]
    check("rsa_oaep_roundtrip", rsa_demo["opened"], b"Bulusma: 14.30")
    exchange = contexts["key_exchange"]
    check("x25519_same_shared_secret", exchange["same_secret"], True)
    check("hkdf_same_encryption_key", exchange["alice_key"] == exchange["bob_key"], True)
    key_nonce = secrets.token_bytes(12)
    encrypted = AESGCM(exchange["alice_key"]).encrypt(key_nonce, b"Bulusma: 14.30", None)
    check("exchange_then_encrypt", AESGCM(exchange["bob_key"]).decrypt(key_nonce, encrypted, None), b"Bulusma: 14.30")

    c = contexts["caesar"]
    check("caesar_shift_three", c["ciphertext"], "PHUKDED")
    check("caesar_roundtrip", c["plaintext"], "MERHABA")
    check("caesar_exhaustive_search", "MERHABA" in [c["caesar"](c["ciphertext"], -k) for k in range(26)], True)
    prng = contexts["prng"]
    check("same_seed_same_sequence", prng["first"], prng["again"])
    check("known_seed_predicts_next", prng["next_alice"], prng["next_bob"])

    b = contexts["base64"]
    check("base64_roundtrip_without_key", b["decoded"], b["message"])
    h = contexts["hash"]
    check("hash_changes_with_message", h["digest"] != h["forged_digest"], True)
    check("untrusted_message_and_hash_replacement_accepted", h["accepted"], True)
    check("trusted_hash_rejects_modified_message", hmac.compare_digest(h["digest"], h["forged_digest"]), False)

    m = contexts["hmac"]
    check("hmac_normal", m["valid"](m["message"], m["tag"]), True)
    check("hmac_modified_message", m["valid"](h["changed"], m["tag"]), False)
    fake = hmac.digest(secrets.token_bytes(32), h["changed"], "sha256")
    check("hmac_wrong_key", m["valid"](h["changed"], fake), False)
    check("hmac_modified_tag", m["valid"](m["message"], bytes(32)), False)
    check("hmac_truncated_tag", m["valid"](m["message"], m["tag"][:-1]), False)
    check("hmac_replay_still_valid", m["valid"](m["message"], m["tag"]), True)
    check("hmac_exact_bytes_required", m["valid"](m["message"] + b" ", m["tag"]), False)

    a = contexts["encrypt"]
    decrypt = a["open_record"]
    args = [a["key"], a["nonce"], a["sealed"], a["aad"]]
    check("aesgcm_normal", decrypt(*args), a["message"])
    check("aesgcm_tag_size", len(a["sealed"]) - len(a["message"]), 16)
    for label, index, replacement in [
        ("ciphertext", 2, bytes([a["sealed"][0] ^ 1]) + a["sealed"][1:]),
        ("tag", 2, a["sealed"][:-1] + bytes([a["sealed"][-1] ^ 1])),
        ("nonce", 1, bytes([a["nonce"][0] ^ 1]) + a["nonce"][1:]),
        ("aad", 3, b"record:99|schema:1"),
        ("key", 0, AESGCM.generate_key(bit_length=256)),
        ("truncated", 2, a["sealed"][:8]),
    ]:
        altered = args.copy()
        altered[index] = replacement
        check(f"aesgcm_reject_{label}", decrypt(*altered) is None, True)
    check("aesgcm_replay_still_decrypts", decrypt(*args), a["message"])

    # KASITLI HATA: aynı anahtar + nonce ile iki şifreleme. Üretimde kullanma.
    # AES-GCM çıktısının son 16 baytı tag'dir; XOR örneği yalnız ciphertext'i alır.
    aes = AESGCM(a["key"])
    first_text, second_text = b"amount=100&to=alice", b"amount=900&to=alice"
    c1 = aes.encrypt(a["nonce"], first_text, a["aad"])[:-16]
    c2 = aes.encrypt(a["nonce"], second_text, a["aad"])[:-16]
    recovered = xor_bytes(xor_bytes(c1, c2), first_text)
    check("nonce_reuse_recovers_second_plaintext", recovered, second_text)
    fresh = aes.encrypt(secrets.token_bytes(12), first_text, a["aad"])
    check("fresh_nonce_changes_ciphertext", fresh != a["sealed"], True)

    s = contexts["sign"]
    check("ed25519_normal", s["public_key"].verify(s["signature"], s["message"]), None)
    for name, key, body in [
        ("modified_message", s["public_key"], s["message"] + b"!"),
        ("wrong_public_key", Ed25519PrivateKey.generate().public_key(), s["message"]),
    ]:
        rejected = False
        try:
            key.verify(s["signature"], body)
        except InvalidSignature:
            rejected = True
        check(f"ed25519_reject_{name}", rejected, True)

    r = contexts["random"]
    check("seeded_prng_repeats", r["first"] == r["again"], True)
    check("token_contains_32_random_bytes", len(base64.urlsafe_b64decode(r["token"] + "=")), 32)

    # Parola özeti örneği: hazır hashlib.scrypt; kendi kripto algoritmamız yok.
    # Bu maliyet yaklaşık 128 MiB bellek gerektirir. Üretim kapasitesi ayrıca ölçülür.
    def password_hash(password, salt):
        return hashlib.scrypt(password, salt=salt, n=2**17, r=8, p=1,
                              maxmem=256 * 1024 * 1024, dklen=32)
    salt_a, salt_b = secrets.token_bytes(16), secrets.token_bytes(16)
    stored = password_hash(b"classroom-example-only", salt_a)
    check("scrypt_correct_password", hmac.compare_digest(stored, password_hash(b"classroom-example-only", salt_a)), True)
    check("scrypt_wrong_password", hmac.compare_digest(stored, password_hash(b"wrong", salt_a)), False)
    check("scrypt_different_salt", stored != password_hash(b"classroom-example-only", salt_b), True)

    def json_value(value):
        return value.decode("ascii") if isinstance(value, bytes) else value
    for row in checks:
        row["actual"], row["expected"] = json_value(row["actual"]), json_value(row["expected"])
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "cryptography": cryptography.__version__,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "all_passed": all(row["passed"] for row in checks), "checks": checks,
        "outputs": {
            "simple_message": simple["message"].decode(),
            "simple_ciphertext_preview": simple["sealed"].hex()[:32] + "...",
            "rsa_ciphertext_preview": rsa_demo["sealed"].hex()[:32] + "...",
            "exchange_equal": exchange["same_secret"],
            "predictable_reset_token": reset["predicted"],
            "caesar_ciphertext": c["ciphertext"],
            "prng_sequence": prng["first"], "prng_next": prng["next_alice"],
            "message": b["message"].decode(), "base64": b["encoded"].decode(),
            "sha256": h["digest"], "changed_sha256": h["forged_digest"],
            "nonce_reuse_recovered": recovered.decode(),
        },
        "limitations": "Yerel sentetik örnekler; kriptografik güvenlik ispatı, istatistiksel RNG testi veya üretim protokolü denetimi değildir. Gizli anahtarlar kaydedilmez.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    options = parser.parse_args()
    report = run_demo()
    for row in report["checks"]:
        print(f"PASS {row['id']}: {row['actual']}")
    if options.json:
        options.json.parent.mkdir(parents=True, exist_ok=True)
        options.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(report['checks'])} kontrol; anahtarlar kaydedilmedi.")
