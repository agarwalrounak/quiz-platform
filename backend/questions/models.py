from django.conf import settings
from django.db import models


class QuestionType(models.TextChoices):
    TEXT = "text", "Text (free response)"
    SINGLE = "single", "Single choice"
    MULTIPLE = "multiple", "Multiple choice"
    NUMERICAL = "numerical", "Numerical input"
    IMAGE = "image", "Image upload"


class Difficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "med", "Medium"
    HARD = "hard", "Hard"


# Types that are graded automatically vs. require manual review.
AUTO_GRADED_TYPES = {
    QuestionType.TEXT,
    QuestionType.SINGLE,
    QuestionType.MULTIPLE,
    QuestionType.NUMERICAL,
}
MANUAL_TYPES = {QuestionType.IMAGE}
CHOICE_TYPES = {QuestionType.SINGLE, QuestionType.MULTIPLE}


class Question(models.Model):
    type = models.CharField(max_length=12, choices=QuestionType.choices)
    prompt = models.TextField()
    category = models.CharField(max_length=80, blank=True, db_index=True)
    difficulty = models.CharField(
        max_length=4, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    is_active = models.BooleanField(
        default=True, help_text="Inactive questions are excluded from the quiz pool."
    )

    # Type-specific answer fields (only the one matching `type` is used).
    accepted_text = models.CharField(
        max_length=255, blank=True, help_text="Accepted answer for text questions."
    )
    numeric_answer = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True,
        help_text="Correct value for numerical questions.",
    )
    image_requirement = models.TextField(
        blank=True, help_text="What the uploaded image must show (for reviewers)."
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="questions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_type_display()}] {self.prompt[:50]}"


class Choice(models.Model):
    question = models.ForeignKey(
        Question, related_name="choices", on_delete=models.CASCADE
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text
