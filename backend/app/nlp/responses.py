"""Bilingual answers for the intents that must never depend on retrieval.

These are hand-written rather than composed from articles because the wording matters:
the emergency answer is read by someone in panic, so it leads with the single action that
still works — calling 1930 inside the first hour — and puts reassurance before explanation.
"""

from __future__ import annotations

EMERGENCY = {
    "en": (
        "Act now — the first hour matters most. Banks can often freeze the money before it is "
        "withdrawn.\n\n"
        "1. Call 1930 immediately. Say you are reporting a cyber fraud.\n"
        "2. Report online at cybercrime.gov.in and keep the acknowledgement number.\n"
        "3. Call your bank and block the card and net banking.\n"
        "4. Do NOT delete anything — the SMS, call log and screenshots are evidence.\n"
        "5. If you installed any app they asked for, uninstall it and restart the phone.\n"
        "6. Tell one family member right now. Do not handle this alone.\n\n"
        "This is not your fault. Doctors, engineers and bank managers have all been caught by "
        "these — they are professionally designed.\n\n"
        "Be careful of anyone who offers to recover your money for a fee. That is a second scam "
        "that specifically targets people who have already been cheated."
    ),
    "ta": (
        "உடனே செயல்படுங்கள் — முதல் ஒரு மணி நேரம் மிக முக்கியம். பணம் எடுக்கப்படும் முன் "
        "வங்கிகள் அதை நிறுத்த முடியும்.\n\n"
        "1. உடனே 1930-ஐ அழையுங்கள். சைபர் மோசடி பற்றி புகார் என்று சொல்லுங்கள்.\n"
        "2. cybercrime.gov.in-ல் புகார் அளித்து ஒப்புகை எண்ணை வைத்திருங்கள்.\n"
        "3. வங்கியை அழைத்து கார்டையும் நெட் பேங்கிங்கையும் முடக்குங்கள்.\n"
        "4. எதையும் அழிக்காதீர்கள் — SMS, அழைப்பு பதிவு, ஸ்கிரீன்ஷாட் எல்லாம் ஆதாரம்.\n"
        "5. அவர்கள் சொன்ன செயலியை நிறுவியிருந்தால் நீக்கிவிட்டு ஃபோனை மறுதொடக்கம் செய்யுங்கள்.\n"
        "6. இப்போதே ஒரு குடும்ப உறுப்பினரிடம் சொல்லுங்கள். தனியாக சமாளிக்க வேண்டாம்.\n\n"
        "இது உங்கள் தவறு அல்ல. மருத்துவர்கள், பொறியாளர்கள், வங்கி மேலாளர்கள் எல்லோரும் "
        "இதில் சிக்கியுள்ளனர் — இவை தொழில்முறையாக வடிவமைக்கப்பட்டவை.\n\n"
        "கட்டணம் வாங்கி பணத்தை மீட்டுத் தருவதாக கூறுபவர்களிடம் கவனமாக இருங்கள். "
        "ஏற்கனவே ஏமாந்தவர்களை குறி வைக்கும் இரண்டாவது மோசடி அது."
    ),
}

REPORT = {
    "en": (
        "How to report a cyber fraud in India:\n\n"
        "1. Call 1930 — the national cyber crime helpline. Free, and available 24 hours.\n"
        "2. Go to cybercrime.gov.in and file a complaint online. Choose 'Financial Fraud' if "
        "money was lost.\n"
        "3. Keep ready: the transaction details, the phone number or UPI ID used, screenshots, "
        "and your bank account number.\n"
        "4. Save the acknowledgement number the portal gives you.\n"
        "5. Inform your bank in writing as well, and ask for a written acknowledgement.\n\n"
        "You can also report fraud calls and SMS at sancharsaathi.gov.in, and illegal lending "
        "apps at sachet.rbi.org.in.\n\n"
        "Report as soon as possible. Reporting inside the first hour gives the best chance of "
        "the money being frozen."
    ),
    "ta": (
        "இந்தியாவில் சைபர் மோசடியை எப்படிப் புகாரளிப்பது:\n\n"
        "1. 1930-ஐ அழையுங்கள் — தேசிய சைபர் கிரைம் உதவி எண். இலவசம், 24 மணி நேரமும் கிடைக்கும்.\n"
        "2. cybercrime.gov.in-ல் ஆன்லைனில் புகார் அளியுங்கள். பணம் இழந்திருந்தால் "
        "'Financial Fraud' தேர்வு செய்யுங்கள்.\n"
        "3. தயாராக வைத்திருங்கள்: பரிவர்த்தனை விவரங்கள், பயன்படுத்திய எண் அல்லது UPI ID, "
        "ஸ்கிரீன்ஷாட்கள், உங்கள் வங்கிக் கணக்கு எண்.\n"
        "4. தளம் தரும் ஒப்புகை எண்ணைச் சேமியுங்கள்.\n"
        "5. வங்கிக்கும் எழுத்தில் தெரிவித்து ஒப்புகை பெறுங்கள்.\n\n"
        "மோசடி அழைப்புகளை sancharsaathi.gov.in-லும், சட்டவிரோத கடன் செயலிகளை "
        "sachet.rbi.org.in-லும் புகாரளிக்கலாம்.\n\n"
        "முடிந்தவரை விரைவாகப் புகாரளியுங்கள். முதல் ஒரு மணி நேரத்தில் அளித்தால் பணத்தை "
        "நிறுத்த வாய்ப்பு அதிகம்."
    ),
}

