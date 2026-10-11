# Güvenli Kodlama ve Programlama

**Secure Coding and Programming** · Seçmeli Lisans Dersi · 2026–27 Güz Dönemi
Eğitmen: **Refik Can Öztaş** (Offensive Security, Turknet)

Bu repo ders sunumlarını, uygulama örneklerini ve dönem projesi yönergesini içerir.

**[Ders için anonim geri bildirim formunu aç →](https://forms.gle/UorMFxBT6SKM1qve9)**

## Sunumlar

| Hafta | Konu | Slayt |
|:---:|---|:---:|
| 1 | Giriş, güvenli tasarım ilkeleri ve tehdit modelleme | [HTML](slaytlar/hafta01.html) · [PDF](slaytlar/hafta01.pdf) |
| 2 | SQL injection, command injection ve path traversal; ek konular | [HTML](slaytlar/hafta02.html) · [PDF](slaytlar/hafta02.pdf) |
| 3 | HTTP ve durum kodları; cookie, session, XSS ve savunmaları | [HTML](slaytlar/hafta03.html) · [PDF](slaytlar/hafta03.pdf) |
| 4 | Neden şifreleriz? Tarihçe, simetrik/asimetrik, Diffie–Hellman, TLS, RNG/nonce, brute force hızları (2026), rainbow table ve salt | [HTML](slaytlar/hafta04.html) · [PDF](slaytlar/hafta04.pdf) |

## Lablar

| Hafta | İçerik | Kurulum ve kullanım |
|:---:|---|---|
| 2 | SQL injection, command injection, path traversal; argument injection, SSTI, XXE ve NoSQL ek örnekleri | [Web labı](lab/hafta02/README.md) · [Kodlar](lab/hafta02/) |
| 4 | Dört rakamlı PIN'e brute force ve hata sayfasından key sızıntısı | [Kripto labı](lab/hafta04/README.md) · [Hazır çözümler](lab/hafta04/cozum.py) |

Python 3.10+ kullanın. Komutları depo kökünde çalıştırın; açık terminal sunucuyu çalışır tutar.

**Hafta 2:**

```powershell
python -m pip install -r lab/hafta02/requirements.txt
python -X utf8 lab/hafta02/app.py
```

Tarayıcıda http://127.0.0.1:5023 adresini açın. Normal ve exploit girdilerini aynı ekranda deneyip hatalı/düzeltilmiş sürümleri karşılaştırın. Command ve argument örnekleri için Git'in PATH üzerinde bulunması gerekir.

**Hafta 4:**

```powershell
python -m pip install -r lab/hafta04/requirements.txt
python -X utf8 lab/hafta04/lab.py
```

Tarayıcıda http://127.0.0.1:8084 adresini açın. Akış: paketi incele → PIN adaylarını veya hata yanıtını göster → notu aç → çözümü açıkla. Bütün işlemler hazır düğmelerle çalışır; derste kod yazılmaz. İki lab da AAD kullanmadan, nonce ve ciphertext/tag ile çalışır. Açıklamalı çözümler labın son adımındadır.

Düzeltilmiş sürümü karşılaştırmak için ikinci terminalde `python -X utf8 lab/hafta04/lab.py --fixed --port 8085` çalıştırıp http://127.0.0.1:8085 adresini açın.

## Dönem projesi

[Zafiyet Analiz: proje yönergesi (PDF)](proje/zafiyet-analiz.pdf) · [HTML](proje/zafiyet-analiz.html) · [LaTeX kaynağı](proje/zafiyet-analiz.tex)

Bireysel çalışma; lab kurulumu, zafiyeti yeniden üretme ve düzeltme sonrası tekrar deneme. Teslim: sayfa sınırı olmayan ayrıntılı PDF rapor, 10–15 dakikalık anlatım videosu ve lab dosyaları. Rapor ve videoda zafiyetin tanımı, root cause, güvenlik etkisi, yeniden üretim ve fix'in doğrulanması açıklanır. Gerçek bir CVE veya Facebook/Instagram gibi uygulamalarda yayımlanmış bir vaka seçilebilir. Web, masaüstü ve mobil uygulamalar, API’ler, embedded sistemler, IoT cihazları ve firmware bileşenleri kapsam dahilindedir. Konu seçiminde mümkün olduğunca yaygın kullanılan, popüler ürünlere veya bilinen güvenlik vakalarına öncelik verilmelidir. Tarih sınırı yoktur; eski konular da popüler bir ürüne veya bilinen bir vakaya ilişkin olması hâlinde seçilebilir. Kapalı kaynak uygulamalar için yapay zekâ desteğiyle temsili lab hazırlanabilir; reverse engineering ile inceleme ve fix geliştirme de isteğe bağlıdır. GitHub reposu tavsiye edilir; repo CV'de bir portföy projesi olarak paylaşılabilir. Video YouTube veya Google Drive bağlantısıyla sunulabilir; eğitmenden ek erişim isteği gerektirmemelidir. Detaylı sorular ve konu uygunluğu için [canoztas.sektorkampuste@gmail.com](mailto:canoztas.sektorkampuste@gmail.com) adresine yazılabilir. Proje dönem notunun %20'sidir. Konu seçimi ve teslim tarihleri ile teslim kanalı ders duyurusunda açıklanacaktır.

## Lisans

Slaytlar [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.tr) ile paylaşılır. Slaytlardaki kurum logoları ve üçüncü taraf görseller bu lisansın kapsamı dışındadır.
