"""Fatura Masası: yerelde çalışan, kasıtlı zafiyetler içeren ders uygulaması."""
from __future__ import annotations

import argparse
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import secrets
import sqlite3
import time

import jwt

from flask import Flask, Response, g, jsonify, request, session
from markupsafe import escape
from werkzeug.exceptions import HTTPException
from code_views import code_view

ACTORS = {
    "alice": {"id": "alice", "name": "Alice", "company": "A", "role": "member", "role_label": "Üye"},
    "bob": {"id": "bob", "name": "Bob", "company": "A", "role": "member", "role_label": "Üye"},
    "deniz": {"id": "deniz", "name": "Deniz", "company": "A", "role": "accountant", "role_label": "Muhasebeci"},
    "ece": {"id": "ece", "name": "Ece", "company": "B", "role": "member", "role_label": "Üye"},
}
PRODUCTS = {
    "hub": {"id": "hub", "name": "USB-C çoklayıcı", "price_cents": 90000},
    "keyboard": {"id": "keyboard", "name": "Kablosuz klavye", "price_cents": 150000},
    "notebook": {"id": "notebook", "name": "Not defteri", "price_cents": 25000},
}
LABS = ("search", "object", "fields", "notes", "price", "coupon", "workflow", "jwt")


def seed_mode():
    return {
        "invoices": [
            {"id": 101, "owner_id": "alice", "company": "A", "title": "Tasarım ekibi ekipmanları", "amount_cents": 300000, "status": "draft", "note": "Bu hafta teslim edilsin."},
            {"id": 102, "owner_id": "bob", "company": "A", "title": "Satış ekibi seyahat giderleri", "amount_cents": 480000, "status": "draft", "note": "Yalnız Bob ve muhasebe görebilir."},
            {"id": 103, "owner_id": "ece", "company": "B", "title": "B şirketi sözleşme bedeli", "amount_cents": 920000, "status": "issued", "note": "B şirketinin özel faturası."},
            {"id": 104, "owner_id": "alice", "company": "A", "title": "Ofis sarf malzemeleri", "amount_cents": 75000, "status": "issued", "note": "Ödendi."},
        ],
        "notes": {actor: "Teslimatı mesai saatlerinde yapınız." for actor in ACTORS},
        "orders": [],
        "coupon": {"totals": {actor: 100000 for actor in ACTORS}, "used_by": []},
        "delivery": {"id": 501, "owner_id": "alice", "amount_cents": 350000, "payment_status": "unpaid", "status": "awaiting_payment"},
    }


def seed_state():
    return {"vulnerable": seed_mode(), "fixed": seed_mode(), "progress": {}, "xss_nonce": secrets.token_hex(16), "jwt_key": secrets.token_hex(32)}


class LabError(Exception):
    def __init__(self, message, status=400, code="invalid_request"):
        self.message, self.status, self.code = message, status, code


