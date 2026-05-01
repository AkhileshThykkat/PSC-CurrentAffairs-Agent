import pytest
from app.services.quiz.generator import validate_quiz_question


class TestQuizGenerator:
    def test_valid_quiz_question(self):
        response = '''
        {
            "question": "What is the capital of Kerala?",
            "options": ["A. Thiruvananthapuram", "B. Kochi", "C. Kozhikode", "D. Thrissur"],
            "correct_answer": "A. Thiruvananthapuram",
            "explanation": "Thiruvananthapuram is the capital of Kerala."
        }'''
        result = validate_quiz_question(response)
        assert result["question"] == "What is the capital of Kerala?"
        assert len(result["options"]) == 4

    def test_wrong_number_of_options(self):
        response = '{"question": "Q", "options": ["A", "B"], "correct_answer": "A", "explanation": "E"}'
        with pytest.raises(ValueError, match="Invalid options"):
            validate_quiz_question(response)

    def test_correct_answer_not_in_options(self):
        response = '{"question": "Q", "options": ["A. X", "B. Y", "C. Z", "D. W"], "correct_answer": "E. V", "explanation": "E"}'
        with pytest.raises(ValueError, match="Correct answer not in options"):
            validate_quiz_question(response)

    def test_single_quotes_in_response(self):
        response = "{'question': 'Q?', 'options': ['A. X', 'B. Y', 'C. Z', 'D. W'], 'correct_answer': 'A. X', 'explanation': 'E'}"
        result = validate_quiz_question(response)
        assert result["question"] == "Q?"

    def test_markdown_wrapped_response(self):
        response = '```json\n{"question": "Q?", "options": ["A. X", "B. Y", "C. Z", "D. W"], "correct_answer": "A. X", "explanation": "E"}\n```'
        result = validate_quiz_question(response)
        assert result["question"] == "Q?"

    def test_list_wrapped_response(self):
        response = '[{"question": "Q?", "options": ["A. X", "B. Y", "C. Z", "D. W"], "correct_answer": "A. X", "explanation": "E"}]'
        result = validate_quiz_question(response)
        assert result["question"] == "Q?"
