from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AttemptViewSet, ReviewQueueView, ReviewVerdictView

router = DefaultRouter()
router.register("attempts", AttemptViewSet, basename="attempt")

urlpatterns = router.urls + [
    path("review/queue/", ReviewQueueView.as_view(), name="review-queue"),
    path("review/answers/<int:pk>/", ReviewVerdictView.as_view(), name="review-verdict"),
]
