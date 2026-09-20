"""Privacy guarantees and the rule engine.

These are the tests that matter most for an awareness app: if redaction leaks, the project
stores exactly the data it tells people to protect.
"""

from __future__ import annotations

from app.ml import rules
from app.ml.redaction import defang_url, hash_phone, redact, undefang_url


class TestRedaction:
    def test_otp_is_removed(self):
        out, found = redact("Your OTP is 483920 please share")
        assert "483920" not in out
        assert found

    def test_phone_is_removed(self):
        out, found = redact("Call me on 9876543210 immediately")
        assert "9876543210" not in out
        assert "phone" in found

    def test_card_number_is_removed(self):
        out, _ = redact("My card is 4532015112830366 expiry 05/28")
        assert "4532015112830366" not in out

    def test_aadhaar_is_removed(self):
        out, _ = redact("Aadhaar 4123 4567 8901 linked")
        assert "4123 4567 8901" not in out

    def test_email_is_removed(self):
        out, found = redact("Write to victim@example.com for details")
        assert "victim@example.com" not in out
        assert "email" in found

    def test_clean_text_is_untouched(self):
        text = "Never share your one time password with anyone"
        out, found = redact(text)
        assert out == text
        assert found == []

    def test_empty_input_is_safe(self):
        assert redact("") == ("", [])

    def test_phone_hash_is_stable_and_irreversible(self):
        h1 = hash_phone("9876543210")
        h2 = hash_phone("98765 43210")  # same number, different formatting
        assert h1 == h2
        assert len(h1) == 64
        assert "9876543210" not in h1

    def test_different_phones_hash_differently(self):
        assert hash_phone("9876543210") != hash_phone("9876543211")


class TestDefang:
    def test_defang_makes_url_unclickable(self):
        out = defang_url("http://evil.example.com/login")
        assert "http://" not in out
        assert "[.]" in out

    def test_defang_roundtrip(self):
        original = "http://sbi-kyc.xyz/verify"
        assert undefang_url(defang_url(original)) == original


class TestRuleEngine:
    def test_otp_request_fires(self):
        hits = rules.evaluate("Please share the OTP you received now")
        assert any(h["rule_id"] == "otp_share_request" for h in hits)

    def test_tamil_otp_request_fires(self):
        hits = rules.evaluate("உங்கள் OTP ஐ அனுப்பவும்")
        assert any(h["rule_id"] == "otp_share_request" for h in hits)

    def test_digital_arrest_fires_in_both_languages(self):
        en = rules.evaluate("This is a digital arrest, stay on the video call")
        ta = rules.evaluate("இது டிஜிட்டல் கைது, வீடியோ அழைப்பில் இருங்கள்")
        assert any(h["rule_id"] == "digital_arrest" for h in en)
        assert any(h["rule_id"] == "digital_arrest" for h in ta)

    def test_legitimate_signal_has_negative_weight(self):
        hits = rules.evaluate("OTP 4829. Do not share this OTP with anyone.")
        assert any(h["weight"] < 0 for h in hits)

    def test_legitimate_message_scores_low(self):
        text = "Rs.2,500 debited from A/c XX4412. Avl Bal Rs.8,330. Do not share OTP with anyone."
        assert rules.rule_score(rules.evaluate(text)) < 0.35

    def test_scam_message_scores_high(self):
        text = "Your KYC expired, account blocked in 24 hours, click http://x.xyz and share OTP"
        assert rules.rule_score(rules.evaluate(text)) >= 0.7

    def test_score_is_bounded(self):
        many = "OTP share KYC expired blocked urgent click http://a.xyz win prize job fee loan"
        assert 0.0 <= rules.rule_score(rules.evaluate(many)) <= 1.0

    def test_no_hits_scores_zero(self):
        assert rules.rule_score([]) == 0.0

    def test_specific_category_beats_generic(self):
        hits = rules.evaluate("Congratulations you won Rs 25 lakh in the lucky draw")
        assert rules.dominant_category(hits) == "lottery"
