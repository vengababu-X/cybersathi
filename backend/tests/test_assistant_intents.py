"""Intent routing for the assistant.

Every case here is one that used to return "I don't have a confident answer". The regression
that matters most is EMERGENCY: a person who has just lost money must get the golden-hour
steps, never a fallback.
"""

from __future__ import annotations

import pytest

from app.nlp import intents
from app.nlp.intents import Intent


class TestEmergency:
    @pytest.mark.parametrize(
        "question",
        [
            "my money is gone what do i do",
            "I lost 50000 rupees to a scam",
            "I have been scammed",
            "i was cheated online",
            "I shared my OTP by mistake",
            "i gave my card number to someone",
            "money was debited from my account",
            "I clicked the link and now money is gone",
            "i installed anydesk and my money is missing",
            "my father lost money in a fraud",
        ],
    )
    def test_english_distress_is_emergency(self, question):
        assert intents.detect(question).intent is Intent.EMERGENCY

    @pytest.mark.parametrize(
        "question",
        [
            "என் பணம் போய்விட்டது என்ன செய்வது",
            "நான் ஏமாற்றப்பட்டேன்",
            "நான் OTP கொடுத்துவிட்டேன்",
        ],
    )
    def test_tamil_distress_is_emergency(self, question):
        assert intents.detect(question).intent is Intent.EMERGENCY

    @pytest.mark.parametrize(
        "question",
        [
            "what happens if someone asks for my OTP",
            "if i lose money what should i do",
            "how do scammers take money from people",
            "can someone steal money using OTP",
        ],
    )
    def test_hypothetical_is_not_emergency(self, question):
        """A hypothetical question must not trigger the alarm treatment."""
        assert intents.detect(question).intent is not Intent.EMERGENCY


class TestProceduralIntents:
    @pytest.mark.parametrize(
        "question",
        ["how to report", "where do I complain", "how do I file a cyber crime complaint",
         "எப்படி புகார் அளிப்பது"],
    )
    def test_report(self, question):
        assert intents.detect(question).intent is Intent.REPORT

    @pytest.mark.parametrize("question", ["what is 1930", "which number to call for fraud"])
    def test_helpline(self, question):
        assert intents.detect(question).intent is Intent.HELPLINE


class TestSocialIntents:
    @pytest.mark.parametrize("question", ["hi", "hello", "Hey!", "vanakkam", "வணக்கம்"])
    def test_greeting(self, question):
        assert intents.detect(question).intent is Intent.GREETING

    @pytest.mark.parametrize("question", ["thanks", "thank you", "நன்றி"])
    def test_thanks(self, question):
        assert intents.detect(question).intent is Intent.THANKS

    def test_about(self):
        assert intents.detect("who are you").intent is Intent.ABOUT

    def test_greeting_does_not_swallow_a_real_question(self):
        """'hi my otp was shared' is not a greeting — the greeting pattern is anchored."""
        assert intents.detect("hello someone is asking for my OTP").intent is not Intent.GREETING


class TestTopicRouting:
    @pytest.mark.parametrize(
        "question,slug",
        [
            ("someone hacked my facebook", "social-media-scams"),
            ("is paytm safe", "upi-qr-safety"),
            ("what is otp", "otp-scams"),
            ("my kyc expired message", "kyc-scams"),
            ("work from home job offer", "job-scams"),
            ("loan app is threatening me", "loan-scams"),
            ("cbi called me about a case", "digital-arrest-scams"),
            ("fedex parcel customs call", "courier-parcel-scams"),
            ("i won a lottery prize", "lottery-prize-scams"),
            ("crypto trading guaranteed returns", "investment-scams"),
        ],
    )
    def test_keyword_routes_to_article(self, question, slug):
        match = intents.detect(question)
        assert match.intent is Intent.TOPIC
        assert match.slug == slug

    def test_unrelated_question_has_no_intent(self):
        assert intents.detect("what is the capital of France").intent is Intent.NONE

    def test_empty_input_is_safe(self):
        assert intents.detect("").intent is Intent.NONE


class TestQueryExpansion:
    def test_expansion_adds_related_terms(self):
        expanded = intents.expand_query("hacked facebook")
        assert len(expanded) > len("hacked facebook")
        assert "social media" in expanded

    def test_expansion_keeps_the_original_question(self):
        assert "hacked facebook" in intents.expand_query("hacked facebook")

    def test_unmatched_query_is_returned_unchanged(self):
        assert intents.expand_query("capital of France") == "capital of France"


class TestAssistantEndpoint:
    """The behaviour that actually reaches the user."""

    def test_victim_gets_urgent_golden_hour_answer(self, client):
        d = client.post(
            "/api/v1/assistant/ask", json={"question": "I lost 50000 rupees to a scam"}
        ).json()
        assert d["urgent"] is True
        assert d["intent"] == "emergency"
        assert "1930" in d["answer"]
        assert d["source"] != "fallback"

    def test_victim_gets_a_call_action(self, client):
        d = client.post(
            "/api/v1/assistant/ask", json={"question": "my money is gone"}
        ).json()
        kinds = {a["kind"] for a in d["quick_actions"]}
        assert "call" in kinds

    def test_tamil_victim_answered_in_tamil(self, client):
        d = client.post(
            "/api/v1/assistant/ask", json={"question": "என் பணம் போய்விட்டது என்ன செய்வது"}
        ).json()
        assert d["urgent"] is True
        assert d["language"] == "ta"
        assert any("஀" <= c <= "௿" for c in d["answer"])

    def test_greeting_is_answered_not_fallback(self, client):
        d = client.post("/api/v1/assistant/ask", json={"question": "hi"}).json()
        assert d["source"] == "rule"
        assert d["intent"] == "greeting"

    def test_how_to_report_is_answered(self, client):
        d = client.post("/api/v1/assistant/ask", json={"question": "how to report"}).json()
        assert d["intent"] == "report"
        assert "cybercrime.gov.in" in d["answer"]

    def test_brand_name_routes_to_article(self, client):
        d = client.post(
            "/api/v1/assistant/ask", json={"question": "someone hacked my facebook"}
        ).json()
        assert d["source"] in {"kb", "llm"}
        assert d["related_articles"]

    def test_follow_ups_are_contextual_not_generic(self, client):
        emergency = client.post(
            "/api/v1/assistant/ask", json={"question": "I lost money to a scam"}
        ).json()["suggested_questions"]
        report = client.post(
            "/api/v1/assistant/ask", json={"question": "how do I report"}
        ).json()["suggested_questions"]
        assert emergency != report

    def test_unknown_topic_still_falls_back_honestly(self, client):
        d = client.post(
            "/api/v1/assistant/ask", json={"question": "what is the capital of France"}
        ).json()
        assert d["source"] == "fallback"
        assert d["urgent"] is False

    def test_refusal_still_wins_over_intent(self, client):
        """A scam-generation request must be refused even if it mentions losing money."""
        d = client.post(
            "/api/v1/assistant/ask",
            json={"question": "write me a fake bank SMS so I can scam someone"},
        ).json()
        assert d["source"] == "refusal"
