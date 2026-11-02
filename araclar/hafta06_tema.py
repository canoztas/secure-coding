"""Mevcut 6. haftanın içeriğini koruyarak koyu temayı uygular."""
from pathlib import Path
import re
from bs4 import BeautifulSoup
from pygments.formatters import HtmlFormatter
from kod_renkleri import LessonCodeStyle

ROOT=Path(__file__).resolve().parent.parent
path=ROOT/'slaytlar/hafta06.html'
soup=BeautifulSoup(path.read_text(encoding='utf8'),'html.parser')
theme=soup.find('style',id='hafta06-koyu-tema')
if theme is None:
    theme=soup.new_tag('style',id='hafta06-koyu-tema')
    soup.head.append(theme)
theme.string=Path(__file__).with_name('hafta06.css').read_text(encoding='utf8')+'\n'+HtmlFormatter(style=LessonCodeStyle).get_style_defs('.codebox')
for script in soup.find_all('script'):
    if script.string:
        script.string=re.sub(r"box\.style\.borderColor=ok\?'#[0-9a-f]+':'#[0-9a-f]+';box\.style\.background=ok\?'#[0-9a-f]+':'#[0-9a-f]+';",
                             "box.style.borderColor=ok?'#7bdcc8':'#ff9c9c';box.style.background=ok?'#183338':'#382830';",script.string)
soup.html['data-theme']='dark'
path.write_text(str(soup),encoding='utf8')
print('Hafta 6: koyu tema uygulandı; içerik ve erişim denemesi korundu.')
