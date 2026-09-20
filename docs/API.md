# API Reference

Base URL: `http://127.0.0.1:8000`
Interactive explorer: **`/docs`** (Swagger UI, generated from the live app)

36 endpoints. Authentication is JWT bearer. The public awareness tools work **anonymously** —
a token is optional and only links the activity to a user account.

---

## Conventions

- All request and response bodies are JSON unless stated otherwise.
- Every response carries `X-Request-ID` and `X-Process-Time-Ms` headers.
- Errors return `{"detail": "...", "code": "...", "request_id": "..."}`.
- `language` accepts `en`, `ta`, or `auto` (detect from the text).
- Rate limit: 60 requests/minute per IP on analysis and login endpoints → `429`.

| Code | Meaning |
|---|---|
| 200/201 | Success |
| 401 | Missing or invalid token |
| 403 | Authenticated, but wrong role |
| 404 | Not found |
| 409 | Conflict (duplicate email) |
| 422 | Validation failure |
| 429 | Rate limited |

---

## Authentication

### `POST /api/v1/auth/register` → 201

```json
{"full_name":"Asha K","email":"asha@example.org","password":"Secret@123",
 "role":"participant","preferred_language":"ta","age_group":"adult"}
```

Returns `{access_token, token_type, user}`. `role` ∈ `admin | volunteer | participant`.
Duplicate email → **409**.

### Account roles

Public registration can create only a `participant` account. An authenticated administrator
creates volunteer and administrator accounts with `POST /api/v1/auth/users`.

### `POST /api/v1/auth/users` — administrator only

Requires an administrator bearer token. Its body uses the same fields as registration and may
set `role` to `admin`, `volunteer`, or `participant`.

### `POST /api/v1/auth/login`

Form-encoded (OAuth2 password flow): `username` (the email) and `password`.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -d "username=admin@cybersathi.org&password=Admin@123"
```

### `GET /api/v1/auth/me` → 200 · requires token
### `POST /api/v1/auth/change-password` → 204 · requires token

---

## Module 1 — Scam Message Analyzer

### `POST /api/v1/scam/analyze` → 200 · auth optional

```json
{"text": "Your SBI KYC expired. Share OTP 483920", "channel": "sms", "language": "auto"}
```

`channel` ∈ `sms | whatsapp | email | call_transcript`. `text` is 1–5000 chars.

**Response (abridged):**

```json
{
  "analysis_id": 217,
  "risk_score": 99.5,
  "risk_label": "high_risk",
  "primary_category": "kyc",
  "language_detected": "en",
  "redacted_text": "Your SBI KYC expired. Share [REDACTED_OTP]",
  "pii_found": ["otp_labelled"],
  "signals": [{"rule_id":"kyc_expiry_threat","matched_snippet":"KYC ... expired",
               "why_en":"A fake 'KYC expired' warning is used to panic you...",
               "why_ta":"'KYC காலாவதி' என்ற போலி எச்சரிக்கை...","weight":0.85}],
  "top_terms": [{"term":"kyc","contribution":0.41}],
  "explanation": {"en":"This message shows strong signs of a scam...","ta":"..."},
  "safe_actions": {"en":["Do not reply..."],"ta":["பதில் அளிக்காதீர்கள்..."]},
  "related_kb_slugs": ["kyc-scams"],
  "helplines": {"cyber_crime":"1930","portal":"cybercrime.gov.in"},
  "disclaimer": {"en":"Advisory only...","ta":"..."},
  "model_used": true
}
```

**Scoring:** `0.55 × P(scam|ML) + 0.45 × rule_score`.
**Labels:** `<35` safe · `35–69` suspicious · `≥70` high_risk.
**Privacy:** `redacted_text` is what gets stored. The original never reaches the database.

### `GET /api/v1/scam/examples?category=&language=` → 200

Curated safe demo samples, so a facilitator never types a real scam message on stage.

---

## Module 2 — Phishing URL Checker

### `POST /api/v1/url/check` → 200 · auth optional

```json
{"url": "http://sbi-kyc-update-verify.xyz/login"}
```

Defanged input is accepted (`hxxp://`, `example[.]com`) and normalised automatically.

```json
{
  "check_id": 152,
  "url_defanged": "hxxp://sbi-kyc-update-verify[.]xyz/login",
  "risk_score": 100.0,
  "risk_label": "high_risk",
  "features": {"url_length": 38.0, "suspicious_tld": 1.0, "num_hyphens": 3.0, "...": 0},
  "top_reasons": [{"feature":"sensitive_word_hit","value":2.0,
                   "why_en":"The link contains words like login, verify or KYC...",
                   "why_ta":"இணைப்பில் login, verify, KYC போன்ற சொற்கள் உள்ளன..."}],
  "lookalike_brand": "SBI",
  "advice": {"en":"Do not open this link...","ta":"..."},
  "model_used": true
}
```

