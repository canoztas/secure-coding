"""İlk yedi haftanın başvuru notu: HTML, bağımsız LaTeX ve Overleaf paketi.
python ozetler/uret.py --pdf
"""
from pathlib import Path
from html import escape
import re, sys, subprocess, zipfile
from cizimler import svg, tikz

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
pages=[]
def page(title,subtitle,blocks):pages.append((title,subtitle,blocks))
def t(head,rows):return ('table',head,rows)
def p(text):return ('p',text)
def h(text):return ('h',text)
def c(text):return ('code',text.strip())
def sources(items):return ('sources',items)  # Kaynaklar çıktı belgelerine basılmaz.
def visual(kind):return ('visual',kind)

page('1 · Güvenlik temelleri','Zafiyet, tehdit modeli ve güvenli tasarım',[
 t(['Kavram','Anlamı ve sınırı'],[
 ['Hata · Zafiyet · İstismar','Bug (hata): yazılımın beklenen davranıştan sapması. Vulnerability (zafiyet): güvenlik etkisi doğuran zayıflık. Exploit (istismar): zafiyeti kullanma yöntemi veya kodu.'],
 ['Tehdit · Risk · Etki','Threat (tehdit): zarara yol açabilecek durum veya eylem. Risk: kayıp olasılığı ve etkisinin değerlendirilmesi. Impact (etki): gerçekleşen olayın zararı.'],
 ['Saldırı yüzeyi / Attack surface · Güven sınırı / Trust boundary','Erişilebilen girişler / farklı güven düzeyleri arasındaki geçiş. Veri sınırı aşınca yeni bağlamda denetlenir.'],
 ['CIA','Confidentiality (gizlilik), Integrity (bütünlük), Availability (kullanılabilirlik).'],
 ['CVE / CWE / CVSS','Common Vulnerabilities and Exposures (Yaygın Zafiyetler ve Maruziyetler): zafiyet kaydı. Common Weakness Enumeration (Yaygın Zayıflık Sınıflandırması): zayıflık türü. Common Vulnerability Scoring System (Yaygın Zafiyet Puanlama Sistemi): teknik şiddet puanı.'],
 ['CTF · Bayrağı yakala','Capture The Flag: izinli ortamda güvenlik görevleri.']]),
 h('Kod incelerken'),
 p('Girdinin kaynağını, ulaştığı kaynağı ve güven sınırını belirle. Hatalı varsayımı, güvenlik etkisini ve düzeltmeyi göster; aynı denemeyi düzeltmeden sonra tekrarla.'),
 t(['İlke','Uygulamadaki karşılığı'],[
 ['Least privilege · en az yetki','Uygulama ve servis hesabı yalnız gereken kaynaklara erişir.'],
 ['Fail-safe defaults · güvenli varsayılan','İzin açıkça tanımlı değilse erişim reddedilir.'],
 ['Complete mediation · tam denetim','Önemli her erişimde karar yeniden uygulanır. Arayüzde düğmeyi gizlemek yeterli olmaz.'],
 ['Defense in depth · katmanlı savunma','Bir kontrol aşılırsa diğerleri etkiyi sınırlayabilir. Ağ kontrolü, uygulamadaki zafiyeti düzeltmez.'],
 ['Open design · açık tasarım','Güvenlik algoritmanın gizli kalmasına dayanmaz; anahtarlar korunur.']]),
 h('STRIDE · Tehdit modelleme / Threat modeling'),
 visual('stride'),
 sources([('Ders sunumu · Hafta 1','../slaytlar/hafta01.html'),('MITRE · CWE','https://cwe.mitre.org/'),('FIRST · CVSS','https://www.first.org/cvss/')])
])
page('2 · Injection ve dosya yolları','Enjeksiyon / Injection · Dizin dışına çıkma / Path traversal',[
 t(['Terim / açılım','Nerede ortaya çıkar? · Temel kontrol'],[
 ['SQLi · SQL enjeksiyonu / SQL Injection','Girdi, SQL (Structured Query Language · Yapılandırılmış Sorgu Dili) sorgusunun yapısını değiştirir. Değerler parametreyle; sütun gibi yapısal seçimler izin listesiyle verilir.'],
 ['Komut enjeksiyonu / Command injection','`name=alice; echo DEMO` shell metnine eklenirse ikinci komut çalışabilir. Sabit programı ayrı argümanlarla çağır: `subprocess.run(["/usr/bin/echo", "Hello", name])`.'],
 ['Argüman enjeksiyonu / Argument injection','Girdi `--help` gibi bir program seçeneği olabilir. Argüman listesi shell’i kaldırır; programın seçenek kuralları ayrıca denetlenir.'],
 ['Dizin dışına çıkma / Path traversal','`../` ile izin verilen klasörün dışına ulaşma. Dosya açmadan önce çözümlenen yolun izinli kök içinde kaldığını denetle.'],
 ['LFI · Yerel dosya dahil etme / Local File Inclusion','Sunucudaki bir dosyanın denetimsiz biçimde uygulamaya dahil edilmesi. Dosya içeriği yanıta sızabilir; içerik ve yorumlayıcıya göre kod da çalışabilir.']]),
 h('SQLi: aynı sorgu, değişen koşul / Changed query condition'),
 p('Örnek tablo: `users` içinde `(1, Alice)` ve `(2, Bob)` var. Aşağıdaki değer URL’den çözümlenmiş `id` parametresidir.'),
 visual('sqli'),
 c('''# Hatalı / Vulnerable: girdi sorgu metnine ekleniyor.
q = "SELECT name FROM users WHERE id = " + user_id
# Güvenli / Safe: aynı girdi tek bir değer olarak bağlanıyor.
rows = db.execute("SELECT name FROM users WHERE id = ?", (user_id,))
'''),
 p('Parametreli sürümde `1 OR 1=1`, SQL operatörü olmaz; bu örnekte hiçbir kullanıcı kimliğiyle eşleşmez.'),
 h('LFI: sayfa seçimi dosya yoluna dönüşür / File inclusion'),
 c('''// Hatalı PHP örneği / Vulnerable PHP example: view.php
include(__DIR__ . "/pages/" . $_GET["page"]);
// İstek / Request: /view.php?page=../private/note.txt
'''),
 visual('lfi'),
 p('Örnekte `note.txt` düz metindir; içeriği yanıta eklenir. Düzeltme: kullanıcıdan dosya yolu alma; `help` gibi bir anahtarı önceden tanımlı dosyaya eşleştir. Tanımsız anahtarı reddet. Bu senaryoda path traversal, LFI’nin izinli klasör dışına ulaşmasını sağlar.'),
 sources([('Ders sunumu · Hafta 2','../slaytlar/hafta02.html'),('OWASP · Injection Prevention','https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html')])
])
page('3 · HTTP, tarayıcı ve oturum','İstek / Request · Yanıt / Response · Çerez / Cookie',[
 t(['Terim / açılım','Hatırlanacak nokta'],[
 ['HTTP / HTTPS / TLS','Hypertext Transfer Protocol (Hiper Metin Aktarım Protokolü) / HTTP over TLS (TLS üzerinden HTTP) / Transport Layer Security (Taşıma Katmanı Güvenliği).'],
 ['Adres / URL · Köken / Origin · Site','Uniform Resource Locator (Birörnek Kaynak Konumlayıcı). Origin = scheme (şema) + host (sunucu adı) + port. Aynı site içindeki iki alt alan farklı origin olabilir.'],
 ['Çerez / Cookie · Oturum / Session','Çerez tarayıcıda tutulan ve kapsamına göre gönderilen veridir. Oturum kaydı sunucuda veya imzalı çerezde olabilir. İmzalı veri, şifreli veri anlamına gelmez.'],
 ['Web depolama / Web storage','localStorage (yerel depolama) ve sessionStorage (sekme oturumuna bağlı depolama) JavaScript’ten okunabilir; HTTP isteğine otomatik eklenmez.'],
 ['XSS · Siteler arası betik çalıştırma / Cross-Site Scripting','Girdi tarayıcıda kod olarak çalışır. Reflected (yansıtılan): yanıta eklenir. Stored (kalıcı): saklanır, sonraki ziyaretçide çalışır. Metin için `textContent`; HTML çıktısında bağlama uygun kodlama kullanılır.']]),
 h('HTTP çerez bayrakları ve öznitelikleri / Cookie flags and attributes'),
 c('Set-Cookie: sid=abc123; Secure; HttpOnly; SameSite=Lax'),
 t(['Bayrak / öznitelik','Tarayıcının uyguladığı kural'],[
 ['Secure · Güvenli aktarım bayrağı','Çerez güvenli bağlantıda (genellikle HTTPS) gönderilir. Çerezin içeriğini ayrıca şifrelemez.'],
 ['HttpOnly · Betik erişimi kısıtı','`document.cookie` gibi JavaScript API’leri çerezi okuyamaz. Tarayıcı uygun isteklere çerezi yine ekler.'],
 ['SameSite · Siteler arası gönderim','Strict: yalnız aynı site bağlamı. Lax: buna ek olarak üst düzey, güvenli metotlu gezinmeler. None: siteler arası gönderime izin verir; Secure gerekir.']]),
 h('HTTP durum kodları / HTTP status codes'),
 visual('http'),
 sources([('Ders sunumu · Hafta 3','../slaytlar/hafta03.html'),('MDN · HTTP','https://developer.mozilla.org/en-US/docs/Web/HTTP'),('OWASP · XSS Prevention','https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html')])
])
page('4 · Uygulamalı kriptografi','Kodlama, şifreleme, özet ve imza',[
 t(['Yöntem / açılım','Sağladığı özellik ve dikkat noktası'],[
 ['Kodlama / Encoding · Base64 / Base64url','Gösterimi değiştirir; anahtar (key) gerektirmez. Gizlilik veya bütünlük sağlamaz.'],
 ['Simetrik şifreleme / Symmetric encryption · AES','Advanced Encryption Standard (Gelişmiş Şifreleme Standardı). Şifreleme ve çözmede aynı gizli anahtar (secret key) kullanılır.'],
 ['Asimetrik yöntemler / Asymmetric methods','Açık anahtar (public key) / özel anahtar (private key) çifti. RSA-OAEP: şifreleme (encryption); Ed25519: imza (signature); Diffie–Hellman ve X25519: anahtar anlaşması (key agreement).'],
 ['Özetleme / Hashing · SHA-256','Secure Hash Algorithm (Güvenli Özet Algoritması), 256 bit. Tek yönlü özet (hash). Güvenilir kaynaktaki özetle karşılaştırma değişikliği saptayabilir.'],
 ['HMAC · Anahtarlı mesaj doğrulama','Hash-based Message Authentication Code (Özet Tabanlı Mesaj Doğrulama Kodu). İçeriği gizlemez; aynı anahtarı bilenler doğrulama etiketi (tag) üretebilir.'],
 ['Dijital imza / Digital signature','Özel anahtar imzalar, açık anahtar doğrular. Açık anahtarın kime ait olduğu ayrıca belirlenir.'],
 ['RNG / PRNG / CSPRNG','Random Number Generator (Rastgele Sayı Üreteci) / Pseudorandom Number Generator (Sözde Rastgele Sayı Üreteci) / Cryptographically Secure PRNG (Kriptografik Olarak Güvenli PRNG). Sabit tohum (seed) ile çalışan `random`, güvenlik token’ı için uygun değildir.'],
 ['Tek kullanımlık değer / Nonce · Tuz / Salt','Nonce: number used once; yöntemin tekrar etmeme kuralına tabi değer. Salt: parola kaydını farklılaştıran değer. Gizli olmaları gerekmez.']]),
 h('Güvenli rastgelelik ve aday sayısı'),
 c('''import secrets
reset_token = secrets.token_urlsafe(32)  # 32 bayt rastgelelik
nonce = secrets.token_bytes(12)         # AES-GCM örneği
'''),
 p('Eşit olasılıkla üretilen L uzunluğunda, A sembollü bir değer için aday sayısı N = A^L. Sabit deneme hızı r ise tam tarama süresi yaklaşık N/r, rastgele hedefte ortalama yaklaşık yarısıdır. 4 rakamlı PIN’in SHA-256 özeti de yalnız 10.000 PIN adayından biridir.'),
 p('Gökkuşağı tablosu (rainbow table), özet ve indirgeme (reduction) zincirleriyle ön hesaplama/bellek takası yapar. Salt, aynı ön hesabın bütün kayıtlarda kullanılmasını engeller. Parola için ayrıca Argon2id gibi maliyetli bir parola özetleme yöntemi gerekir.'),
 sources([('Ders sunumu · Hafta 4','../slaytlar/hafta04.html'),('Python · secrets','https://docs.python.org/3/library/secrets.html'),('cryptography · AEAD','https://cryptography.io/en/latest/hazmat/primitives/aead/')])
])
page('5 · Parola ve kimlik doğrulama','Deneme saldırıları, güvenli saklama ve MFA',[
 t(['Terim / açılım','Ayırıcı özellik'],[
 ['Kimlik doğrulama / Authentication · Yetkilendirme / Authorization','Hangi hesap olduğunu doğrulamak ve hangi işlem/kaynağa erişebileceğine karar vermek ayrı kontrollerdir.'],
 ['Kaba kuvvet / Brute force · Sözlük / Dictionary · Maske / Mask','Aday uzayını tarama / sözlükten aday seçme / bilinen biçime göre aday üretme.'],
 ['Parola püskürtme / Password spraying','Çok hesaba az sayıda yaygın parola deneme. Yalnız hesap başına kilit yeterli olmayabilir.'],
 ['Çalıntı kimlik bilgisi denemesi / Credential stuffing','Başka hizmetten çalınan kullanıcı adı–parola çiftlerini deneme. Tekrar kullanılmayan parolalar ve MFA etkiyi sınırlar.'],
 ['Hesap varlığı tespiti / User enumeration','Mesaj, süre veya yanıt farkıyla hesabın varlığını öğrenme. Tutarlı hata yanıtı ve kontrollü işlem yolu gerekir.'],
 ['Çevrim içi / Online · Çevrim dışı / Offline','Giriş noktasında deneme / ele geçmiş özet üzerinde yerel deneme. İstek hızı sınırı (rate limiting), çevrim dışı denemeyi durdurmaz.'],
 ['Parola özetleme / Password hashing · Argon2id / bcrypt','Maliyetli parola özetleme yöntemleri. Tuz (salt) ve maliyet (cost) ayarı kayıtta tutulur. Hızlı SHA-256 tek başına parola saklama yöntemi değildir.'],
 ['MFA / TOTP','Multi-Factor Authentication (Çok Faktörlü Kimlik Doğrulama) / Time-based One-Time Password (Zaman Tabanlı Tek Kullanımlık Parola). TOTP’de süre ve tekrar kullanım denetlenir.']]),
 h('Kimlik doğrulama faktörleri / Authentication factors'),
 t(['Faktör / Factor','Örnek / Example'],[
 ['Bildiğin bir şey / Something you know','Parola veya PIN: kullanıcının bildiği bilgi.'],
 ['Sahip olduğun bir şey / Something you have','Güvenlik anahtarı veya doğrulama uygulamasının kurulu olduğu telefon: kullanıcının elindeki araç.'],
 ['Olduğun bir şey / Something you are','Parmak izi veya yüz gibi biyometrik özellik.']]),
 p('MFA, en az iki farklı gruptan faktör kullanır: parola + güvenlik anahtarı gibi. İki ayrı parola aynı gruptadır. Geçiş anahtarında (passkey), cihazda veya güvenlik anahtarında tutulan kriptografik anahtar kullanılır. Cihaz PIN’i veya biyometri bu anahtarı yerel olarak kullanıma açabilir.'),
 h('Uygulamada'),
 p('NIST SP 800-63B-4: tek faktörlü parola en az 15 karakter; MFA parçası olduğunda en az 8 karaktere izin verilebilir. Uzun parolalar desteklenir; yaygın/sızmış değerler engellenir. Karakter türü zorlaması ve ihlal belirtisi olmadan dönemsel değişim istenmez. Parola yöneticileri ve yapıştırma desteklenir.'),
 p('Girişlerde hesap, ağ ve genel trafik bağlamında deneme sınırı; tutarlı hata mesajı; yok hesap için maliyetli doğrulama yolu; başarıdan sonra yeni oturum gerekir. Hesap kilidinin hizmet engellemeye dönüşebileceği de düşünülür.'),
 p('Parola sıfırlama (password reset): CSPRNG ile üretilmiş token; kullanıcıya bağlı, kısa ömürlü ve tek kullanımlık kayıt. Token loglanmaz. Bilgi hırsızı yazılım (infostealer), parolayı veya hazır oturumu kopyalayabilir; MFA her oturum hırsızlığını önlemez.'),
 sources([('Ders sunumu · Hafta 5','../slaytlar/hafta05.html'),('NIST · SP 800-63B-4','https://pages.nist.gov/800-63-4/sp800-63b.html'),('OWASP · Password Storage','https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html')])
])
page('6 · Yetkilendirme','Tek vaka: aynı faturada kayıt, işlem ve alan izinleri',[
 p('A şirketinde Alice ve Bob üye, Deniz muhasebecidir. Üyeler kendi veya düzenleyici olarak paylaşılan faturaları okur, notlarını değiştirir. Muhasebeci aynı şirketteki, limiti içindeki taslak faturayı onaylayabilir.'),
 visual('authorization_case'),
 t(['Kontrolün yeri','Aynı vakada ne olur?'],[
 ['IDOR / BOLA','Insecure Direct Object Reference (Güvensiz Doğrudan Nesne Referansı) / Broken Object Level Authorization (Nesne Düzeyinde Yetkilendirme Eksikliği). Alice, `GET /invoices/101` yerine `GET /invoices/102` gönderir. İzni yokken Bob’un faturası dönüyorsa nesne erişimi hatalıdır; bu örnekte iki ad aynı sorunun farklı yönlerini anlatır.'],
 ['BFLA','Broken Function Level Authorization (İşlev Düzeyinde Yetkilendirme Eksikliği). Alice, `POST /invoices/101/approve` çağırır. Fatura kendisinin olsa da onay rolü yoktur; işlem reddedilmelidir.'],
 ['BOPLA','Broken Object Property Level Authorization (Nesne Alanı Düzeyinde Yetkilendirme Eksikliği). Alice 101’in notunu değiştirebilir; aynı istekte `status=approved` göndererek faturayı onaylayamaz. Toplu alan atama (mass assignment) bu sınırı aşmamalıdır.'],
 ['RBAC','Role-Based Access Control (Rol Tabanlı Erişim Kontrolü). Deniz’in muhasebeci rolü onay işlevine erişim sağlar. Alice’in üyeliği sağlamaz.'],
 ['ABAC','Attribute-Based Access Control (Öznitelik Tabanlı Erişim Kontrolü). 102 aynı şirkette, 3.000 tutarı 5.000 limitinin altında ve taslak durumunda: Deniz’in onay koşulları sağlanır.'],
 ['ReBAC','Relationship-Based Access Control (İlişki Tabanlı Erişim Kontrolü). Bob, Alice’i 102’ye düzenleyici olarak eklerse Alice notu değiştirebilir. Bu paylaşım onay yetkisi vermez.']]),
 p('Her işlem için gereken kontroller birlikte uygulanır. UUID (Universally Unique Identifier · Evrensel Benzersiz Tanımlayıcı) kullanmak bu izinleri sağlamaz. Okuma, not değiştirme ve onay için farklı kararlar verilebilir.'),
])

