# test_demo_users.py — demo.env parsing and seeding (users come from demo.env; no admin UI yet).

from pathlib import Path

import pytest

from app.db import demo_users

REPO_ROOT = Path(__file__).resolve().parents[2]

SAMPLE = """
# comment lines and blanks are ignored
TEACHER_1=t1@x.org|Pass@1|Prof. One|Computer Science

TA_1=ta@x.org|Ta@1|TA One|Computer Science
TA_2=ta@x.org|Ta@1|TA One|Physics
STUDENT_1=CS001|S@1|Asha Rao|Computer Science;Physics
STUDENTS_1=Physics|PH|3|S@2
STUDENTS_2=Computer Science|CS|2|S@3
"""


# Why: every role must be read with the right fields from the one config file the user maintains
def test_parse_reads_all_roles():
    d = demo_users.parse_demo_env(SAMPLE)
    assert d["teachers"] == [{"email": "t1@x.org", "password": "Pass@1", "name": "Prof. One",
                              "subject": "Computer Science"}]
    assert [t["email"] for t in d["tas"]] == ["ta@x.org"]
    assert {s["roll_no"] for s in d["students"]} >= {"CS001", "PH001", "PH002", "PH003", "CS002"}


# Why: a TA listed for two subjects is one account that sees both subjects
def test_parse_merges_ta_subjects():
    ta = demo_users.parse_demo_env(SAMPLE)["tas"][0]
    assert ta["subjects"] == ["Computer Science", "Physics"]


# Why: STUDENTS_n generates roll numbers; a roll listed twice is one student enrolled in both subjects
def test_parse_generates_and_merges_students():
    st = {s["roll_no"]: s for s in demo_users.parse_demo_env(SAMPLE)["students"]}
    assert st["PH002"]["subjects"] == ["Physics"] and st["PH002"]["password"] == "S@2"
    assert st["CS001"]["subjects"] == ["Computer Science", "Physics"]   # explicit + generated CS001
    assert st["CS001"]["name"] == "Asha Rao"                              # explicit name wins


# Why: a typo in demo.env must fail loudly with the line's key, not silently drop users
@pytest.mark.parametrize("line", ["TEACHER_1=only|three|fields", "STUDENTS_1=Physics|PH|lots|pw",
                                  "STUDENTS_1=Physics|PH|0|pw", "WHO_1=a|b|c|d"])
def test_parse_rejects_bad_lines(line):
    with pytest.raises(ValueError, match=line.split("=")[0]):
        demo_users.parse_demo_env(line)


# Why: the shipped demo.env must follow the user's rules (teachers with a subject, TAs per subject,
# 10–50 students per subject)
def test_repo_demo_env_follows_the_rules():
    d = demo_users.parse_demo_env((REPO_ROOT / "demo.env").read_text())
    subjects = {t["subject"] for t in d["teachers"]}
    assert subjects
    for subj in subjects:
        assert any(subj in ta["subjects"] for ta in d["tas"]), f"no TA for {subj}"
        n = sum(subj in s["subjects"] for s in d["students"])
        assert 10 <= n <= 50, f"{subj}: {n} students"


# Why: seeding runs at every start-up, so it must create each user once and keep roles/subjects right
@pytest.mark.asyncio
async def test_seed_is_idempotent(db):
    from app.db.seed import seed_users
    await seed_users()
    await seed_users()
    users = db["users"]
    assert await users.count_documents({"role": "teacher"}) == 2
    assert await users.count_documents({"role": "ta"}) == 2
    assert await users.count_documents({"role": "student"}) == 3
    ta = await users.find_one({"email": "ta.cs@evalify.local"})
    assert ta["subjects"] == ["Computer Science"] and ta["password_hash"].startswith("$2")
