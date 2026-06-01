"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Liveness probe used by the SPA and Docker healthchecks."""
    return JsonResponse({"status": "ok", "service": "quiz-backend"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("questions.urls")),
    path("api/", include("quiz.urls")),
]

# Serve uploaded media in development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
