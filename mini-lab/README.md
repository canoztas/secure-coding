# Fatura Masası · Mini lablar

Fatura ve ofis siparişi akışları üzerinde sekiz kısa güvenlik çalışması. Python 3.10+, Flask ve PyJWT kullanır; Docker, Node veya harici veritabanı gerekmez.

```powershell
cd mini-lab
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Tarayıcıda **http://127.0.0.1:5050** adresini açın. macOS/Linux'ta son iki komutta `.venv/bin/python` kullanılır. Başka port için `python app.py --port 5051` çalışır.

Bu uygulama ders amacıyla kasıtlı zafiyetler içerir; yalnız `127.0.0.1` üzerinde, hata ayıklayıcı kapalı olarak başlar. Gerçek veri veya hesap kullanmaz.

## Çalışma biçimi

1. Bir çalışma seçin; önce uygulama ekranından normal işlemi yapın.
2. **Zafiyetli kod** bölümünde ilgili kod parçasını inceleyin. Kod, `app.py` içindeki zafiyetli daldan türetilir; sürüm seçme koşulları ve ilerleme kayıtları örnekten çıkarılır. Panel açılıp kapatılabilir, kod kopyalanabilir.
3. İstek masasında HTTP yöntemini, yolu veya JSON gövdesini değiştirin. Tarayıcının ağ paneli veya bir HTTP istemcisi de kullanılabilir.
4. Sunucunun yanıtını ve uygulamadaki değişikliği inceleyin. Yalnız geçerli bir etki gözlendiğinde çalışma işaretlenir; not labında JavaScript'in tarayıcıda çalışması beklenir.
5. **Düzeltilmiş sürüm** seçilince düzenlediğiniz istek korunur; sürüm yolu değişir. Kod paneli zafiyetli örneği göstermeye devam eder. Aynı isteği tekrar gönderin ve normal işlevin de çalıştığını doğrulayın.
6. Hatanın kök nedenini, kullanılma koşulunu, teknik etkisini ve iş etkisini iki üç cümleyle açıklayın.

| Çalışma | Denenecek durum | Beklenen iş kuralı |
|---|---|---|
| Arama | Arama sonucunun izin sınırlarını aşması | Sonuçlar kullanıcının erişebildiği faturalarla sınırlı |
| Fatura erişimi | Alice'in Bob'un 102 numaralı kaydını açması | Kayıt kimliği, izin belgesi sayılmaz |
| Alan izinleri | Not isteğine onay alanı eklenmesi | Üye not düzenler; onay yetkisi ayrı |
| Teslimat notu | Kaydedilen notun kod olarak yorumlanması | Metin tarayıcıda kod olarak çalışmaz |
| Ürün fiyatı | İstekten gelen düşük fiyatın kullanılması | Fiyatı sunucu kataloğu belirler |
| İndirim kuponu | Tek kullanımlık kupon isteğinin tekrarı | Aynı kullanıcıya bir kez indirim |
| Ödeme akışı | Ödeme adımından önce onay isteği | Ödeme doğrulanmadan teslimat onaylanmaz |
| JWT ile kimlik | Token içindeki kullanıcı/rol bilgisinin değiştirilmesi | İmza doğrulanmadan kimliğe ve role güvenilmez |

Alice ve Bob A şirketinde üye; Deniz A şirketinde muhasebeci; Ece B şirketinde üyedir. **Ders hesabı** seçimi, farklı kişilerin izinlerini karşılaştırmak içindir; bir kimlik doğrulama labı değildir.

İki sürümün verileri birbirinden ayrıdır. Her tarayıcı oturumu kendi çalışma alanını kullanır; **Verileri sıfırla** yalnız o çalışma alanındaki iki sürümü ve ilerlemeyi sıfırlar. Kupon sepeti, ürün siparişi ve 501 numaralı ödeme örneği birbirinden bağımsızdır.

Not önizlemesi, ağ erişimi kapalı bir sandbox içinde gösterilir. `alert(...)`, tarayıcı iletişim kutusu yerine önizlemede mesaj oluşturur. Bu bir **istemci tarafı XSS** örneğidir; sunucuda RCE gösterimi değildir. İlerleme işaretleri öğrencinin gördüğü etkiyi takip eder; güvenilir bir notlandırma sistemi değildir.

## JWT denemesi

**JWT ile kimlik** çalışmasını Alice hesabıyla açın. Normal token ile faturaları getirin. Payload içindeki `sub` değerini `bob` yapıp **Payload’u token’a yaz** düğmesine basın; mevcut imza değiştirilmez. Faturaları yeniden isteyin. Sonra aynı token’ı koruyarak **Düzeltilmiş sürüm** seçin ve isteği tekrarlayın. `role: accountant` ile yapılan deneme de desteklenir.

Token ve payload tarayıcıda çözülür; imza yalnız sunucuda üretilir. Doğrulama anahtarı tarayıcıya gönderilmez. Token’lar 15 dakika geçerlidir; iki sürüm aynı çalışma alanının anahtarını kullanır. Sıfırlama anahtarı değiştirir. JWT isteğinin `Authorization: Bearer ...` başlığı istek masasında ayrıca düzenlenebilir.

İsteğe bağlı olarak [jwt_tool](https://github.com/ticarpi/jwt_tool) ile token’ı okuyup değiştirebilirsiniz. Aracın kendi kurulumundan sonra, uygulamadan kopyaladığınız ders token’ıyla:

```powershell
$labJwt = 'BURAYA_DERS_TOKENINI_YAPISTIR'
python jwt_tool.py "$labJwt"
python jwt_tool.py "$labJwt" -T
```

Aracın ürettiği değiştirilmiş token’ı uygulamadaki **Token** alanına yapıştırıp **Token’ı çöz** ve **Faturaları bu token’la getir** düğmelerini kullanın. Bu akış için jwt_tool zorunlu değildir; aynı değişiklik doğrudan web ekranında yapılabilir.

## Write-up ve kontroller

[Write-up (PDF)](writeup.pdf), sekiz labın adım adım çözümünü, beklenen HTTP yanıtlarını, kök nedenlerini, teknik/iş etkilerini ve düzeltme sonrası kontrolleri içerir.

```powershell
python -m unittest discover -s mini-lab -p test_app.py -v
```

Bu test komutu repo kökünden çalıştırılır. `mini-lab` içindeyken `python -m unittest -v` kullanılabilir. Testler geçici bir veritabanında zafiyetli sonucu, aynı girdinin düzeltilmiş davranışını, normal işlemleri, sıfırlamayı ve çalışma alanlarının ayrılığını denetler.

Uygulama verileri `instance/lab.sqlite3` dosyasındadır; repoya eklenmez. Ana sayfa ve statik dosyalar çevrimdışı kullanılabilir; sunucunun çalışması gerekir.
