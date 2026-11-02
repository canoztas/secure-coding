"""7. hafta sunumu. Çıktı, fontlar ve GIF'lerle birlikte çevrimdışı çalışır."""
from pathlib import Path
from html import escape as e
import re, json, base64
from bs4 import BeautifulSoup
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.lexer import RegexLexer, bygroups
from pygments.formatters import HtmlFormatter
from pygments.token import Token, Text, Keyword, Name, Literal, Comment, Operator, Punctuation, Error
from kod_renkleri import LessonCodeStyle

ROOT=Path(__file__).resolve().parent.parent
previous=BeautifulSoup((ROOT/'slaytlar/hafta06.html').read_text(encoding='utf8'),'html.parser')
fontcss='\n'.join(re.findall(r'@font-face\s*\{[^}]+\}',previous.find('style').string))

class LessonExampleLexer(RegexLexer):
 """HTTP/JSON/kod karışımı anlatım örneklerinde anlamlı parçaları renklendirir."""
 tokens={'root':[
  (r'(?m)^(\s*)(#[^\n]*)',bygroups(Text,Comment.Single)),
  (r'"(?:\\.|[^"\\])*"(?=\s*:)',Name.Tag),
  (r'\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b',Keyword.Reserved),
  (r'\b(?:if|else|return|True|False|None|true|false|null)\b',Keyword),
  (r'[A-Za-z_][\w.-]*(?=\s*=)',Name.Attribute),
  (r'"(?:\\.|[^"\\])*"',Literal.String.Double),
  (r"'(?:\\.|[^'\\])*'",Literal.String.Single),
  (r'https?://[^\s&"<>]+',Literal.String),
  (r'\b\d+(?:\.\d+)?\b',Literal.Number),
  (r'\b[A-Za-z_]\w*(?=\s*\()',Name.Function),
  (r'\b[A-Za-z_]\w*',Name),
  (r'[{}\[\](),.:]',Punctuation),
  (r'[=+&?!<>|*/-]+',Operator),
  (r'\s+',Text.Whitespace),
  (r'.',Text),
 ]}
S={
 'jwt':('RFC 7519 · JWT','https://www.rfc-editor.org/rfc/rfc7519.html'),
 'jws':('RFC 7515 · JWS','https://www.rfc-editor.org/rfc/rfc7515.html'),
 'jwk':('RFC 7517 · JWK / JWKS','https://www.rfc-editor.org/rfc/rfc7517.html'),
 'jwtbcp':('RFC 8725 · JWT güvenliği','https://www.rfc-editor.org/rfc/rfc8725.html'),
 'oauth':('RFC 6749 · OAuth 2.0','https://www.rfc-editor.org/rfc/rfc6749.html'),
 'bearer':('RFC 6750 · Bearer token','https://www.rfc-editor.org/rfc/rfc6750.html'),
 'bcp':('RFC 9700 · OAuth güvenliği','https://www.rfc-editor.org/rfc/rfc9700.html'),
 'pkce':('RFC 7636 · PKCE','https://www.rfc-editor.org/rfc/rfc7636.html'),
 'oidc':('OpenID Connect Core 1.0','https://openid.net/specs/openid-connect-core-1_0.html'),
 'discovery':('RFC 8414 · Sunucu metadata’sı','https://www.rfc-editor.org/rfc/rfc8414.html'),
 'saml':('OASIS · SAML 2.0','https://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf'),
 'introspection':('RFC 7662 · Introspection','https://www.rfc-editor.org/rfc/rfc7662.html'),
 'revoke':('RFC 7009 · Token iptali','https://www.rfc-editor.org/rfc/rfc7009.html'),
 'pyjwt':('PyJWT · Kullanım belgeleri','https://pyjwt.readthedocs.io/en/stable/usage.html'),
 'logs':('OWASP · Logging Cheat Sheet','https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html'),
 'authz':('OWASP · Authorization Cheat Sheet','https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html'),
 'github':('GitHub · OAuth token hırsızlığı · 2022','https://github.blog/news-insights/company-news/security-alert-stolen-oauth-user-tokens/'),
 'okta':('Okta · Destek sistemi olayı · 2023','https://sec.okta.com/articles/2023/11/unauthorized-access-oktas-support-case-management-system-root-cause/'),
 'avengers':('The Avengers · Tony Stark · 2012','https://clip.cafe/the-avengers-2012/because-if-we-cant-protect-the-earth-you-can-be-damn-well-sure-well-avenge-it/'),
 'jwtalg':('RFC 7518 · Anahtarlar ve algoritmalar','https://datatracker.ietf.org/doc/html/rfc7518#section-3'),
 'session':('OWASP · Oturum ve tarayıcıda saklama','https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html'),
 'parsing':('Microsoft · JSON verisini ayrıştırma','https://learn.microsoft.com/en-us/kusto/query/parse-json-function'),
 'visual':('Microsoft · Zaman grafikleri','https://learn.microsoft.com/en-us/kusto/query/visualization-timechart?view=microsoft-fabric'),
 'ml':('Elastic · Makine öğrenmesiyle anomali tespiti','https://www.elastic.co/docs/explore-analyze/machine-learning/anomaly-detection'),
 'rce':('MITRE · CWE-94 · Kod enjeksiyonu','https://cwe.mitre.org/data/definitions/94.html'),
 'log4j':('Apache · Log4Shell · CVE-2021-44228','https://logging.apache.org/security.html#CVE-2021-44228'),
 'upload':('OWASP · Dosya yükleme güvenliği','https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html'),
 'sqli':('MITRE · CWE-89 · SQL enjeksiyonu','https://cwe.mitre.org/data/definitions/89.html'),
 'vader':('Star Wars · Darth Vader · GIF','https://tenor.com/view/star-wars-darth-vader-dark-side-power-of-the-dark-side-if-you-only-knew-the-power-of-the-dark-side-gif-4826489'),
}
slides=[]
def p(t,cls=''):return f'<p class="{cls}">{t}</p>'
def note(t):return p(t,'note')
def code(t,lang='python',size=28):
 lexer=LessonExampleLexer() if lang=='text' else get_lexer_by_name(lang)
 return f'<div class="codebox" data-language="{e(lang)}" style="font-size:{size}px">'+highlight(t.strip(),lexer,HtmlFormatter(nowrap=True)).join(('<pre>','</pre>'))+'</div>'
