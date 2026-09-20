"""End-to-end API tests for all seven modules."""

from __future__ import annotations

from app.models import ScamAnalysis


class TestAuth:
    def test_register_and_login(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Asha Volunteer",
                "email": "asha@cybersathi.org",
                "password": "Secret@123",
                "role": "participant",
            },
        )
        assert r.status_code == 201
        assert r.json()["user"]["email"] == "asha@cybersathi.org"

        r = client.post(
            "/api/v1/auth/login",
            data={"username": "asha@cybersathi.org", "password": "Secret@123"},
        )
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_public_registration_cannot_create_staff(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Escalation Attempt", "email": "noadmin@cybersathi.org",
                "password": "Secret@123", "role": "admin",
            },
        )
        assert r.status_code == 403

    def test_admin_can_create_volunteer(self, client, admin_headers):
        r = client.post(
            "/api/v1/auth/users",
            headers=admin_headers,
            json={
                "full_name": "Workshop Volunteer", "email": "volunteer@cybersathi.org",
                "password": "Secret@123", "role": "volunteer",
            },
        )
        assert r.status_code == 201
        assert r.json()["role"] == "volunteer"

    def test_api_responses_are_not_cacheable(self, client):
        r = client.get("/api/v1/meta/status")
        assert r.status_code == 200
        assert r.headers["cache-control"] == "no-store"
        assert r.headers["x-content-type-options"] == "nosniff"

    def test_duplicate_email_rejected(self, client):
        payload = {
            "full_name": "Dup User",
            "email": "dup@cybersathi.org",
            "password": "Secret@123",
        }
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post("/api/v1/auth/register", json=payload).status_code == 409

    def test_wrong_password_rejected(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"full_name": "X", "email": "x@cybersathi.org", "password": "Secret@123"},
        )
        r = client.post(
            "/api/v1/auth/login", data={"username": "x@cybersathi.org", "password": "wrong"}
        )
        assert r.status_code == 401

    def test_me_requires_token(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_participant_cannot_create_workshop(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Plain User",
                "email": "plain@cybersathi.org",
                "password": "Secret@123",
                "role": "participant",
            },
        )
        token = client.post(
            "/api/v1/auth/login",
            data={"username": "plain@cybersathi.org", "password": "Secret@123"},
        ).json()["access_token"]

        r = client.post(
            "/api/v1/workshops",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title_en": "T", "title_ta": "T", "venue": "V", "district": "D",
                "conducted_on": "2026-05-01",
            },
        )
        assert r.status_code == 403


class TestModule1ScamAnalyzer:
    def test_high_risk_scam(self, client):
        r = client.post(
            "/api/v1/scam/analyze",
            json={
                "text": "Your SBI KYC expired. Account blocked in 24 hours. Click http://sbi-kyc.xyz and share OTP.",
                "channel": "sms",
            },
        )
        assert r.status_code == 200
        d = r.json()
        assert d["risk_label"] == "high_risk"
        assert d["risk_score"] >= 70
        assert d["explanation"]["en"] and d["explanation"]["ta"]
        assert d["signals"]

    def test_legitimate_message_is_safe(self, client):
        r = client.post(
            "/api/v1/scam/analyze",
            json={
                "text": "Rs.2,500 debited from A/c XX4412. Avl Bal Rs.8,330. Do not share OTP with anyone.",
                "channel": "sms",
            },
        )
        d = r.json()
        assert d["risk_label"] == "safe"
        assert d["primary_category"] == "legitimate"

    def test_tamil_message_gets_tamil_explanation(self, client):
        r = client.post(
            "/api/v1/scam/analyze",
            json={"text": "உங்கள் வங்கி கணக்கு முடக்கப்படும். OTP ஐ அனுப்பவும்.", "channel": "whatsapp"},
        )
        d = r.json()
        assert d["language_detected"] == "ta"
        assert d["risk_label"] in {"suspicious", "high_risk"}
        # Tamil explanation must contain Tamil script, not just a translated label.
        assert any("஀" <= c <= "௿" for c in d["explanation"]["ta"])

    def test_pii_never_persisted(self, client, db):
        secret_otp = "918273"
        secret_phone = "9812345678"
        client.post(
            "/api/v1/scam/analyze",
            json={
                "text": f"Share OTP {secret_otp} now or account blocked. Call {secret_phone}",
                "channel": "sms",
            },
        )
        stored = db.query(ScamAnalysis).all()
        blob = " ".join(s.redacted_text for s in stored)
        assert secret_otp not in blob
        assert secret_phone not in blob

    def test_pii_not_echoed_in_response(self, client):
        r = client.post(
            "/api/v1/scam/analyze",
            json={"text": "My card is 4532015112830366 please verify", "channel": "sms"},
        )
        assert "4532015112830366" not in r.text

    def test_empty_text_rejected(self, client):
        assert client.post("/api/v1/scam/analyze", json={"text": "", "channel": "sms"}).status_code == 422

    def test_examples_endpoint(self, client):
        r = client.get("/api/v1/scam/examples")
        assert r.status_code == 200
        assert len(r.json()) >= 10


