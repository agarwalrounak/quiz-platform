from django.contrib import admin

from .models import Choice, Question


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "prompt", "category", "difficulty", "is_active")
    list_filter = ("type", "difficulty", "category", "is_active")
    search_fields = ("prompt", "category")
    inlines = [ChoiceInline]