def cols(a,b):return '<div class="cols"><div>'+a+'</div><div>'+b+'</div></div>'
def table(headers,rows):
 return '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+c+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'
def bullets(items):return '<ul>'+''.join('<li>'+x+'</li>' for x in items)+'</ul>'
def add(title,body,refs=(),cls='',speaker=''):
 slides.append(dict(title=title,body=body,refs=refs,cls=cls,speaker=speaker))
def gif(n):
 panel=previous.select('figure.gif-panel')[n]
 return str(panel)
def avengers_gif():
 media=ROOT/'slaytlar/medya'
 motion=base64.b64encode((media/'avengers-avenge.gif').read_bytes()).decode('ascii')
 still=base64.b64encode((media/'avengers-avenge.png').read_bytes()).decode('ascii')
 return f'<figure class="gif-panel"><a class="gif-link" href="{S["avengers"][1]}" target="_blank" rel="noreferrer"><img class="gif-motion" src="data:image/gif;base64,{motion}" alt="The Avengers: Tony Stark, Loki ile konuşuyor."><img class="gif-still" src="data:image/png;base64,{still}" alt="Tony Stark · The Avengers, 2012"></a></figure>'

def darkside_gif():
 media=ROOT/'slaytlar/medya'
 motion=base64.b64encode((media/'darth-vader-dark-side.gif').read_bytes()).decode('ascii')
 still=base64.b64encode((media/'darth-vader-dark-side.png').read_bytes()).decode('ascii')
 return f'''<figure class="gif-panel darkside-media"><a class="gif-link" href="{S['vader'][1]}" target="_blank" rel="noreferrer"><img class="gif-motion" src="data:image/gif;base64,{motion}" alt="Darth Vader, karanlık tarafın gücünden söz ediyor."><img class="gif-still" src="data:image/png;base64,{still}" alt="Darth Vader · Star Wars"></a></figure>'''
def flow(items,cls=''):return f'<div class="flow {cls}">'+'<b aria-hidden="true">→</b>'.join('<div>'+x+'</div>' for x in items)+'</div>'

def sequence(actors,messages):
 """SVG text stays searchable in PDF; each message is an explicit network hop."""
 xs=[150+i*(1360/(len(actors)-1)) for i in range(len(actors))]
 height=155+len(messages)*88
 marker=f'arrow-{len(slides)+1}'
 out=[f'<svg class="sequence" viewBox="0 0 1660 {height}" role="img" aria-label="'+e('; '.join(t for _,_,t in messages))+'">',
 f'<defs><marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrow-head" d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>']
 for x,a in zip(xs,actors):
  out.append(f'<text x="{x}" y="38" text-anchor="middle" font-size="28" font-weight="600">{e(a)}</text><path class="lifeline" d="M{x} 60 V{height-12}" stroke-dasharray="7 7"/>')
 for i,(a,b,t) in enumerate(messages):
  y=120+i*88
  out.append(f'<path class="message-line" d="M{xs[a]} {y} H{xs[b]}" stroke-width="2" marker-end="url(#{marker})"/><text x="{(xs[a]+xs[b])/2}" y="{y-16}" text-anchor="middle" font-size="25">{e(t)}</text>')
 out.append('</svg>');return ''.join(out)

