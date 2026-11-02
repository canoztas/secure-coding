"""Lab ekranları için çalışan kodun yalnız zafiyetli dalını gösterir."""
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
    "workflow": ("confirm", "order = own_delivery(", 'order["status"] =', "Sipariş onaylanmadan önce hangi koşullar aranıyor?"),
    "jwt": ("jwt_invoices", 'claims = jwt.decode(token, options=', 'claims = jwt.decode(token, options=', "Token yalnız okunuyor mu, yoksa imzası da doğrulanıyor mu?"),
}


@lru_cache(maxsize=1)
def source_tree():
    source = Path(__file__).with_name("app.py").read_text(encoding="utf8")
    return source.splitlines(), ast.parse(source)


class VulnerableBranch(ast.NodeTransformer):
    """Sürüm seçimini çözer; lab ilerleme kaydını örnekten çıkarır."""

    def visit_Compare(self, node):
        node = self.generic_visit(node)
        if len(node.ops) != 1 or not isinstance(node.comparators[0], ast.Constant):
            return node
        left = node.left
        value = None
        if isinstance(left, ast.Name) and left.id == "mode":
            value = "vulnerable"
        elif (isinstance(left, ast.Attribute) and isinstance(left.value, ast.Name)
              and left.value.id == "request" and left.attr == "method"):
            value = "GET"
        if value is None:
            return node
        if isinstance(node.ops[0], ast.Eq):
            return ast.copy_location(ast.Constant(value == node.comparators[0].value), node)
        if isinstance(node.ops[0], ast.NotEq):
            return ast.copy_location(ast.Constant(value != node.comparators[0].value), node)
        return node

    def visit_BoolOp(self, node):
        node = self.generic_visit(node)
        is_and = isinstance(node.op, ast.And)
        values = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, bool):
                if value.value != is_and:
                    return ast.copy_location(ast.Constant(not is_and), node)
            else:
                values.append(value)
        if not values:
            return ast.copy_location(ast.Constant(is_and), node)
        if len(values) == 1:
            return values[0]
        node.values = values
        return node

    def visit_If(self, node):
        node = self.generic_visit(node)
        if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
            return node.body if node.test.value else node.orelse
        if not node.body:
            if not node.orelse:
                return None
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            node.body, node.orelse = node.orelse, []
        return node

    def visit_IfExp(self, node):
        node = self.generic_visit(node)
        if isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool):
            return node.body if node.test.value else node.orelse
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "prove":
            return None
        return self.generic_visit(node)


def excerpt(function, start=None, end=None):
    lines, tree = source_tree()
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == function)
    first, last = node.lineno, node.end_lineno
    if start:
        first = next(i + 1 for i in range(first - 1, last) if lines[i].lstrip().startswith(start))
    if end:
        last = next(i + 1 for i in range(first - 1, last) if lines[i].lstrip().startswith(end))
    source = textwrap.dedent("\n".join(lines[first - 1:last]))
    projected = VulnerableBranch().visit(ast.parse(source))
    code = ast.unparse(ast.fix_missing_locations(projected))
    return {"file": "app.py", "code": code}


def code_view(lab, mode):
    if lab not in VIEWS or mode not in ("vulnerable", "fixed"):
        raise ValueError("Unknown code view")
    function, start, end, question = VIEWS[lab]
    blocks = [excerpt(function, start, end)]
    return {"lab": lab, "mode": mode, "variant": "vulnerable", "question": question, "blocks": blocks}
