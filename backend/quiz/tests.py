from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from questions.models import Choice, Question

from . import grading
from .models import Attempt, AttemptQuestion, AttemptStatus

User = get_user_model()


class GradingUnitTests(TestCase):
    def test_text_normalized_match(self):
        self.assertTrue(grading.grade_text("Paris", "  paris "))
        self.assertTrue(grading.grade_text("Paris", "PARIS"))
        self.assertFalse(grading.grade_text("Paris", "Lyon"))

    def test_numerical_exact(self):
        self.assertTrue(grading.grade_numerical(Decimal("56"), "56"))
        self.assertTrue(grading.grade_numerical(Decimal("56"), 56))
        self.assertFalse(grading.grade_numerical(Decimal("56"), "57"))
        self.assertFalse(grading.grade_numerical(Decimal("56"), ""))

    def test_single(self):
        self.assertTrue(grading.grade_single([2], [2]))
        self.assertFalse(grading.grade_single([2], [3]))
        self.assertFalse(grading.grade_single([2], []))

    def test_multiple_all_or_nothing(self):
        self.assertTrue(grading.grade_multiple([1, 3], [3, 1]))
        self.assertFalse(grading.grade_multiple([1, 3], [1]))      # partial -> wrong
        self.assertFalse(grading.grade_multiple([1, 3], [1, 2, 3]))  # extra -> wrong


def make_questions(n, qtype="single"):
    out = []
    for i in range(n):
        q = Question.objects.create(type=qtype, prompt=f"Q{i}?", is_active=True)
        if qtype in ("single", "multiple"):
            Choice.objects.create(question=q, text="A", is_correct=True, order=0)
            Choice.objects.create(question=q, text="B", is_correct=False, order=1)
        out.append(q)
    return out


