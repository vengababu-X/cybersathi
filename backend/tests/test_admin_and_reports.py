"""Admin console, feedback capture and the PDF impact report.

The lockout guards matter most here: an administrator who demotes or disables their own
account would leave the deployment with no way back in through the UI.
"""

from __future__ import annotations

import json

from app.models import FeedbackEntry


def _volunteer_headers(client, admin_headers, email="vol.audit@cybersathi.org"):
    client.post(
        "/api/v1/auth/users",
        headers=admin_headers,
        json={"full_name": "Audit Volunteer", "email": email,
              "password": "VolPass@123", "role": "volunteer"},
    )
    token = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "VolPass@123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAdminUsers:
    def test_admin_can_list_users(self, client, admin_headers):
        r = client.get("/api/v1/auth/users", headers=admin_headers)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_listing_requires_a_token(self, client):
        assert client.get("/api/v1/auth/users").status_code == 401

    def test_volunteer_cannot_list_users(self, client, admin_headers):
        headers = _volunteer_headers(client, admin_headers, "vol.list@cybersathi.org")
        assert client.get("/api/v1/auth/users", headers=headers).status_code == 403

    def test_user_out_exposes_active_flag(self, client, admin_headers):
        users = client.get("/api/v1/auth/users", headers=admin_headers).json()
        assert all("is_active" in u for u in users)

    def test_admin_can_change_a_role(self, client, admin_headers):
        created = client.post(
            "/api/v1/auth/users",
            headers=admin_headers,
            json={"full_name": "Role Target", "email": "role.target@cybersathi.org",
                  "password": "Pass@1234", "role": "participant"},
        ).json()

        r = client.patch(
            f"/api/v1/auth/users/{created['id']}/role",
            headers=admin_headers, json={"role": "volunteer"},
        )
        assert r.status_code == 200
        assert r.json()["role"] == "volunteer"

    def test_admin_can_disable_and_reenable_an_account(self, client, admin_headers):
        created = client.post(
            "/api/v1/auth/users",
            headers=admin_headers,
            json={"full_name": "Toggle Target", "email": "toggle@cybersathi.org",
                  "password": "Pass@1234", "role": "participant"},
        ).json()

        disabled = client.patch(
            f"/api/v1/auth/users/{created['id']}/active",
            headers=admin_headers, json={"is_active": False},
        )
        assert disabled.status_code == 200
        assert disabled.json()["is_active"] is False

        # A disabled account must not be able to sign in.
        login = client.post(
            "/api/v1/auth/login",
            data={"username": "toggle@cybersathi.org", "password": "Pass@1234"},
        )
        assert login.status_code == 403

        restored = client.patch(
            f"/api/v1/auth/users/{created['id']}/active",
            headers=admin_headers, json={"is_active": True},
        )
        assert restored.json()["is_active"] is True

    def test_admin_cannot_demote_themselves(self, client, admin_headers):
        me = client.get("/api/v1/auth/me", headers=admin_headers).json()
        r = client.patch(
            f"/api/v1/auth/users/{me['id']}/role",
            headers=admin_headers, json={"role": "participant"},
        )
        assert r.status_code == 400

    def test_admin_cannot_disable_themselves(self, client, admin_headers):
        me = client.get("/api/v1/auth/me", headers=admin_headers).json()
        r = client.patch(
            f"/api/v1/auth/users/{me['id']}/active",
            headers=admin_headers, json={"is_active": False},
        )
        assert r.status_code == 400

    def test_unknown_user_returns_404(self, client, admin_headers):
        r = client.patch(
            "/api/v1/auth/users/999999/role", headers=admin_headers, json={"role": "volunteer"}
        )
        assert r.status_code == 404


