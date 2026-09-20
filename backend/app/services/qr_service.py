"""QR / UPI safety analysis and the interactive scenario game.

This module never touches a payment system. It parses the text decoded from a QR code by the
browser and teaches the one rule that prevents most UPI fraud in India: a PIN only ever sends
money out.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, unquote, urlparse

GOLDEN_RULE = {
    "en": "Scanning a QR code or approving a request is ALWAYS to PAY. You never scan, and never enter a PIN, to RECEIVE money.",
    "ta": "QR ஸ்கேன் செய்வதும் கோரிக்கையை ஏற்பதும் எப்போதும் பணம் செலுத்தவே. பணம் பெற ஒருபோதும் ஸ்கேன் செய்யவோ PIN போடவோ தேவையில்லை.",
}

DISCLAIMER = {
    "en": "Advisory only. This tool reads the QR text and never makes or approves any payment.",
    "ta": "ஆலோசனை மட்டுமே. இந்தக் கருவி QR உரையைப் படிக்கிறது, எந்தப் பணப் பரிமாற்றமும் செய்யாது.",
}

_LOOKALIKE = re.compile(r"[Ѐ-ӿͰ-Ͽ]")  # Cyrillic / Greek in a Latin name


def _signal(rule_id: str, weight: float, snippet: str, en: str, ta: str) -> dict:
    return {
        "rule_id": rule_id,
        "category": "upi",
        "matched_snippet": snippet[:120],
        "why_en": en,
        "why_ta": ta,
        "weight": weight,
    }


def analyze_payload(payload: str) -> dict:
    payload = (payload or "").strip()
    signals: list[dict] = []
    parsed: dict[str, str] = {}

    lower = payload.lower()

    if lower.startswith("upi://"):
        payload_type = "upi"
        query = parse_qs(urlparse(payload).query)
        flat = {k: unquote(v[0]) for k, v in query.items() if v}
        parsed = {
            "payee_vpa": flat.get("pa", ""),
            "payee_name": flat.get("pn", ""),
            "amount": flat.get("am", ""),
            "note": flat.get("tn", ""),
            "merchant_code": flat.get("mc", ""),
            "transaction_ref": flat.get("tr", ""),
            "mode": urlparse(payload).netloc or "pay",
        }

        intent = urlparse(payload).netloc.lower()
        if intent in {"collect", "mandate"} or "collect" in lower:
            signals.append(
                _signal(
                    "upi_collect_intent", 0.9, intent or "collect",
                    "This is a COLLECT request — approving it takes money FROM your account, it does not send money to you.",
                    "இது COLLECT கோரிக்கை — ஏற்றால் உங்கள் கணக்கிலிருந்து பணம் போகும், உங்களுக்கு வராது.",
                )
            )

        amount = parsed["amount"]
        if amount:
            try:
                if float(amount) > 0:
                    signals.append(
                        _signal(
                            "prefilled_amount", 0.5, amount,
                            f"The amount Rs {amount} is already filled in. Check it carefully — a tampered QR can carry a much larger amount than you expect.",
                            f"ரூ {amount} ஏற்கனவே நிரப்பப்பட்டுள்ளது. கவனமாகச் சரிபாருங்கள் — மாற்றப்பட்ட QR-ல் நீங்கள் நினைப்பதைவிட பெரிய தொகை இருக்கலாம்.",
                        )
                    )
            except ValueError:
                pass

        note = parsed["note"].lower()
        if any(w in note for w in ["refund", "cashback", "prize", "reward", "receive", "credit", "return"]):
            signals.append(
                _signal(
                    "receive_money_claim", 0.95, parsed["note"],
                    "The note claims this is a refund or reward. Remember: you never scan or approve anything to receive money.",
                    "இது ரீஃபண்ட் அல்லது பரிசு என்று குறிப்பு கூறுகிறது. நினைவில் வையுங்கள்: பணம் பெற எதையும் ஸ்கேன் செய்யவோ ஏற்கவோ தேவையில்லை.",
                )
            )

        name = parsed["payee_name"]
        vpa = parsed["payee_vpa"]
        if name and vpa:
            handle = vpa.split("@")[0].lower()
            simple_name = re.sub(r"[^a-z]", "", name.lower())
            if simple_name and len(simple_name) > 3 and simple_name[:4] not in handle:
                signals.append(
                    _signal(
                        "name_vpa_mismatch", 0.45, f"{name} / {vpa}",
                        "The displayed name does not match the UPI ID. Always confirm the name your own app shows before paying.",
                        "காட்டப்படும் பெயர் UPI ID-யுடன் பொருந்தவில்லை. செலுத்தும் முன் உங்கள் செயலியில் தெரியும் பெயரை உறுதி செய்யுங்கள்.",
                    )
                )

        if _LOOKALIKE.search(name):
            signals.append(
                _signal(
                    "lookalike_characters", 0.7, name,
                    "The payee name uses look-alike foreign characters to imitate a real merchant name.",
                    "பெறுநர் பெயரில் உண்மையான வணிகர் பெயரைப் போல் தோன்ற வேற்று எழுத்துக்கள் உள்ளன.",
                )
            )

    elif lower.startswith(("http://", "https://")):
        payload_type = "url"
        parsed = {"url": payload}
        signals.append(
            _signal(
                "qr_contains_link", 0.5, payload,
                "This QR code opens a website instead of a payment. Treat it exactly like a link in an unknown message.",
                "இந்த QR பணப் பரிமாற்றத்திற்கு பதிலாக ஒரு இணையதளத்தைத் திறக்கிறது. தெரியாத செய்தியில் உள்ள இணைப்பு போலவே கருதுங்கள்.",
            )
        )
        if ".apk" in lower:
            signals.append(
                _signal(
                    "apk_download", 0.95, payload,
                    "This link downloads an app file directly. Never install apps from outside the official Play Store.",
                    "இந்த இணைப்பு செயலிக் கோப்பை நேரடியாகப் பதிவிறக்குகிறது. Play Store-க்கு வெளியே உள்ள செயலிகளை நிறுவ வேண்டாம்.",
                )
            )
    else:
        payload_type = "text"
        parsed = {"text": payload[:300]}
        if any(w in lower for w in ["pin", "otp", "password"]):
            signals.append(
                _signal(
                    "credential_request", 0.9, payload[:60],
                    "This QR content mentions a PIN, OTP or password. No genuine payment code needs these.",
                    "இந்த QR உள்ளடக்கம் PIN, OTP அல்லது கடவுச்சொல்லைக் குறிப்பிடுகிறது. உண்மையான பணக் குறியீட்டுக்கு இவை தேவையில்லை.",
                )
            )

    positive = [s["weight"] for s in signals if s["weight"] > 0]
    score = 0.0
    remaining = 1.0
    for w in sorted(positive, reverse=True):
        score += w * remaining
        remaining = 1.0 - score
    score = round(min(score, 1.0) * 100, 1)

    label = "high_risk" if score >= 70 else "suspicious" if score >= 35 else "safe"

    if label == "high_risk":
        advice = {
            "en": "Do not scan or approve this. It is designed to take money from your account.",
            "ta": "இதை ஸ்கேன் செய்யவோ ஏற்கவோ வேண்டாம். உங்கள் கணக்கிலிருந்து பணம் எடுக்கவே இது வடிவமைக்கப்பட்டுள்ளது.",
        }
    elif label == "suspicious":
        advice = {
            "en": "Check the payee name and amount on your own screen before approving anything.",
            "ta": "எதையும் ஏற்கும் முன் பெறுநர் பெயரையும் தொகையையும் உங்கள் திரையில் சரிபாருங்கள்.",
        }
    else:
        advice = {
            "en": "No strong warning signs found. Still read the payee name and amount on your app before paying.",
            "ta": "வலுவான எச்சரிக்கை அறிகுறிகள் இல்லை. இருப்பினும் செலுத்தும் முன் பெயரையும் தொகையையும் படியுங்கள்.",
        }

    return {
        "payload_type": payload_type,
        "risk_label": label,
        "risk_score": score,
        "parsed": parsed,
        "signals": signals,
        "golden_rule": GOLDEN_RULE,
        "advice": advice,
        "disclaimer": DISCLAIMER,
    }


SCENARIOS: list[dict] = [
    {
        "id": "refund_qr",
        "title_en": "The refund QR code",
        "title_ta": "ரீஃபண்ட் QR குறியீடு",
        "situation_en": "You complained about a failed online order. A 'customer care agent' calls and sends a QR code, saying you must scan it and enter your UPI PIN to receive the Rs 1,200 refund.",
        "situation_ta": "தோல்வியடைந்த ஆர்டர் பற்றி புகார் அளித்தீர்கள். 'கஸ்டமர் கேர்' நபர் அழைத்து, ரூ.1,200 ரீஃபண்ட் பெற QR-ஐ ஸ்கேன் செய்து UPI PIN போட வேண்டும் என்று கூறுகிறார்.",
        "choices": [
            {"text_en": "Scan and enter the PIN to get the refund", "text_ta": "ரீஃபண்ட் பெற ஸ்கேன் செய்து PIN போடுவேன்", "is_safe": False,
             "feedback_en": "This would send Rs 1,200 (or more) out of your account. A PIN never brings money in.", "feedback_ta": "இது உங்கள் கணக்கிலிருந்து பணத்தை அனுப்பும். PIN பணத்தைக் கொண்டு வராது."},
            {"text_en": "Refuse — refunds never need a QR scan or PIN", "text_ta": "மறுப்பேன் — ரீஃபண்டுக்கு QR அல்லது PIN தேவையில்லை", "is_safe": True,
             "feedback_en": "Correct. A genuine refund arrives on its own, to the account you originally paid from.", "feedback_ta": "சரி. உண்மையான ரீஃபண்ட் தானாகவே, நீங்கள் செலுத்திய கணக்குக்கே வரும்."},
            {"text_en": "Scan it but do not enter the PIN", "text_ta": "ஸ்கேன் செய்வேன் ஆனால் PIN போட மாட்டேன்", "is_safe": False,
             "feedback_en": "Safer, but you are still one tap from paying. Do not engage at all.", "feedback_ta": "பரவாயில்லை, ஆனால் ஒரு அழுத்தத்தில் பணம் போகலாம். முற்றிலும் தவிர்க்கவும்."},
        ],
        "lesson_en": "Receiving money requires nothing from you. If a PIN is involved, money is leaving.",
        "lesson_ta": "பணம் பெற உங்களிடமிருந்து எதுவும் தேவையில்லை. PIN தேவைப்பட்டால், பணம் வெளியே போகிறது.",
    },
    {
        "id": "marketplace_advance",
        "title_en": "The buyer who insists on an advance",
        "title_ta": "முன்பணம் தருவதாக வலியுறுத்தும் வாங்குபவர்",
        "situation_en": "You listed a bicycle for sale. A buyer says he is an army officer being transferred, cannot come in person, and will send an advance. He shares a QR code for you to scan 'to receive' the money.",
        "situation_ta": "மிதிவண்டியை விற்பனைக்கு வைத்தீர்கள். வாங்குபவர் தான் இடமாற்றம் ஆகும் ராணுவ அதிகாரி என்றும், நேரில் வர முடியாது என்றும், முன்பணம் அனுப்புவதாகவும் கூறி, 'பணம் பெற' ஸ்கேன் செய்ய QR அனுப்புகிறார்.",
        "choices": [
            {"text_en": "Scan the code to receive the advance", "text_ta": "முன்பணம் பெற குறியீட்டை ஸ்கேன் செய்வேன்", "is_safe": False,
             "feedback_en": "This is the most common marketplace fraud in India. Scanning sends your money to him.", "feedback_ta": "இது இந்தியாவின் மிகப் பொதுவான மார்க்கெட்பிளேஸ் மோசடி. ஸ்கேன் செய்தால் உங்கள் பணம் அவருக்குப் போகும்."},
            {"text_en": "Ask him to transfer directly to your UPI ID instead", "text_ta": "என் UPI ID-க்கு நேரடியாக அனுப்பச் சொல்வேன்", "is_safe": True,
             "feedback_en": "Correct. Anyone can send money to your UPI ID without you doing anything at all.", "feedback_ta": "சரி. நீங்கள் எதுவும் செய்யாமலேயே எவரும் உங்கள் UPI ID-க்கு பணம் அனுப்பலாம்."},
            {"text_en": "Trust him because of the uniform in his profile photo", "text_ta": "சுயவிவரப் படத்தில் சீருடை இருப்பதால் நம்புவேன்", "is_safe": False,
             "feedback_en": "Uniform photos are downloaded from the internet. They prove nothing.", "feedback_ta": "சீருடைப் படங்கள் இணையத்திலிருந்து எடுக்கப்பட்டவை. அவை எதையும் நிரூபிக்காது."},
        ],
        "lesson_en": "To receive money you give only your UPI ID or phone number — never a scan, never a PIN.",
        "lesson_ta": "பணம் பெற உங்கள் UPI ID அல்லது ஃபோன் எண்ணை மட்டும் தருவீர்கள் — ஸ்கேன் அல்ல, PIN அல்ல.",
    },
    {
        "id": "fuel_pump_qr",
        "title_en": "The wrong amount at the fuel pump",
        "title_ta": "பெட்ரோல் நிலையத்தில் தவறான தொகை",
        "situation_en": "You fill petrol worth Rs 500 and scan the QR sticker at the counter. Your app opens with Rs 5,000 already filled in and a payee name you do not recognise.",
        "situation_ta": "ரூ.500 பெட்ரோல் நிரப்பி, கவுண்டரில் உள்ள QR ஸ்டிக்கரை ஸ்கேன் செய்கிறீர்கள். உங்கள் செயலியில் ரூ.5,000 ஏற்கனவே நிரப்பப்பட்டு, தெரியாத பெயர் தெரிகிறது.",
        "choices": [
            {"text_en": "Pay it — the machine must be correct", "text_ta": "செலுத்துவேன் — இயந்திரம் சரியாகத்தான் இருக்கும்", "is_safe": False,
             "feedback_en": "The QR sticker was replaced with a fraudster's. Always read your own screen.", "feedback_ta": "QR ஸ்டிக்கர் மோசடியாளருடையதாக மாற்றப்பட்டுள்ளது. உங்கள் திரையைப் படியுங்கள்."},
            {"text_en": "Cancel, show the staff, and pay by another method", "text_ta": "ரத்து செய்து, ஊழியரிடம் காட்டி, வேறு வழியில் செலுத்துவேன்", "is_safe": True,
             "feedback_en": "Correct. A mismatched amount or unknown payee means the sticker has been tampered with.", "feedback_ta": "சரி. தொகை அல்லது பெயர் பொருந்தவில்லை என்றால் ஸ்டிக்கர் மாற்றப்பட்டுள்ளது."},
            {"text_en": "Edit the amount to Rs 500 and pay anyway", "text_ta": "தொகையை ரூ.500 ஆக மாற்றி செலுத்துவேன்", "is_safe": False,
             "feedback_en": "The amount is not the only problem — the money would still go to a stranger.", "feedback_ta": "தொகை மட்டும் பிரச்சினை அல்ல — பணம் அந்நியருக்கே போகும்."},
        ],
        "lesson_en": "Always read the payee name and amount on your own phone before you approve.",
        "lesson_ta": "ஏற்கும் முன் பெறுநர் பெயரையும் தொகையையும் உங்கள் ஃபோனில் எப்போதும் படியுங்கள்.",
    },
    {
        "id": "cashback_request",
        "title_en": "The cashback payment request",
        "title_ta": "கேஷ்பேக் பணக் கோரிக்கை",
        "situation_en": "A notification appears in your payment app: 'Payment request of Rs 4,999 from RewardsIndia — Note: Diwali cashback credit'. It asks you to approve.",
        "situation_ta": "உங்கள் செயலியில் அறிவிப்பு வருகிறது: 'RewardsIndia-விடமிருந்து ரூ.4,999 பணக் கோரிக்கை — குறிப்பு: தீபாவளி கேஷ்பேக்'. ஏற்கச் சொல்கிறது.",
        "choices": [
            {"text_en": "Approve it to get the cashback", "text_ta": "கேஷ்பேக் பெற ஏற்பேன்", "is_safe": False,
             "feedback_en": "Approving a request pays Rs 4,999 OUT. The word 'cashback' in the note is bait.", "feedback_ta": "கோரிக்கையை ஏற்றால் ரூ.4,999 வெளியே போகும். 'கேஷ்பேக்' என்ற சொல் தூண்டில்."},
            {"text_en": "Decline and report the requester", "text_ta": "நிராகரித்து கோரிக்கையாளரைப் புகாரளிப்பேன்", "is_safe": True,
             "feedback_en": "Correct. Genuine cashback is credited automatically and never needs your approval.", "feedback_ta": "சரி. உண்மையான கேஷ்பேக் தானாகவே வரவு வைக்கப்படும், உங்கள் அனுமதி தேவையில்லை."},
            {"text_en": "Approve but cancel quickly afterwards", "text_ta": "ஏற்றுவிட்டு பின் உடனே ரத்து செய்வேன்", "is_safe": False,
             "feedback_en": "UPI payments are instant and cannot be cancelled after approval.", "feedback_ta": "UPI பணப் பரிமாற்றம் உடனடியானது, ஏற்ற பிறகு ரத்து செய்ய முடியாது."},
        ],
        "lesson_en": "Any request that needs your approval is a request for YOUR money.",
        "lesson_ta": "உங்கள் அனுமதி தேவைப்படும் எந்தக் கோரிக்கையும் உங்கள் பணத்திற்கான கோரிக்கையே.",
    },
    {
        "id": "screen_share",
        "title_en": "The helpful support executive",
        "title_ta": "உதவ வரும் சப்போர்ட் நபர்",
        "situation_en": "Your payment failed. You call a helpline number you found online. The agent asks you to install AnyDesk so he can 'fix the settings' on your phone.",
        "situation_ta": "பணப் பரிமாற்றம் தோல்வியடைந்தது. இணையத்தில் கிடைத்த உதவி எண்ணை அழைக்கிறீர்கள். 'அமைப்புகளைச் சரி செய்ய' AnyDesk நிறுவச் சொல்கிறார்.",
        "choices": [
            {"text_en": "Install it — he is trying to help", "text_ta": "நிறுவுவேன் — அவர் உதவவே முயல்கிறார்", "is_safe": False,
             "feedback_en": "He can now see your PIN as you type it and operate your banking app himself.", "feedback_ta": "நீங்கள் PIN போடுவதை அவர் பார்ப்பார், உங்கள் வங்கி செயலியை இயக்குவார்."},
            {"text_en": "Refuse, hang up, and use the number in the official app", "text_ta": "மறுத்து, துண்டித்து, அதிகாரப்பூர்வ செயலியில் உள்ள எண்ணைப் பயன்படுத்துவேன்", "is_safe": True,
             "feedback_en": "Correct — twice. The online number was likely planted, and no real support needs screen access.", "feedback_ta": "இரு வகையிலும் சரி. இணைய எண் மோசடியாளர் வைத்தது, உண்மையான சப்போர்ட்டுக்கு திரை அனுமதி தேவையில்லை."},
            {"text_en": "Install it but cover the screen with your hand", "text_ta": "நிறுவிவிட்டு கையால் திரையை மறைப்பேன்", "is_safe": False,
             "feedback_en": "Screen sharing transmits the display itself — covering the phone changes nothing.", "feedback_ta": "திரை பகிர்வு காட்சியையே அனுப்பும் — ஃபோனை மறைப்பதால் பலன் இல்லை."},
        ],
        "lesson_en": "Never install a screen-sharing app on the phone you use for banking.",
        "lesson_ta": "வங்கிக்குப் பயன்படுத்தும் ஃபோனில் திரை பகிர்வு செயலியை ஒருபோதும் நிறுவ வேண்டாம்.",
    },
    {
        "id": "prize_scan",
        "title_en": "Scan to receive your prize",
        "title_ta": "பரிசு பெற ஸ்கேன் செய்யுங்கள்",
        "situation_en": "A WhatsApp message says you have won Rs 10,000 in a festival draw. It includes a QR code with the caption 'Scan to receive your prize instantly'.",
        "situation_ta": "பண்டிகை டிராவில் ரூ.10,000 வென்றதாக WhatsApp செய்தி வருகிறது. 'பரிசை உடனே பெற ஸ்கேன் செய்யுங்கள்' என்ற QR உள்ளது.",
        "choices": [
            {"text_en": "Scan it quickly before the offer expires", "text_ta": "சலுகை முடிவதற்குள் ஸ்கேன் செய்வேன்", "is_safe": False,
             "feedback_en": "Two scams at once: a prize you never entered for, and a scan that pays money out.", "feedback_ta": "இரண்டு மோசடிகள்: நீங்கள் பங்கேற்காத பரிசு, மற்றும் பணத்தை அனுப்பும் ஸ்கேன்."},
            {"text_en": "Delete the message without scanning", "text_ta": "ஸ்கேன் செய்யாமல் செய்தியை நீக்குவேன்", "is_safe": True,
             "feedback_en": "Correct. You cannot win a draw you never entered, and prizes never require a scan.", "feedback_ta": "சரி. பங்கேற்காத டிராவில் வெற்றி பெற முடியாது, பரிசுக்கு ஸ்கேன் தேவையில்லை."},
            {"text_en": "Forward it to friends to check if it is real", "text_ta": "உண்மையா எனப் பார்க்க நண்பர்களுக்கு அனுப்புவேன்", "is_safe": False,
             "feedback_en": "Forwarding spreads the scam to people who may fall for it. Delete instead.", "feedback_ta": "அனுப்புவது மோசடியைப் பரப்பும். நீக்கிவிடுங்கள்."},
        ],
        "lesson_en": "A prize that requires you to scan or pay anything is not a prize.",
        "lesson_ta": "ஸ்கேன் செய்யவோ பணம் கட்டவோ கேட்கும் பரிசு, பரிசே அல்ல.",
    },
    {
        "id": "pin_from_stranger",
        "title_en": "The stranger who needs your PIN",
        "title_ta": "உங்கள் PIN கேட்கும் அந்நியர்",
        "situation_en": "A caller says a wrong transfer of Rs 3,000 came into your account by mistake and asks you to return it by entering your UPI PIN on a request he will send.",
        "situation_ta": "தவறுதலாக ரூ.3,000 உங்கள் கணக்கில் வந்துவிட்டது என்றும், அவர் அனுப்பும் கோரிக்கையில் UPI PIN போட்டு திருப்பித் தரச் சொல்லியும் அழைக்கிறார்.",
        "choices": [
            {"text_en": "Check your balance first, then decide", "text_ta": "முதலில் இருப்பைச் சரிபார்த்து பின் முடிவு செய்வேன்", "is_safe": True,
             "feedback_en": "Correct. Usually no money ever arrived. Verify in your own app before doing anything.", "feedback_ta": "சரி. பொதுவாக பணமே வந்திருக்காது. உங்கள் செயலியில் சரிபாருங்கள்."},
            {"text_en": "Approve his request to return the money", "text_ta": "பணத்தைத் திருப்பித் தர கோரிக்கையை ஏற்பேன்", "is_safe": False,
             "feedback_en": "The request amount can be far larger than Rs 3,000, and no money ever came in.", "feedback_ta": "கோரிக்கைத் தொகை ரூ.3,000-ஐ விட அதிகமாக இருக்கலாம், பணமே வரவில்லை."},
            {"text_en": "Send Rs 3,000 to the UPI ID he gives", "text_ta": "அவர் தரும் UPI ID-க்கு ரூ.3,000 அனுப்புவேன்", "is_safe": False,
             "feedback_en": "You would be paying a stranger from your own money for a transfer that never happened.", "feedback_ta": "நடக்காத பரிமாற்றத்திற்கு உங்கள் சொந்தப் பணத்தை அந்நியருக்குத் தருவீர்கள்."},
        ],
        "lesson_en": "Verify in your own app before returning anything. And a PIN is never needed to receive.",
        "lesson_ta": "எதையும் திருப்பித் தரும் முன் உங்கள் செயலியில் சரிபாருங்கள். பணம் பெற PIN தேவையில்லை.",
    },
    {
        "id": "autopay_mandate",
        "title_en": "The one-time payment that repeats",
        "title_ta": "மீண்டும் மீண்டும் வரும் 'ஒருமுறை' கட்டணம்",
        "situation_en": "A shopping app asks you to approve a Rs 1 'verification payment'. The approval screen mentions a mandate valid until 2030 for Rs 2,999 per month.",
        "situation_ta": "ஒரு செயலி ரூ.1 'சரிபார்ப்புக் கட்டணம்' ஏற்கச் சொல்கிறது. அனுமதித் திரையில் 2030 வரை மாதம் ரூ.2,999 என்ற மேண்டேட் குறிப்பிடப்பட்டுள்ளது.",
        "choices": [
            {"text_en": "Approve — it is only Rs 1", "text_ta": "ஏற்பேன் — ரூ.1 தானே", "is_safe": False,
             "feedback_en": "You would be authorising Rs 2,999 every month until 2030, not Rs 1 once.", "feedback_ta": "ரூ.1 அல்ல, 2030 வரை மாதம் ரூ.2,999 அனுமதிப்பீர்கள்."},
            {"text_en": "Read the full mandate details and decline", "text_ta": "முழு விவரத்தைப் படித்து நிராகரிப்பேன்", "is_safe": True,
             "feedback_en": "Correct. Always read the validity period and the recurring amount on a mandate screen.", "feedback_ta": "சரி. மேண்டேட் திரையில் காலம் மற்றும் தொடர் தொகையை எப்போதும் படியுங்கள்."},
            {"text_en": "Approve and cancel it later in the app", "text_ta": "ஏற்றுவிட்டு பின் செயலியில் ரத்து செய்வேன்", "is_safe": False,
             "feedback_en": "Risky — the first deduction may occur before you find the cancellation option.", "feedback_ta": "ஆபத்து — ரத்து விருப்பத்தைக் கண்டுபிடிக்கும் முன் முதல் தொகை பிடிக்கப்படலாம்."},
        ],
        "lesson_en": "On an approval screen, read the amount AND how long the permission lasts.",
        "lesson_ta": "அனுமதித் திரையில் தொகையையும், அனுமதி எவ்வளவு காலம் என்பதையும் படியுங்கள்.",
    },
    {
        "id": "fake_customer_care",
        "title_en": "The first search result",
        "title_ta": "தேடலின் முதல் முடிவு",
        "situation_en": "Your gas booking failed. You search online for the company's customer care number and call the first result. The person asks for your card details to 'process the refund'.",
        "situation_ta": "கேஸ் புக்கிங் தோல்வியடைந்தது. நிறுவனத்தின் கஸ்டமர் கேர் எண்ணை இணையத்தில் தேடி முதல் முடிவை அழைக்கிறீர்கள். 'ரீஃபண்ட் செய்ய' கார்டு விவரம் கேட்கிறார்.",
        "choices": [
            {"text_en": "Give the details — you called them, so it is safe", "text_ta": "விவரம் தருவேன் — நானே அழைத்தேன், பாதுகாப்பானது", "is_safe": False,
             "feedback_en": "This is the trap. Fraudsters plant fake numbers in search results precisely so you call them.", "feedback_ta": "இதுவே பொறி. நீங்களே அழைக்க வேண்டும் என்பதற்காகவே தேடல் முடிவுகளில் போலி எண்களை வைக்கிறார்கள்."},
            {"text_en": "Hang up and use the number inside the official app", "text_ta": "துண்டித்து அதிகாரப்பூர்வ செயலியில் உள்ள எண்ணைப் பயன்படுத்துவேன்", "is_safe": True,
             "feedback_en": "Correct. Calling a number yourself does not make it genuine — check where the number came from.", "feedback_ta": "சரி. நீங்களே அழைப்பதால் எண் உண்மையாகிவிடாது — எண் எங்கிருந்து வந்தது எனப் பாருங்கள்."},
            {"text_en": "Give only the card number, not the CVV", "text_ta": "CVV இல்லாமல் கார்டு எண்ணை மட்டும் தருவேன்", "is_safe": False,
             "feedback_en": "Partial details still enable fraud, and he will ask for the rest next.", "feedback_ta": "பகுதி விவரங்களும் மோசடிக்குப் போதும், மீதியையும் கேட்பார்."},
        ],
        "lesson_en": "A helpline number is only as trustworthy as the place you found it.",
        "lesson_ta": "உதவி எண்ணின் நம்பகத்தன்மை, அது எங்கு கிடைத்தது என்பதைப் பொறுத்தது.",
    },
    {
        "id": "test_transaction",
        "title_en": "The small test transaction",
        "title_ta": "சிறிய 'சோதனை' பரிவர்த்தனை",
        "situation_en": "Someone buying your furniture says he will first send Rs 1 as a 'test' and sends you a request to approve, saying approving is needed to 'open' your account for receiving.",
        "situation_ta": "உங்கள் மரச்சாமான் வாங்குபவர், முதலில் 'சோதனைக்கு' ரூ.1 அனுப்புவதாகக் கூறி, பணம் பெற கணக்கை 'திறக்க' அனுமதி தேவை என்று கோரிக்கை அனுப்புகிறார்.",
        "choices": [
            {"text_en": "Approve the Rs 1 request to open the account", "text_ta": "கணக்கைத் திறக்க ரூ.1 கோரிக்கையை ஏற்பேன்", "is_safe": False,
             "feedback_en": "There is no such thing as 'opening' an account to receive. The request may not even be for Rs 1.", "feedback_ta": "பணம் பெற கணக்கைத் 'திறப்பது' என்று எதுவும் இல்லை. கோரிக்கை ரூ.1 ஆகக் கூட இருக்காது."},
            {"text_en": "Tell him to simply send money to your UPI ID", "text_ta": "என் UPI ID-க்கு நேராக அனுப்பச் சொல்வேன்", "is_safe": True,
             "feedback_en": "Correct. Your account is always ready to receive. Nothing needs to be opened or approved.", "feedback_ta": "சரி. உங்கள் கணக்கு எப்போதும் பணம் பெறத் தயாராக உள்ளது. எதையும் திறக்கவோ ஏற்கவோ தேவையில்லை."},
            {"text_en": "Approve it since Rs 1 is a tiny risk", "text_ta": "ரூ.1 தானே, ஆபத்து இல்லை, ஏற்பேன்", "is_safe": False,
             "feedback_en": "You are approving whatever amount the request actually contains — read your screen.", "feedback_ta": "கோரிக்கையில் உள்ள உண்மையான தொகையையே ஏற்கிறீர்கள் — திரையைப் படியுங்கள்."},
        ],
        "lesson_en": "Your account never needs to be 'activated' or 'opened' to receive money.",
        "lesson_ta": "பணம் பெற உங்கள் கணக்கை 'செயல்படுத்த' அல்லது 'திறக்க' வேண்டிய தேவையே இல்லை.",
    },
]


def get_scenarios() -> list[dict]:
    return SCENARIOS
