from datetime import date

from yfdata import parsing


def test_parse_prices_or_rates_equity() -> None:
    body = {
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

    df = parsing.parse_prices_or_rates(body, "AAPL")

    assert list(df.columns) == ["ticker", "ts", "o", "h", "l", "c", "v"]
    assert df.loc[0, "ticker"] == "aapl"
    assert df.loc[0, "c"] == 1.5


def test_parse_prices_or_rates_empty_result() -> None:
    df = parsing.parse_prices_or_rates({"chart": {"result": []}}, "AAPL")

    assert list(df.columns) == ["instrument", "ts", "o", "h", "l", "c", "v"]
    assert df.empty


def test_parse_financials() -> None:
    body = {
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

    df = parsing.parse_financials(
        body,
        "AAPL",
        "A",
        {"annualTotalRevenue": "total_revenue"},
    )

    assert list(df.columns) == ["ticker", "metric", "freq", "date", "value"]
    assert df.loc[0, "ticker"] == "aapl"
    assert df.loc[0, "metric"] == "total_revenue"
    assert df.loc[0, "value"] == 391035000000.0


def test_parse_financials_empty_result() -> None:
    df = parsing.parse_financials({"timeseries": {"result": []}}, "AAPL", "A", {})

    assert list(df.columns) == ["ticker", "metric", "freq", "date", "value"]
    assert df.empty


def test_parse_dividends() -> None:
    body = {
        "chart": {
            "result": [
                {
                    "events": {
                        "dividends": {
                            "1721826284": {"amount": 0.25},
                        }
                    }
                }
            ]
        }
    }

    df = parsing.parse_dividends(body, "AAPL")

    assert list(df.columns) == ["ticker", "ts", "dividend"]
    assert df.loc[0, "ticker"] == "aapl"
    assert df.loc[0, "ts"] == date(2024, 7, 24)
    assert df.loc[0, "dividend"] == 0.25


def test_parse_dividends_without_events() -> None:
    df = parsing.parse_dividends({"chart": {"result": [{}]}}, "AAPL")

    assert list(df.columns) == ["ticker", "ts", "dividend"]
    assert df.empty
