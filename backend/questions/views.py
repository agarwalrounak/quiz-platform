from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from accounts.permissions import IsAdminOrReadOnly

from .models import Question
from .serializers import QuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    """Admin CRUD for the question bank.

    Authenticated users may read; only admins may create/update/delete.
    Supports filtering by type, category, difficulty, and active state.
    """

    queryset = Question.objects.prefetch_related("choices").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type", "category", "difficulty", "is_active"]
