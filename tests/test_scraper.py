import pytest
from app.services.scraper.rss import compute_hash, get_source_name


class TestScraper:
    def test_compute_hash_is_deterministic(self):
        h1 = compute_hash("Test Title", "Test content here")
        h2 = compute_hash("Test Title", "Test content here")
        assert h1 == h2

    def test_compute_hash_differs_for_different_content(self):
        h1 = compute_hash("Title A", "Content A")
        h2 = compute_hash("Title B", "Content B")
        assert h1 != h2

    def test_get_source_name_known_domains(self):
        assert get_source_name("https://www.thehindu.com/news/kerala") == "The Hindu"
        assert get_source_name("https://www.mathrubhumi.com/news") == "Mathrubhumi"
        assert get_source_name("https://indianexpress.com/article/india") == "Indian Express"

    def test_get_source_name_unknown(self):
        assert get_source_name("https://unknown.com/news") == "Unknown"
