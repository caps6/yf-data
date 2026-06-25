import unittest

from yfdata import urls
from yfdata.constants import (
    FREQ_ANNUAL,
    FREQ_DAILY,
    FREQ_MINUTE,
    FREQ_QUARTERLY,
    MAPPING_BALANCE_METRICS,
    MAPPING_INCOME_METRICS,
    TTM,
)


class TestUrls(unittest.TestCase):
    def test_url_prices(self) -> None:
        """Tests urls for prices."""

        url = urls.build_url_prices("aapl", FREQ_MINUTE)
        self.assertIsInstance(url, str)
        self.assertIn("interval=1m&range=1w", url)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

        url = urls.build_url_prices("aapl", FREQ_DAILY)
        self.assertIsInstance(url, str)
        self.assertIn("interval=1d&range=1mo", url)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

    def test_url_rates(self) -> None:
        """Tests urls for rates."""

        url = urls.build_url_rates("usd", "eur", FREQ_MINUTE)
        self.assertIsInstance(url, str)
        self.assertIn("interval=1m&range=1w", url)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

        url = urls.build_url_rates("usd", "eur", FREQ_DAILY)
        self.assertIsInstance(url, str)
        self.assertIn("interval=1d&range=1mo", url)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

    def test_url_financials(self) -> None:
        """Tests urls for financials."""

        mapping = {k: v[FREQ_QUARTERLY] for k, v in MAPPING_INCOME_METRICS.items()}
        url = urls.build_url_financials("aapl", FREQ_QUARTERLY, mapping)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

        mapping = {k: v[FREQ_ANNUAL] for k, v in MAPPING_INCOME_METRICS.items()}
        url = urls.build_url_financials("aapl", FREQ_ANNUAL, mapping)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

        mapping = {k: v[TTM] for k, v in MAPPING_INCOME_METRICS.items()}
        url = urls.build_url_financials("aapl", FREQ_ANNUAL, mapping)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

        mapping = {k: v[FREQ_QUARTERLY] for k, v in MAPPING_BALANCE_METRICS.items()}
        url = urls.build_url_financials("aapl", FREQ_QUARTERLY, mapping)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

        mapping = {k: v[FREQ_ANNUAL] for k, v in MAPPING_BALANCE_METRICS.items()}
        url = urls.build_url_financials("aapl", FREQ_ANNUAL, mapping)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)

    def test_url_dividends(self) -> None:
        """Tests url for dividends."""

        url = urls.build_url_dividends("aapl")
        self.assertIsInstance(url, str)
        self.assertIn("&interval=1d&events=div", url)
        self.assertIn("period1", url)
        self.assertIn("period2", url)
        self.assertIn("lang=en-US&region=US&corsDomain=finance.yahoo.com", url)
