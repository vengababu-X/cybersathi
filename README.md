<<<<<<< HEAD
# 🛡️ CyberSathi

**A Multilingual AI-Based Cyber-Fraud Awareness and Digital Safety Assistant for Communities**

English + தமிழ் · Runs fully offline · **No API keys required**

---

## What this is

A Community Service Project that combines working software with measurable community impact.
It helps digitally vulnerable people — senior citizens, rural users, school students — recognise
cyber-fraud, and it measures whether an awareness workshop actually taught them anything.

Every piece of analysis runs on the local machine. There is no cloud service, no API key, and no
internet requirement. That is a deliberate design constraint: the app has to work in a village
hall with no Wi-Fi.

---

## The seven modules

| # | Module | What it does | Where |
|---|---|---|---|
| 1 | **Scam Message Analyzer** | SMS/WhatsApp/email text → risk score + plain-language "why" in EN/TA | `POST /api/v1/scam/analyze` |
| 2 | **Phishing URL Checker** | URL → 25 static features → ML verdict. **Never opens the link** | `POST /api/v1/url/check` |
| 3 | **QR/UPI Safety** | UPI deep-link parsing + 10 interactive scam scenarios | `POST /api/v1/qr/analyze` |
| 4 | **Knowledge Base** | 12 bilingual articles across 8+ scam categories | `GET /api/v1/kb/articles` |
| 5 | **Multilingual Assistant** | Intent layer → analyzer routing → TF-IDF retrieval → fallback. Voice in, speech out | `POST /api/v1/assistant/ask` |
| 6 | **Awareness Assessment** | Pre-test → **campaign checklist** → post-test, 48-question bilingual bank | `GET /api/v1/assessment/questions` |
| 7 | **Impact Dashboard** | Improvement %, paired t-test, Cohen's d, CSV/JSON/**PDF report** | `GET /api/v1/dashboard/summary` |
| + | **Admin console** | Accounts and roles, knowledge-base overview, live model status | `/admin` (administrators only) |

---

## Full project report

**[docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md)** — what the project is, how every module
works, the complete technology stack, ML training and results with their caveats, the impact
methodology, testing, limitations and future scope. Start there if you are reading this for
the first time or writing it up.

---

## The commands that matter

```bash
SETUP.bat                  # Windows — run once: installs, trains the models, seeds the database
START.bat                  # Windows — run every time: starts both servers and opens the browser

docker compose up --build  # any OS with Docker — nothing else to install

make install && make fresh && make dev   # Git Bash / WSL / macOS / Linux
```

Everything else — prerequisites, the full manual command list, verification, everyday commands
and troubleshooting — is in the next section.

---

## Run it on another laptop

Everything below assumes the new laptop has nothing installed yet. Budget about 15 minutes; most
of it is `pip install` and one minute of model training.

### Step 1 — What the laptop needs

| Tool | Version | Needed for | Check it with |
|---|---|---|---|
| **Python** | 3.11 — the version this is built and tested on | the API, the ML models, the seeders | `python --version` |
| **Node.js + npm** | 20 LTS or newer | building and serving the web app | `node -v` and `npm -v` |
| **Git** | any recent version | only if you clone the repository, and for `make` | `git --version` |
| **Docker** | any recent version | *optional* — one command replaces all of the above | `docker --version` |

- Download links for all four: **[CYBERSATHI_LINKS_AND_SETUP.md](CYBERSATHI_LINKS_AND_SETUP.md)**, Tier 1.
- **Windows:** tick **"Add python.exe to PATH"** in the Python installer. The single most common
  cause of a failed setup is this box being left unticked.
- **Windows:** `make` needs Git Bash or WSL. Options A, B, C and D do not need it.
- The app itself needs **no internet** once installed, and never needs an API key.

### Step 2 — Get the project onto that laptop

**Option 1 — copy the folder** (zip it, or copy it on a USB stick). Fastest, and it brings
`backend/cybersathi.db` and the trained models along if they are already there.

**Option 2 — clone the repository**

```bash
git clone <repository-url> CyberSathi
cd CyberSathi
```

> **What a fresh copy does not include.** `node_modules/`, `backend/.venv/`,
> `backend/cybersathi.db` and `backend/app/ml/artifacts/*.joblib` are all git-ignored on purpose —
> dependencies, the local database and trained model files do not belong in version control.
> Every option below rebuilds them; training is offline and takes about a minute.

