import pytest

from yfdata import YahooProvider, constants


class Response:
    def __init__(self, body, error=None):
        self._body = body
        self._error = error

    def raise_for_status(self):
        if self._error is not None:
            raise self._error

    def json(self):
        return self._body


class FakeHttpGet:
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        body = self.bodies.pop(0)
        return body if isinstance(body, Response) else Response(body)


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
    assert http_get.calls[0][1] == {"impersonate": "chrome", "timeout": 30.0}


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


def test_request_uses_configured_timeout() -> None:
    http_get = FakeHttpGet([PRICE_BODY])
    provider = YahooProvider(
        http_get=http_get,
        browsers=("chrome",),
        timeout=5.0,
    )

    provider.get_prices("AAPL")

    assert http_get.calls[0][1]["timeout"] == 5.0


def test_request_raises_for_http_errors() -> None:
    error = RuntimeError("HTTP error")
    http_get = FakeHttpGet([Response({}, error=error)])
    provider = YahooProvider(http_get=http_get, browsers=("chrome",))

    with pytest.raises(RuntimeError, match="HTTP error"):
        provider.get_prices("AAPL")


def test_request_rejects_non_object_json() -> None:
    http_get = FakeHttpGet([["unexpected"]])
    provider = YahooProvider(http_get=http_get, browsers=("chrome",))

    with pytest.raises(ValueError, match="non-object JSON"):
        provider.get_prices("AAPL")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"browsers": ()}, "At least one browser"),
        ({"timeout": 0}, "Timeout must be greater than zero"),
    ],
)
def test_rejects_invalid_request_configuration(kwargs, message) -> None:
    with pytest.raises(ValueError, match=message):
        YahooProvider(**kwargs)