page('7 · JWT, OAuth, SSO ve loglama','Token’ın yolculuğu, ortak giriş ve kayıttan alarma',[
 t(['Kavram / Concept','Kısa karşılığı'],[
 ['JWT / JWS / JWE','JSON Web Token (JSON Web Belirteci); JSON Web Signature (JSON Web İmzası); JSON Web Encryption (JSON Web Şifrelemesi). İmzalı JWT’nin içeriği okunabilir.'],
 ['Simetrik / Symmetric · Asimetrik / Asymmetric','HS256: üreten ve doğrulayan hizmet aynı gizli anahtarı bilir. RS256: özel anahtar (private key) imzalar; açık anahtar (public key) doğrular.'],
 ['OAuth / OIDC / SSO','OAuth 2.0 Authorization Framework (Yetkilendirme Çerçevesi): API yetkisi. OpenID Connect: kimlik doğrulama. Single Sign-On (Tek Oturum Açma): bir girişle birden çok uygulama.'],
 ['Access / ID / Refresh token','Erişim / kimlik / yenileme token’ı: API isteği / giriş sonucu / yeni erişim token’ı alma. ID token API’ye erişim belgesi değildir.'],
 ['PKCE / state / nonce','Proof Key for Code Exchange (Kod Değişimi için İspat Anahtarı): kodu istemciye bağlar. State (işlem durumu) dönüşü giriş denemesiyle eşleştirir. Nonce (tek kullanımlık değer), ID token’ı isteğe bağlar.'],
 ['iss / sub / aud / exp','Issuer (üretici) / Subject (özne) / Audience (alıcı) / Expiration Time (bitiş zamanı). API imza, üretici, alıcı ve süreyi; sonra nesne/işlem iznini kontrol eder.'],
 ]),
 h('1 · JWT nerede durur? / Token flow'),
 visual('jwt_route'),
 p('Token istemcide saklanıp istekle gönderilir. HttpOnly çerez ve JavaScript depolarının riskleri farklıdır. Gizli/özel anahtar istemciye verilmez. Sunucu gerektiğinde hesap ve iptal kaydı tutar.'),
 h('2 · Kurumsal giriş / Corporate sign-in'),
 visual('login_route'),
 p('Uygulama dönüşü doğrular ve kendi oturumunu açar. SSO’da ortak giriş hizmetinin açık oturumu ikinci uygulamada da kullanılabilir; uygulamaların yerel oturumları ayrıdır.'),
 h('3 · Kayıttan alarma / Logs to alerts'),
 visual('log_route'),
 p('Data parsing (veri ayrıştırma) alanları çıkarır; data visualization (veri görselleştirme) örüntüyü gösterir. ML (Machine Learning · Makine öğrenmesi), olağan düzenden sapmaları işaretleyebilir. Anomaly detection (anomali tespiti), inceleme sinyalidir; her sapma saldırı değildir.'),
 p('Logda zaman, doğrulanmış kullanıcı, kaynak, sonuç ve istek kimliği bulunur. DEBUG (hata ayıklama), INFO (bilgi), WARNING (uyarı), ERROR (hata). Parola, çerez ve token kaydedilmez.'),
 h('Dosya yükleme / File upload'),
 p('Örnek: Görsel ekinde `Content-Type: image/jpeg` (içerik türü) yazması, dosyanın görsel olduğunu kanıtlamaz. Tür, içerik ve boyut sunucuda denetlenir. Dosya sunucunun verdiği adla web kökü dışında saklanır; yükleme ve indirmede izin aranır.'),
 h('RCE · Uzaktan kod çalıştırma / Remote Code Execution'),
 visual('rce_route'),
 p('RCE etkidir; zafiyetin türü kök nedeni anlatır. Yüklenen dosyanın sunucuda kod olarak çalıştırılması RCE’ye yol açabilir. Log4Shell (CVE-2021-44228) başka bir örnektir. Kod uygulamanın hesabıyla çalışır; otomatik yönetici yetkisi sağlamaz.'),
])