**If the target laptop has no internet at all**, `pip install` and `npm install` cannot run there.
Install once on a machine that does have internet, then copy the built folders across as well —
`backend/.venv/`, `frontend/node_modules/`, `backend/app/ml/artifacts/` and `backend/cybersathi.db`.
Keep the same Python minor version on both machines. Option D avoids the problem entirely: build
the two Docker images on a connected machine, save them with `docker save`, and load them on the
isolated one with `docker load`.

### Step 3 — Install and start (pick one option)

#### Option A — Windows: one click (recommended)

```
SETUP.bat      run once — installs everything, trains the models, seeds the database
START.bat      run every time — starts both servers and opens the browser
```

Double-click `SETUP.bat`. It performs the five steps you would otherwise type by hand:

| Step | What it does |
|---|---|
| 1/5 | creates `backend/.venv` |
| 2/5 | `pip install -r requirements.txt` |
| 3/5 | generates the datasets, trains both models, writes `docs/ML_METRICS.md` |
| 4/5 | creates and seeds `backend/cybersathi.db` — knowledge base, quiz bank, demo cohort |
| 5/5 | `npm install` in `frontend/` |

Then double-click `START.bat` whenever you want to use the app. It opens two terminal windows
(API and web app), waits for each to boot, and opens http://localhost:5173 in your browser.
**Leave both windows open** — closing them stops the servers.

If a step fails the window stays open with the error message. See Step 7 below.

#### Option B — VS Code: one keypress

Open this folder, then press **Ctrl+Shift+B** ("▶ Start CyberSathi") to launch the backend and
frontend together. VS Code will offer to install the recommended extensions on first open.

The tasks call `backend/.venv/Scripts/python.exe` and `frontend/node_modules`, so run Option A or
the manual steps once first — after that this is the quickest way to start. There are also tasks
for both test suites, a model rebuild and a database reseed (Ctrl+Shift+P → *Run Task*).

#### Option C — Manual commands (any OS, step by step)

