import pytest

from yfdata import YahooProvider, constants


class Response:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


class FakeHttpGet:
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response(self.bodies.pop(0))


PRICE_BODY = {
    "chart": {
        "result": [
            {
                "meta": {"instrumentType": "EQUITY"},
                "timestamp": [1721826284],
                "indicators": {
                    "quote": [
                        {
                            "open": [1.0],
                            "high": [2.0],
                            "low": [0.5],
                            "close": [1.5],
                            "volume": [100],
                        }
                    ]
                },
            }
        ]
    }
}

FINANCIAL_BODY = {
    "timeseries": {
        "result": [
            {
                "meta": {"type": ["annualTotalRevenue"]},
                "annualTotalRevenue": [
                    {
                        "asOfDate": "2024-09-30",
                        "reportedValue": {"raw": 391035000000},
                    }
                ],
            }
        ]
    }
}


def test_get_prices_accepts_single_ticker_and_injects_http_client() -> None:
    http_get = FakeHttpGet([PRICE_BODY])
    provider = YahooProvider(http_get=http_get, browsers=("chrome",))

    df = provider.get_prices("AAPL", constants.FREQ_DAILY)

    assert df.loc[0, "ticker"] == "aapl"
    assert "AAPL" in http_get.calls[0][0]
    assert http_get.calls[0][1] == {"impersonate": "chrome"}


def test_get_income_filters_metrics() -> None:
    http_get = FakeHttpGet([FINANCIAL_BODY])
    provider = YahooProvider(http_get=http_get, browsers=("chrome",))

    df = provider.get_income("AAPL", constants.FREQ_ANNUAL, ["total_revenue"])

    assert df.loc[0, "metric"] == "total_revenue"
    assert "type=annualTotalRevenue" in http_get.calls[0][0]


def test_get_balance_rejects_ttm() -> None:
    provider = YahooProvider(http_get=FakeHttpGet([]))

    with pytest.raises(ValueError):
        provider.get_balance("AAPL", constants.TTM)


def test_rejects_unknown_financial_metric() -> None:
    provider = YahooProvider(http_get=FakeHttpGet([]))

    with pytest.raises(ValueError, match="missing_metric"):
        provider.get_income("AAPL", constants.FREQ_ANNUAL, ["missing_metric"])


def test_rejects_empty_ticker_list() -> None:
    provider = YahooProvider(http_get=FakeHttpGet([]))

    with pytest.raises(ValueError, match="At least one ticker"):
        provider.get_prices([])
