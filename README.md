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
| 5 | Authentication: Hafta 1–4 tekrarı, terimleri ve her haftadan gerçek vakalar; parola saldırıları (brute force, sözlük, credential stuffing, password spraying), sızan parolalar, NIST 2025 parola politikası, Argon2id ve MFA; 12 gerçek vaka (kaynak ekran görüntüleriyle) ve terimler | [HTML](slaytlar/hafta05.html) · [PDF](slaytlar/hafta05.pdf) |
| 6 | Yetkilendirme: IDOR/BOLA/BFLA/BOPLA, şirket ve alan erişimleri, RBAC/ABAC/ReBAC kodları, UUID örneği, gerçek vakalar ve etkileşimli erişim denemesi | [HTML](slaytlar/hafta06.html) · [PDF](slaytlar/hafta06.pdf) |
| 7 | JWT’de simetrik/asimetrik doğrulama ve istemcide saklama; OAuth ve SSO; log toplama, ayrıştırma, grafik ve anomali tespitine giriş; dosya yükleme güvenliği; zafiyet türü–etki ayrımı, bağımsız RCE kapanışı ve Log4Shell örneği | [HTML](slaytlar/hafta07.html) · [PDF](slaytlar/hafta07.pdf) |

## Lablar

[Lablar, kurulum ve kullanım yönergeleri](lablar/README.md)

## İlk 7 hafta: cheat sheet

Her haftaya bir sayfa ayıran **7 sayfalık cheat sheet**; kavramların Türkçe ve İngilizce karşılıklarını, kısaltmaların açılımlarını ve kısa kod örneklerini toplar. SQLi/LFI, STRIDE ve HTTP çizimlerine ek olarak 6. sayfada tek fatura vakası; 7. sayfada JWT, kurumsal giriş, log işleme ve RCE akışları bulunur. Dosya yükleme, bir görsel eki örneğiyle; RCE, uygulama yetkileri ve Log4Shell örneğiyle açıklanır. Çizimler PDF’de yerel vektörler olarak yer alır.

[PDF](ozetler/hafta01-07-cheat-sheet.pdf)

7. hafta sunumunun kaynağı [araclar/hafta07_uret.py](araclar/hafta07_uret.py) dosyasındadır; sunum `python araclar/hafta07_uret.py` ile üretilir.

## Mini lab uygulaması

[Fatura Masası](mini-lab/README.md), fatura ve sipariş akışlarında sekiz kısa çalışma içerir: SQL enjeksiyonu, kayıt ve alan izinleri, kalıcı XSS, istemci fiyatı, kupon tekrarı, ödeme adımını atlama ve JWT payload değiştirme. Her çalışma zafiyetli ve düzeltilmiş sürümde denenebilir; çalışan kod görünümü, istek masası, etki takibi ve sıfırlama bulunur. JWT doğrudan web ekranında düzenlenebilir; jwt_tool çıktısı da yapıştırılabilir. Python/Flask ile yerelde çalışır. [Write-up (PDF)](mini-lab/writeup.pdf).

## Dönem projesi

[Zafiyet Analiz: proje yönergesi (PDF)](proje/zafiyet-analiz.pdf) · [HTML](proje/zafiyet-analiz.html) · [LaTeX kaynağı](proje/zafiyet-analiz.tex)

**[Proje konunu bildir: Konu Bildirim Formu →](https://forms.gle/BWrEbR3Rkev5CSZb7)** Formda ad soyad, okul, bölüm, numara, proje konusu, CVE numarası (CVE yoksa vakayı anlatan blog, rapor veya haber bağlantısı) ve uygulama/sistem/ürün adı ile sürümü istenir.

Bireysel çalışma; lab kurulumu, zafiyeti yeniden üretme ve düzeltme sonrası tekrar deneme. Teslim: sayfa sınırı olmayan ayrıntılı PDF rapor, 10–15 dakikalık anlatım videosu ve lab dosyaları. Rapor ve videoda zafiyetin tanımı, root cause, güvenlik etkisi, yeniden üretim ve fix'in doğrulanması açıklanır. Gerçek bir CVE veya Facebook/Instagram gibi uygulamalarda yayımlanmış bir vaka seçilebilir. Web, masaüstü ve mobil uygulamalar, API’ler, embedded sistemler, IoT cihazları ve firmware bileşenleri kapsam dahilindedir. Konu seçiminde mümkün olduğunca yaygın kullanılan, popüler ürünlere veya bilinen güvenlik vakalarına öncelik verilmelidir. Tarih sınırı yoktur; eski konular da popüler bir ürüne veya bilinen bir vakaya ilişkin olması hâlinde seçilebilir. Kapalı kaynak uygulamalar için yapay zekâ desteğiyle temsili lab hazırlanabilir; reverse engineering ile inceleme ve fix geliştirme de isteğe bağlıdır. GitHub reposu tavsiye edilir; repo CV'de bir portföy projesi olarak paylaşılabilir. Video YouTube veya Google Drive bağlantısıyla sunulabilir; eğitmenden ek erişim isteği gerektirmemelidir. Detaylı sorular ve konu uygunluğu için [canoztas.sektorkampuste@gmail.com](mailto:canoztas.sektorkampuste@gmail.com) adresine yazılabilir. Proje dönem notunun %20'sidir. Konu seçimi yukarıdaki form ile bildirilir; teslim tarihleri ve teslim kanalı ders duyurusunda açıklanacaktır.

## Lisans

Slaytlar [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.tr) ile paylaşılır. Slaytlardaki kurum logoları ve üçüncü taraf görseller bu lisansın kapsamı dışındadır.
