import json

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole, IsOwner
from questions.models import Question

from .grading import grade_answer
from .models import Answer, Attempt, AttemptQuestion, AttemptStatus
from .serializers import (
    AttemptListSerializer,
    AttemptReviewSerializer,
    AttemptSerializer,
    ReviewItemSerializer,
)


class AttemptViewSet(viewsets.ModelViewSet):
    """Create attempts, list one's own history, submit answers."""

    permission_classes = [IsAuthenticated, IsOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        # Admins see all; users see only their own.
        qs = Attempt.objects.prefetch_related("attempt_questions__answer")
        if getattr(self.request.user, "is_admin_role", False):
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        return AttemptListSerializer if self.action == "list" else AttemptSerializer

    def retrieve(self, request, *args, **kwargs):
        attempt = self.get_object()
        # Once submitted, reveal answers + correctness for review; while in
        # progress, fall back to the player view (answers hidden).
        serializer_cls = (
            AttemptReviewSerializer if attempt.submitted_at else AttemptSerializer
        )
        return Response(serializer_cls(attempt, context={"request": request}).data)

    def _snapshot(self, attempt, question, order):
        return AttemptQuestion(
            attempt=attempt,
            question=question,
            order=order,
            type=question.type,
            prompt=question.prompt,
            category=question.category,
            difficulty=question.difficulty,
            accepted_text=question.accepted_text,
            numeric_answer=question.numeric_answer,
            image_requirement=question.image_requirement,
            choices=[
                {
                    "id": c.id,
                    "text": c.text,
                    "is_correct": c.is_correct,
                    "order": c.order,
                }
                for c in question.choices.all()
            ],
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        n = getattr(settings, "QUIZ_LENGTH", 10)
        # Random sample without replacement from the active pool.
        pool = list(
            Question.objects.filter(is_active=True)
            .prefetch_related("choices")
            .order_by("?")[:n]
        )
        if not pool:
            return Response(
                {"detail": "No active questions are available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt = Attempt.objects.create(user=request.user, max_score=len(pool))
        AttemptQuestion.objects.bulk_create(
            [self._snapshot(attempt, q, i) for i, q in enumerate(pool)]
        )

        notice = None
        if len(pool) < n:
            notice = f"Only {len(pool)} active questions available (requested {n})."

        data = AttemptSerializer(attempt).data
        if notice:
            data["notice"] = notice
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def submit(self, request, pk=None):
        attempt = self.get_object()
        if attempt.submitted_at is not None:
            return Response(
                {"detail": "This attempt has already been submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answers_in = self._parse_answers(request)
        aq_by_id = {aq.id: aq for aq in attempt.attempt_questions.all()}

        for entry in answers_in:
            aq = aq_by_id.get(entry.get("attempt_question"))
            if aq is None:
                continue
            answer = Answer(attempt_question=aq)
            if aq.type == "text":
                answer.text_value = entry.get("text_value", "") or ""
            elif aq.type == "numerical":
                answer.numeric_value = entry.get("numeric_value") or None
            elif aq.type in ("single", "multiple"):
                ids = entry.get("selected_choice_ids", []) or []
                answer.selected_choice_ids = [int(i) for i in ids]
            elif aq.type == "image":
                f = request.FILES.get(f"image_{aq.id}")
                if f:
                    answer.image = f
            answer.is_correct = grade_answer(aq, answer)
            answer.save()

        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["submitted_at"])
        attempt.recalculate()
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_200_OK)

    @staticmethod
    def _parse_answers(request):
        raw = request.data.get("answers")
        if raw is None:
            return []
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return []
        return raw


class ReviewQueueView(generics.ListAPIView):
    """Admin: list image answers from submitted attempts awaiting a verdict."""

    serializer_class = ReviewItemSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        return (
            Answer.objects.select_related(
                "attempt_question__attempt__user"
            )
            .filter(
                attempt_question__type="image",
                is_correct__isnull=True,
                attempt_question__attempt__submitted_at__isnull=False,
            )
            .order_by("attempt_question__attempt__submitted_at")
        )


class ReviewVerdictView(APIView):
    """Admin: mark a pending image answer correct/incorrect, then finalize the
    parent attempt's score and status."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    @transaction.atomic
    def post(self, request, pk=None):
        try:
            answer = Answer.objects.select_related(
                "attempt_question__attempt"
            ).get(pk=pk, attempt_question__type="image")
        except Answer.DoesNotExist:
            return Response(
                {"detail": "Image answer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_correct = request.data.get("is_correct")
        if not isinstance(is_correct, bool):
            return Response(
                {"detail": "Body must include boolean 'is_correct'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer.is_correct = is_correct
        answer.reviewed_by = request.user
        answer.reviewed_at = timezone.now()
        answer.save(update_fields=["is_correct", "reviewed_by", "reviewed_at"])

        attempt = answer.attempt_question.attempt
        attempt.recalculate()
        return Response(
            {
                "id": answer.id,
                "is_correct": answer.is_correct,
                "attempt_id": attempt.id,
                "attempt_status": attempt.status,
                "attempt_score": attempt.score,
                "attempt_max_score": attempt.max_score,
            },
            status=status.HTTP_200_OK,
        )
