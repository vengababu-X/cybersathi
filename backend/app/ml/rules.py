"""Bilingual (English + Tamil) scam-pattern rule engine.

Why rules *and* ML: the ML model generalises, but it cannot tell a 70-year-old *why* a message
is dangerous. Each rule carries its own plain-language explanation in both languages, so every
verdict can be justified in a sentence the user actually understands. Rules also give the system
a sane floor when a brand-new scam script appears that the training data has never seen.

weight: 0.0-1.0 contribution toward the rule score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    weight: float
    explanation_en: str
    explanation_ta: str
    patterns_en: list[str] = field(default_factory=list)
    patterns_ta: list[str] = field(default_factory=list)
    # Almost every rule wants case-insensitive matching. The exception is the SHOUTING rule,
    # where `[A-Z]{8,}` under IGNORECASE silently matches any 8-letter lowercase word
    # (it fired on "customer"), adding noise to every single message.
    case_sensitive: bool = False


RULES: list[Rule] = [
    Rule(
        id="otp_share_request",
        category="otp",
        weight=0.95,
        explanation_en="The message asks you to share an OTP. No bank, company or government office will ever ask for your OTP.",
        explanation_ta="இந்த செய்தி OTP-ஐ பகிரச் சொல்கிறது. எந்த வங்கியும் அரசு அலுவலகமும் உங்கள் OTP-ஐ கேட்காது.",
        patterns_en=[r"\b(share|send|tell|provide|forward|give)\b.{0,25}\b(otp|o\.t\.p|one[\s-]?time[\s-]?password|verification code|pin)\b",
                     r"\botp\b.{0,20}\b(share|send|tell|sms|whatsapp|number)\b"],
        patterns_ta=[r"(otp|ஓடிபி|கடவுச்சொல்).{0,25}(அனுப்ப|பகிர|சொல்ல|தெரிவி)",
                     r"(அனுப்பவும்|பகிரவும்|சொல்லவும்).{0,25}(otp|ஓடிபி)"],
    ),
    Rule(
        id="kyc_expiry_threat",
        category="kyc",
        weight=0.85,
        explanation_en="A fake 'KYC expired' warning is used to panic you into clicking a link. Banks update KYC in the branch or in their own app, never through an SMS link.",
        explanation_ta="'KYC காலாவதி' என்ற போலி எச்சரிக்கை உங்களை பயமுறுத்தி இணைப்பை அழுத்த வைக்கிறது. வங்கிகள் KYC-ஐ கிளையிலோ அவர்களின் செயலியிலோ மட்டுமே புதுப்பிக்கும்.",
        patterns_en=[r"\bkyc\b.{0,40}\b(expire|expired|expiry|update|pending|suspend|incomplete)\b",
                     r"\b(update|complete|verify)\b.{0,20}\bkyc\b"],
        patterns_ta=[r"(kyc|கேஒய்சி).{0,40}(காலாவதி|புதுப்பி|நிலுவை|முடக்க)"],
    ),
    Rule(
        id="account_block_threat",
        category="banking",
        weight=0.8,
        explanation_en="Threatening that your account will be blocked within hours is a pressure tactic. Real banks give written notice and never a 24-hour ultimatum by SMS.",
        explanation_ta="உங்கள் கணக்கு சில மணி நேரத்தில் முடக்கப்படும் என்று பயமுறுத்துவது ஒரு தந்திரம். உண்மையான வங்கிகள் எழுத்துப்பூர்வ அறிவிப்பு தரும்.",
        patterns_en=[r"\b(account|a/c|card)\b.{0,40}\b(block|blocked|suspend|suspended|freeze|frozen|deactivat|clos)\w*",
                     r"\bwithin\b.{0,15}\b(24|48|2|3)\s*(hour|hrs|hours)\b"],
        patterns_ta=[r"(கணக்கு|அக்கவுண்ட்).{0,40}(முடக்க|நிறுத்த|ரத்து|செயலிழ)",
                     r"(24|48)\s*(மணி|மணிநேர)"],
    ),
    Rule(
        id="urgency_pressure",
        category="impersonation",
        weight=0.45,
        explanation_en="Extreme urgency is the most common scam ingredient. It exists to stop you from checking with family or your bank.",
        explanation_ta="அவசரம் காட்டுவது மோசடியின் முக்கிய அடையாளம். நீங்கள் குடும்பத்திடமோ வங்கியிடமோ கேட்காமல் இருக்கவே அப்படிச் செய்கிறார்கள்.",
        patterns_en=[r"\b(immediately|urgent|urgently|right now|within \d+ (min|hour)|last warning|final notice|act now|hurry|expires today)\b"],
        patterns_ta=[r"(உடனே|அவசரம்|உடனடியாக|இன்றே|கடைசி வாய்ப்பு|விரைவில்)"],
    ),
    Rule(
        id="job_advance_fee",
        category="job",
        weight=0.9,
        explanation_en="You are asked to pay a registration or security fee for a job. A genuine employer never asks a candidate for money.",
        explanation_ta="வேலைக்காக பதிவு கட்டணம் கேட்கிறார்கள். உண்மையான நிறுவனம் விண்ணப்பதாரரிடம் பணம் கேட்காது.",
        # "processing fee" alone is deliberately NOT here: lottery and loan scams use the same
        # phrase, and a bare match was stealing the category from them.
        patterns_en=[r"\b(registration|security|training|interview|placement)\s*(fee|charge|amount|deposit)\b",
                     r"\b(pay|send|deposit|transfer)\b.{0,30}\b(fee|charges?|rs\.?\s*\d+|₹\s*\d+)\b.{0,30}\b(job|work|offer|position|interview)\b",
                     r"\bjob\b.{0,40}\b(pay|fee|deposit|charge)\b"],
        patterns_ta=[r"(வேலை|ஜாப்).{0,40}(கட்டணம்|பணம்|ஃபீஸ்|டெபாசிட்)",
                     r"(பதிவு|ரெஜிஸ்ட்ரேஷன்)\s*(கட்டணம்|ஃபீஸ்)"],
    ),
    Rule(
        id="work_from_home_task",
        category="job",
        weight=0.7,
        explanation_en="'Earn daily by liking videos or rating hotels' is the standard task-fraud script. Small payouts build trust, then a large 'investment' disappears.",
        explanation_ta="'வீடியோ லைக் செய்து தினமும் சம்பாதிக்கலாம்' என்பது டாஸ்க் மோசடி. முதலில் சிறிய பணம் தந்து நம்பிக்கை உருவாக்கி, பின் பெரிய தொகையை ஏமாற்றுவார்கள்.",
        patterns_en=[r"\b(work from home|part[\s-]?time job|daily (income|earning|payout)|earn (up to )?(rs\.?|₹)\s*\d+\s*(daily|per day|\/day))\b",
                     r"\b(like|rate|review|subscribe)\b.{0,25}\b(video|hotel|product|youtube)\b.{0,25}\b(earn|paid|money|income)\b"],
        patterns_ta=[r"(வீட்டிலிருந்து வேலை|பகுதி நேர வேலை|தினமும்.{0,15}சம்பாதி)"],
    ),
    Rule(
        id="investment_guaranteed_return",
        category="investment",
        weight=0.9,
        explanation_en="Guaranteed or doubled returns do not exist. SEBI-registered advisers are legally barred from promising any fixed profit.",
        explanation_ta="உறுதியான லாபம் அல்லது இரட்டிப்பு என்பது இல்லவே இல்லை. பதிவுசெய்யப்பட்ட ஆலோசகர்கள் நிச்சயமான லாபம் தருவதாக வாக்குறுதி தர சட்டப்படி அனுமதி இல்லை.",
        patterns_en=[r"\b(guaranteed|assured|fixed|100%|risk[\s-]?free)\b.{0,20}\b(return|profit|income|daily|monthly)\b",
                     r"\b(double|triple|2x|3x|10x)\b.{0,25}\b(money|investment|amount|profit|in \d+ (day|week|month))\b",
                     r"\b(trading|crypto|forex|bitcoin|stock)\b.{0,30}\b(tips|group|signal|expert|mentor)\b"],
        patterns_ta=[r"(உறுதியான|நிச்சயமான).{0,20}(லாபம்|வருமானம்)",
                     r"(இரட்டிப்பு|டபுள்).{0,20}(பணம்|முதலீடு)"],
    ),
    Rule(
        id="lottery_prize_win",
        category="lottery",
        weight=0.9,
        explanation_en="You cannot win a lottery you never entered. The 'prize' exists only to make you pay a tax or processing fee.",
        explanation_ta="நீங்கள் பங்கேற்காத லாட்டரியில் பரிசு கிடைக்காது. 'பரிசு' என்பது வரி அல்லது கட்டணம் கட்ட வைப்பதற்கான தந்திரம்.",
        patterns_en=[r"\b(congratulations|congrats)\b.{0,50}\b(won|winner|selected|lucky)\b",
                     r"\b(lottery|lucky draw|prize|jackpot|bumper)\b.{0,40}\b(won|win|claim|crore|lakh)\b"],
        patterns_ta=[r"(வாழ்த்துக்கள்|பரிசு|லாட்டரி).{0,40}(வென்ற|வெற்றி|தேர்வு|கோடி|லட்சம்)"],
    ),
    Rule(
        id="loan_preapproved",
        category="loan",
        weight=0.75,
        explanation_en="A pre-approved instant loan with no documents is bait. The 'processing fee' is stolen and the loan never arrives.",
        explanation_ta="ஆவணம் இல்லாமல் உடனடி கடன் என்பது தூண்டில். 'செயலாக்கக் கட்டணம்' திருடப்படும், கடன் வராது.",
        patterns_en=[r"\b(pre[\s-]?approved|instant|quick)\b.{0,25}\bloan\b",
                     r"\bloan\b.{0,35}\b(no documents?|without documents?|zero paperwork|no cibil|any cibil)\b"],
        patterns_ta=[r"(உடனடி|முன்.{0,5}அனுமதி).{0,20}(கடன்|லோன்)",
                     r"(கடன்|லோன்).{0,30}(ஆவணம் இல்லாமல்|சான்றிதழ் தேவையில்லை)"],
    ),
    Rule(
        id="loan_app_harassment",
        category="loan_app_harassment",
        weight=0.8,
        explanation_en="Illegal loan apps threaten to message your contacts or morph your photos. This is extortion — report it, do not pay.",
        explanation_ta="சட்டவிரோத கடன் செயலிகள் உங்கள் தொடர்புகளுக்கு செய்தி அனுப்புவோம் என மிரட்டும். இது மிரட்டல் — பணம் தராதீர்கள், புகார் அளியுங்கள்.",
        patterns_en=[r"\b(contact list|your contacts|all your friends|morph|nude|defame)\b.{0,40}\b(inform|send|share|post|viral)\b",
                     r"\b(loan app)\b.{0,40}\b(threat|abuse|harass)\w*"],
        patterns_ta=[r"(தொடர்பு பட்டியல்|உங்கள் நண்பர்கள்).{0,40}(அனுப்ப|தெரிவிக்க|பகிர)"],
    ),
    Rule(
        id="digital_arrest",
        category="digital_arrest",
        weight=0.97,
        explanation_en="'Digital arrest' does not exist in Indian law. No police officer, CBI, ED or judge will ever question you on a video call or ask you to stay on camera.",
        explanation_ta="'டிஜிட்டல் கைது' என்பது இந்திய சட்டத்தில் கிடையாது. எந்த காவல்துறை, CBI, ED அதிகாரியும் வீடியோ அழைப்பில் விசாரணை செய்யமாட்டார்.",
        patterns_en=[r"\bdigital\s*arrest\b",
                     r"\b(cbi|ed|narcotics|ncb|customs|police|cyber cell|court)\b.{0,50}\b(arrest|warrant|case|fir|summon|investigation)\b.{0,60}\b(video call|skype|whatsapp call|stay online|do not disconnect)\b",
                     r"\b(your (aadhaar|sim|parcel|account))\b.{0,40}\b(illegal|drugs|money laundering|terror)\b"],
        patterns_ta=[r"(டிஜிட்டல் கைது|கைது வாரண்ட்).{0,50}(வீடியோ|அழைப்பு)",
                     r"(போலீஸ்|சிபிஐ).{0,40}(வழக்கு|கைது).{0,40}(வீடியோ கால்|ஆன்லைன்)"],
    ),
    Rule(
        id="courier_parcel_customs",
        category="courier_parcel",
        weight=0.85,
        explanation_en="The 'parcel with drugs held by customs' call is a scripted fraud. Customs never phones an individual to demand an immediate transfer.",
        explanation_ta="'உங்கள் பார்சலில் போதைப்பொருள்' என்ற அழைப்பு ஒரு மோசடி. சுங்கத்துறை தனிநபரை அழைத்து உடனே பணம் கேட்காது.",
        patterns_en=[r"\b(parcel|courier|package|consignment|shipment)\b.{0,50}\b(customs|seized|held|illegal|drugs|narcotic|detained)\b",
                     r"\b(fedex|dhl|blue dart|india post|dtdc)\b.{0,40}\b(seized|customs|clearance fee|held)\b"],
        patterns_ta=[r"(பார்சல்|கூரியர்).{0,50}(சுங்கம்|பறிமுதல்|தடுத்து|சட்டவிரோத)"],
    ),
    Rule(
        id="electricity_disconnection",
        category="impersonation",
        weight=0.85,
        explanation_en="The 'electricity will be cut tonight' SMS with a personal mobile number is a known fraud. TNEB/EB sends bills through official channels, not a WhatsApp number.",
        explanation_ta="'இன்றிரவு மின்சாரம் துண்டிக்கப்படும்' என்ற செய்தி ஒரு மோசடி. மின்வாரியம் அதிகாரப்பூர்வ வழியில்தான் அறிவிக்கும்.",
        patterns_en=[r"\b(electricity|power|eb|tneb|bescom)\b.{0,50}\b(disconnect|cut|discontinu|suspend)\w*",
                     r"\b(previous month|last month)\b.{0,30}\b(bill|payment)\b.{0,30}\b(not updated|pending|failed)\b"],
        patterns_ta=[r"(மின்சாரம்|மின் இணைப்பு|மின்கட்டணம்).{0,50}(துண்டிக்க|நிறுத்த|நிலுவை)"],
    ),
    Rule(
        id="sim_block_threat",
        category="impersonation",
        weight=0.8,
        explanation_en="'Your SIM/Aadhaar link will be blocked' is a fake alert. TRAI does not deactivate individual SIM cards by SMS.",
        explanation_ta="'உங்கள் சிம் முடக்கப்படும்' என்பது போலி எச்சரிக்கை. TRAI தனிநபர் சிம்மை SMS மூலம் முடக்காது.",
        patterns_en=[r"\b(sim|mobile number|connection)\b.{0,40}\b(block|deactivat|disconnect|suspend|barred)\w*",
                     r"\btrai\b.{0,50}\b(block|deactivat|verif)\w*"],
        patterns_ta=[r"(சிம்|மொபைல் எண்).{0,40}(முடக்க|நிறுத்த|ரத்து)"],
    ),
    Rule(
        id="upi_receive_money_myth",
        category="banking",
        weight=0.95,
        explanation_en="You are being asked to enter your UPI PIN or approve a request to RECEIVE money. Receiving money never needs a PIN — approving it sends money out of your account.",
        explanation_ta="பணம் பெற UPI PIN போடச் சொல்கிறார்கள். பணம் பெற PIN தேவையே இல்லை — PIN போட்டால் உங்கள் கணக்கிலிருந்து பணம் போய்விடும்.",
        patterns_en=[r"\b(enter|put|type|confirm|approve)\b.{0,25}\b(upi\s*)?pin\b.{0,40}\b(receive|refund|credit|get|cashback)\b",
                     r"\b(scan|accept|approve)\b.{0,25}\b(qr|request)\b.{0,30}\b(receive|refund|get money|credit)\b"],
        patterns_ta=[r"(பின்|pin).{0,30}(பணம் பெற|திரும்ப பெற|ரீஃபண்ட்)",
                     r"(ஸ்கேன்|க்யூஆர்).{0,30}(பணம் பெற|ரீஃபண்ட்)"],
    ),
    Rule(
        id="remote_access_app",
        category="banking",
        weight=0.93,
        explanation_en="You are asked to install a screen-sharing app such as AnyDesk, TeamViewer or QuickSupport. That hands a stranger full control of your phone and bank app.",
        explanation_ta="AnyDesk, TeamViewer போன்ற திரை பகிர்வு செயலியை நிறுவச் சொல்கிறார்கள். அது உங்கள் ஃபோனையும் வங்கி செயலியையும் அந்நியரிடம் ஒப்படைக்கும்.",
        patterns_en=[r"\b(anydesk|teamviewer|quicksupport|airdroid|screen\s*shar\w+|remote (access|desktop)|mingle ?view)\b"],
        patterns_ta=[r"(திரை பகிர்வு|ரிமோட் ஆக்சஸ்|anydesk|teamviewer)"],
    ),
    Rule(
        id="apk_download",
        category="banking",
        weight=0.92,
        explanation_en="The message pushes an .apk file or an app from outside the Play Store. Side-loaded banking apps are the main way phones get drained.",
        explanation_ta="இந்த செய்தி .apk கோப்பை நிறுவச் சொல்கிறது. Play Store-க்கு வெளியே உள்ள செயலிகள்தான் பணத்தை திருடும் முக்கிய வழி.",
        patterns_en=[r"\.apk\b", r"\b(install|download)\b.{0,30}\b(apk|from the link|attached app)\b"],
        patterns_ta=[r"(\.apk|செயலியை நிறுவ).{0,30}(இணைப்பு|லிங்க்)"],
    ),
    Rule(
        id="shortened_link",
        category="impersonation",
        weight=0.55,
        explanation_en="A shortened link hides the real website address. Legitimate banks and government offices always show their full domain.",
        explanation_ta="சுருக்கப்பட்ட இணைப்பு உண்மையான முகவரியை மறைக்கிறது. உண்மையான வங்கிகள் முழு முகவரியைக் காட்டும்.",
        patterns_en=[r"\b(bit\.ly|tinyurl|t\.co|rb\.gy|cutt\.ly|is\.gd|shorturl|rebrand\.ly|tiny\.cc|ow\.ly|surl\.li)\b"],
        patterns_ta=[r"\b(bit\.ly|tinyurl|cutt\.ly)\b"],
    ),
    Rule(
        id="suspicious_link_present",
        category="impersonation",
        weight=0.35,
        explanation_en="The message contains a link. Never open a link in an unexpected message — type the official website yourself instead.",
        explanation_ta="செய்தியில் இணைப்பு உள்ளது. எதிர்பாராத செய்தியில் உள்ள இணைப்பை திறக்காதீர்கள் — அதிகாரப்பூர்வ தளத்தை நீங்களே தட்டச்சு செய்யுங்கள்.",
        patterns_en=[r"https?://|www\.|hxxps?://|\b\w+\[\.\]\w+"],
        patterns_ta=[r"https?://|www\."],
    ),
    Rule(
        id="fake_bank_sender",
        category="banking",
        weight=0.6,
        explanation_en="The sender imitates a bank name but writes from a personal number or odd address. Check the sender, not just the logo or wording.",
        explanation_ta="அனுப்புநர் வங்கி பெயரைப் பயன்படுத்தினாலும் தனிப்பட்ட எண்ணிலிருந்து வருகிறது. லோகோவை அல்ல, அனுப்புநரை சரிபாருங்கள்.",
        patterns_en=[r"\b(sbi|hdfc|icici|axis|kotak|pnb|canara|union bank|indian bank|bob|yes bank|paytm|phonepe|google ?pay|gpay)\b.{0,60}\b(click|link|verify|update|kyc|blocked?)\b"],
        patterns_ta=[r"(வங்கி|பேங்க்).{0,50}(இணைப்பு|கிளிக்|சரிபார்|புதுப்பி)"],
    ),
    Rule(
        id="refund_bait",
        category="banking",
        weight=0.7,
        explanation_en="A surprise refund, cashback or tax return you did not apply for is bait to make you enter card or UPI details.",
        explanation_ta="நீங்கள் விண்ணப்பிக்காத ரீஃபண்ட் அல்லது கேஷ்பேக் ஒரு தூண்டில். உங்கள் கார்டு விவரங்களை பெறவே இது.",
        patterns_en=[r"\b(refund|cashback|reward|income tax return|gst refund)\b.{0,40}\b(claim|credit|process|click|link|approve)\b"],
        patterns_ta=[r"(ரீஃபண்ட்|பணம் திரும்ப|கேஷ்பேக்).{0,40}(கோர|கிளிக்|இணைப்பு)"],
    ),
    Rule(
        id="impersonate_family_emergency",
        category="impersonation",
        weight=0.85,
        explanation_en="Someone claims to be a relative in trouble and needs money now, from a new number. Always call the person back on their known number first.",
        explanation_ta="புதிய எண்ணிலிருந்து உறவினர் என்று கூறி அவசரமாக பணம் கேட்கிறார்கள். அவரின் பழைய எண்ணுக்கு நீங்களே அழைத்து உறுதி செய்யுங்கள்.",
        patterns_en=[r"\b(this is|i am)\b.{0,25}\b(your (son|daughter|brother|sister|uncle|friend)|mummy|daddy)\b.{0,50}\b(money|urgent|accident|hospital|police)\b",
                     r"\b(new number|changed my number|lost my phone)\b.{0,50}\b(send|transfer|need)\b.{0,20}\b(money|rs|₹)\b"],
        patterns_ta=[r"(புதிய எண்|நம்பர் மாறிவிட்டது).{0,50}(பணம்|அனுப்ப)",
                     r"(மகன்|மகள்|உறவினர்).{0,40}(விபத்து|மருத்துவமனை|பணம் அனுப்ப)"],
    ),
    Rule(
        id="officer_impersonation",
        category="impersonation",
        weight=0.8,
        explanation_en="Callers claiming to be army, police or government officers who insist on advance payment for a deal are a standard marketplace fraud.",
        explanation_ta="ராணுவம், காவல்துறை அதிகாரி என்று கூறி முன்பணம் கேட்பது ஒரு பொதுவான மோசடி.",
        patterns_en=[r"\b(army|military|defence|jawan|police|cbi|officer|government officer|ias|ips)\b.{0,60}\b(advance|token|transfer|gpay|phonepe|paytm|upi|urgent)\b"],
        patterns_ta=[r"(ராணுவம்|ராணுவ அதிகாரி|காவல்துறை).{0,60}(முன்பணம்|அனுப்ப|ஜிபே)"],
    ),
    Rule(
        id="romance_matrimony",
        category="social_media",
        weight=0.75,
        explanation_en="An online friend or match you have never met starts asking for money, gift customs duty or investment help. This is romance fraud.",
        explanation_ta="நேரில் சந்திக்காத ஆன்லைன் நண்பர் பணம் அல்லது பரிசு சுங்க வரி கேட்கிறார். இது காதல் மோசடி.",
        patterns_en=[r"\b(gift|parcel|customs duty|clearance)\b.{0,50}\b(send|pay|release|stuck|airport)\b",
                     r"\b(love you|marry|relationship)\b.{0,60}\b(money|transfer|loan|emergency)\b"],
        patterns_ta=[r"(பரிசு|கிஃப்ட்).{0,50}(சுங்க வரி|விமான நிலையம்|பணம்)"],
    ),
    Rule(
        id="sextortion_threat",
        category="social_media",
        weight=0.9,
        explanation_en="A threat to leak a video unless you pay. Do not pay and do not delete evidence — report it on 1930 or cybercrime.gov.in immediately.",
        explanation_ta="வீடியோவை வெளியிடுவோம் என்று மிரட்டி பணம் கேட்கிறார்கள். பணம் தராதீர்கள், ஆதாரத்தை அழிக்காதீர்கள் — 1930-ல் உடனே புகார் அளியுங்கள்.",
        patterns_en=[r"\b(video|screenshot|recording|photo)\b.{0,50}\b(viral|leak|send to your|upload|youtube|facebook)\b.{0,40}\b(pay|money|transfer)\b",
                     r"\b(nude|obscene|intimate)\b.{0,40}\b(video|call|photo)\b"],
        patterns_ta=[r"(வீடியோ|புகைப்படம்).{0,50}(வெளியிட|பரப்ப|அனுப்ப).{0,40}(பணம்)"],
    ),
    Rule(
        id="fake_customer_care",
        category="impersonation",
        weight=0.8,
        explanation_en="A 'customer care number' found through a web search or social media post is often planted by fraudsters. Use only the number printed on your card or in the official app.",
        explanation_ta="இணையத்தில் தேடி கிடைக்கும் 'கஸ்டமர் கேர்' எண் பெரும்பாலும் மோசடியாளர்கள் வைத்தது. உங்கள் கார்டில் உள்ள எண்ணை மட்டும் பயன்படுத்துங்கள்.",
        patterns_en=[r"\b(customer care|helpline|toll free|support)\b.{0,30}\b(number|no\.?)\b.{0,30}\b(call|whatsapp|contact)\b",
                     r"\bcall\b.{0,20}\b(immediately|now)\b.{0,25}\b\d{10}\b"],
        patterns_ta=[r"(கஸ்டமர் கேர்|உதவி எண்).{0,30}(அழைக்க|தொடர்பு)"],
    ),
    Rule(
        id="social_account_verification",
        category="social_media",
        weight=0.7,
        explanation_en="A fake 'verify your account or it will be deleted' notice steals your social media password. Check notifications inside the app, never through a link.",
        explanation_ta="'கணக்கை சரிபார்க்கவில்லை என்றால் நீக்கப்படும்' என்பது கடவுச்சொல்லை திருட. செயலிக்குள் சென்று சரிபாருங்கள்.",
        patterns_en=[r"\b(facebook|instagram|whatsapp|youtube|twitter|x)\b.{0,50}\b(verify|confirm|copyright|violat|delete|suspend|disable)\w*",
                     r"\b(page|account)\b.{0,30}\b(will be (deleted|disabled|suspended))\b"],
        patterns_ta=[r"(கணக்கு|பக்கம்).{0,40}(நீக்கப்படும்|முடக்கப்படும்|சரிபார்)"],
    ),
    Rule(
        id="otp_do_not_share_legit",
        category="legitimate",
        weight=-0.6,
        explanation_en="The message itself warns you not to share the OTP. Genuine bank alerts include this warning and never ask for a reply.",
        explanation_ta="இந்த செய்தியே OTP-ஐ பகிர வேண்டாம் என்று எச்சரிக்கிறது. உண்மையான வங்கி செய்திகளில் இந்த எச்சரிக்கை இருக்கும்.",
        patterns_en=[r"\b(do not|don't|never)\s*(share|disclose|reveal)\b.{0,30}\b(otp|pin|password|code)\b",
                     r"\bno one from\b.{0,30}\b(bank|will ask)\b"],
        patterns_ta=[r"(யாரிடமும்|எவரிடமும்).{0,25}(பகிர|சொல்ல).{0,15}(வேண்டாம்|கூடாது)"],
    ),
    Rule(
        id="legit_transaction_alert",
        category="legitimate",
        weight=-0.45,
        explanation_en="This reads like a routine transaction or delivery notification with no link and no request for action.",
        explanation_ta="இது ஒரு சாதாரண பரிவர்த்தனை அல்லது டெலிவரி அறிவிப்பு. இணைப்போ செயலோ கேட்கவில்லை.",
        patterns_en=[r"\b(debited|credited|balance|avl bal|txn|transaction)\b.{0,40}\b(a/c|account|card)\b.{0,40}\b(xx|\*{2,}|\[redacted)",
                     r"\b(delivered|out for delivery|shipped|dispatched)\b"],
        patterns_ta=[r"(பற்று|வரவு|இருப்பு).{0,40}(கணக்கு)"],
    ),
    Rule(
        id="all_caps_shouting",
        category="impersonation",
        weight=0.25,
        explanation_en="Heavy capitals and multiple exclamation marks are used to create alarm. Official messages rarely shout.",
        explanation_ta="பெரிய எழுத்துக்களும் ஆச்சரியக்குறிகளும் பீதியை உருவாக்க பயன்படுகின்றன. அதிகாரப்பூர்வ செய்திகள் இப்படி இருக்காது.",
        # Requires a genuinely shouted word (8+ consecutive capitals) or repeated "!!".
        patterns_en=[r"[A-Z]{8,}", r"!{2,}"],
        patterns_ta=[r"!{2,}"],
        case_sensitive=True,
    ),
    Rule(
        id="money_request_generic",
        category="banking",
        weight=0.5,
        explanation_en="The message asks you to transfer money to an account or UPI ID you do not know.",
        explanation_ta="தெரியாத கணக்கு அல்லது UPI ID-க்கு பணம் அனுப்பச் சொல்கிறது.",
        patterns_en=[r"\b(transfer|send|deposit|pay)\b.{0,30}\b(rs\.?\s*\d+|₹\s*\d+|\d{3,6}\s*(rupees|rs))\b",
                     r"\b(gpay|phonepe|paytm|upi id|google pay)\b.{0,30}\b(send|pay|transfer|number)\b"],
        patterns_ta=[r"(பணம்|ரூபாய்).{0,30}(அனுப்ப|செலுத்த|டிரான்ஸ்ஃபர்)"],
    ),
    Rule(
        id="scholarship_subsidy_bait",
        category="job",
        weight=0.7,
        explanation_en="A fake scholarship, subsidy or government scheme payout asks for bank details or a small fee to 'release' the amount.",
        explanation_ta="போலி உதவித்தொகை அல்லது அரசு திட்டம் என்று கூறி வங்கி விவரங்கள் அல்லது கட்டணம் கேட்கிறார்கள்.",
        patterns_en=[r"\b(scholarship|subsidy|yojana|scheme|pm[\s-]?kisan|free (laptop|cycle|gas))\b.{0,50}\b(register|apply|link|bank detail|fee|claim)\b"],
        patterns_ta=[r"(உதவித்தொகை|மானியம்|அரசு திட்டம்).{0,50}(பதிவு|இணைப்பு|வங்கி விவரம்)"],
    ),
    Rule(
        id="bank_detail_request",
        category="banking",
        weight=0.9,
        explanation_en="The message asks for card number, CVV, PIN, net-banking password or full account details. No genuine institution asks for these.",
        explanation_ta="கார்டு எண், CVV, PIN, கடவுச்சொல் கேட்கிறார்கள். உண்மையான நிறுவனம் இவற்றை ஒருபோதும் கேட்காது.",
        patterns_en=[r"\b(card number|cvv|atm pin|net ?banking|internet banking)\b.{0,30}\b(send|share|enter|provide|confirm|update|verify)\b",
                     r"\b(enter|update|confirm)\b.{0,25}\b(debit|credit) card\b"],
        patterns_ta=[r"(கார்டு எண்|சிவிவி|பின் எண்|கடவுச்சொல்).{0,30}(அனுப்ப|பகிர|உள்ளிட)"],
    ),
]


def _flags(rule: Rule) -> int:
    return re.UNICODE if rule.case_sensitive else (re.IGNORECASE | re.UNICODE)


_COMPILED: dict[str, tuple[list[re.Pattern[str]], list[re.Pattern[str]]]] = {
    rule.id: (
        [re.compile(p, _flags(rule)) for p in rule.patterns_en],
        [re.compile(p, _flags(rule)) for p in rule.patterns_ta],
    )
    for rule in RULES
}

_RULES_BY_ID = {r.id: r for r in RULES}


def evaluate(text: str, language: str = "en") -> list[dict]:
    """Run every rule against the text.

    Both language pattern sets always run: real messages from Indian users are routinely mixed
    Tamil + English + Tanglish in a single SMS, so restricting by detected language loses hits.
    """
    if not text:
        return []

    hits: list[dict] = []
    for rule in RULES:
        pats_en, pats_ta = _COMPILED[rule.id]
        matched_snippet = None
        for pattern in pats_en + pats_ta:
            m = pattern.search(text)
            if m:
                matched_snippet = m.group(0)[:120]
                break
        if matched_snippet:
            hits.append(
                {
                    "rule_id": rule.id,
                    "category": rule.category,
                    "weight": rule.weight,
                    "matched_snippet": matched_snippet,
                    "why_en": rule.explanation_en,
                    "why_ta": rule.explanation_ta,
                }
            )
    return hits


def rule_score(hits: list[dict]) -> float:
    """Combine hits into 0..1.

    Uses saturating addition rather than a plain sum: three medium signals should push the score
    up, but no single stack of weak rules should reach certainty on its own. Negative weights
    (legitimacy signals) are subtracted afterwards so a genuine bank alert can pull itself down.
    """
    if not hits:
        return 0.0

    positive = sorted((h["weight"] for h in hits if h["weight"] > 0), reverse=True)
    negative = sum(-h["weight"] for h in hits if h["weight"] < 0)

    score = 0.0
    remaining = 1.0
    for w in positive:
        score += w * remaining
        remaining = 1.0 - score

    score = max(0.0, score - negative)
    return round(min(score, 1.0), 4)


def dominant_category(hits: list[dict]) -> str:
    """Pick the category with the greatest total evidence.

    Summing per category rather than taking the single strongest hit: a message with three
    moderate banking signals is a banking scam even if one unrelated rule scored marginally
    higher on its own.
    """
    positives = [h for h in hits if h["weight"] > 0]
    if not positives:
        return "legitimate"

    totals: dict[str, float] = {}
    for h in positives:
        totals[h["category"]] = totals.get(h["category"], 0.0) + h["weight"]

    # Generic categories only win when nothing more specific fired.
    generic = {"impersonation", "banking"}
    specific = {k: v for k, v in totals.items() if k not in generic}
    pool = specific or totals
    return max(pool.items(), key=lambda kv: kv[1])[0]


def get_rule(rule_id: str) -> Rule | None:
    return _RULES_BY_ID.get(rule_id)
