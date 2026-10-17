# Ders 5 — Parola saldırıları: adım adım gösterim

Derste **yalnız tarayıcıdaki düğmelere basarak** üç örneği göstereceğiz. Kod yazma adımı yok. Her lab dört bölümden oluşur: üç gösterim adımı ve **açıklamalı çözüm**. Sonraki adım, önceki düğmeye basılınca açılır.

## Ders öncesi hazırlık

Python 3.10+ kullanın. Depo kökünde bir kez kurun:

```powershell
python -m pip install -r lablar/hafta05/requirements.txt
```

İlk terminalde alıştırma sürümünü, ikinci terminalde düzeltilmiş sürümü başlatın:

```powershell
python -X utf8 lablar/hafta05/lab.py
```

```powershell
python -X utf8 lablar/hafta05/lab.py --fixed --port 8087
```

[Alıştırma sürümü](http://127.0.0.1:8086) · [Düzeltilmiş sürüm](http://127.0.0.1:8087). Güncel Edge veya Chrome ile açın. Başlangıçta sentetik kullanıcılar için hash'ler hesaplanır (birkaç saniye). Sunucuyu durdurmak için Ctrl+C.

Uygulama yalnız 127.0.0.1 üzerinde çalışır. Bütün kullanıcılar, parolalar ve "görülme sayıları" sentetiktir; gerçek Have I Been Pwned API'si çağrılmaz. Yeniden başlatınca rastgele parolalar ve salt'lar değişir. Bir labı baştan göstermek için **Baştan göster** düğmesini kullanın; Lab 1 sayaçları 1. adımda sıfırlanır.

## Parola kırma simülatörü

Lab sunucusu çalışırken [http://127.0.0.1:8086/simulasyon](http://127.0.0.1:8086/simulasyon) adresini açın (ana sayfada da bağlantısı var). Lab'larla aynı sunucu ve aynı güvenlik başlıkları kullanılır; ek kurulum gerekmez. Beş sekme: hash (MD5, SHA-1, SHA-256, salt'lı PBKDF2), parolanın kırma süresi (2026 GPU hızlarıyla), tarayıcıda canlı brute force, sızan forum yedeğine sözlük saldırısı ve giriş sayfasına brute force / password spraying / credential stuffing (hesap kilidi, toplam hata alarmı, sızmış parola kontrolü ve MFA açılıp kapatılabilir). Bütün hesaplar tarayıcıda yapılır, girilen parola hiçbir yere gönderilmez.

## Lab 1 — Kilit var, yine de girdik (online)

**Senaryo:** ornek.test'in giriş sayfası 5 hatalı denemede hesabı kilitliyor. Saldırgan ekip sayfasından 48 olası kullanıcı adı çıkarmış.

| Adım | Düğme | Gösterilecek sonuç |
| --- | --- | --- |
| 1 | **48 kullanıcı adını dene** | Alıştırma: "Kullanıcı bulunamadı" / "Parola yanlış" ayrımı ve süre farkı → 40 kayıtlı hesap. Düzeltilmiş: tek mesaj, benzer süre. |
| 2 | **alice için 8 parola dene** | 5. hatadan sonra 423 (kilit) veya 429 + Retry-After (artan bekleme). Kilit tek hesaba brute force'u durdurur. |
| 3 | **3 parola × hesapları dene** | Alıştırma: Sonbahar2026! / Ekim2026! kullanan 4 hesaba girilir, yeni kilit yok. Düzeltilmiş: 0 hesap; bu parolalar kayıtta reddedilmişti. |
| 4 | **Çözümü açıkla** | Tek mesaj + sahte hash, artan bekleme, kayıtta yaygın/sızmış parola listesi, MFA. |

## Lab 2 — Sızan forum yedeği (offline)

**Senaryo:** forum.ornek.test'in eski yedeği sızdı. Kilit ve bekleme yok; denemeler tarayıcıda yapılır, sunucuya aday gönderilmez.

| Adım | Düğme | Gösterilecek sonuç |
| --- | --- | --- |
| 1 | **Sızan yedeği göster** | Alıştırma: salt'sız SHA-256, aynı hash'i paylaşan kayıtlar. Düzeltilmiş: PBKDF2-HMAC-SHA256 600.000 tur + kayıt başına salt; tekrar yok. |
| 2 | **Aday listesini hazırla** | 60 kelime × kurallar (Kelime, kelime+yıl, Kelime+yıl+!) = 479 aday. |
| 3 | **Bütün adayları dene / 12 saniye dene ve ölç** | Alıştırma: 16 / 24 kayıt milisaniyelerde. Düzeltilmiş: tarayıcıdaki hız ölçülür, tüm sözlük için süre tahmin edilir; 123456 kullanan 3 kayıt yine de ilk saniyelerde düşer. |
| 4 | **Çözümü açıkla** | Salt + yavaş hash birlikte; maliyet zayıf parolayı güçlü yapmaz. Yeni sistemde Argon2id. |

Tarayıcıda Argon2 olmadığı için düzeltilmiş sürüm PBKDF2 kullanır (OWASP'ın FIPS seçeneği). Ölçülen hız yalnız bu tarayıcıya aittir; GPU hızlarıyla karşılaştırmayın.

## Lab 3 — Parolayı göndermeden sor (sızıntı kontrolü)

**Senaryo:** Kayıt formu yeni parolanın sızıntı listesinde olup olmadığını bir servise soruyor.

| Adım | Düğme | Gösterilecek sonuç |
| --- | --- | --- |
| 1 | Bir örnek parola seç → **Seçili parolayı hazırla** | Alıştırma: parola URL'de gidecek. Düzeltilmiş: SHA-1 özeti; yalnız ilk 5 hex karakter gidecek. |
| 2 | **İsteği gönder** | Düzeltilmiş: 800–1000 satır (dolgu dahil) döner, eşleşme tarayıcıda bulunur. |
| 3 | **Sunucu logunu göster** | Alıştırma: logda parolanın kendisi. Düzeltilmiş: yalnız prefix. |
| 4 | **Çözümü açıkla** | k-anonymity; HIBP Pwned Passwords range API ile aynı yöntem. |

Gerçek parolanızı bu forma yazmayın; yalnız hazır örnekler kullanılır.

## Hazır çözüm kodları

Açıklamalı çözüm her labın 4. adımındadır. Aynı örneklerin bağımsız Python çözümü [cozum.py](cozum.py) dosyasındadır:

```powershell
python -X utf8 lablar/hafta05/cozum.py 1
python -X utf8 lablar/hafta05/cozum.py 2
python -X utf8 lablar/hafta05/cozum.py 3
python -X utf8 lablar/hafta05/cozum.py 2 --port 8087 --seconds 15
```

## Slaytlardaki küçük örnekler

```powershell
python -X utf8 lablar/hafta05/demo.py
```

39 kontrol: eski ve yeni parola politikası, sözlük kuralları, salt'sız hash kırma, salt'lı PBKDF2, user enumeration, password spraying ve hesap kilidi, k-anonymity, Argon2id (argon2-cffi) ve artan bekleme.

Kaynaklar: [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html), [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [OWASP Credential Stuffing Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html), [HIBP API v3](https://haveibeenpwned.com/API/v3).