> Commands below are written for Windows. On **macOS/Linux** substitute `.venv/bin/python` for
> `.venv/Scripts/python.exe` and `python3` for `python`. In `cmd.exe` you may need backslashes
> (`\.venv\Scripts\python.exe`); forward slashes work in PowerShell and Git Bash.
>
> Always call the **venv interpreter explicitly**. Activating the environment
> (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` elsewhere) lets you type plain
> `python`, but mixing that up with the system Python is the most common failure there is.

**1 — backend environment**

```bash
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

**2 — datasets, models and the database** (one minute, fully offline)

```bash
.venv/Scripts/python.exe ml_training/generate_datasets.py    # seeded: same data every time
.venv/Scripts/python.exe ml_training/train_text_model.py     # scam message classifier
.venv/Scripts/python.exe ml_training/train_url_model.py      # phishing URL classifier
.venv/Scripts/python.exe ml_training/evaluate.py             # optional: docs/ML_METRICS.md + docs/img
.venv/Scripts/python.exe -m app.seed.run --all               # KB, quiz bank, demo cohort
```

**3 — start the API** (leave this window running)

```bash
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

**4 — start the web app** (a second window, from the project root)

```bash
cd frontend
npm install
npm run dev
```

Both servers must be running at the same time: Vite proxies `/api` to `127.0.0.1:8000`, which is
why the app needs no CORS configuration in development.

#### Option D — Docker (any OS, nothing to install but Docker)

```bash
docker compose up --build
```

The images are self-contained: dependencies install and **both ML models train during the
build**, so the running containers need no internet and no API key. SQLite lives on the
`cybersathi-db` volume, is seeded on first boot, and is migrated with Alembic on every start.

- The first `--build` takes a few minutes (it trains the models). Later starts are seconds.
- Web app on **:8080**, API on **:8000** — the URLs are in Step 4.
- Stop it with `docker compose down`. Add `-v` to also delete the seeded database volume.
- The frontend container proxies `/api` to the backend container, so nothing else is needed.

#### Option E — make (Git Bash or WSL on Windows)

```bash
make install   # backend venv + frontend node_modules + backend/.env
make fresh     # datasets, trained models, reseeded database
make dev       # API on :8000 and web app on :5173 together
make test      # both test suites
make lint      # ruff + tsc + eslint
```

Schema changes are versioned with Alembic:

```bash
cd backend && .venv/Scripts/python.exe -m alembic upgrade head    # apply migrations
cd backend && .venv/Scripts/python.exe -m alembic revision --autogenerate -m "add a table"
```

> Working with a database created before migrations existed? Mark it as already current once:
> `alembic stamp head`. A database created by the app or the seeders needs no migration — but
> the Docker entrypoint and CI both run `upgrade head`, so a stale schema cannot go unnoticed.

### Step 4 — Open it and sign in

| What | Options A, B, C, E | Option D (Docker) |
|---|---|---|
| **Web app** | http://localhost:5173 | http://localhost:8080 |
| **API docs** (Swagger, runnable) | http://127.0.0.1:8000/docs | same |
| **Health check** | http://127.0.0.1:8000/health | same |

The public tools — message check, link check, QR/UPI, learn, ask — work with no account at all.
Sign in only for the facilitator pages (workshops, assessment, impact dashboard).

**Demo logins**

| Role | Email | Password |
|---|---|---|
| Admin | `admin@cybersathi.org` | `Admin@123` |
| Volunteer | `volunteer@cybersathi.org` | `Volunteer@123` |

The seeded database contains 6 workshops, 118 participants with matched pre/post assessments,
and 90 days of activity — enough to demonstrate the dashboard immediately.

### Step 5 — Prove the install works

```bash
# 1. backend test suite — expect: 154 passed
cd backend && .venv/Scripts/python.exe -m pytest tests/ -q

# 2. frontend test suite — expect: 34 passed
cd frontend && npm test

# 3. the API answers
curl http://127.0.0.1:8000/health
# {"status":"ok","app":"CyberSathi API","version":"1.0.0"}
```

Two more sanity checks worth doing once, both of which catch setup mistakes early:

- **Watch the API's first log line.** It prints `text model: loaded | url model: loaded`. If it says
  `NOT TRAINED`, the training step was skipped — run Step 2 of Option C and restart.
- **Run a real analysis.** The `curl` example under [Try it](#try-it) below posts a scam message and
  should return a risk score near 99 with a bilingual explanation.

### Step 6 — Everyday commands

| I want to… | Command |
|---|---|
| start everything (Windows) | `START.bat` |
| start the API only | `cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000` |
| start the web app only | `cd frontend && npm run dev` |
| stop everything | `Ctrl+C` in each window (or just close them) |
| re-seed the demo data | `cd backend && .venv/Scripts/python.exe -m app.seed.run --all --reset` |
| re-seed one part only | `--kb`, `--quiz`, `--demo` instead of `--all` |
| regenerate datasets + retrain | `cd backend && .venv/Scripts/python.exe ml_training/generate_datasets.py` then `train_text_model.py`, `train_url_model.py` |
| run both test suites | `make test` (Git Bash / WSL), or the two commands in Step 5 |
| check style and types | `make lint`, or `ruff check app ml_training tests`, `npm run lint`, `npx tsc --noEmit` |
| rebuild the frontend for deployment | `cd frontend && npm run build` (output in `frontend/dist/`) |
| preview that production build | `cd frontend && npm run preview` |
| apply a schema migration | `cd backend && .venv/Scripts/python.exe -m alembic upgrade head` |
| install the app on a phone | open the web app in Chrome → menu → **Add to Home screen** (it is a PWA) |

> `--reset` deletes the seeded workshops, participants and assessments, then rebuilds them. It never
touches the knowledge base articles you may have edited through the admin API.

### Step 7 — When something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `python` is not recognized | PATH not set | reinstall Python with **Add python.exe to PATH** ticked, or use `py -3.11` |
| `No module named 'fastapi'` / `'uvicorn'` | the system Python is being used, not the venv | call `.venv/Scripts/python.exe -m …` explicitly, or re-run `pip install -r requirements.txt` |
| `No module named 'app'` | wrong working directory | run backend commands from inside `backend/` |
| Port 8000 or 5173 already in use | an earlier server is still running | Windows: `netstat -ano` to find the PID, then `taskkill /F /PID <pid>` — macOS/Linux: `lsof -ti:8000` then `kill -9 <pid>` |
| API log says `text model: NOT TRAINED` | the training step was skipped | run the training commands, then restart the API |
| Web app loads but every check fails | the API is not running | start it on port 8000 (Step 3, part 3) |
| `make: command not found` (Windows) | `make` is not installed | use Options A–D, or run `make` from Git Bash / WSL |
| `npm run lint` cannot find eslint | devDependencies missing | `cd frontend && npm install` |
| `npm install` fails on an old Node | Node older than 20 | install Node.js 20 LTS or newer |
| `alembic upgrade head` says a table already exists | the database was created before migrations existed | run `alembic stamp head` once — the schema is already correct |
| No voice input button | the browser has no `SpeechRecognition` | use Chrome or Edge; everything else works in every browser |
| Tamil renders as plain or boxed text | an old browser, or `dist/index.html` opened from the filesystem | serve the app properly (`npm run dev`, or nginx in Option D) — the fonts are bundled, not downloaded |
| Docker page 404s on first run | the build is still training the models | wait for the backend healthcheck to go healthy, then reload |

Still stuck? Run the Step 5 checks — a failing test usually names the missing piece directly.
If a server will not start, its own terminal window has the traceback; read the last few lines.

---

## The assessment flow — and why the middle step matters

```
 setup  →  pre-test  →  result  →  AWARENESS CAMPAIGN  →  post-test  →  improvement
                                   ↑
                        the intervention being measured
```

An earlier build jumped from the pre-test result straight to "improvement", which is the wrong
affordance twice over: there is nothing to compare yet, and it skips the part that does the
actual teaching. Without a campaign step the app measures a change it never helped cause.

The campaign screen is **personalised from the participant's own pre-test**. The weak categories
come back with the result, so those topics are pulled to the top and tagged *Priority* — a
facilitator with fifteen minutes spends them where they count. Each topic links straight to the
knowledge-base article, there is a progress counter, and the checklist prints for use away from
a screen. Ticking every box is not required to proceed; the session decides, not the software.

---

## Ask CyberSathi — how the assistant decides

Retrieval alone was not good enough. TF-IDF over twelve articles scored below threshold on the
questions people actually type, so *"my money is gone"*, *"how do I report"*, *"someone hacked
my facebook"* and even *"hi"* all returned **"I don't have a confident answer"** — including,
worst of all, the victim in distress who needs 1930 inside the golden hour.

An intent layer now runs first (`app/nlp/intents.py`), ordered by urgency:

| # | Step | Handles |
|---|------|---------|
| 1 | **Safety gate** | Refuses scam-generation and hacking requests — wins over everything |
| 2 | **EMERGENCY** | "I lost money", "I shared my OTP" → golden-hour checklist, flagged `urgent` |
| 3 | **Pasted content** | A message or link → routed to the analyzer |
| 4 | **Procedural / social** | report · helpline · greeting · thanks · about |
| 5 | **Keyword routing** | Brand and platform names → the right article, deterministically |
| 6 | **TF-IDF retrieval** | With the query expanded by topic keywords |
| 7 | **Optional local LLM** | Ollama, grounded strictly in the retrieved article |
| 8 | **Honest fallback** | Says what it *can* answer instead of shrugging |

Two design notes worth defending in a viva:

**EMERGENCY outranks a pasted message.** Someone who has already lost money needs the steps that
still work, not an explanation of how the scam operated.

**A hypothetical is not an emergency.** *"What happens if someone asks for my OTP"* must not
trigger the alarm treatment, so a guard clause demotes hypothetical phrasing back to a normal
topic question. Both directions are covered by tests.

### What the user gets

- **Urgent answers look urgent** — red alert styling and an "Act now" badge, not the same grey
  bubble as a definition.
- **Quick actions** — a real `tel:1930` button and a report link, tappable straight from the answer.
- **Contextual follow-ups** — after an emergency answer it offers *"What do I say when I call
  1930?"*, not a generic starter list.
- **Voice input** (`ta-IN` / `en-IN`) — typing a question in Tamil is the main barrier for the
  elderly and low-literacy users this app exists for. Speaking sends immediately; an extra tap
  is a real obstacle.
- **Read aloud, copy, clear chat**, and a conversation that survives a page reload.

---

## The frontend

React 18 + TypeScript + Vite + Tailwind. Fourteen pages covering all seven modules, plus an admin console.

- **Fully bilingual.** Every string lives in `src/i18n/locales/` — there are zero hardcoded
  user-facing strings in components, and a test asserts the Tamil and English key sets match.
- **Built for the actual audience.** Font-size control (A / A+ / A++), a high-contrast toggle,
  44px minimum tap targets, full keyboard navigation, and "Read aloud" using the browser's
  speech synthesis in `ta-IN` / `en-IN`.
- **Risk is never colour alone.** Every verdict shows colour **plus** an icon **plus** a text
  label, because roughly 1 in 12 men cannot rely on red/green.
- **QR decoding happens in the browser**, and tries hard. `jsqr` reads the image locally — it is
  never uploaded — behind a fallback ladder (downscale, upscale, centre crop, contrast stretch,
  inverted). A single naive pass fails on most real photographs: a 12MP phone photo returns
  `null` outright, and a printed code under glare has too little contrast for the default
  binariser. Measured on a simulated 12.2MP washed-out photo, the old single pass failed and
  the ladder decodes it. A phone can also open the camera directly.
- **PWA.** Installable, with real 192/512 icons and a service worker that caches the knowledge
  base, the scenarios, the fonts and the app shell, so the learning material still opens in a
  village hall with no signal. Detection endpoints are deliberately *not* cached: a stale
  verdict is worse than an honest "you are offline".
- **Every form is validated with zod through react-hook-form.** The schemas carry i18next keys
  rather than English text, so one set of rules produces inline messages in both languages. The
  client limits mirror the API's own (5000 characters for a message, 1000 for a question, 20
  links per bulk check), which turns a server 422 into an inline hint before anything is sent.

## Try it

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scam/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Your SBI KYC expired. Account blocked in 24 hours. Click http://sbi-kyc.xyz and share OTP 483920","channel":"sms"}'
```

Returns a risk score of ~99, the matched warning signs with explanations in both languages, the
safe actions to take, a link to the relevant knowledge-base article — and the stored copy of the
message with the OTP already stripped out.

---

## Architecture in one paragraph

A FastAPI backend over SQLite. Scam scoring is a **hybrid**: 55% from a calibrated
TF-IDF + Logistic Regression classifier, 45% from a 33-rule bilingual pattern engine. The rules
exist because a machine-learning model cannot explain itself to a 70-year-old, and because a
scam script invented tomorrow will trip a rule before it ever appears in training data. URL
checking uses a Random Forest over 25 features computed from the URL string alone. The assistant
retrieves from the knowledge base with TF-IDF cosine similarity rather than generating text, so
it cannot invent a helpline number.

Full detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Privacy: what happens to a pasted scam message

Every submitted text is scrubbed **before** it touches the database, a log, or a response:

| Input | Stored as |
|---|---|
| `OTP is 483920` | `[REDACTED_OTP]` |
| `4532015112830366` | `[REDACTED_CARD]` |
| `9876543210` | `[REDACTED_PHONE]` |
| Aadhaar, PAN, IFSC, email, UPI VPA | redacted |

Participant phone numbers are stored **only** as a salted SHA-256 hash. The phishing checker
never fetches the URL. Stored URLs are defanged (`hxxp://`, `example[.]com`) so nobody can click
one from a report or the database.

Full detail: [docs/ETHICS_AND_PRIVACY.md](docs/ETHICS_AND_PRIVACY.md)

---

## Impact measurement

$$\text{Awareness Improvement} = \frac{\text{Post-test Score}-\text{Pre-test Score}}{\text{Pre-test Score}}\times 100$$

Two things make this defensible rather than decorative:

**Matched but disjoint tests.** Pre and post papers cover the same categories with different
questions, sampled deterministically. Measured item overlap is **0/10** — the post-test measures
learning, not memory of the paper.

**The division-by-zero guard.** The formula is undefined when the pre-test score is 0, which is
not hypothetical: 10 of 118 seeded participants score zero, and that is realistic for first-time
internet users. Rather than crashing or printing infinity, the system returns `null` for the
percentage and supplies **absolute gain** and **Hake's normalized gain** `(post−pre)/(max−pre)`
instead, with a plain-language note. All three appear in the UI and the CSV export.

The dashboard also reports a paired-samples t-test and Cohen's d, and **warns you when the mean
improvement is inflated** by small denominators — telling you to quote the median instead. On the
seeded cohort: mean 101%, median 80%, Cohen's d 2.27, t = 24.65, p < 0.001, n = 118.

---

## Testing

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

**220 tests, all passing** (173 backend + 47 frontend). Including one that submits a card number
through the API and asserts it appears in neither the database nor the response, and one that
asserts the Tamil and English translation files have identical key sets.

```bash
cd frontend && npm test
```

Linting runs in CI and locally:

```bash
cd backend  && .venv/Scripts/python.exe -m ruff check app ml_training tests
cd frontend && npm run lint          # eslint, flat config
cd frontend && npx tsc --noEmit      # types
```

| Suite | Covers |
|---|---|
| `test_privacy_and_rules.py` | Redaction, hashing, defanging, rule engine |
| `test_improvement_math.py` | The formula, the `pre=0` guard, t-test edge cases |
| `test_api.py` | All 7 modules end-to-end, auth, role guards |
| `test_assistant_intents.py` | Intent detection, the emergency golden-hour reply, refusal guard |
| `src/test/validation.test.ts` | zod schemas and the bilingual message resolution |

---

## Optional: local LLM

The assistant works fully without any model. To add a local LLM layer — still no API key, still
fully offline:

```bash
ollama pull qwen2.5:3b
```

Set `ENABLE_LLM=true` in `.env`. The LLM is prompted strictly from the retrieved article, and
any failure falls back silently to the knowledge-base answer.

---

## Project layout

```
CyberSathi/
├── SETUP.bat / START.bat              One-click setup and launch (Windows)
├── docker-compose.yml + Makefile      Container run and convenience targets
├── .github/workflows/ci.yml           Lint, test, migrate, build
├── .vscode/                           Tasks, debug config, recommended extensions
├── README.md
├── docs/
│   ├── PROJECT_REPORT.md              Full project report — how it works, what was used
│   ├── ARCHITECTURE.md                System design, the hybrid decision, the guard
│   ├── API.md                         Every endpoint
│   ├── ML_METRICS.md                  Real metrics + honest caveats (generated)
│   ├── ETHICS_AND_PRIVACY.md          What is stored and what is refused
│   ├── WORKSHOP_FACILITATOR_GUIDE.md  90-minute session plan + printable forms
│   ├── COMMUNITY_SERVICE_REPORT_TEMPLATE.md
│   └── img/                           generated confusion matrices + feature importances
├── backend/
│   ├── app/
│   │   ├── api/v1/                    auth, detection, knowledge, community, meta
│   │   ├── services/                  business logic
│   │   ├── ml/                        redaction, rules, features, models
│   │   ├── nlp/                       language detection, intent layer, TF-IDF retriever
│   │   ├── seed/                      database seeding
│   │   └── main.py
│   ├── data/                          datasets, knowledge base, quiz bank
│   ├── ml_training/                   dataset generation, training, evaluation
│   ├── alembic/                       migrations (initial revision + env)
│   └── tests/                         173 tests
└── frontend/
    ├── src/
    │   ├── i18n/locales/              en.json + ta.json (all UI text)
    │   ├── api/client.ts              typed API client
    │   ├── components/                RiskMeter, Layout, LanguageToggle, UI bits
    │   ├── context/AppContext.tsx     language, font size, contrast, auth, offline
    │   ├── pages/                     14 pages
    │   ├── forms/validation.ts        every zod schema, in one place
    │   └── test/                      47 tests
    ├── scripts/                       fetch-fonts.py, make-icons.py
    └── public/                        manifest, service worker, fonts, icons
```

---

## Honest limitations

State these in your report before an examiner raises them:

- **ML metrics are an upper bound.** Training data is synthetic (template-generated from
  published fraud patterns — no real victim messages, no live malicious domains). The classes
  are more separable than real traffic. See [docs/ML_METRICS.md](docs/ML_METRICS.md).
- **No control group**, and the post-test runs immediately after the session — it measures
  recall, not 30-day retention.
- **Advisory only.** A "safe" verdict on a novel scam is possible. The app says so every time.
- **Rate limiting is per-process**; a multi-worker deployment would need Redis.
- **Fonts are bundled, not borrowed.** Inter and Noto Sans Tamil ship in `frontend/public/fonts/`
  (regenerate with `python scripts/fetch-fonts.py`), so Tamil renders correctly with no internet
  at all. Nirmala UI / Latha remain as a last-resort fallback on Windows.

---

## Helplines used throughout

| | |
|---|---|
| **Cyber Crime Helpline** | **1930** |
| **Report online** | **cybercrime.gov.in** |
| Fraud calls/SMS | sancharsaathi.gov.in |
| Unregistered lenders | sachet.rbi.org.in |

---

## License

MIT — free to use, adapt and deploy for awareness work.

**This tool is advisory only. It is not a guarantee, and it cannot recover money.
For any real incident, call 1930 immediately.**
=======
# cybersathi
>>>>>>> f09845f8271039b7aee5febb9b3a11f6524f64c4
