"""Hafta 5 için sentetik veri: kullanıcılar, yaygın parola listesi ve sözlük.

Bütün kişiler ve sayılar uydurmadır. Yaygın parolaların sırası NCSC 2019 listesinden
esinlenir; buradaki tekrar sayıları gerçek sızıntı istatistiği DEĞİLDİR.
"""
from __future__ import annotations

import hashlib
import secrets

# Sentetik "sızıntı korpusu": parola → sahte tekrar sayısı (gösterim için).
COMMON = {
    "123456": 23_174, "123456789": 7_671, "qwerty": 3_810, "password": 3_645, "1111111": 3_120,
    "12345678": 2_938, "abc123": 2_877, "parola": 1_904, "sifre123": 1_377, "galatasaray": 1_215,
    "fenerbahce": 1_188, "besiktas": 1_022, "trabzonspor": 811, "istanbul34": 767, "ankara06": 702,
    "galatasaray1905": 655, "fenerbahce1907": 640, "iloveyou": 612, "admin": 590, "letmein": 433,
    "welcome1": 401, "parola1!": 388, "qwerty123!": 356, "sonbahar2026!": 214, "ekim2026!": 187,
    "yaz2026!": 166, "kahve2019!": 92, "sifre": 1_655, "000000": 1_590, "asdasd": 1_133,
}

# Sözlük saldırısının taban kelimeleri (Lab 2 ve demo).
WORDS = [
    "123456", "password", "qwerty", "parola", "sifre", "admin", "letmein", "iloveyou",
    "galatasaray", "fenerbahce", "besiktas", "trabzonspor", "istanbul", "ankara", "izmir",
    "sonbahar", "ilkbahar", "kis", "yaz", "ekim", "kasim", "kahve", "cay", "simit", "deniz",
    "gunes", "ayse", "mehmet", "fatma", "ahmet", "zeynep", "ali", "elif", "can", "kedi",
    "kopek", "aslan", "kartal", "karadeniz", "anadolu", "turkiye", "bilgisayar", "yazilim",
    "okul", "universite", "ogrenci", "merhaba", "sevgi", "ask", "hayat", "dunya", "mavi",
    "kirmizi", "yesil", "siyah", "beyaz", "futbol", "basket", "muzik", "oyun",
]

YEARS = ("2024", "2025", "2026")


def mutate(word):
    """Sözlük kelimesinden politika uyumlu adaylar: hashcat kurallarının küçük bir benzeri."""
    yield word
    yield word.capitalize()
    for year in YEARS:
        yield word + year
        yield word.capitalize() + year + "!"


def candidates():
    seen = set()
    for word in WORDS:
        for guess in mutate(word):
            if guess not in seen:
                seen.add(guess)
                yield guess


# Lab 1: ornek.test çalışanları. Dördü mevsimlik / yaygın parola kullanıyor.
EMPLOYEES = [
    "alice", "bob", "ayse.kaya", "mehmet.demir", "zeynep.celik", "ahmet.sahin", "elif.yildiz",
    "mustafa.aydin", "fatma.ozturk", "emre.arslan", "merve.dogan", "burak.kilic", "seda.aslan",
    "can.ozdemir", "deniz.koc", "ece.kurt", "kerem.polat", "ipek.erdem", "onur.yalcin", "gizem.aksoy",
    "baris.tekin", "derya.cetin", "serkan.kara", "pinar.gunes", "tolga.bulut", "selin.korkmaz",
    "umut.sari", "irem.akin", "cem.yavuz", "esra.tas", "hakan.uysal", "nazli.ates", "volkan.bozkurt",
    "asli.kaplan", "okan.aktas", "berna.ucar", "sinan.cakir", "gul.oral", "tarik.duman", "yasemin.ekinci",
]
WEAK_PASSWORDS = {"ece.kurt": "Sonbahar2026!", "tolga.bulut": "Sonbahar2026!",
                  "irem.akin": "Ekim2026!", "okan.aktas": "Sonbahar2026!"}
# Ekip sayfasından tahmin edilen adlar: 40 gerçek hesap + 8 eski / yanlış ad.
GUESSED_NAMES = EMPLOYEES[:20] + ["selim.acar", "ayca.toprak", "levent.isik", "nur.karaca"] + EMPLOYEES[20:] + [
    "admin", "test", "destek", "info"]
SPRAY_LIST = ["Sonbahar2026!", "Ekim2026!", "Parola1!"]


def employee_passwords(fixed: bool):
    """Düzeltilmiş sürümde kayıt kontrolü yaygın parolaları baştan reddetmişti."""
    result = {}
    for user in EMPLOYEES:
        weak = WEAK_PASSWORDS.get(user)
        result[user] = weak if weak and not fixed else "-".join(secrets.token_urlsafe(6) for _ in range(3))
    return result


# Lab 2: eski bir forumun sızan yedeği. 16 kayıt sözlükten, 8 kayıt rastgele.
FORUM_DUMP = [
    ("forum_alice", None), ("kartal34", "Kartal2025!"), ("sari_kanarya", "fenerbahce"),
    ("cimbom1905", "galatasaray"), ("aslan_kral", "galatasaray"), ("deniz_k", "Deniz2026!"),
    ("bob_forum", None), ("ogr_elif", "123456"), ("ogr_can", "123456"), ("ogr_ali", "123456"),
    ("kahvesever", "Kahve2024!"), ("mavi_gok", None), ("admin_eski", "admin"), ("yazilimci", "yazilim2025"),
    ("kara_kartal", "besiktas"), ("ekim_ruzgari", None), ("simitci", "Simit"), ("cay_ocagi", None),
    ("sonbahar_k", "Sonbahar2026!"), ("ilkbahar", None), ("misafir", "qwerty"), ("gezgin", None),
    ("oyuncu", "oyun2024"), ("anadolu_k", None),
]


def forum_passwords():
    return {user: password or secrets.token_urlsafe(12) for user, password in FORUM_DUMP}


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


PBKDF2_ITERATIONS = 600_000  # OWASP: PBKDF2-HMAC-SHA256


def pbkdf2_record(password: str, salt: bytes | None = None) -> dict:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, 32)
    return {"algorithm": "pbkdf2_sha256", "iterations": PBKDF2_ITERATIONS,
            "salt_hex": salt.hex(), "hash_hex": digest.hex()}


def sha1_upper(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest().upper()


def range_body(prefix: str, corpus=COMMON, padding=True) -> str:
    """Pwned Passwords range yanıtının yerel taklidi: SUFFIX:COUNT satırları.

    Dolgu satırları rastgele suffix'ler ve 0 sayısıyla gelir (HIBP Add-Padding gibi, 800–1000 satır).
    """
    prefix = prefix.upper()
    lines = []
    for password, count in corpus.items():
        for variant in {password, password.capitalize(), password[:1].upper() + password[1:]}:
            digest = sha1_upper(variant)
            if digest.startswith(prefix):
                lines.append(f"{digest[5:]}:{count}")
    lines = sorted(set(lines))
    if padding:
        target = 800 + secrets.randbelow(201)
        while len(lines) < target:
            lines.append(f"{secrets.token_hex(18)[:35].upper()}:0")
        secrets.SystemRandom().shuffle(lines)
    return "\n".join(lines)