def login_chart():
 """Temsili başarısız giriş sayıları; bir ML modelinin çıktısı değildir."""
 values=[2,3,2,1,32,3]
 out=['<svg class="log-chart" viewBox="0 0 1000 315" role="img" aria-label="Dakikadaki başarısız giriş sayıları: 2, 3, 2, 1, 32, 3. Beşinci dakikadaki artış incelenmeli.">',
      '<text x="45" y="28" font-size="23">Örnek veri · Başarısız giriş / dakika</text>',
      '<path class="chart-axis" d="M45 45 V258 H970"/>']
 for i,value in enumerate(values):
  x=82+i*145;height=value*5.6;y=258-height
  cls='chart-bar alert-bar' if i==4 else 'chart-bar'
  out.append(f'<rect class="{cls}" x="{x}" y="{y}" width="86" height="{height}"/><text x="{x+43}" y="{y-12}" text-anchor="middle" font-size="23">{value}</text><text x="{x+43}" y="292" text-anchor="middle" font-size="21">12:{10+i:02d}</text>')
 out.append('</svg>');return ''.join(out)

add('JWT, OAuth ve SSO',
 cols(p('Kurumsal giriş ve güvenli loglama','lead')+
      p('Bir fatura uygulamasında girişin, erişimin ve olay kaydının nasıl çalıştığı.'),gif(1)),
 cls='cover')

add('Kurumsal hesapla giriş',
 flow(['Alice','Fatura uygulaması','Kurumsal giriş hizmeti'])+
 p('Alice, “Kurumsal hesapla giriş” düğmesine basıyor. Hesabını doğruladıktan sonra faturalarına dönüyor.')+
 p('Uygulama, giriş sonucunu kontrol edip Alice için kendi oturumunu açıyor.'))

add('Dört isim, dört farklı görev',
 table(['İsim','Bu dersteki anlamı'],[
  ['JWT · JSON Web Token','Kullanıcı ve erişim bilgilerini taşıyabilen bir veri biçimi.'],
  ['OAuth 2.0','Bir uygulamaya sınırlı API erişimi verme yöntemi.'],
  ['OpenID Connect','OAuth üzerine kurulan, giriş yapan kullanıcının kimliğini doğrulayan standart.'],
  ['SSO · Single Sign-On','Tek oturum açma: bir girişin birden fazla uygulamada kullanılabilmesi.'],
 ])+note('OAuth kullanılması, access token’ın mutlaka JWT biçiminde olacağı anlamına gelmez.'),
 ('jwt','oauth','oidc'))

add('JWT içinde ne var?',
 code('''{
  "sub": "user-42",
  "aud": "fatura-api",
  "exp": 1793020200
}''','json',34)+
 table(['Alan','Örnekteki anlamı'],[
  ['sub','Hangi kullanıcı?'],['aud','Bu token’ı hangi uygulama veya API kabul edebilir?'],
  ['exp','Ne zamana kadar geçerli?'],
 ])+note('Bu, imzalı JWT’nin veri bölümüdür. İçeriği okunabilir; parola veya gizli anahtar konulmaz.'),
 ('jwt',))

add('JWT için iki anahtar düzeni',
 table(['Yöntem','Token’ı üreten hizmet','API doğrulaması'],[
  ['Simetrik · HS256','Ortak gizli anahtarla doğrulama etiketi üretir.','Aynı gizli anahtarı kullanır.'],
  ['Asimetrik · RS256','Özel anahtarla imzalar.','Açık anahtarla doğrular.'],
 ])+
 flow(['Giriş hizmeti: özel anahtar','İstemci: imzalı JWT','API: açık anahtar'])+
 note('HS256’da ortak anahtarı bilen doğrulayıcı da token üretebilir. RS256’da yalnız açık anahtarı olan API imza üretemez. Token üreten hizmetin gizli veya özel anahtarı tarayıcıya verilmez.'),
 ('jwtalg','jwtbcp'),cls='jwt-keys')

