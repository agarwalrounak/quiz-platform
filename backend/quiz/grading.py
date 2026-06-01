"""Pure grading functions.

Each operates on an AttemptQuestion snapshot plus the submitted Answer values and
returns True/False, or None when the answer cannot be auto-graded (image uploads,
which require manual review).

Decisions (see FEATURE_REQUIREMENTS.md):
  - single:    selected set == the one correct id
  - multiple:  selected set == correct set  (all-or-nothing, no partial credit)
  - numerical: exact decimal equality
  - text:      normalized (casefold + trim) equality against the single answer
  - image:     not auto-graded -> None
"""
from decimal import Decimal, InvalidOperation


def _normalize_text(value):
    return (value or "").strip().casefold()


def grade_text(accepted_text, value):
    return _normalize_text(value) == _normalize_text(accepted_text)


def grade_numerical(numeric_answer, value):
    if numeric_answer is None or value in (None, ""):
        return False
    try:
        return Decimal(str(value)) == Decimal(str(numeric_answer))
    except (InvalidOperation, ValueError, TypeError):
        return False


def grade_single(correct_ids, selected_ids):
    return set(selected_ids or []) == set(correct_ids or [])


def grade_multiple(correct_ids, selected_ids):
    # All-or-nothing: the selected set must exactly equal the correct set.
    return set(selected_ids or []) == set(correct_ids or [])


def grade_answer(attempt_question, answer):
    """Return True/False for auto-graded types, or None for manual (image)."""
    qtype = attempt_question.type
    if qtype == "text":
        return grade_text(attempt_question.accepted_text, answer.text_value)
    if qtype == "numerical":
        return grade_numerical(attempt_question.numeric_answer, answer.numeric_value)
    if qtype == "single":
        return grade_single(attempt_question.correct_choice_ids, answer.selected_choice_ids)
    if qtype == "multiple":
        return grade_multiple(attempt_question.correct_choice_ids, answer.selected_choice_ids)
    if qtype == "image":
        return None
    return None