HELPLINE = {
    "en": (
        "1930 is India's national cyber crime helpline.\n\n"
        "• Free to call, available 24 hours, in multiple languages.\n"
        "• Use it the moment you realise money has been taken — the first hour is when a "
        "transfer can still be frozen.\n"
        "• You can also file online at cybercrime.gov.in.\n\n"
        "Other useful numbers:\n"
        "• 112 — general emergency\n"
        "• sancharsaathi.gov.in — report fraud calls and SMS\n"
        "• sachet.rbi.org.in — report illegal loan apps and unregistered lenders\n\n"
        "For your bank, use only the number printed on your own card or passbook — never a "
        "number from a search result or a message."
    ),
    "ta": (
        "1930 என்பது இந்தியாவின் தேசிய சைபர் கிரைம் உதவி எண்.\n\n"
        "• இலவச அழைப்பு, 24 மணி நேரமும், பல மொழிகளில் கிடைக்கும்.\n"
        "• பணம் எடுக்கப்பட்டது தெரிந்த உடனே அழையுங்கள் — முதல் ஒரு மணி நேரத்தில்தான் "
        "பரிமாற்றத்தை நிறுத்த முடியும்.\n"
        "• cybercrime.gov.in-ல் ஆன்லைனிலும் புகார் அளிக்கலாம்.\n\n"
        "மற்ற பயனுள்ள எண்கள்:\n"
        "• 112 — பொது அவசர உதவி\n"
        "• sancharsaathi.gov.in — மோசடி அழைப்பு மற்றும் SMS புகார்\n"
        "• sachet.rbi.org.in — சட்டவிரோத கடன் செயலிகள் புகார்\n\n"
        "உங்கள் வங்கிக்கு, உங்கள் கார்டில் அல்லது பாஸ்புக்கில் அச்சிடப்பட்ட எண்ணை மட்டும் "
        "பயன்படுத்துங்கள் — தேடல் முடிவிலோ செய்தியிலோ உள்ள எண்ணை அல்ல."
    ),
}

GREETING = {
    "en": (
        "Hello! I can help you stay safe from cyber-fraud.\n\n"
        "You can:\n"
        "• Paste a suspicious message or link and I will check it\n"
        "• Ask about any scam — OTP, KYC, job offers, loans, UPI, digital arrest\n"
        "• Ask how to report a fraud\n\n"
        "What would you like to know?"
    ),
    "ta": (
        "வணக்கம்! சைபர் மோசடியிலிருந்து பாதுகாப்பாக இருக்க நான் உதவுகிறேன்.\n\n"
        "நீங்கள்:\n"
        "• சந்தேகமான செய்தி அல்லது இணைப்பை ஒட்டலாம், நான் சரிபார்க்கிறேன்\n"
        "• எந்த மோசடி பற்றியும் கேட்கலாம் — OTP, KYC, வேலை, கடன், UPI, டிஜிட்டல் கைது\n"
        "• மோசடியை எப்படிப் புகாரளிப்பது என்று கேட்கலாம்\n\n"
        "என்ன தெரிந்துகொள்ள விரும்புகிறீர்கள்?"
    ),
}

THANKS = {
    "en": (
        "You're welcome. Stay alert, and please pass on what you learned to one person at "
        "home today — that is how this actually protects a family.\n\n"
        "Remember: 1930 for any real incident."
    ),
    "ta": (
        "மகிழ்ச்சி. எச்சரிக்கையாக இருங்கள், இன்று வீட்டில் ஒருவரிடமாவது இதைச் சொல்லுங்கள் — "
        "அப்படித்தான் ஒரு குடும்பம் உண்மையில் பாதுகாக்கப்படுகிறது.\n\n"
        "நினைவில் வையுங்கள்: உண்மையான சம்பவத்திற்கு 1930."
    ),
}