add('JWT istemcide mi tutulur?',
 flow(['Sunucu token’ı üretir','İstemci token’ı saklar','İstekle API’ye gönderir'])+
 table(['Tarayıcıdaki yer','Dikkat edilecek nokta'],[
  ['HttpOnly çerez · Cookie','JavaScript okuyamaz; tarayıcı uygun isteklere ekler. Siteler arası istek koruması ayrıca gerekir.'],
  ['localStorage / sessionStorage','JavaScript okuyabilir. XSS varsa token ele geçirilebilir.'],
 ])+
 p('Kullanıcı ve süre bilgisi token’ın içinde taşınabilir. İmzalı içerik okunabilir; API her istekte imzayı ve izinleri kontrol eder.')+
 note('Bu, tarayıcıda token tutulan örnektir. JWT sunucuda da saklanabilir; hesap, izin ve iptal kayıtları ayrıca tutulabilir.'),
 ('session','jwt'),cls='jwt-storage')

add('İçeriği değiştirmek yetki kazandırmamalı',
 flow(['Kullanıcı bilgisini değiştir','İmza artık uyuşmaz','İstek reddedilir'])+
 p('Saldırgan, token’ın içindeki kullanıcıyı Alice yerine Bob yapabilir. API imzayı doğruluyorsa değişiklik fark edilir.')+
 p('İmza doğrulanmadan okunan kullanıcı veya rol bilgisiyle erişim verilmez.'),('jwtbcp',))

add('API token’da neleri kontrol eder?',
 table(['Kontrol','Sorulacak soru'],[
  ['İmza','Token’ın içeriği değiştirilmiş mi?'],
  ['Üretici','Token güvendiğimiz giriş hizmetinden mi geliyor?'],
  ['Hedef','Bu token bizim API’miz için mi üretilmiş?'],
  ['Süre','Hâlâ geçerli mi?'],
 ])+note('Bu kontroller geçse bile kullanıcının istenen faturaya erişim izni ayrıca denetlenir.'),
 ('jwtbcp','authz'))

add('Kısa bir JWT doğrulama örneği',
 code('''import jwt

def verify_token(token, public_key):
    return jwt.decode(
        token, public_key, algorithms=["RS256"],
        issuer="https://idp.example.test/",
        audience="fatura-api",
        options={"require": ["exp", "iss", "aud", "sub"]}
    )''',size=30)+
 p('public_key, güvenilir giriş hizmetinden alınmış açık anahtardır. Doğrulama başarısızsa istek reddedilir.'),
 ('pyjwt','jwtbcp'))

add('Geçerli token, her faturaya erişim izni vermez',
 code('''GET /invoices/102 HTTP/1.1
Host: api.example.test
Authorization: Bearer <access_token>''','http',32)+
 flow(['Alice’in kimliği doğrulandı','102 numaralı fatura Bob’un','Erişim reddedilir'])+
 p('6. haftadaki şirket ve sahiplik kontrolleri burada da uygulanır.'),('bearer','authz'))

add('OAuth: başka bir uygulamaya sınırlı izin',
 cols(p('Alice, raporlama uygulamasının faturalarını okumasına izin veriyor.')+
      bullets(['Parolasını raporlama uygulamasına vermez.',
               'Uygulama, izin verilen işlemler için bir erişim token’ı alır.',
               'Okuma izni, fatura silme izni anlamına gelmez.']),gif(0)),
 ('oauth',))

add('Kurumsal girişin akışı',
 sequence(['Tarayıcı','Fatura uygulaması','Giriş hizmeti'],[
  (0,1,'1. Girişi başlat'),
  (1,0,'2. Kurumsal giriş sayfasına yönlendir'),
  (0,2,'3. Kimliği doğrula'),
  (2,0,'4. Uygulamaya dönüş için kısa kod'),
  (0,1,'5. Dönüş isteğini gönder'),
 ])+
 note('Uygulama dönüşü doğrular, kodu token ile değiştirir ve kendi oturumunu açar. Bu işlemleri giriş kütüphanesi yürütür.'),
 ('oauth','oidc'),cls='sequence-slide')

add('Giriş sonucu, erişim ve yenileme',
 table(['Değer','Ne için kullanılır?'],[
  ['ID token · Kimlik token’ı','Uygulama, kimin giriş yaptığını doğrular.'],
  ['Access token · Erişim token’ı','Uygulama, izin verilen API işlemlerini yapar.'],
  ['Refresh token · Yenileme token’ı','Uygulama yeni bir erişim token’ı alır. Her zaman verilmez.'],
 ])+p('API’ye erişim token’ı gönderilir. Kimlik token’ı API erişim belgesi olarak kullanılmaz.'),
 ('oauth','oidc'))

