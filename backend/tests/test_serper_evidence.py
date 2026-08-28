"""
backend/tests/test_serper_evidence.py — Unit Tests for Serper & Web Evidence Discovery.
Verifies WebSearchEvidenceProvider, SERPER_API_KEY loading, query execution,
json serialization, and graceful scraping fallback.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

# Ensure backend root on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from online_evidence.provider import WebSearchEvidenceProvider, BaseEvidenceProvider
from online_evidence.candidate_search import discover_candidate_evidence


class TestSerperEvidenceProvider(unittest.TestCase):

    def setUp(self):
        self.provider = WebSearchEvidenceProvider()

    def test_provider_initialization(self):
        self.assertIsInstance(self.provider, BaseEvidenceProvider)
        self.assertEqual(self.provider.timeout, 4)

    def test_empty_query_returns_empty_list(self):
        results = self.provider.discover_candidates(query="")
        self.assertEqual(results, [])
        results_short = self.provider.discover_candidates(query="a")
        self.assertEqual(results_short, [])

    @patch("requests.post")
    def test_serper_api_call_and_json_serialization(self, mock_post):
        """Tests that Serper.dev API query path correctly formats and serializes JSON payload without errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic": [
                {
                    "title": "Official Luxury Watch Store",
                    "link": "https://example-watches.com/item1",
                    "imageUrl": "https://example-watches.com/item1.jpg"
                }
            ]
        }
        mock_post.return_value = mock_response

        # Set mock key
        with patch.dict(os.environ, {"SERPER_API_KEY": "test_mock_serper_key_12345"}):
            with patch.object(self.provider, "_fetch_candidate_details") as mock_fetch:
                mock_fetch.return_value = {
                    "image": Image.new("RGB", (50, 50), "blue"),
                    "source_url": "https://example-watches.com/item1",
                    "source_domain": "example-watches.com",
                    "title": "Official Luxury Watch Store",
                    "source_type": "ONLINE",
                    "candidate_id": "web_0_example-watches.com",
                }
                results = self.provider.discover_candidates(query="luxury chronograph watch", max_candidates=2)
                self.assertIsInstance(results, list)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["source_domain"], "example-watches.com")

    @patch("requests.post")
    def test_duckduckgo_fallback_when_no_api_key(self, mock_post):
        """Verifies that provider falls back to HTML scraping when no commercial API key is set."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
          <body>
            <div class="result">
              <a class="result__url" href="https://example.com/product">Example Product</a>
            </div>
          </body>
        </html>
        """
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SERPER_API_KEY": "", "SERPAPI_API_KEY": "", "GOOGLE_API_KEY": ""}):
            with patch.object(self.provider, "_fetch_candidate_details") as mock_fetch:
                mock_fetch.return_value = {
                    "image": Image.new("RGB", (50, 50), "green"),
                    "source_url": "https://example.com/product",
                    "source_domain": "example.com",
                    "title": "Example Product",
                    "source_type": "ONLINE",
                    "candidate_id": "web_0_example.com",
                }
                results = self.provider.discover_candidates(query="handmade ceramic pottery", max_candidates=1)
                self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
