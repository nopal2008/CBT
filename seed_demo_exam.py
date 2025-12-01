"""
Seed a demo exam with questions and choices.

Usage:
    python seed_demo_exam.py

Time references use Asia/Jakarta to avoid timestamp offset issues.
"""

import os
from datetime import datetime, timedelta
try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    # Older Python uses backport (already in requirements)
    from backports.zoneinfo import ZoneInfo

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbt_system.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402

from exam.models import Choice, CustomUser, Department, Exam, Question, Subject  # noqa: E402


def ensure_user(username: str, user_type: str, email: str) -> CustomUser:
    user, created = get_user_model().objects.get_or_create(
        username=username,
        defaults={"email": email, "user_type": user_type, "is_active": True},
    )
    if created or not user.has_usable_password():
        user.set_password("demo1234")
        user.user_type = user_type
        user.email = email
        user.is_active = True
        user.save()
    return user


def main():
    jakarta = ZoneInfo("Asia/Jakarta")
    now_jakarta = datetime.now(jakarta)

    # Base reference times
    start_time = now_jakarta - timedelta(minutes=5)
    end_time = start_time + timedelta(minutes=30)
    result_publish_time = end_time + timedelta(minutes=5)

    # Minimal taxonomy
    department, _ = Department.objects.get_or_create(
        code="INF", defaults={"name": "Informatics", "description": "Demo Department"}
    )
    subject, _ = Subject.objects.get_or_create(
        code="PY101",
        defaults={
            "name": "Python 101",
            "description": "Introductory Python exam (demo)",
            "department": department,
        },
    )

    # Users
    teacher = ensure_user("teacher_demo", "teacher", "teacher_demo@example.com")
    teacher.is_staff = True
    teacher.save(update_fields=["is_staff"])
    student = ensure_user("student_demo", "student", "student_demo@example.com")
    student.department = department
    student.save(update_fields=["department"])

    # Exam
    exam, _ = Exam.objects.get_or_create(
        title="Python For Machine Learning (Demo)",
        defaults={
            "description": "Sample CBT exam with multiple-choice questions.",
            "duration_minutes": 30,
            "start_time": start_time,
            "end_time": end_time,
            "result_publish_time": result_publish_time,
            "created_by": teacher,
            "subject": subject,
            "exam_type": "quiz",
            "status": "published",
            "passing_score": 60,
            "max_attempts": 2,
            "shuffle_questions": True,
            "shuffle_choices": True,
            "allow_back_navigation": True,
            "show_result_immediately": True,
        },
    )

    # If exam already existed, refresh its timing to Jakarta refs
    exam.start_time = start_time
    exam.end_time = end_time
    exam.result_publish_time = result_publish_time
    exam.status = "published"
    exam.is_active = True
    exam.subject = subject
    exam.created_by = teacher
    exam.save()

    # Clear existing questions for this demo exam to keep data clean
    exam.questions.all().delete()

    question_payloads = [
        {
            "text": "Apa output dari `print(type([]))` di Python?",
            "options": [
                ("<class 'list'>", True),
                ("<class 'tuple'>", False),
                ("<class 'set'>", False),
                ("<class 'dict'>", False),
            ],
        },
        {
            "text": "Library mana yang umum dipakai untuk manipulasi data tabular di Python?",
            "options": [
                ("matplotlib", False),
                ("numpy", False),
                ("pandas", True),
                ("seaborn", False),
            ],
        },
        {
            "text": "Metode mana yang dipakai untuk melatih model scikit-learn?",
            "options": [
                ("model.predict(X)", False),
                ("model.fit(X, y)", True),
                ("model.transform(X)", False),
                ("model.describe()", False),
            ],
        },
        {
            "text": "Fungsi apa untuk membuat array NumPy berisi nol dengan shape (2, 3)?",
            "options": [
                ("np.zeros((2, 3))", True),
                ("np.ones((2, 3))", False),
                ("np.empty((2, 3))", False),
                ("np.arange(6)", False),
            ],
        },
        {
            "text": "Dalam pandas, atribut apa untuk menampilkan 5 baris teratas DataFrame?",
            "options": [
                ("df.describe()", False),
                ("df.head()", True),
                ("df.sample()", False),
                ("df.tail()", False),
            ],
        },
    ]

    for idx, payload in enumerate(question_payloads, start=1):
        question = Question.objects.create(
            exam=exam,
            question_type="MC",
            text=payload["text"],
            points=1,
            difficulty="easy",
            created_by=teacher,
            is_active=True,
        )
        for order, (choice_text, is_correct) in enumerate(payload["options"], start=1):
            Choice.objects.create(
                question=question,
                text=choice_text,
                is_correct=is_correct,
                order=order,
            )

    # Final log
    print("Seeded exam:")
    print(f"  Title: {exam.title}")
    print(f"  Start (Jakarta): {start_time}")
    print(f"  End   (Jakarta): {end_time}")
    print(f"  Questions: {exam.questions.count()}")
    print("Users:")
    print("  Teacher username: teacher_demo / password: demo1234")
    print("  Student username: student_demo / password: demo1234")


if __name__ == "__main__":
    main()