add('Girişte dikkat edilecekler',
 table(['Kontrol','Uygulama'],[
  ['Dönüş adresi','Giriş hizmetinde önceden tanımlı adres kullanılır.'],
  ['Giriş denemesi','Dönen yanıt, bu tarayıcıda başlatılan işlemle eşleştirilir.'],
  ['Kodun kullanımı','Kodun ele geçirilmesine karşı PKCE koruması kullanılır.'],
 ])+note('PKCE · Proof Key for Code Exchange: kodu, girişi başlatan istemcinin bildiği değere bağlar. Ayrıntıları standart giriş kütüphanesine bırakıyoruz.'),
 ('bcp','pkce'))

add('SSO: iki uygulamada tek giriş',
 sequence(['Tarayıcı','Fatura','Giriş hizmeti','Rapor'],[
  (0,1,'1. Fatura’yı aç'),
  (0,2,'2. Kurumsal hesapla giriş yap'),
  (0,1,'3. Fatura’da oturum açılır'),
  (0,3,'4. Rapor’u aç'),
  (0,2,'5. Mevcut giriş oturumu kullanılır'),
  (0,3,'6. Rapor’da ayrı oturum açılır'),
 ])+note('Rapor yeniden parola istemeyebilir. Yine de kendi giriş sonucunu kontrol eder; iki uygulamanın oturumları ayrıdır.'),
 ('oidc',),cls='sequence-slide')

add('Çıkış yaptığımda ne kapanır?',
 table(['İşlem','Beklenen etki'],[
  ['Fatura’dan çıkış','Fatura uygulamasındaki oturum kapanır.'],
  ['Kurumsal girişten çıkış','Diğer uygulamalara etkisi, ortak çıkış ayarlarına bağlıdır.'],
  ['Bir token’ın kopyasını saklamak','Kopyanın geçerliliği, süre ve iptal kontrollerine bağlıdır.'],
 ])+p('Deneme: Fatura’dan çıkın, Rapor’u yenileyin ve eski token ile API’ye tekrar istek gönderin.'),
 ('revoke','oidc'))

add('Çalınan token da kullanılabilir',
 flow(['Geçerli token','Başkasının eline geçer','Aynı token ile istek'])+
 p('Saldırganın token’ı değiştirmesi gerekmez. Geçerli bir kopyayı kullanabilir.')+
 bullets(['Güvenli bağlantı kullanın; token’ı URL’ye veya loga yazmayın.',
          'Erişim süresini ve izinleri sınırlandırın.',
          'Sızıntıda ilgili token ve oturumları iptal edin.']),('bearer','bcp'))

add('GitHub · çalınan entegrasyon token’ları · 2022',
 p('Heroku ve Travis CI entegrasyonlarına verilmiş OAuth token’ları çalındı. Bu token’larla özel depolara erişildi.')+
 flow(['Entegrasyona verilen token','Token’ın ele geçirilmesi','Özel depolara erişim'])+
 p('Bir entegrasyona verilen yetki, o entegrasyonda saklanan token ele geçirildiğinde de kullanılabilir.'),
 ('github',))

add('Loglama ve olay incelemesi',
 cols(p('“If we can’t protect the Earth, you can be damn well sure we’ll avenge it.”','movie-quote')+
      p('Alice saat 12.15’te 102 numaralı faturayı okumayı denedi. İstek reddedildi.')+
      note('Zaman, kullanıcı, kaynak ve sonuç: kayıtta arayacağımız bilgiler.'),avengers_gif()),
 ('avengers',),cls='logging-gif')

add('Loglar nasıl işlenir?',
 flow(['Uygulama kaydı üretir','Kayıtlar ortak yerde toplanır','Alanlara ayrılır','Arama ve grafik'])+
 table(['Adım','Basit örnek'],[
  ['Toplama · Collection','Uygulama ve API kayıtları birlikte incelenebilir.'],
  ['Ayrıştırma · Data parsing','Bir satırdan zaman, kullanıcı ve sonuç alanları çıkarılır.'],
  ['Görselleştirme · Data visualization','Dakikadaki başarısız giriş sayısı grafiğe dökülür.'],
 ])+
 note('Alan adları ve zaman biçimi tutarlı olursa farklı sunucuların kayıtlarını bir arada aramak ve saymak kolaylaşır.'),
 ('logs','parsing','visual'),cls='log-processing')