@override_settings(QUIZ_LENGTH=5)
class AttemptCreationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="pass12345")
        self.client.force_authenticate(self.user)
        make_questions(12)

    def test_creates_attempt_with_n_questions_no_repeats(self):
        resp = self.client.post("/api/attempts/", {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        qs = resp.data["questions"]
        self.assertEqual(len(qs), 5)
        ids = [q["id"] for q in qs]
        self.assertEqual(len(ids), len(set(ids)))  # no repeats within an attempt
        self.assertEqual(resp.data["max_score"], 5)

    def test_choices_hide_correctness(self):
        resp = self.client.post("/api/attempts/", {}, format="json")
        first_choices = resp.data["questions"][0]["choices"]
        self.assertTrue(all("is_correct" not in c for c in first_choices))

    def test_attempts_are_independently_randomized(self):
        a = self.client.post("/api/attempts/", {}, format="json").data
        b = self.client.post("/api/attempts/", {}, format="json").data
        a_ids = [q["id"] for q in a["questions"]]
        b_ids = [q["id"] for q in b["questions"]]
        # With 12 questions and samples of 5, order/contents should differ.
        self.assertTrue(a_ids != b_ids)

    def test_pool_smaller_than_n(self):
        Question.objects.all().delete()
        make_questions(3)
        resp = self.client.post("/api/attempts/", {}, format="json")
        self.assertEqual(len(resp.data["questions"]), 3)
        self.assertIn("notice", resp.data)


@override_settings(QUIZ_LENGTH=5)
class SubmitTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="pass12345")
        self.other = User.objects.create_user("o", password="pass12345")
        self.client.force_authenticate(self.user)

    def _start(self):
        return self.client.post("/api/attempts/", {}, format="json").data

    def test_owner_only_access(self):
        make_questions(5)
        attempt = self._start()
        self.client.force_authenticate(self.other)
        resp = self.client.get(f"/api/attempts/{attempt['id']}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_grades_objective_types(self):
        # Build a deterministic single-choice bank.
        make_questions(5, "single")
        attempt = self._start()
        answers = []
        for q in attempt["questions"]:
            aq = AttemptQuestion.objects.get(pk=q["id"])
            correct = aq.correct_choice_ids
            answers.append({"attempt_question": q["id"], "selected_choice_ids": correct})
        resp = self.client.post(
            f"/api/attempts/{attempt['id']}/submit/",
            {"answers": answers},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["score"], 5)
        self.assertEqual(resp.data["status"], AttemptStatus.GRADED)

    def test_wrong_answers_score_zero(self):
        make_questions(5, "single")
        attempt = self._start()
        answers = [
            {"attempt_question": q["id"], "selected_choice_ids": []}
            for q in attempt["questions"]
        ]
        resp = self.client.post(
            f"/api/attempts/{attempt['id']}/submit/", {"answers": answers}, format="json"
        )
        self.assertEqual(resp.data["score"], 0)

    def test_image_question_marks_awaiting_review(self):
        Question.objects.create(type="image", prompt="Upload", image_requirement="x", is_active=True)
        attempt = self._start()
        aq = attempt["questions"][0]
        resp = self.client.post(
            f"/api/attempts/{attempt['id']}/submit/",
            {"answers": [{"attempt_question": aq["id"]}]},
            format="json",
        )
        self.assertEqual(resp.data["status"], AttemptStatus.AWAITING_REVIEW)

    def test_cannot_submit_twice(self):
        make_questions(5, "single")
        attempt = self._start()
        self.client.post(f"/api/attempts/{attempt['id']}/submit/", {"answers": []}, format="json")
        resp = self.client.post(
            f"/api/attempts/{attempt['id']}/submit/", {"answers": []}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_history_lists_only_own(self):
        make_questions(5)
        self._start()
        resp = self.client.get("/api/attempts/")
        self.assertEqual(len(resp.data), 1)
        self.client.force_authenticate(self.other)
        self.assertEqual(len(self.client.get("/api/attempts/").data), 0)


@override_settings(QUIZ_LENGTH=5)
class ReviewSerializationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="pass12345")
        self.client.force_authenticate(self.user)

    def _start(self):
        return self.client.post("/api/attempts/", {}, format="json").data

    def test_in_progress_detail_hides_answers(self):
        make_questions(5, "single")
        attempt = self._start()
        resp = self.client.get(f"/api/attempts/{attempt['id']}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Player view: choices carry no is_correct and there is no correct_answer.
        first = resp.data["questions"][0]
        self.assertTrue(all("is_correct" not in c for c in first["choices"]))
        self.assertNotIn("correct_answer", first)

    def test_submitted_detail_reveals_review_data(self):
        make_questions(5, "single")
        attempt = self._start()
        answers = []
        for q in attempt["questions"]:
            aq = AttemptQuestion.objects.get(pk=q["id"])
            answers.append(
                {"attempt_question": q["id"], "selected_choice_ids": aq.correct_choice_ids}
            )
        self.client.post(
            f"/api/attempts/{attempt['id']}/submit/", {"answers": answers}, format="json"
        )
        resp = self.client.get(f"/api/attempts/{attempt['id']}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        q0 = resp.data["questions"][0]
        self.assertIn("correct_answer", q0)
        self.assertIn("user_answer", q0)
        self.assertEqual(q0["is_correct"], True)
        # The correct choice is flagged in the review choices.
        self.assertTrue(any(c["is_correct"] and c["selected"] for c in q0["choices"]))

    def test_text_review_shows_accepted_answer(self):
        Question.objects.create(
            type="text", prompt="Capital?", accepted_text="Paris", is_active=True
        )
        attempt = self._start()
        aq = attempt["questions"][0]
        self.client.post(
            f"/api/attempts/{attempt['id']}/submit/",
            {"answers": [{"attempt_question": aq["id"], "text_value": "paris"}]},
            format="json",
        )
        resp = self.client.get(f"/api/attempts/{attempt['id']}/")
        q0 = resp.data["questions"][0]
        self.assertEqual(q0["correct_answer"], "Paris")
        self.assertEqual(q0["user_answer"], "paris")
        self.assertTrue(q0["is_correct"])  # normalized match


@override_settings(QUIZ_LENGTH=1)
class ImageReviewTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "a@x.com", "pass12345")
        self.user = User.objects.create_user("u", password="pass12345")
        # A bank of exactly one active image question -> attempt always contains it.
        Question.objects.create(
            type="image", prompt="Upload a chart", image_requirement="A bar chart",
            is_active=True,
        )

    def _submitted_image_attempt(self):
        self.client.force_authenticate(self.user)
        attempt = self.client.post("/api/attempts/", {}, format="json").data
        aq = attempt["questions"][0]
        self.client.post(
            f"/api/attempts/{attempt['id']}/submit/",
            {"answers": [{"attempt_question": aq["id"]}]},
            format="json",
        )
        return attempt["id"]

    def test_queue_requires_admin(self):
        self._submitted_image_attempt()
        # still authenticated as the (non-admin) user
        resp = self.client.get("/api/review/queue/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_queue_lists_pending_image_answers(self):
        self._submitted_image_attempt()
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/review/queue/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        item = resp.data[0]
        self.assertEqual(item["user"], "u")
        self.assertEqual(item["image_requirement"], "A bar chart")

    def test_verdict_correct_finalizes_attempt(self):
        attempt_id = self._submitted_image_attempt()
        attempt = Attempt.objects.get(pk=attempt_id)
        self.assertEqual(attempt.status, AttemptStatus.AWAITING_REVIEW)
        self.assertEqual(attempt.score, 0)

        self.client.force_authenticate(self.admin)
        answer_id = self.client.get("/api/review/queue/").data[0]["id"]
        resp = self.client.post(
            f"/api/review/answers/{answer_id}/", {"is_correct": True}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["attempt_status"], AttemptStatus.GRADED)
        self.assertEqual(resp.data["attempt_score"], 1)

        # Item leaves the queue once reviewed.
        self.assertEqual(len(self.client.get("/api/review/queue/").data), 0)

    def test_verdict_incorrect_grades_zero(self):
        self._submitted_image_attempt()
        self.client.force_authenticate(self.admin)
        answer_id = self.client.get("/api/review/queue/").data[0]["id"]
        resp = self.client.post(
            f"/api/review/answers/{answer_id}/", {"is_correct": False}, format="json"
        )
        self.assertEqual(resp.data["attempt_status"], AttemptStatus.GRADED)
        self.assertEqual(resp.data["attempt_score"], 0)

    def test_verdict_requires_boolean(self):
        self._submitted_image_attempt()
        self.client.force_authenticate(self.admin)
        answer_id = self.client.get("/api/review/queue/").data[0]["id"]
        resp = self.client.post(
            f"/api/review/answers/{answer_id}/", {"is_correct": "yes"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
