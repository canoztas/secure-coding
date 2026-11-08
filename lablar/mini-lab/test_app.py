"""Aynı girdinin zafiyetli ve düzeltilmiş sürümdeki etkisini karşılaştırır."""
from pathlib import Path
import tempfile
import unittest

from app import create_app


class LabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-only", "DATABASE": str(Path(self.tmp.name) / "test.sqlite3")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def get(self, path):
        return self.client.get(path)

    def post(self, path, data=None):
        return self.client.post(path, json=data or {})

    def progress(self):
        return self.get("/api/bootstrap").json["progress"]

    def test_search_injection_and_parameterized_query(self):
        self.assertEqual(self.get("/api/vulnerable/invoices/search?q=Ofis").json["count"], 1)
        attack = {"q": "%' OR 1=1 -- "}
        bad = self.client.get("/api/vulnerable/invoices/search", query_string=attack)
        fixed = self.client.get("/api/fixed/invoices/search", query_string=attack)
        self.assertEqual({x["id"] for x in bad.json["invoices"]}, {101, 102, 103, 104})
        self.assertEqual(fixed.json["invoices"], [])
        self.assertIn("search", self.progress())
        # Üst üste SQL deyimi yürütülmez; uygulama veri deposuna erişilmez.
        self.assertEqual(self.client.get("/api/vulnerable/invoices/search", query_string={"q": "'; DROP TABLE workspaces; --"}).status_code, 400)
        self.assertEqual(self.get("/api/bootstrap").status_code, 200)

    def test_record_and_company_boundaries(self):
        self.assertEqual(self.get("/api/vulnerable/invoices/102").status_code, 200)
        self.assertEqual(self.get("/api/fixed/invoices/102").status_code, 403)
        self.assertEqual(self.get("/api/fixed/invoices/101").status_code, 200)
        self.post("/api/actor", {"actor": "deniz"})
        self.assertEqual(self.get("/api/fixed/invoices/102").status_code, 200)
        self.assertEqual(self.get("/api/fixed/invoices/103").status_code, 403)
        self.assertIn("object", self.progress())

    def test_field_permissions_and_atomic_rejection(self):
        payload = {"note": "Yarın teslim", "status": "approved"}
        bad = self.client.patch("/api/vulnerable/invoices/101", json=payload)
        fixed = self.client.patch("/api/fixed/invoices/101", json=payload)
        self.assertEqual(bad.json["invoice"]["status"], "approved")
        self.assertEqual(fixed.status_code, 403)
        fixed_invoice = self.get("/api/fixed/invoices/101").json["invoice"]
        self.assertEqual(fixed_invoice["status"], "draft")
        self.assertNotEqual(fixed_invoice["note"], payload["note"])
        legitimate = self.client.patch("/api/fixed/invoices/101", json={"note": "Yarın teslim"})
        self.assertEqual(legitimate.json["invoice"]["note"], "Yarın teslim")
        self.assertIn("fields", self.progress())

    def test_stored_note_escaping_and_preview_boundary(self):
        attack = '<img src=x onerror="alert(\'merhaba\')">'
        for mode in ("vulnerable", "fixed"):
            self.assertEqual(self.post(f"/api/{mode}/notes", {"note": attack}).status_code, 200)
        bad = self.get("/preview/vulnerable/notes")
        fixed = self.get("/preview/fixed/notes")
        self.assertIn(attack, bad.text)
        self.assertNotIn(attack, fixed.text)
        self.assertIn("&lt;img", fixed.text)
        self.assertIn("default-src 'none'", bad.headers["Content-Security-Policy"])
        self.assertNotIn("notes", self.progress())  # Kaydetmek, kod çalışması kanıtı değildir.
        self.assertEqual(self.post("/api/fixed/notes/proof", {"nonce": "fake"}).status_code, 403)

    def test_server_controls_price_and_quantity(self):
        payload = {"product_id": "hub", "quantity": 2, "unit_price_cents": 100}
        bad = self.post("/api/vulnerable/orders", payload)
        fixed = self.post("/api/fixed/orders", payload)
        self.assertEqual(bad.json["order"]["total_cents"], 200)
        self.assertEqual(fixed.json["order"]["total_cents"], 180000)
        self.assertIn("price", self.progress())
        for quantity in (-1, 0, 1.5, True, "2", 100):
            self.assertEqual(self.post("/api/fixed/orders", {"product_id": "hub", "quantity": quantity}).status_code, 400)

    def test_coupon_replay_and_user_scope(self):
        payload = {"code": "MERHABA20"}
        self.assertEqual(self.post("/api/vulnerable/coupons/apply", payload).json["total_cents"], 80000)
        self.assertEqual(self.post("/api/vulnerable/coupons/apply", payload).json["total_cents"], 64000)
        self.assertEqual(self.post("/api/fixed/coupons/apply", payload).json["total_cents"], 80000)
        self.assertEqual(self.post("/api/fixed/coupons/apply", payload).status_code, 409)
        self.assertEqual(self.get("/api/fixed/overview").json["coupon"]["total_cents"], 80000)
        self.post("/api/actor", {"actor": "bob"})
        self.assertEqual(self.post("/api/fixed/coupons/apply", payload).status_code, 200)
        self.assertIn("coupon", self.progress())

    def test_payment_step_cannot_be_skipped_after_fix(self):
        bad = self.post("/api/vulnerable/orders/501/confirm")
        self.assertEqual(bad.json["order"]["status"], "confirmed")
        self.assertEqual(bad.json["order"]["payment_status"], "unpaid")
        self.assertEqual(self.post("/api/fixed/orders/501/confirm").status_code, 409)
        self.post("/api/fixed/orders/501/pay")
        self.assertEqual(self.post("/api/fixed/orders/501/confirm").json["order"]["status"], "confirmed")
        self.assertEqual(self.post("/api/fixed/orders/501/confirm").status_code, 409)
        self.assertIn("workflow", self.progress())

    def test_workspaces_are_separate_and_reset_clears_both_modes(self):
        self.client.patch("/api/vulnerable/invoices/101", json={"status": "approved"})
        another = self.app.test_client()
        self.assertEqual(another.get("/api/vulnerable/invoices/101").json["invoice"]["status"], "draft")
        self.assertEqual(another.get("/api/bootstrap").json["progress"], {})
        self.post("/api/reset")
        self.assertEqual(self.progress(), {})
        for mode in ("vulnerable", "fixed"):
            self.assertEqual(self.get(f"/api/{mode}/invoices/101").json["invoice"]["status"], "draft")

    def test_invalid_inputs_and_cross_origin_requests(self):
        self.assertEqual(self.post("/api/actor", {"actor": []}).status_code, 400)
        self.assertEqual(self.post("/api/vulnerable/orders", {"product_id": []}).status_code, 400)
        self.assertEqual(self.client.post("/api/reset", json={}, headers={"Origin": "https://elsewhere.test"}).status_code, 403)
        self.assertEqual(self.client.get("/api/bootstrap", headers={"Host": "elsewhere.test"}).status_code, 400)
        self.assertEqual(self.client.post("/api/vulnerable/orders", json=[]).status_code, 400)

    def test_code_views_show_only_vulnerable_branch_without_changing_progress(self):
        import ast
        for lab in ("search", "object", "fields", "notes", "price", "coupon", "workflow", "jwt"):
            versions = []
            for mode in ("vulnerable", "fixed"):
                response = self.get(f"/api/{mode}/code/{lab}")
                self.assertEqual(response.status_code, 200)
                view = response.json
                self.assertEqual((view["lab"], view["mode"]), (lab, mode))
                self.assertEqual(view["variant"], "vulnerable")
                self.assertTrue(view["question"])
                versions.append([block["code"] for block in view["blocks"]])
                for block in view["blocks"]:
                    parsed = ast.parse(block["code"])
                    for node in ast.walk(parsed):
                        if isinstance(node, (ast.If, ast.IfExp)):
                            self.assertFalse(any(isinstance(part, ast.Name) and part.id == "mode" for part in ast.walk(node.test)))
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                            self.assertNotEqual(node.func.id, "prove")
                    self.assertNotIn("SECRET_KEY", block["code"])
            self.assertEqual(versions[0], versions[1])
        self.assertEqual(self.get("/api/fixed/code/unknown").status_code, 404)
        self.assertEqual(self.get("/api/unknown/code/search").status_code, 404)
        self.assertEqual(self.progress(), {})
        fixed = self.get("/api/fixed/code/search").json["blocks"][0]
        vulnerable = self.get("/api/vulnerable/code/search").json["blocks"][0]
        self.assertEqual(fixed["code"], vulnerable["code"])
        jwt_code = self.get("/api/fixed/code/jwt").json["blocks"][0]["code"]
        self.assertIn("'verify_signature': False", jwt_code)
        self.assertNotIn("algorithms", jwt_code)
        object_code = self.get("/api/fixed/code/object").json["blocks"][0]["code"]
        self.assertNotIn("can_read", object_code)

    def test_jwt_payload_and_role_tampering(self):
        import base64
        import json
        token = self.post("/api/vulnerable/jwt/issue").json["token"]
        read = lambda mode, value: self.client.get(f"/api/{mode}/jwt/invoices", headers={"Authorization": "Bearer " + value})
        for mode in ("vulnerable", "fixed"):
            response = read(mode, token)
            self.assertEqual(response.status_code, 200)
            self.assertEqual({x["id"] for x in response.json["invoices"]}, {101, 104})
        self.assertNotIn("jwt", self.progress())
        header, payload, signature = token.split(".")
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        for changed in (claims | {"sub": "bob"}, claims | {"role": "accountant"}):
            encoded = base64.urlsafe_b64encode(json.dumps(changed).encode()).rstrip(b"=").decode()
            forged = header + "." + encoded + "." + signature
            response = read("vulnerable", forged)
            self.assertEqual(response.status_code, 200)
            self.assertIn(102, {x["id"] for x in response.json["invoices"]})
            self.assertEqual(read("fixed", forged).status_code, 401)
        self.assertIn("jwt", self.progress())

    def test_jwt_fixed_checks_claims_algorithm_and_workspace(self):
        from contextlib import closing
        import jwt
        import sqlite3
        import json
        import time
        token = self.post("/api/vulnerable/jwt/issue").json["token"]
        with self.client.session_transaction() as session:
            wid = session["workspace"]
        with closing(sqlite3.connect(self.app.config["DATABASE"])) as conn:
            state = json.loads(conn.execute("SELECT state FROM workspaces WHERE id=?", (wid,)).fetchone()[0])
        key = state["jwt_key"]
        claims = jwt.decode(token, key, algorithms=["HS256"], audience="fatura-api", issuer="fatura-masasi")
        read = lambda value: self.client.get("/api/fixed/jwt/invoices", headers={"Authorization": "Bearer " + value})
        for changes in ({"exp": int(time.time()) - 30}, {"aud": "other"}, {"iss": "other"}, {"iat": int(time.time()) + 300}, {"exp": None}):
            self.assertEqual(read(jwt.encode(claims | changes, key, algorithm="HS256")).status_code, 401)
        self.assertEqual(read(jwt.encode({k:v for k,v in claims.items() if k != "exp"}, key, algorithm="HS256")).status_code, 401)
        self.assertEqual(read(jwt.encode(claims, "", algorithm="none")).status_code, 401)
        self.assertEqual(read("not-a-jwt").status_code, 401)
        self.assertEqual(self.get("/api/fixed/jwt/invoices").status_code, 401)
        other = self.app.test_client()
        self.assertEqual(other.get("/api/fixed/jwt/invoices", headers={"Authorization":"Bearer " + token}).status_code, 401)
        self.post("/api/reset")
        self.assertEqual(read(token).status_code, 401)


if __name__ == "__main__":
    unittest.main()