add('Grafikten anomaliye',
 login_chart()+
 table(['Yöntem','Ne yapar?'],[
  ['Basit kural','Örneğin dakikada 20’den fazla başarısız girişte alarm üretir.'],
  ['ML · Machine Learning / Makine öğrenmesi','Yeterli geçmiş veriden olağan düzeni öğrenip farklı saat, hesap veya kaynaklardaki sapmaları işaretleyebilir.'],
 ])+
 note('Artış bir saldırı, uygulama hatası veya yoğun kullanım olabilir. Alarmın nedeni incelenir; modelin işaretlediği her olay saldırı değildir.'),
 ('visual','ml'),cls='log-anomaly')

add('İşe yarayan bir log kaydı',
 code('''{
  "time": "2026-10-26T12:15:00Z",
  "event": "invoice.read",
  "actor_id": "alice",
  "invoice_id": 102,
  "result": "denied",
  "reason": "not_owner",
  "request_id": "r-7f3c21"
}''','json',30)+
 p('Kim, ne zaman, hangi kayda erişmek istedi? Sonuç neydi, neden reddedildi?')+
 note('Kullanıcı bilgisi, doğrulanmış oturumdan alınır.'),('logs',))

add('Log seviyeleri',
 table(['Seviye','Ne zaman?','Örnek'],[
  ['DEBUG · Hata ayıklama','Ayrıntılı teşhis gerektiğinde.','Hangi işlem adımına gelindi?'],
  ['INFO · Bilgi','Olağan bir olayda.','Fatura onaylandı.'],
  ['WARNING · Uyarı','İncelenmesi gereken bir durumda.','Tekrarlanan erişim retleri.'],
  ['ERROR · Hata','İşlem beklenmedik biçimde tamamlanamadığında.','Veritabanına ulaşılamadı.'],
 ])+note('Her başarısız giriş aynı önemde değildir. Seviye, olayın bağlamıyla seçilir.'),('logs',))

add('İsteğin tamamını loglamak',
 code('''# Hatalı: parola, çerez ve token kayıtlara sızabilir.
logger.info("headers=%s body=%s",
            dict(request.headers), request.get_json())''',size=31)+
 bullets(['Authorization ve Cookie başlıkları kimlik bilgisi taşıyabilir.',
          'İstek gövdesi parola veya kişisel veri içerebilir.',
          'Kaydedeceğimiz alanları önceden seçelim.']),('logs',))

add('Seçilmiş alanlarla kayıt',
 code('''import json

def log_denied_read(logger, user, invoice):
    event = {"event": "invoice.read",
             "actor_id": user.id,
             "invoice_id": invoice.id,
             "result": "denied"}
    logger.info(json.dumps(event, ensure_ascii=False))''',size=30)+
 p('Kullanıcı doğrulanmış oturumdan gelir. Zaman ve istek kimliği log altyapısında eklenir.')+
 note('JSON ile yazmak, girdideki satır sonlarının ayrı bir olay gibi görünmesini de önler.'),('logs',))

add('Okta · destek dosyasından sızan oturum · 2023',
 p('Destek için yüklenen bazı ağ kayıtlarında geçerli oturum token’ları vardı. Dosyaları ele geçiren saldırgan, bu token’larla müşteri oturumlarını kullandı.')+
 flow(['Tarayıcı ağ kaydı','Destek sistemine yükleme','Token’ın ele geçirilmesi','Hesaba erişim'],'incident-flow')+
 p('Hata ayıklama dosyalarını paylaşmadan önce kimlik bilgilerini temizlemek gerekir.'),('okta',),cls='okta-case')

add('Kısa kod incelemesi',
 code('''claims = jwt.decode(token, options={"verify_signature": False})
invoice = db.get_invoice(request.args["id"])
logger.info("token=%s", token)
return invoice.to_json()''',size=32)+
 p('Kimlik hangi satırda doğrulanıyor? Fatura kime ait? Loga hangi bilgi gidiyor?'))

add('İncelemenin sonucu',
 table(['Sorun','Düzeltme'],[
  ['Token doğrulanmıyor.','İmza, üretici, hedef ve süre kontrol edilir.'],
  ['Faturaya erişim izni yok sayılıyor.','Şirket ve sahiplik kontrolü uygulanır.'],
  ['Token loga yazılıyor.','Yalnız gerekli olay alanları kaydedilir.'],
 ])+p('Yanlış token, başka kullanıcının faturası ve loga bilgi sızması ayrı ayrı denenir.'))

