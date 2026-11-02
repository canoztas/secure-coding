"""Eğitmen write-up'ından çevrimdışı HTML ve isteğe bağlı PDF üretir."""
from pathlib import Path
from html import escape
import argparse
import markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    source = (root / "COZUMLER.md").read_text(encoding="utf8")
    body = markdown.markdown(source, extensions=["fenced_code", "tables", "attr_list"])
    intro, chapters = body.split("<h2", 1)
    body = '<div class="intro">' + intro + '</div><h2' + chapters
    css = """
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#eceee8;color:#242b26;font:16px/1.65 Georgia,'Times New Roman',serif}
    main{max-width:900px;margin:30px auto;background:#fffefa;padding:55px 65px}h1{font-size:35px;line-height:1.2;font-weight:500;margin:0 0 14px}h2{font-size:26px;line-height:1.3;margin:50px 0 20px;border-top:1px solid #8fa08e;padding-top:20px}h3{font-size:18px;line-height:1.4;margin:25px 0 10px}p{margin:12px 0}a{color:#285b42;text-decoration:underline;text-underline-offset:3px}code{font: .85em/1.6 Consolas,'Liberation Mono',monospace}pre{background:#f0f3eb;border-left:3px solid #9aaa91;padding:14px 17px;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.6}pre code{font:inherit}table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.5;margin:20px 0}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #d6ddd1;padding:9px 10px}th{border-top:1px solid #87957e;background:#f1f3ed;font-weight:600}li{margin:7px 0}strong{font-weight:600}
    @media(max-width:700px){main{margin:0;padding:28px 20px}h1{font-size:29px}h2{font-size:23px}table{font-size:11px}td,th{padding:7px 5px}pre{font-size:11px}}
    @page{size:A4;margin:18mm 18mm 21mm}
    @media print{html{scroll-behavior:auto}body{background:white;font-size:10.2pt;line-height:1.45}main{max-width:none;margin:0;padding:0;background:white}h1{font-size:25pt}h2{break-before:page;font-size:19pt;margin:0 0 12pt;padding-top:0;border-top:0}h3{font-size:11.5pt;margin:15pt 0 6pt;break-after:avoid}p{margin:6pt 0;orphans:3;widows:3}pre{font-size:8.2pt;line-height:1.45;padding:8pt 10pt;break-inside:avoid;print-color-adjust:exact}table{font-size:8pt;line-height:1.35;margin:10pt 0}th,td{padding:5pt 6pt}tr{break-inside:avoid}thead{display:table-header-group}h1,h2,h3{break-after:avoid}li{margin:4pt 0}a{color:#242b26;text-decoration:none}.intro p{margin:5pt 0}.intro h3{margin:10pt 0 5pt}.intro table{font-size:7.7pt;line-height:1.3;margin:7pt 0}.intro td,.intro th{padding:3pt 4pt}.intro pre{padding:6pt 8pt;margin:6pt 0}}
    """
    css += "\n@media print{.intro{font-size:10pt;line-height:1.4}}"
    css = "\n".join(line.rstrip() for line in css.splitlines())
    title = "Fatura Masası · Sekiz labın çözümü"
    document = ('<!doctype html><html lang="tr"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'">'
                '<title>' + escape(title) + '</title><style>' + css + '</style></head><body><main>' + body + '</main></body></html>')
    html = root / "lab-writeup.html"
    html.write_text(document, encoding="utf8")
    if args.pdf:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.goto(html.as_uri())
            page.evaluate("document.fonts.ready")
            page.pdf(path=str(root / "lab-writeup.pdf"), prefer_css_page_size=True,
                     print_background=True, display_header_footer=True,
                     header_template="<span></span>",
                     footer_template='<div style="width:100%;text-align:right;padding-right:18mm;font:9px Arial;color:#72796d"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
            browser.close()
    print("Write-up HTML" + (" ve PDF" if args.pdf else "") + " üretildi.")


if __name__ == "__main__":
    main()
