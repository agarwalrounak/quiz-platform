"""Idempotent seed for the question bank + demo users.

Run:  python manage.py seed_questions
Re-running is safe — questions are keyed on their prompt, users on username.

Covers all five question types with a spread of categories and difficulties
(24 questions total, comfortably above the 20-question / quiz-length requirement).
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from questions.models import Choice, Question

User = get_user_model()

# Demo accounts (documented in the README).
DEMO_USERS = [
    {"username": "admin", "password": "adminpass123", "email": "admin@example.com", "admin": True},
    {"username": "player1", "password": "s3cretpass99", "email": "player1@example.com", "admin": False},
]

# Each entry: type, prompt, category, difficulty, + type-specific answer data.
QUESTIONS = [
    # --- Single choice ---
    {"type": "single", "category": "geography", "difficulty": "easy",
     "prompt": "What is the capital of France?",
     "choices": [("Paris", True), ("Lyon", False), ("Marseille", False), ("Nice", False)]},
    {"type": "single", "category": "science", "difficulty": "easy",
     "prompt": "Which planet is known as the Red Planet?",
     "choices": [("Venus", False), ("Mars", True), ("Jupiter", False), ("Saturn", False)]},
    {"type": "single", "category": "history", "difficulty": "med",
     "prompt": "In which year did World War II end?",
     "choices": [("1943", False), ("1945", True), ("1948", False), ("1950", False)]},
    {"type": "single", "category": "literature", "difficulty": "med",
     "prompt": "Who wrote 'Romeo and Juliet'?",
     "choices": [("Charles Dickens", False), ("William Shakespeare", True),
                 ("Jane Austen", False), ("Mark Twain", False)]},
    {"type": "single", "category": "science", "difficulty": "hard",
     "prompt": "What is the chemical symbol for gold?",
     "choices": [("Go", False), ("Gd", False), ("Au", True), ("Ag", False)]},
    {"type": "single", "category": "technology", "difficulty": "easy",
     "prompt": "What does 'CPU' stand for?",
     "choices": [("Central Processing Unit", True), ("Computer Personal Unit", False),
                 ("Central Print Unit", False), ("Core Processing Utility", False)]},

    # --- Multiple choice ---
    {"type": "multiple", "category": "geography", "difficulty": "med",
     "prompt": "Which of the following are continents?",
     "choices": [("Africa", True), ("Greenland", False), ("Asia", True),
                 ("Australia", True), ("Madagascar", False)]},
    {"type": "multiple", "category": "science", "difficulty": "med",
     "prompt": "Which of these are noble gases?",
     "choices": [("Helium", True), ("Oxygen", False), ("Neon", True),
                 ("Argon", True), ("Nitrogen", False)]},
    {"type": "multiple", "category": "technology", "difficulty": "hard",
     "prompt": "Which of the following are programming languages?",
     "choices": [("Python", True), ("HTML", False), ("Java", True),
                 ("Rust", True), ("HTTP", False)]},
    {"type": "multiple", "category": "math", "difficulty": "easy",
     "prompt": "Which of these numbers are prime?",
     "choices": [("2", True), ("9", False), ("7", True), ("15", False), ("11", True)]},
    {"type": "multiple", "category": "history", "difficulty": "hard",
     "prompt": "Which of these were ancient civilizations?",
     "choices": [("Mesopotamia", True), ("Atlantis", False), ("Indus Valley", True),
                 ("Roman Empire", True), ("El Dorado", False)]},

    # --- Numerical input ---
    {"type": "numerical", "category": "math", "difficulty": "easy",
     "prompt": "What is 7 multiplied by 8?", "numeric_answer": "56"},
    {"type": "numerical", "category": "math", "difficulty": "med",
     "prompt": "What is the square root of 144?", "numeric_answer": "12"},
    {"type": "numerical", "category": "science", "difficulty": "med",
     "prompt": "At what temperature (in °C) does water boil at sea level?",
     "numeric_answer": "100"},
    {"type": "numerical", "category": "math", "difficulty": "hard",
     "prompt": "How many degrees are in the interior angles of a triangle (sum)?",
     "numeric_answer": "180"},
    {"type": "numerical", "category": "general", "difficulty": "easy",
     "prompt": "How many sides does a hexagon have?", "numeric_answer": "6"},

    # --- Text (free response) ---
    {"type": "text", "category": "geography", "difficulty": "easy",
     "prompt": "What is the largest ocean on Earth? (one word)",
     "accepted_text": "Pacific"},
    {"type": "text", "category": "science", "difficulty": "med",
     "prompt": "What gas do plants primarily absorb during photosynthesis? (one word)",
     "accepted_text": "carbon dioxide"},
    {"type": "text", "category": "literature", "difficulty": "hard",
     "prompt": "Who is the author of 'The Origin of Species'? (surname)",
     "accepted_text": "Darwin"},
    {"type": "text", "category": "technology", "difficulty": "med",
     "prompt": "What does the acronym 'API' stand for? (expanded form)",
     "accepted_text": "Application Programming Interface"},

    # --- Image upload (manually reviewed) ---
    {"type": "image", "category": "art", "difficulty": "easy",
     "prompt": "Upload a photo of a hand-drawn smiley face.",
     "image_requirement": "Image clearly shows a hand-drawn smiley face."},
    {"type": "image", "category": "science", "difficulty": "med",
     "prompt": "Upload a labelled diagram of the water cycle.",
     "image_requirement": "Diagram shows evaporation, condensation, and precipitation, labelled."},
    {"type": "image", "category": "math", "difficulty": "hard",
     "prompt": "Upload a photo of your handwritten proof that the angles of a triangle sum to 180°.",
     "image_requirement": "Legible handwritten geometric proof reaching the 180° conclusion."},
    {"type": "image", "category": "general", "difficulty": "easy",
     "prompt": "Upload a photo of a red object.",
     "image_requirement": "Photo prominently features a predominantly red object."},
]


class Command(BaseCommand):
    help = "Seed the question bank with demo users and 20+ questions (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        admin_user = self._seed_users()
        created, skipped = self._seed_questions(admin_user)

        total = Question.objects.count()
        by_type = {
            t: Question.objects.filter(type=t).count()
            for t in ("text", "single", "multiple", "numerical", "image")
        }
        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {created} created, {skipped} already existed. "
            f"Bank now holds {total} questions."
        ))
        self.stdout.write(f"By type: {by_type}")

    def _seed_users(self):
        admin_user = None
        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={"email": spec["email"]},
            )
            if created:
                user.set_password(spec["password"])
            if spec["admin"]:
                user.role = "admin"
                user.is_staff = True
                user.is_superuser = True
                admin_user = user
            user.save()
            self.stdout.write(
                f"{'Created' if created else 'Found'} user "
                f"'{spec['username']}' ({'admin' if spec['admin'] else 'user'})"
            )
        return admin_user or User.objects.filter(role="admin").first()

    def _seed_questions(self, created_by):
        created = skipped = 0
        for spec in QUESTIONS:
            question, was_created = Question.objects.get_or_create(
                prompt=spec["prompt"],
                defaults={
                    "type": spec["type"],
                    "category": spec.get("category", ""),
                    "difficulty": spec.get("difficulty", "med"),
                    "accepted_text": spec.get("accepted_text", ""),
                    "numeric_answer": spec.get("numeric_answer"),
                    "image_requirement": spec.get("image_requirement", ""),
                    "created_by": created_by,
                    "is_active": True,
                },
            )
            if not was_created:
                skipped += 1
                continue
            created += 1
            for order, (text, is_correct) in enumerate(spec.get("choices", [])):
                Choice.objects.create(
                    question=question, text=text, is_correct=is_correct, order=order
                )
        return created, skipped