add('Dosya yükleme / File upload',
 p('Alice faturaya bir görsel ekliyor. Sunucu dosyanın türüne ve adına güvenebilir mi?')+
 cols(code('''# Hatalı örnek · Sözde kod / Pseudocode
require_login()
file = request.file("attachment")
if file.content_type != "image/jpeg":
    reject(415)
file.save("/var/www/uploads/" + file.name)
return "/uploads/" + file.name''','text',26),
 bullets(['Content-Type (içerik türü) başlığını istemci belirler; dosyanın gerçekten görsel olduğunu kanıtlamaz.',
          'Dosya adı da kullanıcı girdisidir. Hedef yolu kullanıcı seçmemeli.',
          'Giriş yapmak, bu faturaya dosya ekleme veya eki okuma izni vermez.']))+
 note('Koda bakarak tartışalım: boyut sınırı nerede, içerik nasıl doğrulanıyor, dosyaya kim erişebiliyor?'),
 ('upload','authz'),cls='file-upload-review upload-theme')

add('Dosyayı kabul ettik. Peki sonra?',
 flow(['Yükleme isteği','Özel bekleme alanı','Sunucuda kontroller','Özel depolama'])+
 table(['Kontrol','Bu uygulamada ne yaparız?'],[
  ['Tür ve içerik / Type and content','Yalnız gereken türleri kabul et; uzantıyı ve gerçek içeriği birlikte doğrula.'],
  ['Boyut / Size','Yükleme boyutunu sınırla; görsel boyutlarına ve işleme süresine de sınır koy.'],
  ['Ad ve konum / Name and location','Sunucu yeni bir dosya adı üretir. Dosya, web kökünün dışında saklanır; kod olarak çalıştırılmaz.'],
  ['Erişim / Access','Yükleme ve indirmede fatura iznini denetle. Dosya inceleme araçlarını güncel ve sınırlı yetkili tut.'],
 ])+
 note('Dosya yüklemek tek başına RCE değildir. Sunucu yüklenen içeriği kod olarak çalıştırırsa veya dosyayı işleyen bileşende kullanılabilir bir zafiyet varsa RCE’ye dönüşebilir.'),
 ('upload',),cls='file-upload-controls upload-theme')

add('Zafiyetlerin kralı: RCE',
 darkside_gif()+
 p('Uzaktan kod çalıştırma / Remote Code Execution','lead')+
 flow(['Uzaktan gelen istek','Zafiyetli uygulama','Saldırganın kodu çalışır'],'incident-flow')+
 bullets(['Dosyaları ve erişim anahtarlarını okuyabilir.',
          'Verileri değiştirebilir veya silebilir.',
          'Erişebildiği diğer servislere ilerleyebilir.'])+
 note('RCE otomatik olarak root veya yönetici olmak demek değildir. Kod, uygulamanın çalıştığı hesabın yetkileriyle çalışır.'),
 ('rce',),cls='rce-intro darkside-theme')

add('Zafiyetin türü başka, etkisi başka',
 flow(['Zafiyetin türü / Weakness type','Kullanılma koşulu / Exploit condition','Teknik etki / Technical impact'])+
 table(['Hata nerede?','Hangi koşulda?','Saldırgan ne yapabiliyor?'],[
  ['Tehlikeli dosya yükleme / Unsafe file upload','Yüklenen dosya sunucuda kod olarak çalıştırılıyor.','RCE · Uzaktan kod çalıştırma.'],
  ['Komut enjeksiyonu / Command injection','Kullanıcı girdisi sunucunun çalıştırdığı komuta karışıyor.','Uygulamanın yetkileriyle komut çalıştırma; uzaktan tetiklenirse RCE.'],
  ['SQL enjeksiyonu / SQL injection','Kullanıcı girdisi SQL sorgusunun yapısını değiştiriyor.','İzinsiz veri okuma veya değiştirme; otomatik olarak RCE değildir.'],
 ])+
 p('Kod çalıştırmanın iş etkisi: faturaların sızması, kayıtların değiştirilmesi veya hizmetin durması olabilir.')+
 note('“RCE var” ifadesi etkiyi anlatır; hatanın kök nedenini tek başına açıklamaz. Aynı etki farklı zafiyet türlerinden doğabilir.'),
 ('upload','sqli','rce'),cls='rce-cause-impact darkside-theme')

add('Bir RCE örneği: Log4Shell',
 p('Log4j’nin etkilenen sürümlerinde özel hazırlanmış bir log girdisi, koşullar uygunsa uzaktan kod çalıştırılmasına yol açabiliyordu.')+
 flow(['Saldırganın girdisi','Zafiyetli Log4j bileşeni','Sunucuda kod çalışması'],'incident-flow')+
 table(['Zafiyetin nedeni / Weakness','Teknik etki / Technical impact'],[
  ['Güvenilmeyen log verisi, saldırganın denetlediği dış kaynaklara başvuran arama (lookup) mekanizmasını tetikleyebiliyordu.','RCE · Uygulamanın çalıştığı makinede saldırganın kodu çalışabiliyordu.'],
 ])+
 p('CVE-2021-44228 · 2021. Veri olarak kaydedilmesi gereken girdi, kod çalıştırmaya uzanan bir işlem zincirini başlatıyordu.')+
 note('RCE farklı zafiyetlerden doğabilir: komut enjeksiyonu, güvensiz veri işleme veya bellek hataları. Log4Shell burada yalnız bir örnek.'),
 ('log4j','rce'),cls='rce-example darkside-theme')

