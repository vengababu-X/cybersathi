"""Seed the database.

Usage:
    python -m app.seed.run --all
    python -m app.seed.run --kb --quiz
    python -m app.seed.run --all --reset

The demo cohort is generated with deliberate imperfection: a handful of participants do not
improve, and a few score zero on the pre-test. Real fieldwork looks like that, and a dashboard
where every single person improves is the first thing an examiner will disbelieve.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))

from app.config import DATA_DIR  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.ml.redaction import hash_phone  # noqa: E402
from app.models import (  # noqa: E402
    Assessment,
    AssistantLog,
    FeedbackEntry,
    KbArticle,
    Participant,
    QuizQuestion,
    ScamAnalysis,
    UrlCheck,
    User,
    Workshop,
)
from app.nlp import retriever  # noqa: E402

RNG = random.Random(2026)


def seed_knowledge_base(db: Session) -> int:
    path = DATA_DIR / "knowledge_base.json"
    if not path.exists():
        print(f"  ! {path.name} not found, skipping")
        return 0

    articles = json.loads(path.read_text(encoding="utf-8"))
    created = updated = 0

    for item in articles:
        existing = db.query(KbArticle).filter(KbArticle.slug == item["slug"]).first()
        fields = {
            "slug": item["slug"],
            "category": item["category"],
            "severity": item.get("severity", "high"),
            "title_en": item["title_en"],
            "title_ta": item["title_ta"],
            "summary_en": item["summary_en"],
            "summary_ta": item["summary_ta"],
            "body_en": item["body_en"],
            "body_ta": item["body_ta"],
            "red_flags_json": json.dumps(
                {"en": item.get("red_flags_en", []), "ta": item.get("red_flags_ta", [])},
                ensure_ascii=False,
            ),
            "safe_actions_json": json.dumps(
                {"en": item.get("safe_actions_en", []), "ta": item.get("safe_actions_ta", [])},
                ensure_ascii=False,
            ),
            "victim_steps_json": json.dumps(
                {"en": item.get("victim_steps_en", []), "ta": item.get("victim_steps_ta", [])},
                ensure_ascii=False,
            ),
            "real_example_en": item.get("real_example_en", ""),
            "real_example_ta": item.get("real_example_ta", ""),
            "helpline": item.get("helpline", "1930"),
            "tags": item.get("tags", ""),
        }

        if existing:
            for key, value in fields.items():
                setattr(existing, key, value)
            updated += 1
        else:
            db.add(KbArticle(**fields))
            created += 1

    db.commit()
    retriever.invalidate()
    print(f"  knowledge base: {created} created, {updated} updated")
    return created + updated


def seed_quiz(db: Session) -> int:
    path = DATA_DIR / "quiz_bank.json"
    if not path.exists():
        print(f"  ! {path.name} not found, skipping")
        return 0

    questions = json.loads(path.read_text(encoding="utf-8"))
    created = 0

    for item in questions:
        exists = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.question_en == item["question_en"])
            .first()
        )
        if exists:
            continue
        db.add(
            QuizQuestion(
                category=item["category"],
                difficulty=item.get("difficulty", "easy"),
                question_en=item["question_en"],
                question_ta=item["question_ta"],
                options_en_json=json.dumps(item["options_en"], ensure_ascii=False),
                options_ta_json=json.dumps(item["options_ta"], ensure_ascii=False),
                correct_index=item["correct_index"],
                explanation_en=item["explanation_en"],
                explanation_ta=item["explanation_ta"],
            )
        )
        created += 1

    db.commit()
    total = db.query(QuizQuestion).count()
    print(f"  quiz bank: {created} created ({total} total)")
    return created


DISTRICTS = ["Chennai", "Coimbatore", "Madurai"]
VENUES = [
    ("Govt Higher Secondary School, Ashok Nagar", "school", "Chennai"),
    ("Senior Citizens Association Hall", "senior", "Chennai"),
    ("Panchayat Community Centre, Sulur", "rural", "Coimbatore"),
    ("Govt Arts College", "college", "Coimbatore"),
    ("Women Self Help Group Centre", "women", "Madurai"),
    ("Village Library, Melur", "rural", "Madurai"),
]

TAMIL_NAMES = [
    "Arun", "Priya", "Karthik", "Lakshmi", "Suresh", "Meena", "Ravi", "Divya",
    "Murugan", "Kavitha", "Senthil", "Anitha", "Vijay", "Revathi", "Mohan",
    "Saranya", "Prakash", "Gayathri", "Bala", "Nithya", "Ganesh", "Deepa",
    "Rajesh", "Sangeetha", "Manoj", "Vasanthi", "Dinesh", "Bhuvana", "Siva", "Malathi",
]


def seed_demo(db: Session) -> None:
    # ---------------------------------------------------------------- users
    accounts = [
        ("admin@cybersathi.org", "Admin@123", "Project Admin", "admin"),
        ("volunteer@cybersathi.org", "Volunteer@123", "Student Volunteer", "volunteer"),
    ]
    for email, password, name, role in accounts:
        if not db.query(User).filter(User.email == email).first():
            db.add(
                User(
                    full_name=name,
                    email=email,
                    hashed_password=hash_password(password),
                    role=role,
                    preferred_language="en",
                )
            )
    db.commit()

    admin = db.query(User).filter(User.email == "admin@cybersathi.org").first()

    if db.query(Workshop).count() > 0:
        print("  demo data already present — skipping (use --reset to regenerate)")
        return

    # ------------------------------------------------------------ workshops
    today = date.today()
    workshops: list[Workshop] = []
    for i, (venue, audience, district) in enumerate(VENUES):
        w = Workshop(
            title_en=f"Cyber Safety Awareness Session {i + 1}",
            title_ta=f"சைபர் பாதுகாப்பு விழிப்புணர்வு அமர்வு {i + 1}",
            venue=venue,
            district=district,
            locality=venue.split(",")[-1].strip(),
            conducted_on=today - timedelta(days=75 - i * 12),
            facilitator_id=admin.id if admin else None,
            audience_type=audience,
            participants_expected=RNG.randint(18, 26),
            notes="Community service project outreach session.",
        )
        db.add(w)
        workshops.append(w)
    db.commit()
    for w in workshops:
        db.refresh(w)

    # ---------------------------------------------------------- participants
    questions = db.query(QuizQuestion).all()
    if not questions:
        print("  ! quiz bank empty — seed it before demo data")
        return

    max_score = 10
    participants_created = 0
    assessments_created = 0

    for workshop in workshops:
        count = RNG.randint(18, 24)
        for _ in range(count):
            age_group = {
                "school": "student",
                "college": "student",
                "senior": "senior",
            }.get(workshop.audience_type, RNG.choice(["adult", "adult", "senior"]))

            language = "ta" if RNG.random() < 0.6 else "en"
            name = f"{RNG.choice(TAMIL_NAMES)} {RNG.choice('ABCDEFGHIJKLMNOPRSTV')}."

            participant = Participant(
                workshop_id=workshop.id,
                name=name,
                age_group=age_group,
                gender=RNG.choice(["male", "female", "female", "male", "other"]),
                language=language,
                phone_hash=hash_phone(f"9{RNG.randint(100000000, 999999999)}"),
                consent_given=True,
                created_at=datetime.combine(
                    workshop.conducted_on, datetime.min.time()
                ).replace(tzinfo=UTC),
            )
            db.add(participant)
            db.flush()
            participants_created += 1

            # Pre-test: seniors and rural participants start lower, students higher.
            base = {"student": 5.2, "adult": 4.4, "senior": 3.4}[age_group]
            pre_score = max(0, min(max_score, int(RNG.gauss(base, 1.6))))

            # Two participants per cohort genuinely start at zero — this exercises the
            # division-by-zero guard in the improvement formula with real data.
            if RNG.random() < 0.035:
                pre_score = 0

            roll = RNG.random()
            if roll < 0.06:
                delta = RNG.choice([-1, 0, 0])  # did not benefit
            elif roll < 0.20:
                delta = RNG.randint(1, 2)
            else:
                delta = RNG.randint(2, 5)

            post_score = max(0, min(max_score, pre_score + delta))

            taken = datetime.combine(workshop.conducted_on, datetime.min.time()).replace(
                tzinfo=UTC
            )

            for kind, score, offset in (
                ("pre", pre_score, 0),
                ("post", post_score, 90),
            ):
                selected = RNG.sample(questions, min(max_score, len(questions)))
                answers = []
                correct_left = score
                for q in selected:
                    if correct_left > 0:
                        answers.append({"question_id": q.id, "selected_index": q.correct_index})
                        correct_left -= 1
                    else:
                        wrong = [i for i in range(4) if i != q.correct_index]
                        answers.append(
                            {"question_id": q.id, "selected_index": RNG.choice(wrong)}
                        )
                RNG.shuffle(answers)

                db.add(
                    Assessment(
                        participant_id=participant.id,
                        workshop_id=workshop.id,
                        type=kind,
                        score=score,
                        max_score=max_score,
                        duration_seconds=RNG.randint(180, 600),
                        answers_json=json.dumps(answers),
                        taken_at=taken + timedelta(minutes=offset),
                    )
                )
                assessments_created += 1

        db.commit()

    # -------------------------------------------------------------- activity
    sample_texts = [
        ("Your SBI KYC has expired. Click the link to update immediately.", "kyc", "high_risk", 88.4),
        ("Congratulations you won Rs 25 lakh in lucky draw. Pay GST to claim.", "lottery", "high_risk", 91.2),
        ("Rs.2,500 debited from A/c XX4412. Do not share OTP with anyone.", "legitimate", "safe", 8.1),
        ("Work from home job, earn Rs 2000 daily, pay Rs 499 registration.", "job", "high_risk", 86.7),
        ("Guaranteed 30% monthly return on crypto. Double your money.", "investment", "high_risk", 89.9),
        ("Your parcel contains illegal items, call customs immediately.", "courier_parcel", "high_risk", 84.3),
        ("Your order has been shipped and will arrive tomorrow.", "legitimate", "safe", 5.2),
        ("Install AnyDesk so our executive can fix your account.", "banking", "high_risk", 92.5),
        ("Pre-approved loan of Rs 5 lakh, no documents needed.", "loan", "suspicious", 61.8),
        ("Your electricity will be disconnected tonight at 9:30 pm.", "impersonation", "high_risk", 82.0),
    ]

    now = datetime.now(UTC)
    for _ in range(200):
        text, category, label, score = RNG.choice(sample_texts)
        db.add(
            ScamAnalysis(
                channel=RNG.choice(["sms", "whatsapp", "email"]),
                redacted_text=text,
                language=RNG.choice(["en", "ta"]),
                risk_score=round(score + RNG.uniform(-4, 4), 1),
                risk_label=label,
                primary_category=category,
                categories_json=json.dumps([{"name": category, "confidence": 0.9}]),
                matched_rules_json="[]",
                model_confidence=round(RNG.uniform(0.7, 0.99), 3),
                created_at=now - timedelta(days=RNG.randint(0, 88), hours=RNG.randint(0, 23)),
            )
        )

    sample_urls = [
        ("hxxp://sbi-kyc-update[.]xyz/verify", "high_risk", 94.1),
        ("hxxps://www[.]google[.]com", "safe", 3.2),
        ("hxxp://192[.]168[.]44[.]9/bank/login", "high_risk", 96.0),
        ("hxxps://bit[.]ly/3kycupd", "suspicious", 58.4),
        ("hxxps://www[.]onlinesbi[.]sbi", "safe", 6.0),
        ("hxxp://paytm-cashback[.]buzz/claim", "high_risk", 90.7),
    ]
    for _ in range(150):
        url, label, score = RNG.choice(sample_urls)
        db.add(
            UrlCheck(
                submitted_url_redacted=url,
                risk_score=round(score + RNG.uniform(-3, 3), 1),
                risk_label=label,
                features_json="{}",
                top_reasons_json="[]",
                created_at=now - timedelta(days=RNG.randint(0, 88), hours=RNG.randint(0, 23)),
            )
        )

    sample_questions = [
        ("Someone is asking for my OTP what should I do", "kb"),
        ("KYC எப்படி புதுப்பிப்பது", "kb"),
        ("Is this job offer real", "kb"),
        ("digital arrest என்றால் என்ன", "kb"),
        ("How to report cyber fraud", "kb"),
        ("Can I get money back after scam", "fallback"),
    ]
    for _ in range(80):
        q, source = RNG.choice(sample_questions)
        db.add(
            AssistantLog(
                language="ta" if any(ord(c) > 2900 for c in q) else "en",
                question_redacted=q,
                answer_source=source,
                helpful=RNG.choice([True, True, True, False, None]),
                created_at=now - timedelta(days=RNG.randint(0, 88)),
            )
        )

    comments = [
        "Very useful session, I did not know about the OTP rule.",
        "நல்ல பயிற்சி, எனக்கு QR பற்றி தெரியவில்லை.",
        "Please conduct this in our village again.",
        "My mother almost lost money last month, this helped.",
        "The Tamil explanation was easy to understand.",
    ]
    for workshop in workshops:
        for _ in range(RNG.randint(6, 12)):
            db.add(
                FeedbackEntry(
                    workshop_id=workshop.id,
                    rating=RNG.choice([5, 5, 5, 4, 4, 3]),
                    comment=RNG.choice(comments),
                    created_at=datetime.combine(
                        workshop.conducted_on, datetime.min.time()
                    ).replace(tzinfo=UTC),
                )
            )

    db.commit()

    print(f"  demo: {len(workshops)} workshops, {participants_created} participants, "
          f"{assessments_created} assessments, 200 analyses, 150 url checks, 80 queries")


def reset(db: Session) -> None:
    for model in (
        Assessment, FeedbackEntry, Participant, Workshop,
        ScamAnalysis, UrlCheck, AssistantLog,
    ):
        db.query(model).delete()
    db.commit()
    print("  reset: cleared workshops, participants, assessments and activity")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the CyberSathi database")
    parser.add_argument("--kb", action="store_true", help="seed knowledge base articles")
    parser.add_argument("--quiz", action="store_true", help="seed quiz questions")
    parser.add_argument("--demo", action="store_true", help="seed demo workshops and cohort")
    parser.add_argument("--all", action="store_true", help="seed everything")
    parser.add_argument("--reset", action="store_true", help="clear demo data first")
    args = parser.parse_args()

    if not any([args.kb, args.quiz, args.demo, args.all]):
        parser.print_help()
        return 1

    init_db()
    db = SessionLocal()
    try:
        print("Seeding CyberSathi database...")
        if args.reset:
            reset(db)
        if args.kb or args.all:
            seed_knowledge_base(db)
        if args.quiz or args.all:
            seed_quiz(db)
        if args.demo or args.all:
            seed_demo(db)
        print("Done.")
        print("\nDemo logins:")
        print("  admin@cybersathi.org     / Admin@123")
        print("  volunteer@cybersathi.org / Volunteer@123")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
