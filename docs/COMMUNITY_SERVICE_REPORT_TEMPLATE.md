# Community Service Project — Report Template

Fill each section. Bracketed text `[like this]` is a prompt to replace. Figures marked
**[from dashboard]** come straight from **Dashboard → Export CSV** or `/api/v1/dashboard/summary`.

---

## Title page

> **CyberSathi: A Multilingual AI-Based Cyber-Fraud Awareness and Digital Safety Assistant for Communities**
>
> A Community Service Project Report submitted in partial fulfilment of the requirements for
> [degree], [department], [college], [university].
>
> Submitted by: [names and register numbers]
> Guide: [name and designation]
> [Month, Year]

---

## 1. Abstract (200–250 words)

Cover, in this order: the problem, what you built, what you did in the community, and the
measured result.

> Template: *Cyber-fraud in India increasingly targets digitally inexperienced users — senior
> citizens, rural residents and first-time smartphone users — through OTP theft, fake KYC
> messages, UPI misuse and impersonation. Existing awareness material is largely English-only,
> text-heavy and not available offline. This project developed CyberSathi, a bilingual
> (English–Tamil) awareness assistant combining a rule-based detector with machine-learning
> classifiers for scam messages and phishing URLs, an interactive UPI/QR safety module, a
> twelve-article bilingual knowledge base, and a pre-test/post-test assessment engine. The system
> runs entirely offline with no external API dependency, making it usable in venues without
> internet. [N] awareness workshops were conducted across [districts], reaching [N] participants.
> Awareness was measured using matched pre- and post-tests. Mean scores rose from [X]% to [Y]%,
> a median improvement of [Z]%, with a paired-samples t-test showing [t(df) = _, p < _] and a
> Cohen's d of [d], indicating a [large] effect.*

**Keywords:** cyber-fraud awareness, multilingual NLP, machine learning, community service,
digital safety, Tamil.

---

## 2. Introduction

- **2.1 Background** — cyber-fraud in India; cite cybercrime.gov.in and RBI/CERT-In material.
- **2.2 Motivation** — why digitally vulnerable groups are targeted disproportionately.
- **2.3 Problem statement** — existing material is English-only, requires internet, explains
  little, and measures nothing.
- **2.4 Objectives** — list them numbered; they should map to your seven modules.
- **2.5 Scope and limitations** — awareness only; advisory, not a guarantee; no money recovery.

---

## 3. Need analysis

- Who the beneficiaries are and why you selected them.
- Any preliminary survey you ran (include the instrument as an appendix).
- Local scam patterns reported in your area.
- The gap your project addresses.

---

## 4. Literature / existing system review

| Existing resource | Strengths | Gaps CyberSathi addresses |
|---|---|---|
| cybercrime.gov.in | Official, authoritative | Reporting portal, not a learning tool |
| Bank SMS warnings | Reach everyone | One line, no explanation, English-heavy |
| Awareness posters | Simple | Static, no feedback, no measurement |
| Commercial scam-detection apps | Sophisticated | Paid, cloud-dependent, English-only, no Tamil |

---

## 5. Methodology

- **5.1 Approach** — software development plus community intervention.
- **5.2 Intervention design** — pre-test → awareness campaign → post-test.
- **5.3 Sampling** — how participants were selected; state that participation was voluntary.
- **5.4 Ethical considerations** — consent, data minimisation, phone-number hashing, right to
  deletion. Reference [ETHICS_AND_PRIVACY.md](ETHICS_AND_PRIVACY.md).
- **5.5 Instruments** — the 48-question bilingual bank, matched pre/post sampling.

---

## 6. System design

Pull the diagrams from [ARCHITECTURE.md](ARCHITECTURE.md):

- **6.1** System architecture diagram
- **6.2** ER diagram
- **6.3** Scam-analysis sequence diagram
- **6.4** Module breakdown (the seven modules)
- **6.5** Technology stack and why each was chosen — **emphasise the zero-API-key, offline-first
  constraint**, since that is what makes the system deployable in a village hall

---

## 7. Implementation

- **7.1** Scam Message Analyzer — hybrid rule + ML scoring, the 0.55/0.45 weighting and why
- **7.2** Phishing URL Checker — 25 static features; the URL is never fetched, and why that matters
- **7.3** QR/UPI Safety — the golden rule, UPI deep-link parsing, 10 scenarios
- **7.4** Knowledge Base — 12 bilingual articles across 8+ categories
- **7.5** Multilingual Assistant — safety gate → analyzer routing → TF-IDF retrieval → fallback
- **7.6** Assessment engine — matched-but-disjoint question sets
- **7.7** Impact Dashboard — statistics and exports
- **7.8** Privacy implementation — redaction pipeline, hashing

Include code snippets for the scoring function and the improvement calculation.

---

## 8. Testing

| Type | Coverage | Result |
|---|---|---|
| Unit — privacy/redaction | 13 tests | All pass |
| Unit — rule engine | 10 tests | All pass |
| Unit — improvement maths | 26 tests | All pass |
| Integration — API, all 7 modules | 45 tests | All pass |
| **Total** | **94 tests** | **94 passed** |

Note explicitly that privacy is enforced by test: a card number submitted through the API is
asserted to appear neither in the database nor in the response.

---

## 9. Community engagement

### 9.1 Workshop log

| # | Date | Venue | District | Audience | Registered | Completed both tests |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| | | | | **Total** | | |

