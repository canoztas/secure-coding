"""Lab ekranları için yalnız izin verilen işlevlerden gerçek kaynak satırları."""
import ast
from functools import lru_cache
from pathlib import Path
import textwrap


VIEWS = {
    "search": ("search", "scope =", "rows =", "Arama metni SQL sorgusuna nasıl giriyor?"),
    "object": ("invoice_detail", "invoice = invoice_by_id", "return jsonify(invoice=invoice)", "Kayıt seçildikten sonra okuma izni nerede denetleniyor?"),
    "fields": ("invoice_detail", "payload = body()", "invoice.update(", "Gelen alanlardan hangileri faturaya aktarılıyor?"),
    "notes": ("note_preview", "note = selected(", "rendered =", "Kaydedilen not HTML çıktısına nasıl ekleniyor?"),
    "price": ("order", "unit =", "record =", "Birim fiyat istekten mi, sunucudaki katalogdan mı geliyor?"),
    "coupon": ("coupon", "uid =", 'coupon["used_by"].append(', "Kullanım kontrolü ile tutar değişikliği hangi sırayla yapılıyor?"),
    "workflow": ("confirm", 'if mode == "fixed"', 'order["status"] =', "Sipariş onaylanmadan önce hangi koşullar aranıyor?"),
    "jwt": ("jwt_invoices", "try:", 'raise LabError("Token doğrulanamadı:', "Token yalnız okunuyor mu, yoksa imzası da doğrulanıyor mu?"),
}


@lru_cache(maxsize=1)
def source_tree():
    source = Path(__file__).with_name("app.py").read_text(encoding="utf8")
    return source.splitlines(), ast.parse(source)


def excerpt(function, start=None, end=None, mode=None):
    lines, tree = source_tree()
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == function)
    first, last = node.lineno, node.end_lineno
    if start:
        first = next(i + 1 for i in range(first - 1, last) if lines[i].lstrip().startswith(start))
    if end:
        last = next(i + 1 for i in range(first - 1, last) if lines[i].lstrip().startswith(end))
    focus = set()
    for item in ast.walk(node):
        if not isinstance(item, ast.If):
            continue
        guards = [n for n in ast.walk(item.test) if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) and n.left.id == "mode"]
        for guard in guards:
            if len(guard.ops) != 1 or not isinstance(guard.ops[0], ast.Eq) or not isinstance(guard.comparators[0], ast.Constant):
                continue
            branch = item.body if guard.comparators[0].value == mode else item.orelse
            for statement in branch:
                focus.update(range(statement.lineno, statement.end_lineno + 1))
    code = textwrap.dedent("\n".join(lines[first - 1:last]))
    return {"file": "app.py", "start_line": first, "end_line": last, "code": code, "focus_lines": sorted(n for n in focus if first <= n <= last)}


def code_view(lab, mode):
    if lab not in VIEWS or mode not in ("vulnerable", "fixed"):
        raise ValueError("Unknown code view")
    function, start, end, question = VIEWS[lab]
    blocks = [excerpt(function, start, end, mode)]
    if lab == "object":
        blocks.append(excerpt("can_read", mode=mode))
    return {"lab": lab, "mode": mode, "question": question, "blocks": blocks}