def create_app(config=None):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        DATABASE=str(Path(__file__).parent / "instance" / "lab.sqlite3"),
        MAX_CONTENT_LENGTH=32 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_NAME="fatura_lab",
        DEBUG=False,
    )
    if config:
        app.config.update(config)
    app.json.ensure_ascii = False
    db_path = Path(app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, state TEXT NOT NULL)")
        conn.commit()

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10, isolation_level=None)
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        conn = g.pop("db", None)
        if conn:
            conn.close()

    @contextmanager
    def workspace():
        wid = session.setdefault("workspace", secrets.token_hex(24))
        conn = db()
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT state FROM workspaces WHERE id=?", (wid,)).fetchone()
            state = json.loads(row[0]) if row else seed_state()
            yield state
            conn.execute("INSERT INTO workspaces(id,state) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state", (wid, json.dumps(state, ensure_ascii=False)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def actor():
        return ACTORS[session.get("actor", "alice")]

    def selected(state, mode):
        if mode not in ("vulnerable", "fixed"):
            raise LabError("Sürüm bulunamadı.", 404)
        return state[mode]

    def body():
        data = request.get_json()
        if not isinstance(data, dict):
            raise LabError("İstek gövdesi bir JSON nesnesi olmalı.")
        return data

    def prove(state, lab, evidence):
        state["progress"][lab] = {"complete": True, "evidence": evidence, "time": datetime.now(timezone.utc).isoformat()}

    def can_read(invoice, user):
        return invoice["company"] == user["company"] and (invoice["owner_id"] == user["id"] or user["role"] == "accountant")

    def invoice_by_id(data, invoice_id):
        invoice = next((x for x in data["invoices"] if x["id"] == invoice_id), None)
        if not invoice:
            raise LabError("Fatura bulunamadı.", 404, "not_found")
        return invoice

    def own_delivery(data):
        order = data["delivery"]
        if order["owner_id"] != actor()["id"]:
            raise LabError("Bu sipariş için izniniz yok.", 403, "forbidden")
        return order

    @app.before_request
    def local_boundary():
        if request.host.split(":")[0] not in ("127.0.0.1", "localhost"):
            raise LabError("Uygulamayı localhost üzerinden açınız.", 400)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("Origin")
            if origin and origin != request.host_url.rstrip("/"):
                raise LabError("İstek aynı uygulama kökeninden gelmeli.", 403)

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'")
        return response

    @app.errorhandler(LabError)
    def lab_error(error):
        return jsonify(error=error.code, message=error.message), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {400: "İstek çözümlenemedi.", 404: "Adres bulunamadı.", 405: "Bu adres bu yöntemi kabul etmiyor.", 413: "İstek gövdesi çok büyük.", 415: "JSON içerik türü gerekli."}
        return jsonify(error=error.name, message=messages.get(error.code, error.description)), error.code

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/bootstrap")
    def bootstrap():
        with workspace() as state:
            return jsonify(actor=actor(), actors=list(ACTORS.values()), products=list(PRODUCTS.values()), progress=state["progress"], labs=list(LABS))

    @app.post("/api/actor")
    def switch_actor():
        key = body().get("actor")
        if not isinstance(key, str) or key not in ACTORS:
            raise LabError("Kullanıcı bulunamadı.")
        # Ders hesabı seçimi; gerçek bir giriş sistemi olarak tasarlanmamıştır.
        session["actor"] = key
        return jsonify(actor=actor())

    @app.get("/api/<mode>/code/<lab>")
    def lab_code(mode, lab):
        try:
            return jsonify(code_view(lab, mode))
        except ValueError:
            raise LabError("Kod görünümü bulunamadı.", 404, "not_found")

    @app.post("/api/reset")
    def reset():
        body()
        with workspace() as state:
            state.clear()
            state.update(seed_state())
        session["actor"] = "alice"
        return jsonify(message="Her iki sürümün verileri başlangıca döndü.")

    @app.get("/api/<mode>/overview")
    def overview(mode):
        with workspace() as state:
            data, user = selected(state, mode), actor()
            return jsonify(
                invoices=[x for x in data["invoices"] if can_read(x, user)],
                note=data["notes"][user["id"]],
                orders=[x for x in data["orders"] if x["owner_id"] == user["id"]],
                coupon={"code": "MERHABA20", "total_cents": data["coupon"]["totals"][user["id"]], "used": user["id"] in data["coupon"]["used_by"]},
                delivery=data["delivery"] if data["delivery"]["owner_id"] == user["id"] else None,
                progress=state["progress"],
            )

    @app.get("/api/<mode>/invoices/search")
    def search(mode):
        query = request.args.get("q", "")
        if len(query) > 300:
            raise LabError("Arama en fazla 300 karakter olabilir.")
        with workspace() as state:
            data, user = selected(state, mode), actor()
            # SQLi yalnız bu geçici ders tablosunda çalışır; uygulama veritabanı ayrı kalır.
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("CREATE TABLE invoices(id INTEGER,owner_id TEXT,company TEXT,title TEXT,amount_cents INTEGER,status TEXT,note TEXT)")
                conn.executemany("INSERT INTO invoices VALUES(:id,:owner_id,:company,:title,:amount_cents,:status,:note)", data["invoices"])
                scope = "company = ?" if user["role"] == "accountant" else "company = ? AND owner_id = ?"
                params = [user["company"]] if user["role"] == "accountant" else [user["company"], user["id"]]
                if mode == "vulnerable":
                    sql = f"SELECT * FROM invoices WHERE {scope} AND title LIKE '%{query}%' ORDER BY id"
                else:
                    sql = f"SELECT * FROM invoices WHERE {scope} AND title LIKE ? ORDER BY id"
                    params.append("%" + query + "%")
                rows = [dict(x) for x in conn.execute(sql, params).fetchall()]
            except sqlite3.Error:
                raise LabError("Arama sorgusu çalıştırılamadı.", 400, "query_error")
            finally:
                conn.close()
            if mode == "vulnerable" and any(not can_read(x, user) for x in rows):
                prove(state, "search", "Arama, kullanıcının erişememesi gereken faturaları döndürdü.")
            return jsonify(invoices=rows, count=len(rows))

    @app.post("/api/<mode>/jwt/issue")
    def issue_jwt(mode):
        body()
        with workspace() as state:
            selected(state, mode)
            user = actor()
            claims = {"sub": user["id"], "role": user["role"], "company": user["company"],
                      "iss": "fatura-masasi", "aud": "fatura-api", "iat": int(time.time()), "exp": int(time.time()) + 900}
            key = state.setdefault("jwt_key", secrets.token_hex(32))
            token = jwt.encode(claims, key, algorithm="HS256")
            return jsonify(token=token, expires_in=900)

    @app.get("/api/<mode>/jwt/invoices")
    def jwt_invoices(mode):
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token.strip() or len(token) > 4096:
            raise LabError("Authorization başlığında Bearer token gerekli.", 401, "token_required")
        token = token.strip()
        with workspace() as state:
            data = selected(state, mode)
            key = state.setdefault("jwt_key", secrets.token_hex(32))
            try:
                if mode == "vulnerable":
                    claims = jwt.decode(token, options={"verify_signature": False})
                else:
                    claims = jwt.decode(token, key, algorithms=["HS256"],
                                        issuer="fatura-masasi", audience="fatura-api",
                                        options={"require": ["sub", "role", "company", "iss", "aud", "exp", "iat"]})
            except (jwt.InvalidTokenError, TypeError, ValueError, OverflowError):
                raise LabError("Token doğrulanamadı: imza, süre veya hedef bilgisi geçersiz.", 401, "invalid_token")
            sub, role, company = claims.get("sub"), claims.get("role"), claims.get("company")
            if not isinstance(sub, str) or sub not in ACTORS or role not in ("member", "accountant") or company not in ("A", "B"):
                raise LabError("Token içindeki kullanıcı, rol veya şirket bilgisi geçersiz.", 401, "invalid_claims")
            token_user = {"id": sub, "role": role, "company": company}
            invoices = [x for x in data["invoices"] if can_read(x, token_user)]
            authentic = True
            if mode == "vulnerable":
                try:
                    jwt.decode(token, key, algorithms=["HS256"], issuer="fatura-masasi", audience="fatura-api")
                except jwt.InvalidTokenError:
                    authentic = False
                if not authentic and any(not can_read(x, actor()) for x in invoices):
                    prove(state, "jwt", "İmzası doğrulanmayan token ile başka kullanıcının faturası okundu.")
            return jsonify(identity={"sub": sub, "name": ACTORS[sub]["name"], "role": role, "company": company}, invoices=invoices)

    @app.route("/api/<mode>/invoices/<int:invoice_id>", methods=["GET", "PATCH"])
    def invoice_detail(mode, invoice_id):
        with workspace() as state:
            data, user = selected(state, mode), actor()
            invoice = invoice_by_id(data, invoice_id)
            if request.method == "GET":
                if mode == "fixed" and not can_read(invoice, user):
                    raise LabError("Bu faturayı okuma izniniz yok.", 403, "forbidden")
                if mode == "vulnerable" and not can_read(invoice, user):
                    prove(state, "object", f"{user['name']}, {invoice_id} numaralı izinsiz faturayı okudu.")
                return jsonify(invoice=invoice)
            # Nesne izni iki sürümde de var. Bu lab yalnız alan iznini değiştirir.
            if invoice["company"] != user["company"] or invoice["owner_id"] != user["id"]:
                raise LabError("Bu faturayı düzenleme izniniz yok.", 403, "forbidden")
            payload = body()
            if mode == "fixed" and set(payload) - {"note"}:
                raise LabError("Bu işlemde yalnız note alanı değiştirilebilir.", 403, "field_forbidden")
            if "note" in payload and (not isinstance(payload["note"], str) or len(payload["note"]) > 1000):
                raise LabError("Not en fazla 1000 karakterlik metin olmalı.")
            if "status" in payload and payload["status"] not in ("draft", "approved", "issued"):
                raise LabError("Geçersiz fatura durumu.")
            allowed = {"note", "status"} if mode == "vulnerable" else {"note"}
            invoice.update({k: v for k, v in payload.items() if k in allowed})
            if mode == "vulnerable" and user["role"] == "member" and invoice["status"] == "approved":
                prove(state, "fields", "Üye, not güncellemesine status ekleyerek faturayı onayladı.")
            return jsonify(invoice=invoice)

    @app.route("/api/<mode>/notes", methods=["GET", "POST"])
    def notes(mode):
        with workspace() as state:
            data = selected(state, mode)
            if request.method == "POST":
                note = body().get("note")
                if not isinstance(note, str) or len(note) > 2000:
                    raise LabError("Not en fazla 2000 karakterlik metin olmalı.")
                data["notes"][actor()["id"]] = note
            return jsonify(note=data["notes"][actor()["id"]], preview=f"/preview/{mode}/notes")

    @app.get("/preview/<mode>/notes")
    def note_preview(mode):
        with workspace() as state:
            note = selected(state, mode)["notes"][actor()["id"]]
            rendered = note if mode == "vulnerable" else str(escape(note))
            nonce = json.dumps(state["xss_nonce"])
        # Kasıtlı XSS, ağ erişimi olmayan sandbox önizlemesinde gösterilir.
        html = '''<!doctype html><html lang="tr"><meta charset="utf-8"><style>body{font:16px/1.6 Georgia,serif;color:#283b32;padding:18px;margin:0}small{color:#6d756d}#message{border-top:1px solid #ddd;margin-top:14px;padding-top:12px}</style><small>Teslimat notu</small><script>window.alert=function(message){parent.postMessage({type:'lab:xss',nonce:NONCE},'*');const p=document.createElement('p');p.id='message';p.textContent='Çalışan kodun mesajı: '+String(message);document.body.append(p);};</script><div>CONTENT</div></html>'''
        html = html.replace("NONCE", nonce).replace("CONTENT", rendered)
        response = Response(html, content_type="text/html; charset=utf-8")
        response.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-ancestors 'self'; base-uri 'none'; form-action 'none'"
        return response

    @app.post("/api/<mode>/notes/proof")
    def note_proof(mode):
        payload = body()
        with workspace() as state:
            selected(state, mode)
            if mode != "vulnerable" or payload.get("nonce") != state["xss_nonce"]:
                raise LabError("Bu sürümde çalıştırılmış not kodu gözlenmedi.", 403)
            prove(state, "notes", "Kaydedilen nottaki JavaScript, tarayıcı önizlemesinde çalıştı.")
        return jsonify(message="Tarayıcıda kod çalışması gözlendi.")

    @app.post("/api/<mode>/orders")
    def order(mode):
        payload = body()
        product_id = payload.get("product_id")
        product = PRODUCTS.get(product_id) if isinstance(product_id, str) else None
        quantity = payload.get("quantity", 1)
        if not product or type(quantity) is not int or not 1 <= quantity <= 10:
            raise LabError("Ürün ve 1–10 arası tam sayı adet gerekli.")
        with workspace() as state:
            data = selected(state, mode)
            unit = payload.get("unit_price_cents", product["price_cents"]) if mode == "vulnerable" else product["price_cents"]
            if type(unit) is not int or not 1 <= unit <= 10000000:
                raise LabError("Birim fiyat pozitif tam sayı kuruş olmalı.")
            record = {"id": 601 + len(data["orders"]), "owner_id": actor()["id"], "product_id": product["id"], "quantity": quantity, "unit_price_cents": unit, "total_cents": unit * quantity}
            data["orders"].append(record)
            if mode == "vulnerable" and unit < product["price_cents"]:
                prove(state, "price", "Sunucu, katalog fiyatından düşük istemci fiyatını kabul etti.")
            return jsonify(order=record), 201

    @app.post("/api/<mode>/coupons/apply")
    def coupon(mode):
        if body().get("code") != "MERHABA20":
            raise LabError("Kupon bulunamadı.", 404)
        with workspace() as state:
            coupon = selected(state, mode)["coupon"]
            uid = actor()["id"]
            used = uid in coupon["used_by"]
            if mode == "fixed" and used:
                raise LabError("Bu kuponu daha önce kullandınız.", 409, "already_used")
            coupon["totals"][uid] = coupon["totals"][uid] * 80 // 100
            if not used:
                coupon["used_by"].append(uid)
            if mode == "vulnerable" and used:
                prove(state, "coupon", "Tek kullanımlık kupon aynı kullanıcıya tekrar indirim sağladı.")
            return jsonify(total_cents=coupon["totals"][uid], coupon="MERHABA20", message="%20 indirim uygulandı.")

    @app.post("/api/<mode>/orders/501/pay")
    def pay(mode):
        body()
        with workspace() as state:
            order = own_delivery(selected(state, mode))
            if order["status"] == "confirmed":
                raise LabError("Onaylanan siparişin ödeme adımı değiştirilemez.", 409)
            order["payment_status"] = "paid"
            order["status"] = "ready"
            return jsonify(order=order, message="Deneme ödemesi kaydedildi.")

    @app.post("/api/<mode>/orders/501/confirm")
    def confirm(mode):
        body()
        with workspace() as state:
            order = own_delivery(selected(state, mode))
            if mode == "fixed" and order["payment_status"] != "paid":
                raise LabError("Ödeme doğrulanmadan teslimat onaylanamaz.", 409, "payment_required")
            if order["status"] == "confirmed":
                raise LabError("Bu sipariş zaten onaylandı.", 409)
            order["status"] = "confirmed"
            if mode == "vulnerable" and order["payment_status"] == "unpaid":
                prove(state, "workflow", "Ödemesi yapılmamış sipariş teslimat için onaylandı.")
            return jsonify(order=order)

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    create_app().run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
