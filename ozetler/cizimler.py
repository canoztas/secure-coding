"""Aynı çizim verisinden arama yapılabilir SVG ve yerel TikZ üretir."""
from html import escape

def drawing(kind):
    shapes=[]
    def box(x,y,w,h,fill='F5F6F8'):
        shapes.append(('rect',x,y,w,h,fill))
    def text(x,y,value,size=21,bold=False):
        shapes.append(('text',x,y,value,size,bold))
    def arrow(x1,y1,x2,y2):
        shapes.append(('arrow',x1,y1,x2,y2))
    if kind=='stride':
        entries=[
            ('S','Spoofing','Kimliğe bürünme',['Bob’un oturumunu','ele geçirip kullanmak.']),
            ('T','Tampering','İzinsiz değiştirme',['Fatura tutarını','100’den 900’e çevirmek.']),
            ('R','Repudiation','İşlemi inkâr',['Onayı kimin verdiğinin','gösterilememesi.']),
            ('I','Information Disclosure','Bilgi ifşası',['Başka şirketin','faturasını okumak.']),
            ('D','Denial of Service','Hizmet engelleme',['Ağır isteklerle servisi','kullanılamaz hâle getirmek.']),
            ('E','Elevation of Privilege','Yetki yükseltme',['Üye hesabıyla yönetici','işlemini çalıştırmak.']),
        ]
        for i,(letter,en,tr,example) in enumerate(entries):
            x=(i%3)*340;y=(i//3)*142
            box(x,y,320,130)
            text(x+14,y+35,letter,33,True)
            text(x+57,y+29,en,21,True)
            text(x+57,y+56,tr,21)
            for j,line in enumerate(example):text(x+14,y+88+j*25,line,20)
        height=274
    elif kind=='sqli':
        for x in [0,350,700]:box(x,0,300,110)
        text(14,26,'Girdi / Input',22,True)
        text(14,61,'id = 1 OR 1=1',23)
        text(364,26,'Sorgu / Query',22,True)
        text(364,59,'WHERE id = 1 OR 1=1',22)
        text(364,91,'Koşul her satırda doğru.',20)
        text(714,26,'Sonuç / Result',22,True)
        text(714,61,'Alice + Bob',24)
        text(714,91,'İki kayıt da döner.',20)
        arrow(305,55,343,55);arrow(655,55,693,55)
        height=112
    elif kind=='lfi':
        for x in [0,350,700]:box(x,0,300,120)
        text(14,26,'İstenen sayfa / Page',22,True)
        text(14,61,'../private/note.txt',22)
        text(364,26,'Dosya yolu / File path',22,True)
        text(364,58,'/app/pages/../private/',21)
        text(364,84,'note.txt',21)
        text(714,26,'Dahil edilen / Included',22,True)
        text(714,60,'/app/private/note.txt',21)
        text(714,92,'pages/ klasörü dışında.',20)
        arrow(305,60,343,60);arrow(655,60,693,60)
        height=122
    elif kind=='authorization_case':
        box(0,12,235,138)
        text(14,40,'Alice · Üye / Member',19,True)
        text(14,73,'Şirket / Company: A',20)
        text(14,103,'Kendi faturası: 101',20)
        text(14,131,'102’yi okumak istiyor.',19)
        box(340,12,320,154,'EFF3F9')
        text(355,40,'102 · Bob’un faturası',23,True)
        text(355,73,'Şirket: A · Tutar: 3.000',21)
        text(355,105,'Durum / Status: taslak',21)
        text(355,137,'Sahip / Owner: Bob',21)
        box(765,12,235,138)
        text(778,40,'Deniz · Muhasebeci',19,True)
        text(778,71,'Accountant · Şirket A',19)
        text(778,103,'Onay limiti: 5.000',20)
        text(778,131,'102’yi onaylayabilir.',19)
        text(249,78,'GET 102',18)
        arrow(241,95,332,95)
        text(682,78,'Onay',18)
        text(269,121,'Ret',18)
        text(698,121,'İzin',18)
        arrow(758,95,667,95)
        height=171
    elif kind=='jwt_route':
        for x in [0,350,700]:box(x,0,300,98)
        for x,title,line in [(14,'Sunucu / Server','İmzalı token üretir.'),(364,'İstemci / Client','Token’ı saklar ve taşır.'),(714,'API','İmza, süre ve izin kontrolü.')]:
            text(x,31,title,23,True);text(x,70,line,20)
        arrow(305,49,343,49);arrow(655,49,693,49)
        height=100
    elif kind in ['login_route','log_route']:
        entries=(
            [('Girişi başlat','Start login'),('Kimliği doğrula','Authenticate'),('Dönüşü denetle','Validate return'),('Oturum aç','App session')]
            if kind=='login_route' else
            [('Topla / Collect','Uygulama kayıtları'),('Ayrıştır / Parse','Zaman, kullanıcı'),('Göster / Visualize','Zaman grafiği'),('Uyar / Alert','Kural veya ML')]
        )
        for i,(title,line) in enumerate(entries):
            x=i*260;box(x,0,220,90)
            text(x+12,31,title,21,True);text(x+12,67,line,19)
            if i<3:arrow(x+225,45,x+253,45)
        height=92
    elif kind=='rce_route':
        for x in [0,350,700]:box(x,0,300,54)
        for x,label in [(14,'Girdi / Input'),(364,'Zafiyet / Vulnerability'),(714,'Kod çalışır / Execution')]:
            text(x,35,label,21,True)
        arrow(305,27,343,27);arrow(655,27,693,27)
        height=56
    elif kind=='http':
        entries=[
            ('1xx','Bilgilendirme','Informational','F5F6F8',['100 Continue — Devam et']),
            ('2xx','Başarılı','Successful','EEF5F0',['200 OK — Başarılı · 201 Created — Oluşturuldu', '204 No Content — Yanıt gövdesi yok']),
            ('3xx','Yönlendirme','Redirection','EFF3F9',['303 See Other — Diğer adrese GET ile git', '304 Not Modified — Temsil değişmedi']),
            ('4xx','İstemci hatası','Client Error','FBF5EC',['400 Bad Request — Bozuk istek · 404 Not Found — Bulunamadı', '409 Conflict — Çakışma · 429 Too Many Requests — Çok fazla istek']),
            ('5xx','Sunucu hatası','Server Error','F9EEEE',['500 Internal Server Error — İç hata · 503 Service Unavailable — Hizmet yok', '502 Bad Gateway — Geçersiz yanıt · 504 Gateway Timeout — Zaman aşımı']),
        ]
        for i,(number,tr,en,fill,examples) in enumerate(entries):
            y=i*76;box(0,y,1000,69,fill)
            text(15,y+43,number,32,True)
            text(122,y+28,tr,21,True);text(122,y+54,en,19)
            for j,line in enumerate(examples):text(340,y+28+j*27,line,18)
        # Aynı kaynak, farklı kimlik bağlamı: iki ayrı yanıt.
        for i,(middle,status,label) in enumerate([
            ('Kimlik bilgisi yok / No credentials','401 Unauthorized','Geçerli kimlik bilgisi gerekli'),
            ('Alice: yönetici değil / Not an admin','403 Forbidden','Erişim yasak'),
        ]):
            y=391+i*78
            box(0,y,205,66,'FFFFFF');text(12,y+27,'İstek / Request',21,True);text(12,y+53,'GET /admin',21)
            box(256,y,388,66,'FFFFFF');text(270,y+39,middle,20)
            box(695,y,305,66,'FFFFFF');text(708,y+28,status,23,True);text(708,y+53,label,19)
            arrow(210,y+33,249,y+33);arrow(649,y+33,688,y+33)
        height=538
    else:
        raise ValueError(kind)
    return height,shapes

def svg(kind):
    height,shapes=drawing(kind)
    out=[f'<svg class="diagram diagram-{kind}" xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 1004 {height+4}" role="img" aria-label="{kind.upper()} açıklama çizimi">',
         '<defs><marker id="a-'+kind+'" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#465c74"/></marker></defs>']
    for item in shapes:
        if item[0]=='rect':
            _,x,y,w,h,fill=item
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#{fill}" stroke="#b9c3cd" stroke-width="1.2"/>')
        elif item[0]=='text':
            _,x,y,value,size,bold=item
            out.append(f'<text x="{x}" y="{y}" fill="#222b35" font-size="{size}" font-weight="{700 if bold else 400}">{escape(value)}</text>')
        else:
            _,x1,y1,x2,y2=item
            out.append(f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="#465c74" stroke-width="2" marker-end="url(#a-{kind})"/>')
    return ''.join(out)+'</svg>'

def tikz(kind,tex_escape):
    height,shapes=drawing(kind)
    out=[r'\par\noindent\begin{tikzpicture}[x=.00099\linewidth,y=-.00099\linewidth]',
         f'\\path[use as bounding box] (0,0) rectangle (1000,{height});']
    colors={item[5] for item in shapes if item[0]=='rect'}
    for color in colors:out.append(r'\definecolor{v'+color+r'}{HTML}{'+color+'}')
    for item in shapes:
        if item[0]=='rect':
            _,x,y,w,h,fill=item
            out.append(f'\\draw[draw=diagramline,line width=.4pt,fill=v{fill}] ({x},{y}) rectangle ({x+w},{y+h});')
        elif item[0]=='text':
            _,x,y,value,size,bold=item
            # SVG baseline = TikZ base west. Scale is about 0.5 pt per unit.
            font=round(size*.4989,2)
            out.append(f'\\node[anchor=base west,inner sep=0pt,text=diagramink,font=\\fontsize{{{font}}}{{{font*1.15:.2f}}}\\selectfont'+(r'\bfseries' if bold else '')+f'] at ({x},{y}) {{{tex_escape(value)}}};')
        else:
            _,x1,y1,x2,y2=item
            out.append(f'\\draw[-{{Stealth[length=1.6mm]}},draw=diagramarrow,line width=.6pt] ({x1},{y1}) -- ({x2},{y2});')
    return '\n'.join(out)+r'\end{tikzpicture}\par'+'\n'
