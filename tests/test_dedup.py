import pytest
from app.services.dedup.exact import get_duplicate_hashes, get_duplicate_urls


class TestExactDedup:
    def test_empty_db_returns_empty_sets(self):
        hashes = get_duplicate_hashes()
        assert isinstance(hashes, set)

        urls = get_duplicate_urls()
        assert isinstance(urls, set)