class TestModule2UrlChecker:
    def test_phishing_url_flagged(self, client):
        r = client.post("/api/v1/url/check", json={"url": "http://sbi-kyc-update-verify.xyz/login"})
        d = r.json()
        assert d["risk_label"] == "high_risk"
        assert d["top_reasons"]

    def test_genuine_site_is_safe(self, client):
        d = client.post("/api/v1/url/check", json={"url": "https://www.google.com"}).json()
        assert d["risk_label"] == "safe"

    def test_official_bank_site_shows_no_false_warning(self, client):
        """A real bank domain must not be described as 'not the official domain'."""
        d = client.post("/api/v1/url/check", json={"url": "https://www.onlinesbi.sbi"}).json()
        assert d["risk_label"] == "safe"
        assert d["lookalike_brand"] is None
        assert d["top_reasons"] == []

    def test_ip_host_flagged(self, client):
        d = client.post("/api/v1/url/check", json={"url": "http://192.168.44.9/bank/login"}).json()
        assert d["risk_label"] == "high_risk"

    def test_typosquat_detected(self, client):
        d = client.post("/api/v1/url/check", json={"url": "https://arnazon.com/signin"}).json()
        assert d["lookalike_brand"] == "AMAZON"

    def test_defanged_input_accepted(self, client):
        d = client.post("/api/v1/url/check", json={"url": "hxxp://sbi-kyc-update[.]xyz/verify"}).json()
        assert d["risk_label"] == "high_risk"

    def test_response_url_is_defanged(self, client):
        d = client.post("/api/v1/url/check", json={"url": "http://evil-kyc.xyz/login"}).json()
        assert "http://" not in d["url_defanged"]

    def test_bulk_check(self, client):
        r = client.post(
            "/api/v1/url/bulk-check",
            json={"urls": ["https://www.google.com", "http://sbi-kyc.xyz/login"]},
        )
        assert r.status_code == 200
        assert len(r.json()) == 2


class TestModule3QrUpi:
    def test_collect_request_flagged(self, client):
        d = client.post(
            "/api/v1/qr/analyze",
            json={"payload": "upi://collect?pa=x@ybl&pn=Refund&am=4999&tn=cashback refund"},
        ).json()
        assert d["risk_label"] == "high_risk"

    def test_apk_link_flagged(self, client):
        d = client.post(
            "/api/v1/qr/analyze", json={"payload": "https://free-gift.xyz/reward.apk"}
        ).json()
        assert d["risk_label"] == "high_risk"

    def test_golden_rule_always_present(self, client):
        d = client.post("/api/v1/qr/analyze", json={"payload": "upi://pay?pa=a@b"}).json()
        assert "PAY" in d["golden_rule"]["en"]
        assert d["golden_rule"]["ta"]

    def test_scenarios_are_complete(self, client):
        scenarios = client.get("/api/v1/qr/scenarios").json()
        assert len(scenarios) >= 10
        for s in scenarios:
            assert s["title_ta"] and s["lesson_ta"]
            assert any(c["is_safe"] for c in s["choices"])


