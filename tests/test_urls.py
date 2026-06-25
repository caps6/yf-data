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


def assert_common_query_params(url: str) -> None:
    assert "period1" in url
    assert "period2" in url
    assert "lang=en-US&region=US&corsDomain=finance.yahoo.com" in url


def test_url_prices() -> None:
    url = urls.build_url_prices("aapl", FREQ_MINUTE)
    assert isinstance(url, str)
    assert "interval=1m&range=1w" in url
    assert_common_query_params(url)

    url = urls.build_url_prices("aapl", FREQ_DAILY)
    assert isinstance(url, str)
    assert "interval=1d&range=1mo" in url
    assert_common_query_params(url)


def test_url_rates() -> None:
    url = urls.build_url_rates("usd", "eur", FREQ_MINUTE)
    assert isinstance(url, str)
    assert "interval=1m&range=1w" in url
    assert_common_query_params(url)

    url = urls.build_url_rates("usd", "eur", FREQ_DAILY)
    assert isinstance(url, str)
    assert "interval=1d&range=1mo" in url
    assert_common_query_params(url)


def test_url_financials() -> None:
    mapping = {k: v[FREQ_QUARTERLY] for k, v in MAPPING_INCOME_METRICS.items()}
    url = urls.build_url_financials("aapl", FREQ_QUARTERLY, mapping)
    assert_common_query_params(url)

    mapping = {k: v[FREQ_ANNUAL] for k, v in MAPPING_INCOME_METRICS.items()}
    url = urls.build_url_financials("aapl", FREQ_ANNUAL, mapping)
    assert_common_query_params(url)

    mapping = {k: v[TTM] for k, v in MAPPING_INCOME_METRICS.items()}
    url = urls.build_url_financials("aapl", FREQ_ANNUAL, mapping)
    assert_common_query_params(url)

    mapping = {k: v[FREQ_QUARTERLY] for k, v in MAPPING_BALANCE_METRICS.items()}
    url = urls.build_url_financials("aapl", FREQ_QUARTERLY, mapping)
    assert_common_query_params(url)

    mapping = {k: v[FREQ_ANNUAL] for k, v in MAPPING_BALANCE_METRICS.items()}
    url = urls.build_url_financials("aapl", FREQ_ANNUAL, mapping)
    assert_common_query_params(url)


def test_url_dividends() -> None:
    url = urls.build_url_dividends("aapl")
    assert isinstance(url, str)
    assert "&interval=1d&events=div" in url
    assert_common_query_params(url)
