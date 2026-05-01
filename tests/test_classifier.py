import pytest
from app.services.classifier.filter import should_keep


class TestClassifier:
    def test_kerala_always_kept(self):
        article = {"category": "Kerala", "importance": "LOW"}
        assert should_keep(article, []) is True

    def test_international_high_kept(self):
        article = {"category": "International", "importance": "HIGH"}
        assert should_keep(article, []) is True

    def test_international_low_rejected(self):
        article = {"category": "International", "importance": "LOW"}
        assert should_keep(article, []) is False

    def test_india_top_70_percent_kept(self):
        articles = [
            {"category": "India", "importance": "HIGH"},
            {"category": "India", "importance": "MEDIUM"},
            {"category": "India", "importance": "LOW"},
            {"category": "India", "importance": "LOW"},
            {"category": "India", "importance": "LOW"},
        ]
        assert should_keep(articles[0], articles) is True
        assert should_keep(articles[1], articles) is True
        assert should_keep(articles[4], articles) is False
