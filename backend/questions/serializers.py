from rest_framework import serializers

from .models import CHOICE_TYPES, Choice, Question, QuestionType


class ChoiceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Choice
        fields = ("id", "text", "is_correct", "order")


class ChoicePublicSerializer(serializers.ModelSerializer):
    """Choices as seen by a quiz player — correctness is hidden."""

    class Meta:
        model = Choice
        fields = ("id", "text", "order")


class QuestionSerializer(serializers.ModelSerializer):
    """Admin-facing serializer: full read/write incl. correct answers."""

    choices = ChoiceSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = (
            "id",
            "type",
            "prompt",
            "category",
            "difficulty",
            "is_active",
            "accepted_text",
            "numeric_answer",
            "image_requirement",
            "choices",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        # Resolve effective type/choices (supports partial updates).
        qtype = attrs.get("type", getattr(self.instance, "type", None))
        choices = attrs.get(
            "choices",
            None
            if self.instance is None
            else list(self.instance.choices.values("is_correct")),
        )

        errors = {}

        if qtype in CHOICE_TYPES:
            choices = choices or []
            if len(choices) < 2:
                errors["choices"] = "Provide at least two choices."
            else:
                correct = sum(1 for c in choices if c.get("is_correct"))
                if qtype == QuestionType.SINGLE and correct != 1:
                    errors["choices"] = "Single choice must have exactly one correct option."
                if qtype == QuestionType.MULTIPLE and correct < 1:
                    errors["choices"] = "Multiple choice must have at least one correct option."
        elif qtype == QuestionType.TEXT:
            if not (attrs.get("accepted_text") or getattr(self.instance, "accepted_text", "")):
                errors["accepted_text"] = "An accepted answer is required for text questions."
        elif qtype == QuestionType.NUMERICAL:
            has_value = attrs.get("numeric_answer") is not None or (
                self.instance and self.instance.numeric_answer is not None
            )
            if not has_value:
                errors["numeric_answer"] = "A correct value is required for numerical questions."
        elif qtype == QuestionType.IMAGE:
            if not (
                attrs.get("image_requirement")
                or getattr(self.instance, "image_requirement", "")
            ):
                errors["image_requirement"] = (
                    "Describe what the uploaded image must show."
                )

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        choices = validated_data.pop("choices", [])
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        question = Question.objects.create(**validated_data)
        self._sync_choices(question, choices)
        return question

    def update(self, instance, validated_data):
        choices = validated_data.pop("choices", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if choices is not None:
            instance.choices.all().delete()
            self._sync_choices(instance, choices)
        return instance

    @staticmethod
    def _sync_choices(question, choices):
        for idx, choice in enumerate(choices):
            Choice.objects.create(
                question=question,
                text=choice["text"],
                is_correct=choice.get("is_correct", False),
                order=choice.get("order", idx),
            )


class QuestionPublicSerializer(serializers.ModelSerializer):
    """Player-facing serializer: never leaks correct answers."""

    choices = ChoicePublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = (
            "id",
            "type",
            "prompt",
            "category",
            "difficulty",
            "image_requirement",
            "choices",
        )
        read_only_fields = fields