> **The URL is never fetched.** All 25 features are computed from the string.
> A genuine bank domain returns `top_reasons: []` — the checker does not warn about real sites.

### `POST /api/v1/url/bulk-check` → 200

`{"urls": ["...", "..."]}` — max 20, for workshop demos. Not persisted.

---

## Module 3 — QR / UPI Safety

### `POST /api/v1/qr/analyze` → 200

```json
{"payload": "upi://collect?pa=x@ybl&pn=Refund&am=4999&tn=cashback"}
```

Accepts the text decoded from a QR **by the browser** (client-side, e.g. `jsqr`). No image upload.

Detects: collect/mandate intent, pre-filled amounts, name↔VPA mismatch, look-alike Unicode
characters, embedded URLs, `.apk` downloads, and credential requests.

Every response carries the `golden_rule` in both languages:

> *Scanning a QR code or approving a request is ALWAYS to PAY. You never scan, and never enter a
> PIN, to RECEIVE money.*

### `GET /api/v1/qr/scenarios` → 200

10 interactive scenarios, each with a situation, 3 choices with feedback, and a lesson — all
bilingual.

---

## Module 4 — Knowledge Base

| Endpoint | Notes |
|---|---|
| `GET /api/v1/kb/articles?category=&q=` | `q` searches **both** languages simultaneously |
| `GET /api/v1/kb/categories` | Counts + bilingual labels |
| `GET /api/v1/kb/articles/{slug}` | Full article; increments `views`. 404 if unknown |

Article detail returns `body_en`/`body_ta`, plus `red_flags`, `safe_actions` and `victim_steps`
as `{en: [...], ta: [...]}`.

12 articles covering all 8 required categories plus `digital_arrest`, `courier_parcel` and
`lottery`.

---

## Module 5 — Multilingual Assistant

### `POST /api/v1/assistant/ask` → 200 · auth optional

```json
{"question": "Someone is asking for my OTP", "language": "auto", "simple_mode": false}
```

`simple_mode: true` returns sentences under 12 words with no technical terms — for elderly or
first-time users.

**Response:**

```json
{
  "log_id": 812,
  "answer": "Act now — the first hour matters most...",
  "language": "en",
  "source": "rule",
  "intent": "emergency",
  "confidence": 1.0,
  "urgent": true,
  "related_articles": [],
  "suggested_questions": ["What do I say when I call 1930?", "..."],
  "quick_actions": [
    {"kind": "call", "value": "1930", "label": "Call 1930"},
    {"kind": "link", "value": "https://cybercrime.gov.in", "label": "Report online"}
  ],
  "disclaimer": "General awareness guidance only..."
}
```

**`source`** — which layer produced the answer:

| `source` | When |
|---|---|
| `refusal` | Request to write scam content or hack an account. Wins over everything |
| `rule` | An intent matched: emergency, report, helpline, greeting, thanks, about |
| `analyzer` | A message or URL was pasted → routed to module 1 or 2 |
| `kb` | Keyword route or knowledge-base match above threshold |
| `llm` | Ollama enabled **and** reachable; grounded in the retrieved article |
| `fallback` | No confident match; lists what the assistant *can* answer, plus 1930 |

**`intent`** — `emergency`, `report`, `helpline`, `greeting`, `thanks`, `about`, `topic`,
`analyzer`, `refusal`, `fallback`, `none`.

**`urgent`** — `true` when the person has already been defrauded. The UI renders these as a red
alert with an "Act now" badge. Clients should not style an urgent answer like a definition.

**`quick_actions`** — tappable chips. `kind` is `call` (dial `value`), `link` (open externally)
or `route` (navigate in-app to `value`).

**`suggested_questions`** — follow-ups contextual to *this* answer, not a fixed starter list.

> Works with **no LLM and no internet**. `ENABLE_LLM=false` is the default, and steps 1–6 and 8
> of the resolution order are fully deterministic.

### `POST /api/v1/assistant/feedback` → 204 · `{"log_id": 12, "helpful": true}`
### `GET /api/v1/assistant/suggestions?language=ta` → 200

---

## Module 6 — Workshops and Assessment

### `POST /api/v1/workshops` → 201 · **admin/volunteer**
### `GET /api/v1/workshops?district=&date_from=&date_to=` → 200

### `POST /api/v1/workshops/{id}/participants` → 201 · **admin/volunteer**

```json
[{"name":"Lakshmi R","age_group":"senior","gender":"female",
  "language":"ta","phone":"9876543210","consent_given":true}]
```

> `phone` is hashed to SHA-256 on arrival. **The raw number is never stored** and cannot be
> retrieved.

### `GET /api/v1/assessment/questions` → 200

Query: `workshop_id`, `participant_id`, `type` (`pre`|`post`), `language`, `count` (default 10).

