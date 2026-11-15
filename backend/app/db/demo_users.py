# demo_users.py — read the demo user list (teachers, TAs, students) from demo.env.
#
# There is no admin UI for users yet (user decision, 15 Nov): teachers with their subject, the TAs of each
# subject and the enrolled demo students all come from one file. Format, one entry per line:
#   TEACHER_<n>=<email>|<password>|<name>|<subject>
#   TA_<n>=<email>|<password>|<name>|<subject>[;<subject>…]        (same email again = one TA, more subjects)
#   STUDENT_<n>=<roll no>|<password>|<name>|<subject>[;<subject>…]
#   STUDENTS_<n>=<subject>|<roll prefix>|<count>|<password>         (generates <prefix>001 … with demo names)
# Blank lines and lines starting with # are ignored.

from __future__ import annotations

import re
from typing import Dict, List

# Names for generated demo students (cycled when a subject has more students than names)
DEMO_NAMES = [
    "Aarav Sharma", "Priya Patel", "Rohit Verma", "Ananya Singh", "Vikram Nair", "Sneha Reddy", "Arjun Mehta",
    "Kavya Iyer", "Rahul Gupta", "Diya Kapoor", "Karan Malhotra", "Isha Joshi", "Aditya Rao", "Meera Pillai",
    "Siddharth Das", "Pooja Kulkarni", "Nikhil Bansal", "Riya Chatterjee", "Varun Saxena", "Tanvi Desai",
    "Harsh Agarwal", "Neha Mishra", "Yash Thakur", "Simran Kaur", "Manav Shah", "Aditi Banerjee", "Kunal Jain",
    "Shreya Menon", "Dev Choudhary", "Nisha Yadav", "Abhinav Tiwari", "Ritika Sinha", "Om Prakash", "Lavanya Krishnan",
    "Pranav Hegde", "Swati Pandey", "Rohan Bhatt", "Anjali Dubey", "Gaurav Chauhan", "Divya Nambiar", "Sameer Khan",
    "Pallavi Ghosh", "Akash Pandit", "Bhavna Rawat", "Tarun Sethi", "Zoya Ahmed", "Mohit Arora", "Charu Vohra",
    "Ishaan Kohli", "Prerna Bhatia",
]


def _fields(key: str, value: str, n: int) -> List[str]:
    """Split 'a|b|c|d' into exactly n trimmed, non-empty fields, or fail naming the key."""
    parts = [p.strip() for p in value.split("|")]
    if len(parts) != n or not all(parts):
        raise ValueError(f"{key}: expected {n} fields separated by '|', got {value!r}")
    return parts


def _subjects(s: str) -> List[str]:
    """'Physics; Chemistry' → ['Physics', 'Chemistry']."""
    return [x.strip() for x in s.split(";") if x.strip()]


def _add_student(students: Dict[str, dict], roll: str, password: str, name: str, subjects: List[str],
                 explicit: bool) -> None:
    """Insert or merge a student; an explicit STUDENT_n line wins over a generated name/password."""
    s = students.get(roll)
    if s is None:
        students[roll] = {"roll_no": roll, "password": password, "name": name, "subjects": list(subjects),
                          "_explicit": explicit}
        return
    if explicit and not s["_explicit"]:
        s.update(password=password, name=name, _explicit=True)
    s["subjects"] += [x for x in subjects if x not in s["subjects"]]


def parse_demo_env(text: str) -> dict:
    """demo.env text → {"teachers": [...], "tas": [...], "students": [...]} (raises ValueError on a bad line)."""
    teachers: Dict[str, dict] = {}
    tas: Dict[str, dict] = {}
    students: Dict[str, dict] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        kind = re.sub(r"_\d+$", "", key)
        if kind == "TEACHER":
            email, pw, name, subject = _fields(key, value, 4)
            teachers[email] = {"email": email, "password": pw, "name": name, "subject": subject}
        elif kind == "TA":
            email, pw, name, subj = _fields(key, value, 4)
            ta = tas.setdefault(email, {"email": email, "password": pw, "name": name, "subjects": []})
            ta["subjects"] += [x for x in _subjects(subj) if x not in ta["subjects"]]
        elif kind == "STUDENT":
            roll, pw, name, subj = _fields(key, value, 4)
            _add_student(students, roll, pw, name, _subjects(subj), explicit=True)
        elif kind == "STUDENTS":
            subject, prefix, count, pw = _fields(key, value, 4)
            if not count.isdigit() or not 1 <= int(count) <= 200:
                raise ValueError(f"{key}: count must be a number from 1 to 200, got {count!r}")
            for i in range(1, int(count) + 1):
                _add_student(students, f"{prefix}{i:03d}", pw, DEMO_NAMES[(i - 1) % len(DEMO_NAMES)], [subject],
                             explicit=False)
        else:
            raise ValueError(f"{key}: unknown entry (use TEACHER_n, TA_n, STUDENT_n or STUDENTS_n)")
    for s in students.values():
        s.pop("_explicit")
    return {"teachers": list(teachers.values()), "tas": list(tas.values()), "students": list(students.values())}