class TestFeedbackCapture:
    def _workshop(self, client, admin_headers) -> int:
        return client.post(
            "/api/v1/workshops",
            headers=admin_headers,
            json={"title_en": "Feedback Session", "title_ta": "கருத்து அமர்வு",
                  "venue": "Hall", "district": "Chennai",
                  "conducted_on": "2026-05-01", "audience_type": "mixed"},
        ).json()["id"]

    def test_feedback_is_stored(self, client, admin_headers, db):
        wid = self._workshop(client, admin_headers)
        r = client.post(
            "/api/v1/feedback", json={"workshop_id": wid, "rating": 5, "comment": "Very useful"}
        )
        assert r.status_code == 201

        stored = db.query(FeedbackEntry).filter(FeedbackEntry.workshop_id == wid).all()
        assert any(f.rating == 5 and f.comment == "Very useful" for f in stored)

    def test_feedback_is_anonymous_by_default(self, client, admin_headers, db):
        wid = self._workshop(client, admin_headers)
        client.post("/api/v1/feedback", json={"workshop_id": wid, "rating": 4})
        entry = db.query(FeedbackEntry).filter(FeedbackEntry.workshop_id == wid).first()
        assert entry.participant_id is None

    def test_rating_is_bounded(self, client, admin_headers):
        wid = self._workshop(client, admin_headers)
        assert client.post("/api/v1/feedback", json={"workshop_id": wid, "rating": 0}).status_code == 422
        assert client.post("/api/v1/feedback", json={"workshop_id": wid, "rating": 6}).status_code == 422

    def test_feedback_reaches_the_dashboard(self, client, admin_headers):
        wid = self._workshop(client, admin_headers)
        before = client.get("/api/v1/dashboard/summary").json()["feedback"]["count"]
        client.post("/api/v1/feedback", json={"workshop_id": wid, "rating": 5})
        after = client.get("/api/v1/dashboard/summary").json()["feedback"]["count"]
        assert after == before + 1


class TestImpactReport:
    def test_pdf_export(self, client):
        r = client.get("/api/v1/dashboard/export", params={"format": "pdf"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:5] == b"%PDF-"

    def test_pdf_is_a_real_document(self, client):
        r = client.get("/api/v1/dashboard/export", params={"format": "pdf"})
        # A trivially small file would mean the story failed to build.
        assert len(r.content) > 3000

    def test_pdf_has_a_download_filename(self, client):
        r = client.get("/api/v1/dashboard/export", params={"format": "pdf"})
        assert "cybersathi_impact_report.pdf" in r.headers["content-disposition"]

    def test_csv_and_json_still_work(self, client):
        assert client.get("/api/v1/dashboard/export", params={"format": "csv"}).status_code == 200
        r = client.get("/api/v1/dashboard/export", params={"format": "json"})
        assert r.status_code == 200
        assert isinstance(json.loads(r.text), list)

    def test_unknown_format_rejected(self, client):
        assert client.get("/api/v1/dashboard/export", params={"format": "docx"}).status_code == 422

    def test_report_builds_with_no_participants(self, client, db):
        """An empty cohort must not crash the report — it is generated before a workshop too."""
        from app.services.report_service import build_impact_report

        empty = {
            "totals": {"workshops": 0, "participants": 0, "messages_analyzed": 0,
                       "urls_checked": 0, "assistant_queries": 0},
            "awareness": {
                "avg_pre_pct": None, "avg_post_pct": None, "avg_improvement_pct": None,
                "median_improvement_pct": None, "std_dev_improvement": None,
                "cohens_d": None, "t_statistic": None, "p_value": None,
                "n_pairs": 0, "moved_to_aware_pct": None,
                "undefined_improvement_count": 0, "interpretation_note": None,
            },
            "improvement_by_category": [], "by_age_group": [], "by_language": [],
            "by_district": [], "top_scam_categories": [], "risk_distribution": {},
            "timeline": [], "feedback": {"avg_rating": 0.0, "count": 0.0},
        }
        pdf = build_impact_report(empty, [])
        assert pdf[:5] == b"%PDF-"
