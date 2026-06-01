from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Question

User = get_user_model()


class SeedCommandTests(APITestCase):
    def test_seed_creates_all_types_and_is_idempotent(self):
        call_command("seed_questions")
        first = Question.objects.count()
        self.assertGreaterEqual(first, 20)

        types = set(Question.objects.values_list("type", flat=True))
        self.assertEqual(
            types, {"text", "single", "multiple", "numerical", "image"}
        )

        # Single-choice questions must each have exactly one correct choice.
        for q in Question.objects.filter(type="single"):
            self.assertEqual(q.choices.filter(is_correct=True).count(), 1)

        # Demo users exist with expected roles.
        self.assertTrue(User.objects.filter(username="admin", role="admin").exists())
        self.assertTrue(User.objects.filter(username="player1", role="user").exists())

        # Re-running must not duplicate questions.
        call_command("seed_questions")
        self.assertEqual(Question.objects.count(), first)


def question_url(pk=None):
    return f"/api/questions/{pk}/" if pk else "/api/questions/"


class QuestionPermissionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "a@x.com", "pass12345")
        self.user = User.objects.create_user("user", password="pass12345")

    def test_anonymous_cannot_list(self):
        self.assertEqual(
            self.client.get(question_url()).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_can_read_but_not_write(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(question_url()).status_code, status.HTTP_200_OK)
        resp = self.client.post(
            question_url(),
            {"type": "text", "prompt": "Q?", "accepted_text": "a"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            question_url(),
            {"type": "text", "prompt": "Q?", "accepted_text": "answer"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


class ValidationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "a@x.com", "pass12345")
        self.client.force_authenticate(self.admin)

    def _post(self, payload):
        return self.client.post(question_url(), payload, format="json")

    def test_single_requires_exactly_one_correct(self):
        bad = self._post({
            "type": "single",
            "prompt": "Pick one",
            "choices": [
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": True},
            ],
        })
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("choices", bad.data)

        ok = self._post({
            "type": "single",
            "prompt": "Pick one",
            "choices": [
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": False},
            ],
        })
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)

    def test_single_rejects_zero_correct(self):
        resp = self._post({
            "type": "single",
            "prompt": "Pick one",
            "choices": [
                {"text": "A", "is_correct": False},
                {"text": "B", "is_correct": False},
            ],
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_multiple_requires_at_least_one_correct(self):
        bad = self._post({
            "type": "multiple",
            "prompt": "Pick some",
            "choices": [
                {"text": "A", "is_correct": False},
                {"text": "B", "is_correct": False},
            ],
        })
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

        ok = self._post({
            "type": "multiple",
            "prompt": "Pick some",
            "choices": [
                {"text": "A", "is_correct": True},
                {"text": "B", "is_correct": True},
            ],
        })
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)

    def test_choice_question_needs_two_choices(self):
        resp = self._post({
            "type": "single",
            "prompt": "Pick",
            "choices": [{"text": "A", "is_correct": True}],
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_numerical_requires_value(self):
        bad = self._post({"type": "numerical", "prompt": "2+2?"})
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        ok = self._post({"type": "numerical", "prompt": "2+2?", "numeric_answer": "4"})
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)

    def test_text_requires_accepted_answer(self):
        bad = self._post({"type": "text", "prompt": "Capital of France?"})
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_requires_requirement(self):
        bad = self._post({"type": "image", "prompt": "Upload a chart"})
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        ok = self._post({
            "type": "image",
            "prompt": "Upload a chart",
            "image_requirement": "A bar chart of sales",
        })
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)


class ReadSerializationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "a@x.com", "pass12345")

    def test_admin_list_filters_by_type(self):
        self.client.force_authenticate(self.admin)
        self.client.post(
            question_url(),
            {"type": "text", "prompt": "T?", "accepted_text": "x"},
            format="json",
        )
        self.client.post(
            question_url(),
            {"type": "numerical", "prompt": "N?", "numeric_answer": "1"},
            format="json",
        )
        resp = self.client.get(question_url() + "?type=text")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        types = {q["type"] for q in resp.data}
        self.assertEqual(types, {"text"})