def tex_escape(s):
 mapping={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','→':r'\(\rightarrow\)'}
 def plain(x):return ''.join(mapping.get(ch,ch) for ch in x)
 chunks=re.split(r'(`[^`]+`)',s)
 return ''.join(r'\texttt{'+plain(x[1:-1])+'}' if x.startswith('`') else plain(x) for x in chunks)
def html_text(s):return re.sub(r'`([^`]+)`',lambda m:'<code>'+escape(m[1])+'</code>',escape(s))

TEX=r'''\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\setmainfont{Latin Modern Roman}
\setmonofont{Latin Modern Mono}[Scale=0.9]
\usepackage[turkish,shorthands=off]{babel}
\usepackage[left=17mm,right=17mm,top=18mm,bottom=18mm,headheight=13pt,headsep=5mm,footskip=9mm]{geometry}
\usepackage{microtype,booktabs,tabularx,array,fancyhdr,lastpage,fvextra}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\definecolor{diagramline}{HTML}{B9C3CD}
\definecolor{diagramink}{HTML}{222B35}
\definecolor{diagramarrow}{HTML}{465C74}
\usepackage[hidelinks,unicode]{hyperref}
\hypersetup{pdftitle={Güvenli Kodlama · İlk 7 Hafta · Kavramlar ve Kısaltmalar},pdfauthor={},pdflang={tr-TR}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\setlength{\emergencystretch}{2em}
\renewcommand{\arraystretch}{1.13}
\setlength{\tabcolsep}{5pt}
\newcolumntype{L}{>{\raggedright\arraybackslash}p{.255\linewidth}}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\footnotesize Güvenli Kodlama ve Programlama}
\fancyhead[R]{\footnotesize Kavramlar ve Kısaltmalar · Hafta 1–7}
\fancyfoot[R]{\footnotesize\thepage\,/\,\pageref*{LastPage}}
\newcommand{\AltBaslik}[1]{\par\vspace{3pt}\textbf{#1}\par\nobreak}
\begin{document}
'''
HTML=[]
for n,(title,subtitle,blocks) in enumerate(pages,1):
 if n>1:TEX+='\n\\newpage\n'
 if n==7:TEX+=r'\setlength{\parskip}{2pt}\renewcommand{\AltBaslik}[1]{\par\vspace{1pt}\textbf{#1}\par\nobreak}'+'\n'
 TEX+=r'{\Large\bfseries '+tex_escape(title)+r'}\\[3pt]'+'\n'+r'{\normalsize '+tex_escape(subtitle)+r'}\\[5pt]'+'\n'
 body=[]
 for block in blocks:
  if block[0]=='table':
   head,rows=block[1:]
   TEX+=r'\begingroup\small\begin{tabularx}{\linewidth}{@{}LY@{}}\toprule'+'\n'+tex_escape(head[0])+' & '+tex_escape(head[1])+r'\\\midrule'+'\n'
   for a,b in rows:TEX+=tex_escape(a)+' & '+tex_escape(b)+r'\\[2pt]'+'\n'
   TEX+=r'\bottomrule\end{tabularx}\endgroup\par'+'\n'
   body.append('<table><thead><tr>'+''.join('<th>'+html_text(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr><td>'+html_text(a)+'</td><td>'+html_text(b)+'</td></tr>' for a,b in rows)+'</tbody></table>')
  elif block[0]=='p':
   TEX+=tex_escape(block[1])+'\n\n';body.append('<p>'+html_text(block[1])+'</p>')
  elif block[0]=='h':
   TEX+=r'\AltBaslik{'+tex_escape(block[1])+'}\n';body.append('<h3>'+html_text(block[1])+'</h3>')
  elif block[0]=='code':
   TEX+=r'\begin{Verbatim}[fontsize=\footnotesize,breaklines=true,breakanywhere=true,frame=lines,framesep=3mm]'+'\n'+block[1]+'\n'+r'\end{Verbatim}'+'\n'
   body.append('<pre>'+escape(block[1])+'</pre>')
  elif block[0]=='visual':
   TEX+=tikz(block[1],tex_escape)
   body.append(svg(block[1]))
 HTML.append('<section class="page"><header><span>Güvenli Kodlama ve Programlama</span><span>Hafta 1–7 · Cheat sheet</span></header><h1>'+escape(title)+'</h1><p class="subtitle">'+escape(subtitle)+'</p>'+''.join(body)+f'<footer><span>{n} / 7</span></footer></section>')
TEX+='\n\\end{document}\n'
stem='hafta01-07-cheat-sheet'
(OUT/(stem+'.tex')).write_text(TEX,encoding='utf8')
CSS='''*{box-sizing:border-box}body{margin:0;background:#e6e7e3;color:#222;font:11pt/1.38 Georgia,'Times New Roman',serif}.page{width:210mm;min-height:297mm;padding:18mm 17mm;margin:18px auto;background:white;position:relative}header,footer{display:flex;justify-content:space-between;font-size:9pt;color:#555}header{border-bottom:1px solid #777;padding-bottom:4mm;margin-bottom:5mm}footer{margin-top:5mm;padding-top:3mm;border-top:1px solid #ccc}h1{font-size:19pt;line-height:1.2;margin:0 0 2mm}h3{font-size:11pt;margin:4mm 0 1mm}.subtitle{margin:0 0 4mm;color:#555}p{margin:2mm 0}table{width:100%;border-collapse:collapse;font-size:10pt;line-height:1.3;margin:2mm 0 3mm}td,th{padding:2mm 1.5mm;vertical-align:top;border-bottom:1px solid #ddd;text-align:left}th{border-top:1px solid #333;border-bottom:1px solid #777}td:first-child{width:27%;font-weight:bold}pre{font:9pt/1.3 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;padding:3mm;background:#f3f4f0;border-block:1px solid #bbb}code{font: .9em Consolas,monospace}.sources{font-size:8.5pt;line-height:1.4;margin-top:4mm}a{color:#28515d;text-decoration:none}@media(max-width:820px){.page{width:auto;min-height:0;margin:0;padding:24px}header{gap:15px}table{font-size:10pt}}@page{size:A4;margin:0}@media print{body{background:white}.page{margin:0;break-after:page;width:210mm;height:297mm;min-height:0;padding:18mm 17mm;font-size:10pt;line-height:1.3;overflow:visible}.page:last-child{break-after:auto}table{font-size:9pt}td,th{padding:1.5mm}footer{position:absolute;bottom:12mm;left:17mm;right:17mm}.sources{font-size:8pt}a{color:#222}}
'''
CSS+='''\n.diagram{display:block;width:100%;height:auto;margin:3mm 0;font-family:Georgia,'Times New Roman',serif}footer{justify-content:flex-end}.page:nth-child(2) table{font-size:9.5pt}.page:nth-child(2) pre{font-size:8.5pt}@media print{.diagram{margin:2mm 0}.page:nth-child(2) table{font-size:9pt}}'''
CSS+='''@media print{h3{margin:2mm 0 1mm}pre{padding:2mm;margin:2mm 0}.page:nth-child(3) table{font-size:8.7pt}.page:nth-child(3) td,.page:nth-child(3) th{padding:1.1mm 1.5mm}.page:nth-child(3) .diagram{width:99%;margin-top:0}}'''
CSS+='''@media print{.page:nth-child(7) td,.page:nth-child(7) th{padding:.9mm 1.5mm}.page:nth-child(7) p{margin:.6mm 0}.page:nth-child(7) .diagram{width:96%;margin:.5mm auto}.page:nth-child(7) h3{margin:1.5mm 0 .8mm}}'''
CSS+='''@media print{.page:nth-child(7) header{padding-bottom:2mm;margin-bottom:2mm}.page:nth-child(7) table{margin:1.5mm 0 2mm}}'''
CSS+='''@media print{body{font-family:'Times New Roman',serif}.page:nth-child(5) td,.page:nth-child(5) th{padding-top:1.35mm;padding-bottom:1.35mm}}'''
(OUT/(stem+'.html')).write_text('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>İlk 7 hafta · Kavramlar ve kısaltmalar</title><style>'+CSS+'</style></head><body>'+''.join(HTML)+'</body></html>',encoding='utf8')
(OUT/'OVERLEAF.txt').write_text('Overleaf: New Project > Upload Project ile ZIP paketini yükleyin.\nCompiler: XeLaTeX\nMain document: main.tex\nHarici font veya görsel gerektirmez.\nKaynak belge: hafta01-07-cheat-sheet.tex\n',encoding='utf8')
with zipfile.ZipFile(OUT/'hafta01-07-overleaf.zip','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('main.tex',TEX);z.write(OUT/'OVERLEAF.txt','OVERLEAF.txt')
if '--pdf' in sys.argv:
 build=ROOT/'.runtime/cheat-sheet-latex';build.mkdir(parents=True,exist_ok=True)
 for _ in range(2):
  result=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error','-output-directory='+str(build),str(OUT/(stem+'.tex'))],cwd=OUT,capture_output=True,text=True,encoding='utf8',errors='replace')
  (build/'console.txt').write_text(result.stdout+result.stderr,encoding='utf8')
  if result.returncode:raise RuntimeError('XeLaTeX başarısız: '+str(build/'console.txt'))
 import shutil
 shutil.copy2(build/(stem+'.pdf'),OUT/(stem+'.pdf'))
print('Üretildi:',stem,'· 7 hafta')
