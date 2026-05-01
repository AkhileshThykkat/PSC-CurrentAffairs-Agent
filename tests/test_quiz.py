import pytest
from app.services.quiz.generator import validate_quiz_response


class TestQuizGenerator:
    def test_valid_quiz_response(self):
        response = '''[
            {
                "question": "What is the capital of Kerala?",
                "options": ["A. Thiruvananthapuram", "B. Kochi", "C. Kozhikode", "D. Thrissur"],
                "correct_answer": "A. Thiruvananthapuram",
                "explanation": "Thiruvananthapuram is the capital of Kerala."
            }
        ]'''
        result = validate_quiz_response(response)
        assert len(result) == 1
        assert result[0]["question"] == "What is the capital of Kerala?"
        assert len(result[0]["options"]) == 4

    def test_wrong_number_of_options(self):
        response = '[{"question": "Q", "options": ["A", "B"], "correct_answer": "A", "explanation": "E"}]'
        with pytest.raises(ValueError, match="Invalid options"):
            validate_quiz_response(response)

    def test_correct_answer_not_in_options(self):
        response = '[{"question": "Q", "options": ["A. X", "B. Y", "C. Z", "D. W"], "correct_answer": "E. V", "explanation": "E"}]'
        with pytest.raises(ValueError, match="Correct answer not in options"):
            validate_quiz_response(response)
