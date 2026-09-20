"""Test fixtures. Each run gets its own throwaway SQLite file, never the dev database."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from app.config import DATA_DIR
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import KbArticle, QuizQuestion, User
from app.nlp import retriever


@pytest.fixture(scope="session")
def engine(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    eng = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def seeded(session_factory):
    """Load the real knowledge base and quiz bank so retrieval tests are meaningful."""
    db = session_factory()
    try:
        articles = json.loads((DATA_DIR / "knowledge_base.json").read_text(encoding="utf-8"))
        for item in articles:
            db.add(
                KbArticle(
                    slug=item["slug"],
                    category=item["category"],
                    severity=item.get("severity", "high"),
                    title_en=item["title_en"],
                    title_ta=item["title_ta"],
                    summary_en=item["summary_en"],
                    summary_ta=item["summary_ta"],
                    body_en=item["body_en"],
                    body_ta=item["body_ta"],
                    red_flags_json=json.dumps(
                        {"en": item.get("red_flags_en", []), "ta": item.get("red_flags_ta", [])},
                        ensure_ascii=False,
                    ),
                    safe_actions_json=json.dumps(
                        {"en": item.get("safe_actions_en", []), "ta": item.get("safe_actions_ta", [])},
                        ensure_ascii=False,
                    ),
                    victim_steps_json=json.dumps(
                        {"en": item.get("victim_steps_en", []), "ta": item.get("victim_steps_ta", [])},
                        ensure_ascii=False,
                    ),
                    real_example_en=item.get("real_example_en", ""),
                    real_example_ta=item.get("real_example_ta", ""),
                    helpline=item.get("helpline", "1930"),
                    tags=item.get("tags", ""),
                )
            )

        questions = json.loads((DATA_DIR / "quiz_bank.json").read_text(encoding="utf-8"))
        for item in questions:
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
        db.commit()
    finally:
        db.close()

    retriever.invalidate()
    yield
    retriever.invalidate()


@pytest.fixture
def db(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers(client, session_factory):
    db = session_factory()
    admin = db.query(User).filter(User.email == "testadmin@cybersathi.org").first()
    if not admin:
        db.add(User(
            full_name="Test Admin", email="testadmin@cybersathi.org",
            hashed_password=hash_password("TestPass@123"), role="admin",
            preferred_language="en",
        ))
        db.commit()
    db.close()
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testadmin@cybersathi.org", "password": "TestPass@123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
