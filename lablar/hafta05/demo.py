"""Hafta 5 parola saldırıları: yalnızca sentetik veri; ağ ve dış servis erişimi yok.

python -X utf8 lablar/hafta05/demo.py --json varliklar/hafta05/lab-dogrulama.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import veri  # noqa: E402

# Bu bloklar slaytlara aynı kaynaktan alınır ve aşağıda doğrudan çalıştırılır.
SNIPPETS = {
    "old_policy": '''import re
def old_policy(password):
    rules = [len(password) >= 8,
             re.search(r"[A-Z]", password),
             re.search(r"[a-z]", password),
             re.search(r"[0-9]", password),
             re.search(r"[^A-Za-z0-9]", password)]
    return all(rules)''',
    "new_policy": '''def check_new_password(password, blocklist, mfa=False):
    minimum = 8 if mfa else 15           # NIST SP 800-63B-4
    if len(password) < minimum:
        return f"En az {minimum} karakter"
    if len(password) > 256:              # en az 64 karakter kabul edilmeli
        return "En fazla 256 karakter"
    if password.lower() in blocklist:    # parolanın tamamı karşılaştırılır
        return "Yaygın / sızmış parola listesinde"
    return "Kabul"''',
    "mutate": '''def mutate(word):
    yield word                                 # kahve
    yield word.capitalize()                    # Kahve
    for year in ("2024", "2025", "2026"):
        yield word + year                      # kahve2026
        yield word.capitalize() + year + "!"   # Kahve2026!''',
    "crack_unsalted": '''import hashlib
lookup = {}
for word in words:
    for guess in mutate(word):
        digest = hashlib.sha256(guess.encode()).hexdigest()
        lookup[digest] = guess            # tek tablo, bütün kullanıcılar
cracked = {user: lookup[h] for user, h in dump.items() if h in lookup}''',
    "enum_bad": '''def login(username, password):
    user = users.get(username)
    if user is None:
        return "Kullanıcı bulunamadı"
    if not verify(user["hash"], password):
        return "Parola yanlış"
    return "ok"''',
    "enum_good": '''def login(username, password):
    user = users.get(username)
    # Kayıt yoksa da hash hesapla: süre benzer kalsın
    stored = user["hash"] if user else DUMMY_HASH
    ok = verify(stored, password)
    if user and ok:
        return "ok"
    return "Kullanıcı adı veya parola hatalı"''',
    "spray": '''found = []
for password in ["Sonbahar2026!", "Ekim2026!", "Parola1!"]:
    for user in users:              # her hesaba en fazla 3 deneme
        if login(user, password) == "ok":
            found.append((user, password))''',
    "kanon": '''import hashlib
digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
prefix, suffix = digest[:5], digest[5:]
body = get_range(prefix)              # GET /range/{prefix}
counts = dict(line.split(":") for line in body.splitlines())
seen = int(counts.get(suffix, "0"))''',
    "argon2": '''from argon2 import PasswordHasher
ph = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
stored = ph.hash("kirmizi bisiklet sabah cayi")
ph.verify(stored, "kirmizi bisiklet sabah cayi")   # yanlışsa hata
if ph.check_needs_rehash(stored):                  # ayarlar değiştiyse
    stored = ph.hash("kirmizi bisiklet sabah cayi")''',
    "throttle": '''def wait_seconds(failures):
    # İlk 5 hata beklemesiz; sonra 30 sn, 60 sn, ... en fazla 1 saat
    if failures < 5:
        return 0
    return min(30 * 2 ** (failures - 5), 3600)''',
}

BENCH = json.loads((HERE.parent.parent / "varliklar/hafta04/bruteforce-2026.json").read_text(encoding="utf-8")) \
    if (HERE.parent.parent / "varliklar/hafta04/bruteforce-2026.json").is_file() else None


def run_demo() -> dict:
    checks = []

    def check(name, actual, expected):
        checks.append({"id": name, "actual": actual, "expected": expected, "passed": actual == expected})
        if actual != expected:
            raise AssertionError(checks[-1])

    def run(name, context=None):
        context = {} if context is None else context
        exec(compile(SNIPPETS[name], f"slide:{name}", "exec"), context)
        return context

    # Eski politika: kurala uyan tahmin edilebilir parolalar geçer, uzun parola cümlesi kalır.
    old = run("old_policy")["old_policy"]
    old_rows = {pw: old(pw) for pw in ("Parola1!", "Sonbahar2026!", "kirmizi bisiklet sabah cayi", "parola")}
    check("old_policy_accepts_Parola1!", old_rows["Parola1!"], True)
    check("old_policy_accepts_seasonal", old_rows["Sonbahar2026!"], True)
    check("old_policy_rejects_long_passphrase", old_rows["kirmizi bisiklet sabah cayi"], False)

    blocklist = {p.lower() for p in veri.COMMON} | {"ornek.test", "ornekfirma", "ornekfirma2026"}
    new = run("new_policy")["check_new_password"]
    new_rows = {pw: new(pw, blocklist) for pw in ("Parola1!", "Sonbahar2026!", "galatasaray1905", "Galatasaray1905",
                                                   "kirmizi bisiklet sabah cayi")}
    check("new_policy_rejects_short", new_rows["Parola1!"], "En az 15 karakter")
    check("new_policy_rejects_seasonal_short", new_rows["Sonbahar2026!"], "En az 15 karakter")
    check("new_policy_blocklist_case_insensitive", new_rows["Galatasaray1905"], "Yaygın / sızmış parola listesinde")
    check("new_policy_accepts_passphrase", new_rows["kirmizi bisiklet sabah cayi"], "Kabul")
    check("new_policy_mfa_allows_8", new("Parola1!x", blocklist, mfa=True), "Kabul")
    check("new_policy_max_length", new("a" * 257, blocklist), "En fazla 256 karakter")
    check("new_policy_unicode_code_points", new("çğıöşü" * 3, blocklist), "Kabul")

    mut = run("mutate")["mutate"]
    check("mutate_kahve", list(mut("kahve")), ["kahve", "Kahve", "kahve2024", "Kahve2024!", "kahve2025",
                                               "Kahve2025!", "kahve2026", "Kahve2026!"])
    check("mutate_same_as_lab_rules", list(mut("ekim")), list(veri.mutate("ekim")))

    # Salt'sız sızıntı: tek sözlük tablosu bütün kayıtlara uygulanır.
    forum = veri.forum_passwords()
    dump = {user: veri.sha256_hex(pw) for user, pw in forum.items()}
    started = time.perf_counter()
    crack = run("crack_unsalted", {"words": veri.WORDS, "mutate": mut, "dump": dump})
    crack_seconds = time.perf_counter() - started
    cracked = crack["cracked"]
    expected_weak = {user for user, pw in veri.FORUM_DUMP if pw}
    check("unsalted_cracks_dictionary_users", sorted(cracked), sorted(expected_weak))
    check("unsalted_lookup_size", len(crack["lookup"]), len(list(veri.candidates())))
    duplicate_hashes = [h for h, n in Counter(dump.values()).items() if n > 1]
    check("unsalted_identical_hashes_visible", len(duplicate_hashes), 2)  # 123456 ×3, galatasaray ×2

    # Salt + PBKDF2: aynı parola farklı kayıt; doğrulama hâlâ çalışır.
    a = veri.pbkdf2_record("123456")
    b = veri.pbkdf2_record("123456")
    check("salted_same_password_different_hash", a["hash_hex"] != b["hash_hex"], True)
    again = veri.pbkdf2_record("123456", bytes.fromhex(a["salt_hex"]))
    check("salted_verify_same_salt", again["hash_hex"], a["hash_hex"])
    started = time.perf_counter()
    veri.pbkdf2_record("galatasaray", bytes(16))
    pbkdf2_seconds = time.perf_counter() - started
    sha_started = time.perf_counter()
    for i in range(20_000):
        veri.sha256_hex(f"aday{i}")
    sha_rate = 20_000 / (time.perf_counter() - sha_started)

    # Kullanıcı adı numaralandırma: iki farklı mesaj vs tek mesaj.
    users = {"alice": {"hash": "H(alice)"}}
    verify = lambda stored, password: stored == f"H({password})"  # noqa: E731 – sadeleştirilmiş doğrulama
    bad = run("enum_bad", {"users": users, "verify": verify})["login"]
    good = run("enum_good", {"users": users, "verify": verify, "DUMMY_HASH": "H(dummy-never-matches)"})["login"]
    check("enum_bad_reveals_missing_user", bad("mallory", "x"), "Kullanıcı bulunamadı")
    check("enum_bad_reveals_existing_user", bad("alice", "x"), "Parola yanlış")
    check("enum_good_same_message", good("mallory", "x") == good("alice", "x") == "Kullanıcı adı veya parola hatalı", True)
    check("enum_good_valid_login", good("alice", "alice"), "ok")
    check("enum_good_dummy_not_usable", good("mallory", "dummy-never-matches"), "Kullanıcı adı veya parola hatalı")

    # Password spraying: hesap başına 5 hata kilidi tetiklenmez.
    employee_pw = veri.employee_passwords(fixed=False)
    failures = Counter()

    def login(user, password):
        if failures[user] >= 5:
            return "locked"
        if employee_pw[user] == password:
            return "ok"
        failures[user] += 1
        return "fail"
    spray = run("spray", {"users": veri.EMPLOYEES, "login": login})
    check("spray_finds_weak_accounts", sorted(spray["found"]), sorted(veri.WEAK_PASSWORDS.items()))
    check("spray_no_account_locked", max(failures.values()) <= 3, True)
    check("spray_request_count", sum(failures.values()) + len(spray["found"]), 3 * len(veri.EMPLOYEES))
    # Aynı 5 hata kilidi tek hesaba brute force'u durdurur.
    failures.clear()
    brute = [login("alice", f"{n:04d}") for n in range(10)]
    check("lockout_stops_single_account_bruteforce", brute.count("locked"), 5)
    fixed_pw = veri.employee_passwords(fixed=True)
    check("fixed_registration_has_no_spray_passwords", any(fixed_pw[u] in veri.SPRAY_LIST for u in veri.EMPLOYEES), False)

    # k-anonymity: sunucuya yalnız 5 hex karakter gider.
    def get_range(prefix):
        get_range.requests.append(prefix)
        return veri.range_body(prefix)
    get_range.requests = []
    results = {}
    for password in ("Sonbahar2026!", "123456", "kirmizi bisiklet sabah cayi"):
        k = run("kanon", {"password": password, "get_range": get_range})
        results[password] = {"prefix": k["prefix"], "seen": k["seen"], "lines": len(k["body"].splitlines())}
    check("kanon_finds_seasonal", results["Sonbahar2026!"]["seen"], veri.COMMON["sonbahar2026!"])
    check("kanon_finds_123456", results["123456"]["seen"], veri.COMMON["123456"])
    check("kanon_unknown_zero", results["kirmizi bisiklet sabah cayi"]["seen"], 0)
    check("kanon_only_prefix_sent", all(len(p) == 5 for p in get_range.requests), True)
    check("kanon_padding_800_1000", all(800 <= r["lines"] <= 1000 for r in results.values()), True)
    check("kanon_sha1_123456", veri.sha1_upper("123456"), "7C4A8D09CA3762AF61E59520943DC26494F8941B")

    # Argon2id: OWASP asgari parametreleri.
    ag = run("argon2")
    from argon2.exceptions import VerifyMismatchError
    try:
        ag["ph"].verify(ag["stored"], "yanlis parola")
        wrong = "accepted"
    except VerifyMismatchError:
        wrong = "VerifyMismatchError"
    check("argon2_wrong_password", wrong, "VerifyMismatchError")
    check("argon2_parameters_in_record", ag["stored"].startswith("$argon2id$v=19$m=19456,t=2,p=1$"), True)
    check("argon2_salted", ag["ph"].hash("x") != ag["ph"].hash("x"), True)
    from argon2 import PasswordHasher
    check("argon2_old_params_need_rehash", ag["ph"].check_needs_rehash(PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash("x")), True)

    wait = run("throttle")["wait_seconds"]
    check("throttle_values", [wait(n) for n in (0, 4, 5, 6, 7, 12, 50)], [0, 0, 30, 60, 120, 3600, 3600])

    # Aday sayıları ve süre hesapları (Hafta 4'teki 2026 ölçümleriyle).
    sizes = {
        "random8_ascii95": 95 ** 8,
        "mask_Ulllll_dd": 26 ** 6 * 10 ** 2,
        "word100k_year_bang": 100_000 * 80,
        "diceware4": 7776 ** 4,
        "diceware5": 7776 ** 5,
        "random15_lower": 26 ** 15,
    }
    check("diceware4_value", sizes["diceware4"], 3_656_158_440_062_976)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "argon2_cffi": version("argon2-cffi"),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "veri_sha256": hashlib.sha256((HERE / "veri.py").read_bytes()).hexdigest(),
        "all_passed": all(row["passed"] for row in checks), "checks": checks,
        "outputs": {
            "old_policy": old_rows, "new_policy": new_rows,
            "forum_records": len(dump), "forum_cracked": len(cracked), "forum_candidates": len(crack["lookup"]),
            "crack_seconds_local_cpu": round(crack_seconds, 4),
            "duplicate_hash_groups": len(duplicate_hashes),
            "pbkdf2_seconds_one_guess_local_cpu": round(pbkdf2_seconds, 3),
            "sha256_rate_local_python": round(sha_rate),
            "spray_found": len(spray["found"]), "spray_attempts": 3 * len(veri.EMPLOYEES),
            "kanon": results, "candidate_space": sizes,
            "argon2_record_prefix": "$".join(ag["stored"].split("$")[1:4]),
        },
        "limitations": "Yerel sentetik örnekler. Süre ölçümleri bu bilgisayarda tek çekirdek Python içindir; GPU kırma hızı değildir. Gerçek HIBP API'si çağrılmaz.",
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
    print(f"PASS: {len(report['checks'])} kontrol.")