ABOUT = {
    "en": (
        "I am CyberSathi, a cyber-safety helper for everyday people in India.\n\n"
        "I can:\n"
        "• Check whether an SMS or WhatsApp message is a scam, and explain why\n"
        "• Check whether a link is fake — without ever opening it\n"
        "• Explain UPI and QR payment safety\n"
        "• Teach you about OTP, KYC, job, loan, investment and impersonation scams\n"
        "• Tell you exactly what to do if you have been cheated\n\n"
        "I run entirely on this computer. Nothing you type is sent to any outside service, and "
        "personal details like OTPs are removed automatically before anything is saved.\n\n"
        "I give advice, not a guarantee. For any real incident, call 1930."
    ),
    "ta": (
        "நான் சைபர்சாதி, இந்தியாவில் சாதாரண மக்களுக்கான சைபர் பாதுகாப்பு உதவியாளர்.\n\n"
        "நான் செய்யக்கூடியவை:\n"
        "• SMS அல்லது WhatsApp செய்தி மோசடியா என்பதைச் சரிபார்த்து ஏன் என்று விளக்குவேன்\n"
        "• இணைப்பு போலியா என்பதைச் சரிபார்ப்பேன் — அதைத் திறக்காமலேயே\n"
        "• UPI மற்றும் QR பணப் பாதுகாப்பை விளக்குவேன்\n"
        "• OTP, KYC, வேலை, கடன், முதலீடு, ஆள்மாறாட்ட மோசடிகளைக் கற்றுத் தருவேன்\n"
        "• ஏமாற்றப்பட்டிருந்தால் சரியாக என்ன செய்வது என்று சொல்வேன்\n\n"
        "நான் முழுவதும் இந்தக் கணினியிலேயே இயங்குகிறேன். நீங்கள் தட்டச்சு செய்வது வெளியே "
        "அனுப்பப்படுவதில்லை. OTP போன்ற தனிப்பட்ட விவரங்கள் சேமிக்கும் முன் நீக்கப்படும்.\n\n"
        "நான் ஆலோசனை தருகிறேன், உத்தரவாதம் அல்ல. உண்மையான சம்பவத்திற்கு 1930-ஐ அழையுங்கள்."
    ),
}

FALLBACK = {
    "en": (
        "I'm not sure about that one yet, but I can help with these:\n\n"
        "• OTP, KYC and bank messages\n"
        "• Job offers that ask for a fee\n"
        "• Investment and trading promises\n"
        "• UPI, QR codes and payment requests\n"
        "• Loan apps and harassment\n"
        "• Fake officers and 'digital arrest' calls\n"
        "• Social media account theft and blackmail\n\n"
        "You can also paste the message or link itself and I will check it directly.\n\n"
        "For any real incident, call 1930 or report at cybercrime.gov.in."
    ),
    "ta": (
        "அதைப் பற்றி எனக்கு இன்னும் உறுதியாகத் தெரியவில்லை, ஆனால் இவற்றில் உதவ முடியும்:\n\n"
        "• OTP, KYC மற்றும் வங்கி செய்திகள்\n"
        "• கட்டணம் கேட்கும் வேலை வாய்ப்புகள்\n"
        "• முதலீடு மற்றும் வர்த்தக வாக்குறுதிகள்\n"
        "• UPI, QR குறியீடுகள், பணக் கோரிக்கைகள்\n"
        "• கடன் செயலிகள் மற்றும் மிரட்டல்\n"
        "• போலி அதிகாரிகள், 'டிஜிட்டல் கைது' அழைப்புகள்\n"
        "• சமூக ஊடக கணக்குத் திருட்டு மற்றும் மிரட்டல்\n\n"
        "செய்தியையோ இணைப்பையோ நேரடியாக ஒட்டினால் நான் சரிபார்க்கிறேன்.\n\n"
        "உண்மையான சம்பவத்திற்கு 1930-ஐ அழையுங்கள்."
    ),
}


# Quick actions the UI renders as tappable chips under the answer.
# `kind` maps to a frontend behaviour; `value` is the payload.
def quick_actions(intent: str, language: str) -> list[dict]:
    ta = language == "ta"

    call = {
        "kind": "call", "value": "1930",
        "label": "1930-ஐ அழை" if ta else "Call 1930",
    }
    report = {
        "kind": "link", "value": "https://cybercrime.gov.in",
        "label": "ஆன்லைனில் புகார்" if ta else "Report online",
    }
    check_msg = {
        "kind": "route", "value": "/analyzer",
        "label": "செய்தியைச் சரிபார்" if ta else "Check a message",
    }
    check_link = {
        "kind": "route", "value": "/url",
        "label": "இணைப்பைச் சரிபார்" if ta else "Check a link",
    }
    learn = {
        "kind": "route", "value": "/learn",
        "label": "மோசடிகளைக் கற்க" if ta else "Learn about scams",
    }

    if intent in {"emergency", "report", "helpline"}:
        return [call, report]
    if intent in {"greeting", "about", "fallback"}:
        return [check_msg, check_link, learn]
    if intent == "refusal":
        return [call, learn]
    return [check_msg, call]
