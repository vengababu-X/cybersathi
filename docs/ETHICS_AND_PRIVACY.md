# Ethics and Privacy

An awareness project that leaks the very data it teaches people to protect would be worse than
no project at all. This document states what CyberSathi does with data, and what it refuses to do.

---

## 1. Data minimisation

**Nothing sensitive is stored, ever.** Every piece of user-submitted text passes through
`app/ml/redaction.py` *before* it reaches the database, a log line, or an API response.

Redacted automatically:

| Type | Example input | Stored as |
|---|---|---|
| OTP | `OTP is 483920` | `[REDACTED_OTP]` |
| Card number | `4532015112830366` | `[REDACTED_CARD]` |
| Aadhaar | `4123 4567 8901` | `[REDACTED_AADHAAR]` |
| Phone | `9876543210` | `[REDACTED_PHONE]` |
| Email | `name@example.com` | `[REDACTED_EMAIL]` |
| UPI VPA | `someone@okaxis` | `[REDACTED_UPI]` |
| PAN / IFSC | `ABCDE1234F` | `[REDACTED_PAN]` |
| PIN / CVV | `CVV 456` | `[REDACTED_PIN]` |

This is enforced by tests (`tests/test_privacy_and_rules.py`), including one that submits a
card number through the API and asserts it appears neither in the database nor in the response.

## 2. Participant phone numbers are hashed, not stored

Workshop rosters need to de-duplicate participants across sessions without holding their
numbers. The API accepts a phone number, immediately converts it to a salted SHA-256 hash, and
discards the original. The raw number is never written to the database.

```
9876543210  ->  997a3dae72d1d923a64e...  (one-way, 64 hex characters)
```

## 3. Consent is recorded

Every `Participant` row carries `consent_given`. The facilitator guide includes a printable
bilingual consent form. Participants who decline are still welcome at the workshop — they simply
are not recorded in the impact dataset.

Participants may request deletion at any time. To delete one person's data completely:

```bash
python -c "
from app.database import SessionLocal
from app.models import Participant, Assessment
db = SessionLocal()
pid = 42  # the participant id
db.query(Assessment).filter(Assessment.participant_id == pid).delete()
db.query(Participant).filter(Participant.id == pid).delete()
db.commit()
"
```

## 4. The phishing checker never opens the URL

`app/ml/features.py` computes all 25 features from the URL *string*. No network request is ever
made. This matters for two reasons:

- Fetching the URL would confirm to the attacker that a human read the message, marking that
  phone number as live and valuable.
- It would risk executing a drive-by payload on a student's laptop during a demo.

Stored and displayed URLs are **defanged** (`hxxp://`, `example[.]com`) so nobody can click one
from a report, a slide, or the database.

## 5. Advisory only — never a guarantee

Every verdict carries a disclaimer in both languages. The app does not tell anyone that a
message is definitely safe; it says no strong warning signs were found and directs the user to
verify independently. A "safe" result on a novel scam is a real possibility, and the UI says so.

Every response includes the helpline **1930** and **cybercrime.gov.in**.

## 6. The assistant refuses to produce scam content

`app/services/assistant_service.py` gates requests to write phishing messages, fake bank SMS,
or to hack an account — including requests framed as testing or revenge. It answers with an
awareness explanation and the helpline instead.

It also refuses "help me recover my money" schemes, and warns that anyone offering paid recovery
is running a well-documented **second** scam targeting people who have already been defrauded.

## 7. No third-party data sharing

The application makes **no outbound network calls** in its default configuration. There are no
analytics, no telemetry, no external APIs, and no API keys. All data stays in the local SQLite
file. If the optional Ollama integration is enabled, the request goes to `localhost` only.

## 8. Synthetic training data only

No real victim message is in the training corpus. Every row in `data/scam_messages.csv` and
`data/urls.csv` is generated from templates based on publicly documented fraud patterns
(cybercrime.gov.in advisories, RBI/NPCI awareness material, CERT-In notes). No live malicious
domain appears anywhere in the repository.

The trade-off is documented honestly in [ML_METRICS.md](ML_METRICS.md): synthetic data inflates
the accuracy figures, and those numbers are reported as an upper bound rather than field accuracy.

## 9. Anonymised case studies

The knowledge-base articles include short real-world style examples. These are composites drawn
from publicly reported fraud patterns. They name no real person, and the locations are used only
to make the scenario recognisable to a Tamil Nadu audience.

## 10. Responsible disclosure

If you find a security issue in this project, please report it privately to the project
maintainer before disclosing publicly. Do not test against live systems or real victims.

---

## Limitations we state openly

- Rate limiting is per-process and in-memory; a multi-worker deployment would need Redis.
- The default `SECRET_KEY` is for development. Any shared deployment must set its own.
- There is no field-tested accuracy figure yet — only synthetic-corpus performance.
- The app cannot recover stolen money and never claims to. It routes users to 1930.
