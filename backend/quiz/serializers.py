from rest_framework import serializers

from .models import Answer, Attempt, AttemptQuestion


class AttemptQuestionPublicSerializer(serializers.ModelSerializer):
    """Player-facing view of a served question — never leaks correct answers."""

    choices = serializers.SerializerMethodField()

    class Meta:
        model = AttemptQuestion
        fields = (
            "id",
            "order",
            "type",
            "prompt",
            "category",
            "difficulty",
            "image_requirement",
            "choices",
        )

    def get_choices(self, obj):
        # Strip is_correct from the snapshot.
        return [
            {"id": c["id"], "text": c["text"], "order": c.get("order", 0)}
            for c in obj.choices
        ]


class AttemptSerializer(serializers.ModelSerializer):
    """Summary of an attempt (list + create response)."""

    questions = AttemptQuestionPublicSerializer(
        source="attempt_questions", many=True, read_only=True
    )

    class Meta:
        model = Attempt
        fields = (
            "id",
            "status",
            "score",
            "max_score",
            "created_at",
            "submitted_at",
            "questions",
        )
        read_only_fields = fields


class AttemptListSerializer(serializers.ModelSerializer):
    """Lightweight attempt summary for the history list (no questions)."""

    class Meta:
        model = Attempt
        fields = ("id", "status", "score", "max_score", "created_at", "submitted_at")
        read_only_fields = fields


class AttemptReviewSerializer(serializers.ModelSerializer):
    """Detailed view of a *submitted* attempt: prompt, the user's answer, the
    correct answer(s), and per-question correctness. Only used after submission,
    so revealing correct answers here is safe.
    """

    questions = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = (
            "id",
            "status",
            "score",
            "max_score",
            "created_at",
            "submitted_at",
            "questions",
        )
        read_only_fields = fields

    def _image_url(self, answer):
        if not (answer and answer.image):
            return None
        request = self.context.get("request")
        url = answer.image.url
        return request.build_absolute_uri(url) if request else url

    def get_questions(self, obj):
        out = []
        for aq in obj.attempt_questions.all():
            answer = getattr(aq, "answer", None)
            selected = set(answer.selected_choice_ids) if answer else set()

            # Per-type rendering of the user's answer and the correct answer.
            if aq.type in ("single", "multiple"):
                user_answer = [c["text"] for c in aq.choices if c["id"] in selected]
                correct_answer = [c["text"] for c in aq.choices if c.get("is_correct")]
                choices = [
                    {
                        "id": c["id"],
                        "text": c["text"],
                        "is_correct": c.get("is_correct", False),
                        "selected": c["id"] in selected,
                    }
                    for c in aq.choices
                ]
            elif aq.type == "numerical":
                user_answer = str(answer.numeric_value) if answer and answer.numeric_value is not None else None
                correct_answer = str(aq.numeric_answer) if aq.numeric_answer is not None else None
                choices = []
            elif aq.type == "text":
                user_answer = answer.text_value if answer else None
                correct_answer = aq.accepted_text
                choices = []
            elif aq.type == "image":
                user_answer = self._image_url(answer)
                correct_answer = aq.image_requirement  # the requirement reviewers grade against
                choices = []
            else:
                user_answer = correct_answer = None
                choices = []

            out.append({
                "id": aq.id,
                "order": aq.order,
                "type": aq.type,
                "prompt": aq.prompt,
                "category": aq.category,
                "difficulty": aq.difficulty,
                "is_correct": answer.is_correct if answer else None,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "choices": choices,
            })
        return out


class ReviewItemSerializer(serializers.ModelSerializer):
    """A pending image submission awaiting admin review."""

    attempt_id = serializers.IntegerField(source="attempt_question.attempt_id", read_only=True)
    user = serializers.CharField(source="attempt_question.attempt.user.username", read_only=True)
    prompt = serializers.CharField(source="attempt_question.prompt", read_only=True)
    image_requirement = serializers.CharField(
        source="attempt_question.image_requirement", read_only=True
    )
    category = serializers.CharField(source="attempt_question.category", read_only=True)
    difficulty = serializers.CharField(source="attempt_question.difficulty", read_only=True)
    image = serializers.SerializerMethodField()
    submitted_at = serializers.DateTimeField(
        source="attempt_question.attempt.submitted_at", read_only=True
    )

    class Meta:
        model = Answer
        fields = (
            "id",
            "attempt_id",
            "user",
            "prompt",
            "image_requirement",
            "category",
            "difficulty",
            "image",
            "submitted_at",
        )
        read_only_fields = fields

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url
