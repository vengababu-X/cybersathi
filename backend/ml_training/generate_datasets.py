"""Generate the training datasets.

All data is SYNTHETIC: templates composed from publicly documented fraud patterns
(cybercrime.gov.in advisories, RBI/NPCI awareness material, CERT-In notes). No real victim
message, no real phone number and no live malicious domain is included. URLs are fictional
and are defanged before being written anywhere a human might click them.

Run:  python ml_training/generate_datasets.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)

random.seed(20260920)  # reproducible datasets => reproducible metrics in the report

BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak", "PNB", "Canara Bank", "Union Bank"]
WALLETS = ["Paytm", "PhonePe", "Google Pay", "BHIM"]
AMOUNTS = ["499", "999", "1,250", "2,500", "4,999", "10,000", "25,000", "50,000"]
BIG_AMOUNTS = ["5,00,000", "10,00,000", "25,00,000", "50,00,000", "1 Crore"]
FAKE_LINKS = [
    "http://sbi-kyc-update.xyz/verify", "http://hdfc-secure-login.top/kyc",
    "http://bit.ly/3kycupd", "http://icici-netbank.click/auth",
    "http://paytm-cashback.buzz/claim", "http://tinyurl.com/kyc-updt",
    "http://192.168.44.9/bank/login", "http://epfo-claim-online.work/pf",
    "http://irctc-refund.cyou/ticket", "http://rbi-verify-account.icu/form",
]
PHONES = ["9876543210", "8123456789", "7012345678", "9445566778", "6383991122"]
OTPS = ["483920", "112233", "907845", "554411", "220199"]


def _pick(seq):
    return random.choice(seq)


# --------------------------------------------------------------------------- SCAM TEMPLATES
SCAM_TEMPLATES: dict[str, list[str]] = {
    "otp": [
        "Dear customer, your {bank} account needs verification. Share the OTP {otp} received on your mobile to complete the process.",
        "We are calling from {bank} card division. To upgrade your card kindly tell the OTP sent just now.",
        "Your {wallet} account is on hold. Reply with the 6 digit code {otp} to reactivate immediately.",
        "Sir OTP {otp} aaya hoga, please forward kijiye, warna account block ho jayega.",
        "{bank} security team here. Confirm OTP {otp} within 10 minutes or your net banking will be disabled.",
        "To stop the unauthorised transaction of Rs {amount}, share the verification code immediately.",
    ],
    "kyc": [
        "Dear customer your {bank} KYC has expired. Account will be blocked within 24 hours. Click {link} to update.",
        "URGENT: {wallet} KYC pending. Complete now at {link} or wallet will be frozen today.",
        "Your bank account KYC is incomplete as per RBI. Update immediately {link} to avoid suspension.",
        "{bank} alert: Aadhaar not linked with account. Re-verify KYC at {link} before tonight.",
        "Final notice - KYC verification pending. Download the form from {link} and submit today.",
    ],
    "job": [
        "Congratulations! You are selected for work from home job. Earn Rs {amount} daily. Pay registration fee Rs 499 to start. Contact {phone}",
        "Part time job available. Like YouTube videos and earn Rs 500 per day. Join WhatsApp {phone}",
        "Amazon hiring work from home. Daily payout. Security deposit Rs 1500 refundable. Apply {link}",
        "Your resume is shortlisted for MNC. Interview fee Rs 999 payable to confirm slot. Call {phone}",
        "Data entry job, no experience needed. Earn Rs {amount} weekly. Registration charge only Rs 750.",
        "Hotel rating task available. Complete 5 tasks get Rs 1000. Send joining fee to this UPI.",
    ],
    "investment": [
        "Guaranteed 30% monthly return on crypto trading. Invest Rs {amount} and double your money in 15 days. Join {link}",
        "Stock market tips group. 100% assured profit. Limited seats. Contact expert {phone}",
        "Invest in our forex plan. Risk free returns, get 3x in 30 days. Whatsapp {phone}",
        "Bitcoin investment scheme approved by RBI. Minimum Rs {amount}, daily profit credited. Register {link}",
        "Mutual fund double scheme, fixed 20% return guaranteed every month. Limited offer.",
    ],
    "banking": [
        "Your {bank} account will be suspended today. Update PAN at {link} to continue services.",
        "Dear user, Rs {amount} debited. If not done by you call {phone} immediately.",
        "{bank}: Your debit card is blocked. Share card number and CVV to reactivate.",
        "To receive your refund of Rs {amount}, scan this QR and enter your UPI PIN.",
        "Install AnyDesk app and share screen so our executive can update your account details.",
        "Your net banking password expires today. Confirm your card number and CVV at {link}.",
        "Accept the payment request on {wallet} to receive cashback of Rs {amount}. Enter PIN to confirm.",
    ],
    "loan": [
        "Pre-approved personal loan of Rs {amount} approved. No documents required. Pay processing fee Rs 999. Call {phone}",
        "Instant loan without CIBIL check. Get money in 10 minutes. Apply {link}",
        "Your loan of Rs {amount} is sanctioned. Pay insurance charge Rs 1500 to release amount.",
        "Low interest loan available any CIBIL score. Zero paperwork. Contact {phone}",
    ],
    "impersonation": [
        "Dear consumer your electricity will be disconnected tonight 9:30 pm because previous month bill not updated. Contact electricity officer {phone}",
        "This is from TRAI. Your SIM will be deactivated in 2 hours due to Aadhaar mismatch. Press 1 to verify.",
        "Hello beta, this is your uncle, I changed my number. I need Rs {amount} urgently, will return tomorrow.",
        "I am Major Rajesh from Indian Army, posted transfer. Pay advance Rs {amount} for the furniture, I will send truck.",
        "Your gas subsidy is pending. Update bank account at {link} to receive Rs {amount}.",
        "Mummy my phone is broken, this is my new number. Send Rs {amount} to this GPay urgently.",
    ],
    "social_media": [
        "Your Facebook page violates copyright. Verify within 24 hours at {link} or page will be deleted.",
        "Your Instagram account will be permanently disabled. Confirm your identity here {link}",
        "I have your private video. Pay Rs {amount} or I will send it to all your contacts.",
        "WhatsApp subscription expired. Renew now at {link} to avoid losing your chats.",
        "You have been tagged in a post. See photo here {link}",
    ],
    "lottery": [
        "Congratulations! You won Rs {big} in KBC lucky draw. Call {phone} and pay processing fee to claim prize.",
        "Your mobile number is selected in Coca Cola lucky draw. Prize Rs {big}. Contact WhatsApp {phone}",
        "CONGRATULATIONS!! You are the lucky winner of Rs {big}. Send your bank details to claim.",
        "Your number won the Diwali bumper prize of Rs {big}. Pay GST of Rs {amount} to release the amount.",
    ],
    "courier_parcel": [
        "Your FedEx parcel is held at customs due to illegal items. Call {phone} immediately to avoid legal action.",
        "This is from Mumbai customs. Your parcel contains narcotics. Stay on this call, do not disconnect.",
        "Courier delivery failed. Pay Rs 49 redelivery charge at {link} to reschedule.",
        "Your consignment is seized. Clearance fee Rs {amount} required. Contact {phone}",
    ],
    "digital_arrest": [
        "I am CBI officer. Your Aadhaar is used in money laundering case. This is a digital arrest, stay on video call.",
        "Mumbai Cyber Police. FIR registered against you. Join Skype video call now, do not inform anyone.",
        "ED department. Your account is linked to terror funding. Transfer Rs {amount} to verification account for clearance.",
        "You are under digital arrest. Do not disconnect the video call or warrant will be issued.",
    ],
    "electricity_bill": [
        "Dear customer your electricity connection will be disconnected tonight because bill is not updated. Call officer {phone}",
        "EB notice: immediate disconnection at 9 pm. Update payment at {link}",
    ],
}

SCAM_TEMPLATES_TA: dict[str, list[str]] = {
    "otp": [
        "உங்கள் {bank} கணக்கு சரிபார்க்க வேண்டும். இப்போது வந்த OTP {otp} ஐ அனுப்பவும்.",
        "வங்கியிலிருந்து பேசுகிறோம். கார்டு புதுப்பிக்க OTP எண்ணை உடனே சொல்லுங்கள்.",
        "உங்கள் கணக்கு முடக்கப்படும். OTP {otp} ஐ பகிரவும், இல்லையெனில் சேவை நிறுத்தப்படும்.",
        "{wallet} கணக்கு நிறுத்தப்பட்டுள்ளது. சரிபார்ப்பு குறியீட்டை உடனே தெரிவிக்கவும்.",
    ],
    "kyc": [
        "உங்கள் {bank} KYC காலாவதியாகிவிட்டது. 24 மணி நேரத்தில் கணக்கு முடக்கப்படும். {link} ஐ அழுத்தவும்.",
        "KYC புதுப்பிக்கவில்லை. இன்றே {link} சென்று விவரங்களை பதிவு செய்யவும்.",
        "ஆதார் இணைக்கப்படவில்லை. உடனே {link} மூலம் சரிபார்க்கவும், இல்லையெனில் கணக்கு நிறுத்தப்படும்.",
    ],
    "job": [
        "வீட்டிலிருந்து வேலை. தினமும் ரூ {amount} சம்பாதிக்கலாம். பதிவு கட்டணம் ரூ 499 செலுத்தவும். தொடர்பு {phone}",
        "பகுதி நேர வேலை உள்ளது. வீடியோ லைக் செய்து தினமும் ரூ 500 பெறலாம். ஜாயின் {phone}",
        "உங்கள் விண்ணப்பம் தேர்வாகியுள்ளது. நேர்காணல் கட்டணம் ரூ 999 செலுத்தி உறுதி செய்யவும்.",
    ],
    "investment": [
        "மாதம் 30% உறுதியான லாபம். ரூ {amount} முதலீடு செய்து 15 நாளில் இரட்டிப்பு பெறுங்கள். {link}",
        "பங்குச்சந்தை குறிப்புகள் குழு. நிச்சயமான லாபம். இடம் குறைவு. தொடர்பு {phone}",
        "கிரிப்டோ திட்டத்தில் முதலீடு செய்யுங்கள். ரிஸ்க் இல்லாத வருமானம் உறுதி.",
    ],
    "banking": [
        "உங்கள் {bank} கணக்கு இன்று முடக்கப்படும். {link} சென்று PAN புதுப்பிக்கவும்.",
        "ரூ {amount} பற்று வைக்கப்பட்டது. நீங்கள் செய்யவில்லை என்றால் {phone} ஐ உடனே அழைக்கவும்.",
        "பணம் திரும்ப பெற இந்த QR ஐ ஸ்கேன் செய்து உங்கள் UPI PIN ஐ உள்ளிடவும்.",
        "AnyDesk செயலியை நிறுவி திரையை பகிரவும், எங்கள் அதிகாரி கணக்கை சரி செய்வார்.",
    ],
    "loan": [
        "முன்கூட்டியே அனுமதிக்கப்பட்ட ரூ {amount} கடன். ஆவணம் தேவையில்லை. செயலாக்க கட்டணம் ரூ 999. {phone}",
        "CIBIL சரிபார்ப்பு இல்லாமல் உடனடி கடன். 10 நிமிடத்தில் பணம். {link}",
    ],
    "impersonation": [
        "உங்கள் மின் இணைப்பு இன்றிரவு துண்டிக்கப்படும். முந்தைய மாத கட்டணம் புதுப்பிக்கப்படவில்லை. அலுவலர் {phone}",
        "அம்மா என் ஃபோன் உடைந்துவிட்டது, இது என் புதிய எண். ரூ {amount} உடனே அனுப்புங்கள்.",
        "நான் ராணுவ அதிகாரி. இடமாற்றம் ஆகிவிட்டது. முன்பணம் ரூ {amount} அனுப்புங்கள்.",
        "TRAI இலிருந்து அழைக்கிறோம். ஆதார் பொருந்தவில்லை, உங்கள் சிம் 2 மணி நேரத்தில் முடக்கப்படும்.",
    ],
    "social_media": [
        "உங்கள் Facebook பக்கம் விதிமுறை மீறல். 24 மணி நேரத்தில் {link} சரிபார்க்கவும், இல்லையெனில் நீக்கப்படும்.",
        "உங்கள் தனிப்பட்ட வீடியோ என்னிடம் உள்ளது. ரூ {amount} தரவில்லை என்றால் அனைவருக்கும் அனுப்புவேன்.",
    ],
    "lottery": [
        "வாழ்த்துக்கள்! KBC லக்கி டிராவில் ரூ {big} பரிசு வென்றுள்ளீர்கள். {phone} ஐ அழைக்கவும்.",
        "உங்கள் எண் தேர்வாகியுள்ளது. பரிசு ரூ {big}. வங்கி விவரங்களை அனுப்பவும்.",
    ],
    "courier_parcel": [
        "உங்கள் பார்சல் சுங்கத்தில் தடுத்து வைக்கப்பட்டுள்ளது. சட்டவிரோத பொருட்கள் உள்ளன. உடனே {phone} அழைக்கவும்.",
        "உங்கள் பார்சலில் போதைப்பொருள் உள்ளது. அழைப்பை துண்டிக்காதீர்கள்.",
    ],
    "digital_arrest": [
        "நான் CBI அதிகாரி. உங்கள் ஆதார் பணமோசடி வழக்கில் உள்ளது. இது டிஜிட்டல் கைது, வீடியோ அழைப்பில் இருங்கள்.",
        "சைபர் காவல்துறை. உங்கள் மீது வழக்கு பதிவு. வீடியோ அழைப்பில் இணையுங்கள், யாரிடமும் சொல்லாதீர்கள்.",
    ],
    "electricity_bill": [
        "உங்கள் மின்சாரம் இன்றிரவு துண்டிக்கப்படும். கட்டணம் புதுப்பிக்கப்படவில்லை. அலுவலர் {phone} ஐ தொடர்பு கொள்ளவும்.",
    ],
}

# ---------------------------------------------------------------------- LEGITIMATE TEMPLATES
LEGIT_EN = [
    "Rs.{amount} debited from A/c XX4412 on 12-05-26. Avl Bal Rs.8,330. Not you? Call 18001234. Do not share OTP with anyone.",
    "{otp} is your OTP for {bank} login. Valid for 10 minutes. Do not share this OTP with anyone, including bank staff.",
    "Your order has been shipped and will be delivered by tomorrow 7 PM. Track in the app.",
    "Dear customer, your electricity bill of Rs.{amount} for May is due on 20-05-2026. Pay through the official app or nearest office.",
    "Your appointment at the government hospital is confirmed for 15-05-2026 at 10:30 AM. Please bring your ID card.",
    "Thank you for your payment of Rs.{amount}. Receipt number 88213. This is a system generated message.",
    "Your monthly statement for A/c XX4412 is ready. View it by logging into the official {bank} net banking portal.",
    "Reminder: your LPG cylinder booking is confirmed. Delivery within 2 working days. Pay only to the delivery person.",
    "Your exam results are published. Visit the official university website and log in with your register number.",
    "{bank}: Rs.{amount} credited to your account on 03-06-26 by NEFT. Avl bal Rs.12,400.",
    "Dear parent, the school will remain closed tomorrow due to heavy rain. Classes resume on Monday.",
    "Your train PNR 4451223 is confirmed, coach S4 berth 32. Happy journey.",
    "Your insurance premium of Rs.{amount} is due on 28-05-2026. Pay via the official portal or your agent.",
    "Beneficiary added successfully to your account. If this was not done by you, contact your branch immediately.",
    "Your PF passbook has been updated. Login to the official EPFO member portal to view the balance.",
    "Sir, this is Kumar from the water board. We will do the meter reading tomorrow between 10 AM and 12 PM.",
    "Your parcel has been delivered and received by the security guard at your address.",
    "Your request for a new chequebook has been registered. It will reach you in 7 working days.",
    "Congratulations on completing the cyber safety workshop. Your certificate is ready for collection.",
    "Your mobile recharge of Rs.{amount} is successful. Validity 28 days. Thank you.",
    "Dear customer, the branch will be closed on 26-01-2026 for the public holiday. Normal banking resumes the next working day.",
    "Your cheque number 445122 for Rs.{amount} has been cleared on 14-05-2026.",
    "Your ration card e-KYC has been completed successfully at the fair price shop. No further action needed.",
    "Your gas cylinder has been booked. Booking ID 7781234. Delivery in 2 working days.",
    "Your Aadhaar update request 8812 has been accepted at the enrolment centre. Check status on the official portal after 7 days.",
    "Your scholarship application has been received by the college office. Results will be displayed on the notice board.",
    "Your bus pass renewal is complete. Collect it from the depot counter with your old pass.",
    "Your electricity meter reading was taken today. The bill will be delivered within 3 days.",
    "Your library book is due on 22-05-2026. Please return it at the counter to avoid a late fee.",
    "Your blood donation camp registration is confirmed for Sunday 9 AM at the community hall.",
]

LEGIT_TA = [
    "ரூ.{amount} உங்கள் கணக்கிலிருந்து பற்று வைக்கப்பட்டது. இருப்பு ரூ.8,330. OTP ஐ யாரிடமும் பகிர வேண்டாம்.",
    "{otp} உங்கள் உள்நுழைவு OTP. 10 நிமிடம் செல்லுபடியாகும். இதை யாரிடமும் சொல்ல வேண்டாம்.",
    "உங்கள் ஆர்டர் அனுப்பப்பட்டது. நாளை மாலைக்குள் வந்துவிடும். செயலியில் பார்க்கவும்.",
    "உங்கள் மின் கட்டணம் ரூ.{amount} மே மாதத்திற்கு 20-05-2026 அன்று செலுத்த வேண்டும். அதிகாரப்பூர்வ செயலியில் செலுத்துங்கள்.",
    "அரசு மருத்துவமனையில் உங்கள் சந்திப்பு 15-05-2026 காலை 10:30 மணிக்கு உறுதி செய்யப்பட்டது.",
    "உங்கள் பணம் ரூ.{amount} பெறப்பட்டது. ரசீது எண் 88213. இது தானியங்கி செய்தி.",
    "நாளை கனமழை காரணமாக பள்ளிக்கு விடுமுறை. திங்கள் அன்று வகுப்புகள் தொடங்கும்.",
    "உங்கள் ரயில் PNR 4451223 உறுதி செய்யப்பட்டது. பெட்டி S4, இருக்கை 32. பயணம் இனிதாகட்டும்.",
    "உங்கள் சிலிண்டர் பதிவு உறுதியானது. 2 வேலை நாட்களில் வழங்கப்படும். டெலிவரி நபரிடம் மட்டும் பணம் தரவும்.",
    "உங்கள் தேர்வு முடிவுகள் வெளியாகியுள்ளன. பல்கலைக்கழக அதிகாரப்பூர்வ தளத்தில் பார்க்கவும்.",
    "சைபர் பாதுகாப்பு பயிற்சியை முடித்ததற்கு வாழ்த்துக்கள். உங்கள் சான்றிதழ் தயாராக உள்ளது.",
    "உங்கள் ரீசார்ஜ் ரூ.{amount} வெற்றிகரமாக முடிந்தது. 28 நாட்கள் செல்லுபடியாகும்.",
    "உங்கள் காசோலை எண் 445122, ரூ.{amount} 14-05-2026 அன்று செலுத்தப்பட்டது.",
    "உங்கள் ரேஷன் அட்டை e-KYC நியாய விலைக் கடையில் முடிக்கப்பட்டது. வேறு நடவடிக்கை தேவையில்லை.",
    "உங்கள் சிலிண்டர் பதிவு எண் 7781234. இரண்டு வேலை நாட்களில் வழங்கப்படும்.",
    "உங்கள் உதவித்தொகை விண்ணப்பம் கல்லூரி அலுவலகத்தில் பெறப்பட்டது. முடிவுகள் அறிவிப்பு பலகையில் இடம்பெறும்.",
    "வங்கி 26-01-2026 அன்று விடுமுறை காரணமாக மூடப்படும். அடுத்த வேலை நாளில் இயல்பு சேவை.",
    "உங்கள் மின் மீட்டர் அளவீடு இன்று எடுக்கப்பட்டது. மூன்று நாட்களில் பில் வழங்கப்படும்.",
    "உங்கள் பேருந்து பாஸ் புதுப்பிக்கப்பட்டது. பழைய பாஸுடன் டிப்போவில் பெற்றுக் கொள்ளவும்.",
]

TANGLISH_SCAM = [
    "Anna urgent ah OTP {otp} share pannunga illana account block aagidum",
    "Sir job confirm aagiduchu, registration fee Rs 499 pay pannunga, {phone} ku call pannunga",
    "Neenga lucky winner! Rs {big} prize jeichuruken. Claim panna {link} click pannunga",
    "Bank la irundhu pesuren, card block aagiduchu, CVV number sollunga update panren",
    "Loan approve aagiduchu Rs {amount}, processing fee mattum pay pannunga, documents thevai illa",
    "Ungaluku refund varum, QR scan panni UPI PIN enter pannunga",
    "Investment panna 30% guaranteed return, double money 15 days la, join {link}",
    "Parcel customs la hold aagiduchu, illegal item irukku, udane {phone} ku call pannunga",
    "Mummy phone udanju pochu, ithu en new number, Rs {amount} urgent ah anuppunga",
    "Electricity tonight cut aagum, bill update aagala, officer {phone} ku call pannunga",
    "Anydesk app install pannunga, screen share panna naanga account correct panrom",
    "Digital arrest la irukeenga, video call cut pannadheenga, CBI officer pesuren",
]

TANGLISH_LEGIT = [
    "Ungaloda order ship aagiduchu, naalaiku delivery aagum, app la track pannunga",
    "Rs.{amount} debit aagiduchu account XX4412 la, balance Rs.8,330, OTP yaarukum share pannadheenga",
    "Naalaiku school leave, heavy rain, Monday class start aagum",
    "Ungaloda exam result vandhuduchu, official website la login panni paarunga",
    "Cylinder booking confirm aagiduchu, 2 days la delivery, delivery person kitta mattum pay pannunga",
]


def _fill(template: str) -> str:
    return (
        template.replace("{bank}", _pick(BANKS))
        .replace("{wallet}", _pick(WALLETS))
        .replace("{amount}", _pick(AMOUNTS))
        .replace("{big}", _pick(BIG_AMOUNTS))
        .replace("{link}", _pick(FAKE_LINKS))
        .replace("{phone}", _pick(PHONES))
        .replace("{otp}", _pick(OTPS))
    )


def _vary(text: str) -> str:
    """Light surface variation so the model cannot memorise exact template strings."""
    r = random.random()
    if r < 0.12:
        text = text.upper()
    elif r < 0.22:
        text = text + " " + _pick(["Thank you.", "Regards.", "Team", "Act fast!", ""])
    elif r < 0.30:
        text = _pick(["", "Dear customer, ", "Attention! ", "Important: "]) + text
    if random.random() < 0.10:
        text = text.replace(".", "..")
    return text.strip()


def build_messages() -> list[dict]:
    rows: list[dict] = []

    # English scams
    for category, templates in SCAM_TEMPLATES.items():
        for _ in range(max(6, 28 // max(1, len(templates)) * len(templates) // 4)):
            for tpl in templates:
                rows.append(
                    {"text": _vary(_fill(tpl)), "language": "en", "label": "scam",
                     "category": category, "source": "synthetic_template"}
                )

    # Tamil scams
    for category, templates in SCAM_TEMPLATES_TA.items():
        for _ in range(3):
            for tpl in templates:
                rows.append(
                    {"text": _vary(_fill(tpl)), "language": "ta", "label": "scam",
                     "category": category, "source": "synthetic_template"}
                )

    # Tanglish scams
    for _ in range(6):
        for tpl in TANGLISH_SCAM:
            rows.append(
                {"text": _vary(_fill(tpl)), "language": "ta", "label": "scam",
                 "category": "impersonation", "source": "synthetic_tanglish"}
            )

    # Legitimate. Higher repeat counts than the scam side because the de-duplication step
    # culls far more of these: many legitimate templates carry no {placeholder} to vary.
    for _ in range(30):
        for tpl in LEGIT_EN:
            rows.append(
                {"text": _vary(_fill(tpl)), "language": "en", "label": "legitimate",
                 "category": "legitimate", "source": "synthetic_template"}
            )
    for _ in range(28):
        for tpl in LEGIT_TA:
            rows.append(
                {"text": _vary(_fill(tpl)), "language": "ta", "label": "legitimate",
                 "category": "legitimate", "source": "synthetic_template"}
            )
    for _ in range(26):
        for tpl in TANGLISH_LEGIT:
            rows.append(
                {"text": _vary(_fill(tpl)), "language": "ta", "label": "legitimate",
                 "category": "legitimate", "source": "synthetic_tanglish"}
            )

    # De-duplicate exact repeats produced by the variation step
    seen: set[str] = set()
    unique = []
    for r in rows:
        key = r["text"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    random.shuffle(unique)
    return unique


# --------------------------------------------------------------------------- URL DATASET
SAFE_DOMAINS = [
    "google.com", "wikipedia.org", "gov.in", "cybercrime.gov.in", "rbi.org.in", "npci.org.in",
    "onlinesbi.sbi", "hdfcbank.com", "icicibank.com", "axisbank.com", "paytm.com",
    "phonepe.com", "amazon.in", "flipkart.com", "irctc.co.in", "epfindia.gov.in",
    "uidai.gov.in", "incometax.gov.in", "nic.in", "tn.gov.in", "python.org", "github.com",
    "moodle.org", "swayam.gov.in", "nptel.ac.in", "annauniv.edu", "digilocker.gov.in",
    "indiapost.gov.in", "passportindia.gov.in", "sancharsaathi.gov.in", "cert-in.org.in",
]
SAFE_PATHS = ["", "/", "/about", "/login", "/help/contact", "/services", "/faq",
              "/account/summary", "/search?q=cyber+safety", "/en/home", "/docs/guide"]

PHISH_HOST_PATTERNS = [
    "{brand}-kyc-update.{tld}", "{brand}-secure-login.{tld}", "verify-{brand}.{tld}",
    "{brand}.account-verify.{tld}", "{brand}-netbanking.{tld}", "www-{brand}.{tld}",
    "{brand}-refund-claim.{tld}", "secure.{brand}-online.{tld}", "{brand}support.{tld}",
    "update-{brand}-kyc.{tld}", "{brand}-rewards.{tld}", "login-{brand}-in.{tld}",
]
PHISH_BRANDS = ["sbi", "hdfc", "icici", "axis", "paytm", "phonepe", "amazon", "flipkart",
                "irctc", "epfo", "uidai", "netflix", "jio", "airtel", "gpay", "bhim"]
TYPOSQUATS = ["arnazon.com", "amazn.in", "flipkartt.com", "paytnm.com", "phonepey.com",
              "icicibnk.com", "hdfcbnk.net", "sbionline.top", "irctcc.co", "netflx.cc"]
BAD_TLDS = ["xyz", "top", "click", "buzz", "icu", "cyou", "tk", "ml", "ga", "cf", "work",
            "loan", "win", "rest", "sbs", "fit"]
PHISH_PATHS = ["/login.php", "/verify?id=8823&token=a91k2", "/kyc/update", "/secure/account",
               "/claim-reward", "/signin?next=%2Faccount", "/update-card-details",
               "/otp-verify", "/netbanking/login.jsp", "/wallet/refund?amt=4999"]
SHORTENER_HOSTS = ["bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "is.gd", "t.ly", "surl.li"]


def build_urls() -> list[dict]:
    rows: list[dict] = []

    # Safe
    for domain in SAFE_DOMAINS:
        for path in SAFE_PATHS:
            scheme = "https" if random.random() < 0.85 else "http"
            sub = _pick(["", "www.", "www.", ""])
            rows.append({"url": f"{scheme}://{sub}{domain}{path}", "label": "safe",
                         "source": "synthetic_known_good"})

    # Brand-impersonating phishing hosts.
    # Deliberately HTTPS-heavy: free certificates mean the padlock no longer signals safety,
    # and an http/https split by class would let the model "cheat" on that one feature
    # instead of learning the host patterns that actually matter.
    for brand in PHISH_BRANDS:
        for pattern in PHISH_HOST_PATTERNS:
            host = pattern.format(brand=brand, tld=_pick(BAD_TLDS))
            scheme = "https" if random.random() < 0.8 else "http"
            rows.append({"url": f"{scheme}://{host}{_pick(PHISH_PATHS)}", "label": "phishing",
                         "source": "synthetic_pattern"})

    # Typosquats
    for host in TYPOSQUATS:
        for _ in range(4):
            scheme = "https" if random.random() < 0.8 else "http"
            rows.append({"url": f"{scheme}://{host}{_pick(PHISH_PATHS)}", "label": "phishing",
                         "source": "synthetic_typosquat"})

    # IP-host URLs
    for _ in range(45):
        ip = f"{random.randint(11,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        port = _pick(["", "", ":8080", ":8000", ":4433"])
        rows.append({"url": f"http://{ip}{port}{_pick(PHISH_PATHS)}", "label": "phishing",
                     "source": "synthetic_ip_host"})

    # Shorteners (mostly used to hide phishing in this dataset)
    for host in SHORTENER_HOSTS:
        for _ in range(7):
            code = "".join(random.choices("abcdefghijkmnopqrstuvwxyz0123456789", k=random.randint(5, 8)))
            scheme = "https" if random.random() < 0.7 else "http"
            rows.append({"url": f"{scheme}://{host}/{code}", "label": "phishing",
                         "source": "synthetic_shortener"})

    # "@" trick and punycode
    for brand in PHISH_BRANDS[:10]:
        rows.append({"url": f"https://{brand}.com@{_pick(BAD_TLDS)}-login.{_pick(BAD_TLDS)}/verify",
                     "label": "phishing", "source": "synthetic_at_trick"})
        rows.append({"url": f"https://xn--{brand}-9ua.{_pick(BAD_TLDS)}/login",
                     "label": "phishing", "source": "synthetic_punycode"})

    # Long deep-subdomain phishing
    for _ in range(40):
        brand = _pick(PHISH_BRANDS)
        host = f"{brand}.{_pick(['secure','login','verify','account'])}.{_pick(['in','co','com'])}.{_pick(BAD_TLDS)}-serv.{_pick(BAD_TLDS)}"
        scheme = "https" if random.random() < 0.8 else "http"
        rows.append({"url": f"{scheme}://{host}{_pick(PHISH_PATHS)}", "label": "phishing",
                     "source": "synthetic_deep_subdomain"})

    # Extra safe: deep but legitimate paths, so depth alone is not a giveaway
    for domain in SAFE_DOMAINS:
        for _ in range(3):
            deep = "/".join(random.choices(
                ["services", "citizen", "portal", "public", "info", "en", "forms", "downloads"],
                k=random.randint(2, 4)))
            rows.append({"url": f"https://www.{domain}/{deep}", "label": "safe",
                         "source": "synthetic_known_good"})

    seen: set[str] = set()
    unique = []
    for r in rows:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    random.shuffle(unique)
    return unique


def main() -> int:
    messages = build_messages()
    urls = build_urls()

    msg_path = DATA / "scam_messages.csv"
    with msg_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["text", "language", "label", "category", "source"])
        w.writeheader()
        w.writerows(messages)

    url_path = DATA / "urls.csv"
    with url_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["url", "label", "source"])
        w.writeheader()
        w.writerows(urls)

    scam_n = sum(1 for m in messages if m["label"] == "scam")
    ta_n = sum(1 for m in messages if m["language"] == "ta")
    phish_n = sum(1 for u in urls if u["label"] == "phishing")

    print(f"messages : {len(messages):4d}  (scam {scam_n}, legitimate {len(messages)-scam_n}, tamil/tanglish {ta_n})")
    print(f"urls     : {len(urls):4d}  (phishing {phish_n}, safe {len(urls)-phish_n})")
    print(f"written  : {msg_path.name}, {url_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
