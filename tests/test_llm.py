import pytest
from app.services.llm.validator import validate_llm_response, extract_json_block, parse_json_lenient


class TestLLMValidator:
    def test_valid_response(self):
        response = """
        {
            "title": "Test article title",
            "summary": "A brief summary of the article",
            "key_points": ["Point one", "Point two", "Point three"],
            "category": "Kerala",
            "importance": "HIGH",
            "exam_relevance": "Relevant for Kerala PSC"
        }
        """
        result = validate_llm_response(response)
        assert result["title"] == "Test article title"
        assert result["category"] == "Kerala"
        assert result["importance"] == "HIGH"
        assert len(result["key_points"]) == 3

    def test_invalid_category(self):
        response = '{"title": "T", "summary": "S", "key_points": ["A", "B"], "category": "Asia", "importance": "HIGH", "exam_relevance": null}'
        with pytest.raises(ValueError, match="Invalid category"):
            validate_llm_response(response)

    def test_invalid_importance(self):
        response = '{"title": "T", "summary": "S", "key_points": ["A", "B"], "category": "India", "importance": "CRITICAL", "exam_relevance": null}'
        with pytest.raises(ValueError, match="Invalid importance"):
            validate_llm_response(response)

    def test_missing_fields(self):
        response = '{"title": "T"}'
        with pytest.raises(ValueError, match="Missing fields"):
            validate_llm_response(response)

    def test_key_points_count(self):
        response = '{"title": "T", "summary": "S", "key_points": ["A"], "category": "India", "importance": "HIGH", "exam_relevance": null}'
        result = validate_llm_response(response)
        assert len(result["key_points"]) >= 2

    def test_extract_json_block_from_markdown(self):
        text = '```json\n{"title": "test"}\n```'
        result = extract_json_block(text)
        assert result == '{"title": "test"}'

    def test_parse_json_lenient_with_single_quotes(self):
        text = "{'title': 'test', 'summary': 's', 'key_points': ['a', 'b'], 'category': 'India', 'importance': 'HIGH', 'exam_relevance': 'e'}"
        result = parse_json_lenient(text)
        assert result["title"] == "test"

    def test_parse_json_lenient_with_markdown(self):
        text = '```json\n{"title": "test", "summary": "s", "key_points": ["a", "b"], "category": "India", "importance": "HIGH", "exam_relevance": "e"}\n```'
        result = parse_json_lenient(text)
        assert result["title"] == "test"