### 9.2 Participant demographics

| Category | Count | % |
|---|---|---|
| Students / Adults / Seniors | | |
| Male / Female / Other | | |
| Tamil / English preference | | |

### 9.3 Activities conducted
Describe the session structure; reference the
[Workshop Facilitator Guide](WORKSHOP_FACILITATOR_GUIDE.md).

---

## 10. Impact analysis ⭐

> This is the section that distinguishes a community service project from a software project.
> Be precise, and state the caveats yourself before an examiner raises them.

### 10.1 The measurement instrument

Matched pre- and post-tests: the same category profile, different questions. State that measured
item overlap was **0/10**, so the post-test measures learning rather than recall of the paper.

### 10.2 The improvement formula

$$\text{Awareness Improvement} = \frac{\text{Post-test Score}-\text{Pre-test Score}}{\text{Pre-test Score}}\times 100$$

**State the guard explicitly.** The formula is undefined when the pre-test score is zero — which
occurred for **[N]** participants, a realistic outcome for first-time internet users. For those
participants the system reports two alternatives instead:

$$\text{Absolute Gain} = \text{Post} - \text{Pre} \qquad
\text{Normalized Gain} = \frac{\text{Post}-\text{Pre}}{\text{Max}-\text{Pre}}$$

Normalized gain (Hake's g) is standard in education research and is defined for all non-perfect
pre-scores.

### 10.3 Overall results **[from dashboard]**

| Metric | Value |
|---|---|
| Participants with both tests (n) | |
| Mean pre-test score (%) | |
| Mean post-test score (%) | |
| **Median improvement (%)** | |
| Mean improvement (%) | |
| Standard deviation | |
| Participants moved from low awareness (<50%) to aware (≥70%) | |
| Participants with undefined improvement (pre = 0) | |

> **Report the median as your headline figure, not the mean.** Ratio-based improvement is
> inflated by small denominators — a participant going from 1/10 to 5/10 registers as +400%.
> The dashboard flags this automatically when the mean exceeds 1.15 × the median. Quoting the
> mean without this caveat is the most likely point of challenge in a viva.

### 10.4 Statistical significance

| Test | Value |
|---|---|
| Paired-samples t-statistic | |
| Degrees of freedom (n − 1) | |
| p-value | |
| Cohen's d (effect size) | |

Interpretation of d: 0.2 small, 0.5 medium, 0.8+ large.

Write the conclusion in words: *"The improvement was statistically significant (t([df]) = [t],
p < [p]), with a Cohen's d of [d] indicating a [large] practical effect."*

### 10.5 Improvement by scam category **[from dashboard]**

| Category | Pre (%) | Post (%) | Δ |
|---|---|---|---|

Discuss which topics improved most and least, and what that suggests about your teaching.

### 10.6 Improvement by demographic

Tables by age group, language and district. Comment on which group started lowest and which
gained most — usually the most interesting finding in the whole report.

### 10.7 Qualitative feedback

Average rating out of 5, plus 3–5 representative quotes (with consent). Include at least one
piece of critical feedback — it makes the rest credible.

### 10.8 Threats to validity

Be your own examiner:

- **Testing effect** — taking a pre-test primes attention; mitigated by disjoint items.
- **Social desirability** — participants may answer as they think you want.
- **Self-selection** — those who attend may already be more interested.
- **No control group** — improvement cannot be attributed to the intervention with certainty.
- **Short interval** — post-test immediately after the session measures recall, not retention.
  **A follow-up test after 30 days would substantially strengthen this claim.**
- **Sample size / geography** — limits generalisation.

---

## 11. Results and discussion

Interpret rather than repeat. Which modules did participants engage with most? What surprised
you? What did you change between the first and last workshop?

---

## 12. Challenges faced

Technical, logistical (venue, attendance, language), and methodological. Say how you handled each.

---

## 13. Conclusion

Restate objectives, state what was achieved against each, and give the headline impact figure —
with its caveat.

---

## 14. Future scope

- Follow-up retention testing after 30 days
- A real, consent-collected validation set to replace synthetic-only ML metrics
- More Indian languages (Telugu, Hindi, Malayalam)
- Voice interface for non-literate users
- Android app with SMS-read permission for on-device scanning
- Partnership with the district cyber cell

---

## 15. References

Cite: cybercrime.gov.in, RBI Sachet, CERT-In advisories, NPCI UPI guidelines, Hake (1998) on
normalized gain, Cohen (1988) on effect size, plus the libraries used (scikit-learn, FastAPI).

---

## Appendices

- **A** — Consent form (bilingual)
- **B** — Pre/post question bank (48 questions)
- **C** — Workshop handout
- **D** — Photographs with consent
- **E** — Raw data export (`cybersathi_impact.csv`)
- **F** — [ML_METRICS.md](ML_METRICS.md) — model performance **with its synthetic-data caveat**
- **G** — Source code repository link

---

## Checklist before submission

- [ ] Every `[bracketed]` placeholder replaced
- [ ] Median quoted as headline improvement, not the mean alone
- [ ] `pre = 0` guard explained in section 10.2
- [ ] Synthetic-data caveat stated in the ML section, not buried in an appendix
- [ ] Threats to validity written honestly
- [ ] Consent forms collected and filed
- [ ] At least one critical piece of feedback included
- [ ] Test results (94 passing) included
- [ ] Helpline 1930 appears in the report as it does in the app