Returns **matched but disjoint** sets: the pre- and post-tests cover the same categories with
different questions, seeded deterministically so a page reload does not reshuffle the paper.

### `POST /api/v1/assessment/submit` → 200

```json
{"participant_id": 5, "workshop_id": 1, "type": "post",
 "answers": [{"question_id": 12, "selected_index": 1}],
 "duration_seconds": 240, "language": "en"}
```

Returns score, percentage, per-category breakdown, weak categories, and a full review with the
correct answer and explanation for each question. Re-submitting updates rather than duplicating.

### `GET /api/v1/assessment/participant/{id}/improvement` → 200

```json
{"participant_id": 5, "pre_score": 0, "post_score": 5, "max_score": 10,
 "pre_percentage": 0.0, "post_percentage": 50.0,
 "improvement_percentage": null,
 "absolute_gain": 5, "normalized_gain": 0.5,
 "band": "partially aware",
 "note": "Pre-test score was 0, so percentage improvement is mathematically undefined..."}
```

> **`improvement_percentage` is `null` when `pre_score = 0`** — division by zero. Use
> `absolute_gain` and `normalized_gain` for those participants. Clients must handle `null`.

---

## Module 7 — Impact Dashboard

### `GET /api/v1/dashboard/summary` → 200

Filters: `date_from`, `date_to`, `district`, `audience`.

```json
{
  "totals": {"workshops":6,"participants":126,"messages_analyzed":216,
             "urls_checked":171,"assistant_queries":91},
  "awareness": {
    "avg_pre_pct":36.35,"avg_post_pct":65.40,
    "avg_improvement_pct":86.99,"median_improvement_pct":75.0,
    "std_dev_improvement":66.34,
    "cohens_d":1.7963,"t_statistic":20.1638,"p_value":0.0,
    "n_pairs":126,"moved_to_aware_pct":29.37,
    "undefined_improvement_count":8,
    "interpretation_note":"The mean improvement (86.99%) is inflated by participants with very low pre-test scores... Quote the median (75.0%) and the effect size."
  },
  "improvement_by_category":[{"category":"impersonation","pre":26.2,"post":68.3,"delta":42.1}],
  "by_age_group":[{"group":"senior","avg_pre":27.4,"avg_post":57.2,"avg_improvement":102.6,"n":39}],
  "by_language":[], "by_district":[],
  "top_scam_categories":[{"name":"impersonation","count":30}],
  "risk_distribution":{"safe":40,"suspicious":17,"high_risk":159},
  "timeline":[{"date":"2026-07-01","analyses":3,"participants":0}],
  "feedback":{"avg_rating":4.37,"count":52.0}
}
```

> `interpretation_note` appears when the mean exceeds 1.15 × the median. Display it — quoting
> the mean alone overstates the result.

### `GET /api/v1/dashboard/export?format=csv|json` → 200

Per-participant rows including both scores, all three improvement metrics, band and note.
Returns `text/csv` with a `Content-Disposition` attachment header.

### `GET /api/v1/certificates/{participant_id}` → `application/pdf`

Bilingual PDF certificate with pre/post scores and improvement.
**400** if the post-test is not yet complete. Falls back to English-only with a visible note if
no Tamil-capable font is installed.

### `POST /api/v1/feedback` → 201 · `{workshop_id, rating: 1-5, comment}`

---

## System

| Endpoint | Returns |
|---|---|
| `GET /health` | `{"status":"ok"}` |
| `GET /api/v1/meta/status` | Model load state, `api_keys_required: false`, `offline_capable: true` |
| `GET /api/v1/meta/model-metrics` | Real training metrics **plus the synthetic-data caveat** |
| `GET /api/v1/meta/helplines` | 1930, cybercrime.gov.in, Sanchar Saathi, RBI Sachet |


---

## Admin (administrators only)

| Endpoint | Notes |
|---|---|
| `GET /api/v1/auth/users` | List all accounts. 403 for non-administrators |
| `POST /api/v1/auth/users` | Create a participant, volunteer or administrator account |
| `PATCH /api/v1/auth/users/{id}/role` | Change a role. **400** if you try to demote yourself |
| `PATCH /api/v1/auth/users/{id}/active` | Enable/disable. **400** if you try to disable yourself |

> The self-lockout guards exist because an administrator who removed their own role would
> leave the deployment with no administrator and no recovery path through the UI. A disabled
> account is refused at login with **403**.

## Feedback

### `POST /api/v1/feedback` → 201

```json
{"workshop_id": 3, "participant_id": null, "rating": 5, "comment": "Very useful"}
```

`rating` is 1–5 and `participant_id` is optional, so a session rating stays anonymous.
This is what populates `feedback.avg_rating` on the dashboard and the feedback section of the
PDF report.
