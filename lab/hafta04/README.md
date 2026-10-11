# Ders 4 — Alice ve Bob: adım adım kripto gösterimi

Derste **yalnız tarayıcıdaki düğmelere basarak** iki örneği göstereceğiz. Kod yazma, TODO tamamlama veya cevap yapıştırma adımı yok. Her lab dört bölümden oluşur: **paket → ilk gözlem → notu aç → açıklamalı çözüm**. Sonraki bölüm, ilgili düğmeye basılınca açılır.

## Ders öncesi hazırlık

Python 3.10+ kullanın. Depo kökünde bir kez kurun:

```powershell
python -m pip install -r lab/hafta04/requirements.txt
```

İlk terminalde hatalı sürümü, ikinci terminalde düzeltilmiş sürümü başlatın:

```powershell
python -X utf8 lab/hafta04/lab.py
```

```powershell
python -X utf8 lab/hafta04/lab.py --fixed --port 8085
```

[Hatalı sürüm](http://127.0.0.1:8084) · [Düzeltilmiş sürüm](http://127.0.0.1:8085). Güncel Edge veya Chrome ile açın. İki terminal açık kalsın; derste yalnız tarayıcı kullanılacak. Sunucuyu durdurmak için Ctrl+C.

Uygulama yalnız 127.0.0.1 üzerinde çalışır. Bütün notlar ve key'ler sentetiktir. Yeniden başlatınca paketler, PIN ve key'ler değişir. Gösterimi aynı paketle tekrarlamak için sayfadaki **Baştan göster** düğmesini kullanın.

İki labda da ek doğrulama verisi (AAD) kullanılmaz; Python çağrılarındaki son argüman bu yüzden `None` olur. Paket nonce ve ciphertext/tag içerir. AES-GCM, şifreli verinin bütünlüğünü tag ile doğrulamaya devam eder.

## Lab 1 — 10.000 olasılık

**Senaryo:** Alice, Bob'a şifreli bir not gönderiyor. Uygulama AES key'ini `SHA-256(4 haneli PIN)` ile üretmiş. Bu kasıtlı hatadır.

İlk adımda **Uygulama bu paketi hangi kodla üretti?** bölümünü açın. `pin → SHA-256 → key → AES-GCM encrypt` akışı hazır kodla gösterilir. Gerçek PIN ekranda verilmez. İkinci adımda olası PIN'ler (`0000`, `0001`, …, `9999`) ve ilk adayın ürettiği key görünür.

Üçüncü adımdaki **Brute force'u nereye uyguluyoruz?** görseli hedefi açıklar: `GET /api/lab/1` ile alınan aynı ciphertext/tag ve nonce üzerinde tarayıcıda decrypt denemeleri yapılır. İstek sayaçları paket indirmeyi ve yalnız başarıda gönderilen sonuç kontrolünü gösterir. **Hazır deneme döngüsünü göster** bölümü bu işlemin kısa Python karşılığını açar; derste kod yazılmaz.

| Adım | Basılacak düğme | Gösterilecek sonuç / anlatılacak nokta |
| --- | --- | --- |
| 1 | **Şifreli paketi göster** | Paket elimizde; secret key yok. JSON ayrıntısı istenirse açılabilir. |
| 2 | **2. adıma geç → 0000 PIN'ini dene** | Tek bir PIN'den aday key üretilir. AES-GCM paketi doğrulamazsa not açılmaz. PIN gerçekten 0000 ise ilk adayda bulunur. |
| 3 | **3. adıma geç → Adayları tara** | Kalan adaylar tarayıcıda gerçekten denenir. Sayaç, örnek denemeler, bulunan PIN ve çözülen not gösterilir. Not sunucudaki kayıtla otomatik doğrulanır. |
| 4 | **4. Çözümü açıkla** | Hazır açıklama ve düzeltme ekrana gelir. Ardından düzeltilmiş sürüm bağlantısını açın. |

**Çözüm:** Her sayı dört ASCII rakama çevrilir (`0000`…`9999`). SHA-256 özeti aday key olur; AES-GCM ile nonce ve ciphertext/tag kullanılarak çözme denenir. Doğrulama başarısızsa sıradaki adaya geçilir. Doğru adayda not açılır. Deneme sayısı, PIN'in sayısal değeri + 1'dir. İlk adımda denenen 0000 yeniden hesaplanmaz.

**Çıkarım:** SHA-256 çıktısı 256 bit olsa da yalnız 10.000 farklı PIN vardır. Algoritma adı, zayıf key üretimini düzeltmez.

**Düzeltilmiş sürümde:** Aynı düğmelere basın. Key güvenli rastgele 256 bit değerden üretilir; 10.000 PIN adayı biter ve not açılamaz. Bu gözlem, yalnız bu dar PIN yönteminin başarısızlığını gösterir.

## Lab 2 — Fazla konuşan hata

**Senaryo:** Alice'in Bob'a gönderdiği not güçlü bir rastgele key ile şifrelenmiş. Ancak uygulamanın hata sayfası fazla bilgi veriyor.

| Adım | Basılacak düğme | Gösterilecek sonuç / anlatılacak nokta |
| --- | --- | --- |
| 1 | **Şifreli paketi göster** | Nonce ve şifreli içerik var; key yok. |
| 2 | **2. adıma geç → XML önizlemeyi aç** | Gerçek HTTP 500 yanıtı ekranda gösterilir. Ayarlardaki `AES_KEY_HEX` değerini işaret edin. İstenirse aynı hata ayrı sekmede açılır. |
| 3 | **3. adıma geç → Key'i bul ve notu çöz** | Hazır çözüm, key'i bu hata yanıtından alır; notu tarayıcıda çözer ve sunucudaki kayıtla doğrular. |
| 4 | **4. Çözümü açıkla** | Key sızıntısı, hex dönüşümü ve hata yanıtının düzeltilmesi açıklanır. |

**Çözüm:** Hata yanıtındaki hex key baytlara çevrilir. Paketin nonce ve ciphertext/tag alanlarıyla AES-GCM decrypt uygulanır. Notun açılmasını sağlayan bilgi secret key'dir; nonce tek başına yeterli değildir. Hex çözmek yalnız gösterimi değiştirir.

**Düzeltilmiş sürümde:** XML isteği genel bir HTTP 400 yanıtı verir; key ve traceback görünmez. Hazır çözüm key bulamaz ve not açılamaz. [Normal JSON önizleme](http://127.0.0.1:8085/lab/2/preview?format=json) çalışmaya devam eder. Önceden sızmış gerçek bir key için rotasyon ve etkilenen verinin değerlendirilmesi de gerekir.

## Hazır çözüm kodları

Açıklamalı çözüm her labın **4. adımındadır**. Kod, aynı bölümdeki **Hazır çözüm kodu · isteğe bağlı** alanında görüntülenebilir veya indirilebilir. Dersteki gösterim için bu alanı açmak gerekmez.

Tarayıcı çözümü [lab.js](lab.js) içindeki hazır Web Crypto işlemleriyle çalışır. Paket bir kez alınır; brute force adayları sunucuya gönderilmez. Ekrandaki ilerleme gerçek denemelerdir; gösterim süresi GPU benchmark'ıyla karşılaştırılmamalıdır.

Aynı örneklerin bağımsız Python çözümü [cozum.py](cozum.py) dosyasındadır:

```powershell
python lab/hafta04/cozum.py 1
python lab/hafta04/cozum.py 2
python lab/hafta04/cozum.py 1 --port 8085
python lab/hafta04/cozum.py 2 --port 8085
```

## Slaytlardaki küçük örnekler

```powershell
python -X utf8 lab/hafta04/demo.py
```

44 kontrol: küçük sayılarla Diffie–Hellman, tahmin edilebilir reset token'ı, Sezar, RSA-OAEP, X25519 + HKDF + AES-GCM, PRNG, Base64, hash, HMAC, nonce tekrarı, Ed25519 ve scrypt. Örnek kişiler Alice ve Bob'dur. Scrypt örneği yaklaşık 128 MiB bellek kullanır.

Kaynaklar: [cryptography AES-GCM](https://cryptography.io/en/stable/hazmat/primitives/aead/), [Python secrets](https://docs.python.org/3/library/secrets.html), [OWASP hata yönetimi](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html).
