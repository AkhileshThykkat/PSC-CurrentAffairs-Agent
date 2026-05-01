import pytest
from app.services.classifier.filter import should_keep


class TestClassifier:
    def test_kerala_above_threshold_kept(self):
        article = {"category": "Kerala", "importance": "LOW", "psc_score": 5.0}
        assert should_keep(article, []) is True

    def test_kerala_below_threshold_rejected(self):
        article = {"category": "Kerala", "importance": "LOW", "psc_score": 2.0}
        assert should_keep(article, []) is False

    def test_international_high_kept(self):
        article = {"category": "International", "importance": "HIGH", "psc_score": 6.0}
        assert should_keep(article, []) is True

    def test_international_low_rejected(self):
        article = {"category": "International", "importance": "LOW"}
        assert should_keep(article, []) is False

    def test_india_above_threshold_kept(self):
        article = {"category": "India", "importance": "HIGH", "psc_score": 8.0}
        articles = [article, {"category": "India", "importance": "LOW", "psc_score": 3.0}]
        assert should_keep(article, articles) is True

    def test_india_below_threshold_rejected(self):
        article = {"category": "India", "importance": "LOW", "psc_score": 3.0}
        assert should_keep(article, []) is False

    def test_low_psc_score_rejected(self):
        article = {"category": "Kerala", "importance": "HIGH", "psc_score": 1.0}
        assert should_keep(article, []) is False