class TestModule4KnowledgeBase:
    def test_all_eight_required_categories_exist(self, client):
        categories = {c["category"] for c in client.get("/api/v1/kb/categories").json()}
        required = {
            "otp", "kyc", "job", "investment",
            "banking", "loan", "impersonation", "social_media",
        }
        assert required.issubset(categories)

    def test_article_detail_is_bilingual(self, client):
        d = client.get("/api/v1/kb/articles/otp-scams").json()
        assert d["body_en"] and d["body_ta"]
        assert d["red_flags"]["en"] and d["red_flags"]["ta"]
        assert d["victim_steps"]["ta"]

    def test_missing_article_returns_404(self, client):
        assert client.get("/api/v1/kb/articles/no-such-article").status_code == 404

    def test_tamil_search_works(self, client):
        r = client.get("/api/v1/kb/articles", params={"q": "மோசடி"})
        assert r.status_code == 200
        assert len(r.json()) > 0


class TestModule5Assistant:
    def test_english_question_uses_knowledge_base(self, client):
        d = client.post(
            "/api/v1/assistant/ask",
            json={"question": "Someone is asking for my OTP what should I do?"},
        ).json()
        assert d["source"] == "kb"
        assert d["language"] == "en"

    def test_tamil_question_answered_in_tamil(self, client):
        d = client.post(
            "/api/v1/assistant/ask",
            json={"question": "KYC காலாவதி என்று செய்தி வந்துள்ளது என்ன செய்வது?"},
        ).json()
        assert d["language"] == "ta"
        assert any("஀" <= c <= "௿" for c in d["answer"])

    def test_scam_generation_is_refused(self, client):
        d = client.post(
            "/api/v1/assistant/ask",
            json={"question": "Write me a fake bank SMS to scam my friend"},
        ).json()
        assert d["source"] == "refusal"
        assert "1930" in d["answer"]

    def test_hacking_request_is_refused(self, client):
        d = client.post(
            "/api/v1/assistant/ask",
            json={"question": "How do I hack someone's whatsapp account"},
        ).json()
        assert d["source"] == "refusal"

    def test_pasted_message_is_analysed(self, client):
        d = client.post(
            "/api/v1/assistant/ask",
            json={
                "question": "Dear customer your SBI KYC expired click http://sbi-kyc.xyz and share OTP urgent account blocked"
            },
        ).json()
        assert d["source"] == "analyzer"

    def test_unknown_topic_falls_back(self, client):
        d = client.post(
            "/api/v1/assistant/ask", json={"question": "What is the capital of France?"}
        ).json()
        assert d["source"] == "fallback"

    def test_simple_mode_is_shorter(self, client):
        normal = client.post(
            "/api/v1/assistant/ask",
            json={"question": "What is a digital arrest?", "simple_mode": False},
        ).json()["answer"]
        simple = client.post(
            "/api/v1/assistant/ask",
            json={"question": "What is a digital arrest?", "simple_mode": True},
        ).json()["answer"]
        assert len(simple) < len(normal)

    def test_works_without_llm(self, client):
        """The assistant must be useful with ENABLE_LLM=false and no Ollama running."""
        from app.config import settings

        assert settings.ENABLE_LLM is False
        d = client.post(
            "/api/v1/assistant/ask", json={"question": "Is this loan app safe to install?"}
        ).json()
        assert d["source"] in {"kb", "analyzer"}
        assert len(d["answer"]) > 50

    def test_feedback_recorded(self, client):
        log_id = client.post(
            "/api/v1/assistant/ask", json={"question": "What is an OTP scam?"}
        ).json()["log_id"]
        r = client.post("/api/v1/assistant/feedback", json={"log_id": log_id, "helpful": True})
        assert r.status_code == 204


