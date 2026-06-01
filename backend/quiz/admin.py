from django.contrib import admin

from .models import Answer, Attempt, AttemptQuestion


class AttemptQuestionInline(admin.TabularInline):
    model = AttemptQuestion
    extra = 0
    fields = ("order", "type", "prompt")
    readonly_fields = fields
    can_delete = False


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "score", "max_score", "created_at", "submitted_at")
    list_filter = ("status",)
    inlines = [AttemptQuestionInline]


admin.site.register(Answer)
