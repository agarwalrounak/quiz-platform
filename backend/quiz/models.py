from django.conf import settings
from django.db import models

from questions.models import Question


class AttemptStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", "In progress"
    AWAITING_REVIEW = "awaiting_review", "Awaiting review"
    GRADED = "graded", "Graded"


class Attempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="attempts", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, choices=AttemptStatus.choices, default=AttemptStatus.IN_PROGRESS
    )
    # Score is provisional while any image answers await review.
    score = models.PositiveIntegerField(null=True, blank=True)
    max_score = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attempt #{self.pk} by {self.user_id} ({self.status})"

    def recalculate(self):
        """Recompute score + status from the current answers."""
        answers = [aq.answer for aq in self.attempt_questions.all() if hasattr(aq, "answer")]
        self.score = sum(1 for a in answers if a.is_correct is True)
        has_pending = any(a.is_correct is None for a in answers)
        # Pending only matters once the attempt has been submitted.
        if self.submitted_at and has_pending:
            self.status = AttemptStatus.AWAITING_REVIEW
        elif self.submitted_at:
            self.status = AttemptStatus.GRADED
        self.save(update_fields=["score", "status"])


class AttemptQuestion(models.Model):
    """A question as served in one attempt.

    Fields are a frozen snapshot taken at attempt-creation time so that later
    edits/deletes to the live Question never alter a historical attempt.
    """

    attempt = models.ForeignKey(
        Attempt, related_name="attempt_questions", on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question, null=True, blank=True, on_delete=models.SET_NULL
    )
    order = models.PositiveIntegerField(default=0)

    # --- Snapshot ---
    type = models.CharField(max_length=12)
    prompt = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    difficulty = models.CharField(max_length=4, blank=True)
    accepted_text = models.CharField(max_length=255, blank=True)
    numeric_answer = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    image_requirement = models.TextField(blank=True)
    # List of {id, text, is_correct, order}
    choices = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("attempt", "order")

    @property
    def correct_choice_ids(self):
        return [c["id"] for c in self.choices if c.get("is_correct")]


def attempt_image_path(instance, filename):
    return f"attempts/{instance.attempt_question.attempt_id}/{instance.attempt_question_id}_{filename}"


class Answer(models.Model):
    attempt_question = models.OneToOneField(
        AttemptQuestion, related_name="answer", on_delete=models.CASCADE
    )
    # Per-type payloads (only the relevant one is populated).
    text_value = models.TextField(blank=True)
    numeric_value = models.DecimalField(
        max_digits=20, decimal_places=6, null=True, blank=True
    )
    selected_choice_ids = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to=attempt_image_path, null=True, blank=True)

    # None = not yet graded (pending manual review for image questions).
    is_correct = models.BooleanField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_answers",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