add('Sorular ve tartışma',
 cols(p('Bir token geçerliyken erişim neden reddedilebilir?')+
      p('Bir uygulamadan çıkınca diğeri neden açık kalabilir?')+
      p('Token’ı kaydetmeden bir olayı nasıl inceleriz?'),gif(4)))

keys=['oauth','bcp','jwt','jwtbcp','jwtalg','oidc','logs','ml','github','okta','upload','log4j']
add('Kaynaklar',
 '<div class="sources">'+''.join(
  f'<a href="{S[k][1]}" target="_blank" rel="noreferrer">{e(S[k][0])}</a>'
  for k in keys)+'</div>',cls='source-page')

CSS=Path(__file__).with_name('hafta07.css').read_text(encoding='utf8')
CSS+='\n'+HtmlFormatter(style=LessonCodeStyle).get_style_defs('.codebox')
CSS+='\n.codebox pre{line-height:1.38}.codebox .err{background:none;border:0}'
# Reuse tested navigation, omit the week-6-only permission simulator.
JS=previous.find('script').string.split('  const identities=')[0]+'''
  document.querySelector('#motion').onclick=()=>{
    const paused=document.body.classList.toggle('gif-paused');
    document.querySelector('#motion').setAttribute('aria-pressed',String(paused));
  };
})();'''
# Önceden paylaşılan bağlantılar, ilgili slaytın yeni konumunu açar.
legacy={36:next(i+1 for i,s in enumerate(slides) if s['cls']=='okta-case'),
        30:next(i+1 for i,s in enumerate(slides) if s['cls']=='logging-gif')}
legacy={old:new for old,new in legacy.items() if old>len(slides)}
JS=JS.replace('const v=Number(location.hash.slice(1));',
              'const raw=Number(location.hash.slice(1));const v=('+json.dumps(legacy)+')[raw]??raw;')
parts=[]
for i,s in enumerate(slides,1):
 heading='h1' if i==1 else 'h2'
 title_html='Zafiyetlerin kralı:<span class="rce-name">RCE</span>' if 'rce-intro' in s['cls'].split() else e(s['title'])
 refs=''.join(f'<a href="{S[k][1]}" target="_blank" rel="noreferrer">{e(S[k][0])}</a>' for k in s['refs'])
 parts.append(f'''<section class="deck-slide" id="{i}" aria-roledescription="slide" aria-label="{i} / {len(slides)}: {e(s['title'])}"><div class="deck-fit"><div class="deck-scaler"><div class="sheet {s['cls']}"><header><{heading}>{title_html}</{heading}></header><div class="content" data-check-layout="content">{s['body']}</div><div class="refs">{refs}</div><footer class="footer"><span>Güvenli Kodlama ve Programlama · Hafta 07</span><span>{i:02d} / {len(slides)}</span></footer><aside class="speaker-note">{e(s['speaker'])}</aside></div></div></div></section>''')
document='''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; font-src data:; img-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"><title>Hafta 7 · JWT, OAuth, SSO ve loglama</title><meta name="description" content="JWT anahtarları ve istemcide saklama; OAuth ve SSO; log ayrıştırma, görselleştirme, ML ve anomali tespitine kısa bakış; dosya yükleme güvenliği; zafiyet türü, RCE etkisi ve Log4Shell."><style>'''+fontcss+CSS+'</style></head><body><main aria-label="7. hafta sunumu">'+''.join(parts)+'''</main><nav class="deck-nav" aria-label="Sunum gezinmesi"><span class="keyhint">← → · F</span><button id="prev" aria-label="Önceki slayt">←</button><output id="counter" aria-live="polite"></output><button id="next" aria-label="Sonraki slayt">→</button><button id="fullscreen" aria-label="Tam ekran">⛶</button><button id="motion" aria-label="GIF hareketini durdur veya sürdür" aria-pressed="false">GIF</button></nav><script>'''+JS+'</script></body></html>'
(ROOT/'slaytlar/hafta07.html').write_text(document,encoding='utf8')
print(json.dumps({'slides':len(slides),'bytes':len(document.encode())}))