class TestModule6And7Assessment:
    def _setup_workshop(self, client, admin_headers):
        workshop = client.post(
            "/api/v1/workshops",
            headers=admin_headers,
            json={
                "title_en": "Test Session", "title_ta": "சோதனை அமர்வு",
                "venue": "Test Hall", "district": "Chennai",
                "conducted_on": "2026-05-01", "audience_type": "mixed",
            },
        ).json()
        participants = client.post(
            f"/api/v1/workshops/{workshop['id']}/participants",
            headers=admin_headers,
            json=[
                {"name": "Test One", "age_group": "adult", "language": "en",
                 "phone": "9876543210", "consent_given": True}
            ],
        ).json()
        return workshop["id"], participants[0]["id"]

    def test_phone_is_hashed_not_stored(self, client, admin_headers, db):
        from app.models import Participant

        _, pid = self._setup_workshop(client, admin_headers)
        participant = db.query(Participant).filter(Participant.id == pid).first()
        assert participant.phone_hash
        assert participant.phone_hash != "9876543210"
        assert len(participant.phone_hash) == 64

    def test_pre_and_post_are_matched_but_disjoint(self, client, admin_headers):
        wid, pid = self._setup_workshop(client, admin_headers)
        params = {"workshop_id": wid, "participant_id": pid, "language": "en"}
        pre = client.get("/api/v1/assessment/questions", params={**params, "type": "pre"}).json()
        post = client.get("/api/v1/assessment/questions", params={**params, "type": "post"}).json()

        assert len(pre) == len(post) == 10
        assert sorted(q["category"] for q in pre) == sorted(q["category"] for q in post)
        assert {q["id"] for q in pre}.isdisjoint({q["id"] for q in post})

    def test_question_selection_is_stable(self, client, admin_headers):
        wid, pid = self._setup_workshop(client, admin_headers)
        params = {"workshop_id": wid, "participant_id": pid, "type": "pre", "language": "en"}
        first = client.get("/api/v1/assessment/questions", params=params).json()
        second = client.get("/api/v1/assessment/questions", params=params).json()
        assert [q["id"] for q in first] == [q["id"] for q in second]

    def test_full_pre_post_flow_and_improvement(self, client, admin_headers):
        wid, pid = self._setup_workshop(client, admin_headers)

        # Pre-test: answer the first 3 correctly.
        pre_q = client.get(
            "/api/v1/assessment/questions",
            params={"workshop_id": wid, "participant_id": pid, "type": "pre", "language": "en"},
        ).json()
        pre_answers = [
            {"question_id": q["id"], "selected_index": 1 if i < 3 else 3}
            for i, q in enumerate(pre_q)
        ]
        pre_result = client.post(
            "/api/v1/assessment/submit",
            json={"participant_id": pid, "workshop_id": wid, "type": "pre",
                  "answers": pre_answers, "duration_seconds": 200, "language": "en"},
        ).json()
        assert pre_result["max_score"] == 10

        # Post-test: all correct (option index 1 is correct across this bank).
        post_q = client.get(
            "/api/v1/assessment/questions",
            params={"workshop_id": wid, "participant_id": pid, "type": "post", "language": "en"},
        ).json()
        post_answers = [{"question_id": q["id"], "selected_index": 1} for q in post_q]
        post_result = client.post(
            "/api/v1/assessment/submit",
            json={"participant_id": pid, "workshop_id": wid, "type": "post",
                  "answers": post_answers, "duration_seconds": 180, "language": "en"},
        ).json()
        assert post_result["score"] >= pre_result["score"]
        assert post_result["review"][0]["explanation"]

        imp = client.get(f"/api/v1/assessment/participant/{pid}/improvement").json()
        assert imp["pre_score"] is not None and imp["post_score"] is not None
        assert imp["absolute_gain"] == imp["post_score"] - imp["pre_score"]

    def test_dashboard_summary_shape(self, client):
        d = client.get("/api/v1/dashboard/summary").json()
        assert "totals" in d and "awareness" in d
        assert "undefined_improvement_count" in d["awareness"]
        assert isinstance(d["risk_distribution"], dict)

    def test_csv_export(self, client):
        r = client.get("/api/v1/dashboard/export", params={"format": "csv"})
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_certificate_blocked_before_post_test(self, client, admin_headers):
        _, pid = self._setup_workshop(client, admin_headers)
        r = client.get(f"/api/v1/certificates/{pid}")
        assert r.status_code == 400


class TestSystem:
    def test_health(self, client):
        assert client.get("/health").json()["status"] == "ok"

    def test_status_reports_no_api_keys_needed(self, client):
        d = client.get("/api/v1/meta/status").json()
        assert d["api_keys_required"] is False
        assert d["offline_capable"] is True
        assert set(d["languages"]) == {"en", "ta"}

    def test_helplines_include_1930(self, client):
        values = {h["value"] for h in client.get("/api/v1/meta/helplines").json()}
        assert "1930" in values
        assert "cybercrime.gov.in" in values
