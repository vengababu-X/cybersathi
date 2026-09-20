# CyberSathi — All Links & Setup Steps

**Rule of thumb:** Tier 1 is mandatory. Tier 2 is what you sign into with your Gmail (optional,
free). Tier 3 is content you should cite inside the app. Tier 4 is optional datasets/APIs.
The app is designed to run with **no API key at all**.

---

## TIER 1 — Required installs (free, no account, no email)

| Tool | Link | Why |
|------|------|-----|
| VS Code | https://code.visualstudio.com/download | The editor |
| Node.js (LTS 20+) | https://nodejs.org/en/download | Frontend build + npm |
| Python 3.11 | https://www.python.org/downloads/ | Backend + ML (skip if frontend-only) |
| Git | https://git-scm.com/downloads | Version control, required for submission |
| Ollama (optional local AI) | https://ollama.com/download | Offline LLM, no key, no account |

**Steps**
1. Install VS Code → Node.js → Python → Git, in that order.
2. During Python install, **tick "Add python.exe to PATH"** (the #1 cause of later errors).
3. Verify in a terminal:
   ```bash
   node -v && npm -v && python --version && git --version
   ```
4. All four must print a version number. If Python fails, reinstall with the PATH box ticked.

---

## TIER 2 — VS Code AI extensions (install one)

Easiest path: open VS Code → `Ctrl+Shift+X` → search the name → Install.

| Extension | Search name in VS Code | Notes |
|-----------|------------------------|-------|
| Cline | `Cline` | Best agentic file-writing; my top pick for this project |
| Roo Code | `Roo Code` | Cline fork, more modes |
| Kilo Code | `Kilo Code` | Cline/Roo fork, free credits on signup |
| Continue | `Continue` | Great with local Ollama |
| GitHub Copilot | `GitHub Copilot` | Free tier for students |

Marketplace browse: https://marketplace.visualstudio.com/vscode

> Search by name rather than trusting a publisher ID — these extensions change publishers often.

---

## TIER 3 — Free AI model access (this is where your Gmail is used)

You need **one** of these to power the extension. **You must sign up yourself** — I cannot
create accounts or enter credentials for you.

### Option A — Google AI Studio (recommended; direct Gmail login, generous free tier)
1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Gmail account.
3. Accept the terms → click **Create API key** → choose/create a project.
4. Click **Copy**.
5. In VS Code, open Cline → gear icon → API Provider = **Google Gemini** → paste key →
   Model = `gemini-2.0-flash` (or the newest Flash listed).
6. Never commit the key. Keep it in `.env`, and make sure `.env` is in `.gitignore`.

### Option B — Groq (very fast, free tier)
- https://console.groq.com/keys — sign in with Google → Create API Key.

### Option C — OpenRouter (aggregates many free models)
- https://openrouter.ai/keys — sign in → Create Key. Filter models by "free".

### Option D — Ollama (ZERO signup, fully offline, best for a demo with no internet)
```bash
ollama pull qwen2.5-coder:7b
ollama serve
```
Then in Continue/Cline set provider = **Ollama**, base URL `http://localhost:11434`.
This is the option I'd use for the live viva demo — no Wi-Fi dependency, no quota.

---

## TIER 4 — Free hosting & deployment (optional, all Gmail/GitHub login)

| Service | Link | Use |
|---------|------|-----|
| GitHub | https://github.com/signup | Repo + submission link |
| GitHub Pages | https://pages.github.com | Free static hosting (frontend-only build) |
| Netlify | https://app.netlify.com/signup | Free static hosting + custom URL |
| Vercel | https://vercel.com/signup | Free static hosting |
| Render | https://render.com | Free tier if you keep the FastAPI backend |
| Supabase | https://supabase.com | Free Postgres + auth, if you ever want shared data |

**Steps for GitHub Pages (simplest):**
1. Create repo `cybersathi` on GitHub.
2. `git remote add origin <url>` → `git push -u origin main`
3. Repo → **Settings → Pages** → Source = GitHub Actions → pick the Vite/static workflow.
4. Your live URL becomes `https://<username>.github.io/cybersathi/`

---

## TIER 5 — Official Indian cyber-safety sources (cite these INSIDE the app)

These are the authoritative references your knowledge base and helpline banner must point to.
Examiners look for exactly this.

| Resource | Link | Use in project |
|----------|------|----------------|
| **National Cyber Crime Reporting Portal** | https://cybercrime.gov.in | Primary "report here" link |
| **Cyber Crime Helpline** | **Dial 1930** | Golden-hour reporting, put in every verdict |
| CERT-In | https://www.cert-in.org.in | Advisories, credibility citations |
| Cyber Dost (MHA / I4C) | https://x.com/CyberDost | Bite-sized awareness content to paraphrase |
| RBI Sachet | https://sachet.rbi.org.in | Report illegal lending apps / unregistered entities |
| RBI Kehta Hai | https://rbikehtahai.rbi.org.in | Official banking-fraud awareness, bilingual material |
| Sanchar Saathi (DoT) | https://sancharsaathi.gov.in | Report fraud calls/SMS (Chakshu), block lost phones |
| NPCI | https://www.npci.org.in | Official UPI safety rules for your QR/UPI module |
| ISEA (Info Security Education & Awareness) | https://isea.gov.in | Free awareness posters/material for workshops |
| UIDAI | https://uidai.gov.in | Aadhaar do's and don'ts for the KYC module |
| TRAI | https://www.trai.gov.in | DND / spam-SMS regulation references |

> For your state-level unit, search "Tamil Nadu Cyber Crime Wing official site" and verify the
> `.gov.in` domain before adding it — state portals change URLs, so confirm rather than trust a
> link copied from anywhere (including me).

---

## TIER 6 — Optional public datasets (only if you want real data instead of synthetic)

| Dataset | Link | Account? |
|---------|------|----------|
| UCI SMS Spam Collection | https://archive.ics.uci.edu/dataset/228/sms+spam+collection | No |
| UCI Phishing Websites | https://archive.ics.uci.edu/dataset/327/phishing+websites | No |
| Kaggle — SMS Spam / Malicious URLs | https://www.kaggle.com/datasets | Yes (Gmail login) |
| Hugging Face Datasets | https://huggingface.co/datasets | Optional |
| OpenPhish community feed | https://openphish.com/phishing_feeds.html | No |
| PhishTank developer data | https://phishtank.org/developer_info.php | Yes (free) |

**Safety rule:** if you import a live phishing feed, **defang every URL** (`hxxp://`, `example[.]com`)
before it touches your CSV, your repo, or your slides. Never let the app fetch those URLs.

### Optional live-lookup APIs (free tier, your Gmail)
| API | Link | Notes |
|-----|------|-------|
| Google Safe Browsing | https://developers.google.com/safe-browsing | Free with a Google Cloud project |
| VirusTotal | https://www.virustotal.com/gui/join-us | Free key, 4 lookups/min |
| urlscan.io | https://urlscan.io | Free key |

> These are **enhancements, not requirements**. Your ML classifier must still work offline if the
> key is missing — that's what makes it a real ML project rather than an API wrapper.

---

## TIER 7 — Assets & library docs (no account)

| Item | Link |
|------|------|
| Noto Sans Tamil font | https://fonts.google.com/noto/specimen/Noto_Sans_Tamil |
| Inter font | https://fonts.google.com/specimen/Inter |
| Lucide icons | https://lucide.dev |
| Tailwind CSS docs | https://tailwindcss.com/docs |
| React docs | https://react.dev |
| Vite | https://vite.dev |
| FastAPI | https://fastapi.tiangolo.com |
| scikit-learn | https://scikit-learn.org/stable/ |
| Dexie (IndexedDB) | https://dexie.org |
| jsQR (QR decoding) | https://github.com/cozmo/jsQR |
| Recharts | https://recharts.org |
| i18next | https://www.i18next.com |
| SheetJS (Excel export) | https://sheetjs.com |

Download the two fonts as `.ttf`/`.woff2` and bundle them in `frontend/public/fonts/` so Tamil
renders offline in a village hall with no internet.

---

## The absolute minimum path (if you are short on time)

1. Install **VS Code + Node.js + Git**. (Skip Python if you go frontend-only.)
2. Install the **Cline** extension.
3. Get a **free Gemini key** at https://aistudio.google.com/apikey with your Gmail.
4. Paste `CYBERSATHI_MASTER_PROMPT.md` → PROMPT 0, then PROMPT 1, and continue.
5. For the demo, add only **1930** and **cybercrime.gov.in** as live links. Everything else is
   optional polish.

---

## What I cannot do for you

- Create accounts, sign up, or log in anywhere on your behalf.
- Enter or handle your passwords, API keys, or payment details.
- Generate API keys for you — every key must be created under your own account so it stays
  yours and can be revoked by you.

Paste keys into `.env` only, and confirm `.env` is listed in `.gitignore` before your first
commit. A key pushed to a public GitHub repo is compromised within minutes — scanners find them
automatically. If that happens, revoke it in the provider's console immediately and issue a new one.
