from datetime import UTC, date, datetime

import pandas as pd
import pytest

from yfdata import parsing


def test_parse_minute_prices_uses_utc_timestamps() -> None:
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

    df = parsing.parse_prices_or_rates(body, "AAPL", "1m")

    assert list(df.columns) == ["ticker", "ts", "o", "h", "l", "c", "v"]
    assert df.loc[0, "ticker"] == "aapl"
    assert df.loc[0, "c"] == 1.5
    assert df.loc[0, "ts"].tzinfo is UTC


def test_parse_daily_prices_uses_exchange_civil_date() -> None:
    timestamp = int(datetime(2024, 7, 24, 2, tzinfo=UTC).timestamp())
    body = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "instrumentType": "EQUITY",
                        "exchangeTimezoneName": "America/New_York",
                    },
                    "timestamp": [timestamp],
                    "indicators": {"quote": [{"close": [1.5]}]},
                }
            ]
        }
    }

    df = parsing.parse_prices_or_rates(body, "AAPL", "1D")

    assert df.loc[0, "ts"] == date(2024, 7, 23)
    assert type(df.loc[0, "ts"]) is date


def test_parse_daily_prices_falls_back_to_utc_date_for_unknown_timezone() -> None:
    timestamp = int(datetime(2024, 7, 24, 2, tzinfo=UTC).timestamp())
    body = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "instrumentType": "EQUITY",
                        "exchangeTimezoneName": "Invalid/Timezone",
                    },
                    "timestamp": [timestamp],
                    "indicators": {"quote": [{"close": [1.5]}]},
                }
            ]
        }
    }

    df = parsing.parse_prices_or_rates(body, "AAPL", "1D")

    assert df.loc[0, "ts"] == date(2024, 7, 24)


def test_parse_daily_prices_empty_result() -> None:
    df = parsing.parse_prices_or_rates({"chart": {"result": []}}, "AAPL", "1D")

    assert list(df.columns) == ["ticker", "ts", "o", "h", "l", "c", "v"]
    assert df.empty
    assert df["ts"].dtype == object


def test_parse_rates_empty_result_keeps_pair_and_utc_schema() -> None:
    df = parsing.parse_prices_or_rates({"chart": {"result": []}}, "eur/usd", "1D")

    assert list(df.columns) == ["pair", "ts", "o", "h", "l", "c", "v"]
    assert df.empty
    assert str(df["ts"].dtype).endswith("UTC]")


def test_parse_daily_rates_uses_utc_timestamps() -> None:
    body = {
        "chart": {
            "result": [
                {
                    "meta": {"instrumentType": "CURRENCY"},
                    "timestamp": [1721826284],
                    "indicators": {"quote": [{"close": [1.1]}]},
                }
            ]
        }
    }

    df = parsing.parse_prices_or_rates(body, "eur/usd", "1D")

    assert df.loc[0, "ts"].tzinfo is UTC


@pytest.mark.parametrize(
    "body",
    [
        {"chart": None},
        {"chart": {"result": [None]}},
        {"chart": {"result": [{"meta": {"instrumentType": "EQUITY"}}]}},
        {
            "chart": {
                "result": [
                    {
                        "meta": {"instrumentType": "EQUITY"},
                        "timestamp": [1721826284],
                        "indicators": {"quote": []},
                    }
                ]
            }
        },
    ],
)
def test_parse_prices_or_rates_handles_incomplete_responses(body) -> None:
    df = parsing.parse_prices_or_rates(body, "AAPL", "1m")

    assert list(df.columns) == ["ticker", "ts", "o", "h", "l", "c", "v"]
    assert df.empty


def test_parse_prices_or_rates_fills_missing_quote_values() -> None:
    body = {
        "chart": {
            "result": [
                {
                    "meta": {"instrumentType": "EQUITY"},
                    "timestamp": [1721826284, 1721826344],
                    "indicators": {"quote": [{"close": [1.5]}]},
                }
            ]
        }
    }

    df = parsing.parse_prices_or_rates(body, "AAPL", "1m")

    assert len(df) == 2
    assert df.loc[0, "c"] == 1.5
    assert pd.isna(df.loc[1, "c"])
    assert df[["o", "h", "l", "v"]].isna().all().all()


def test_parse_prices_or_rates_rejects_unknown_instrument() -> None:
    body = {"chart": {"result": [{"meta": {"instrumentType": "CRYPTOCURRENCY"}}]}}

    with pytest.raises(ValueError, match="CRYPTOCURRENCY"):
        parsing.parse_prices_or_rates(body, "BTC-USD", "1m")


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
    assert df.loc[0, "date"] == date(2024, 9, 30)
    assert type(df.loc[0, "date"]) is date
    assert df.loc[0, "value"] == 391035000000.0


def test_parse_financials_empty_result() -> None:
    df = parsing.parse_financials({"timeseries": {"result": []}}, "AAPL", "A", {})

    assert list(df.columns) == ["ticker", "metric", "freq", "date", "value"]
    assert df.empty


def test_parse_financials_skips_malformed_items() -> None:
    body = {
        "timeseries": {
            "result": [
                None,
                {"meta": None},
                {
                    "meta": {"type": ["annualTotalRevenue"]},
                    "annualTotalRevenue": [
                        None,
                        {"asOfDate": "2024-09-30"},
                        {
                            "asOfDate": "2024-09-30",
                            "reportedValue": {"raw": "invalid"},
                        },
                    ],
                },
            ]
        }
    }

    df = parsing.parse_financials(
        body,
        "AAPL",
        "A",
        {"annualTotalRevenue": "total_revenue"},
    )

    assert df.empty


def test_parse_financials_skips_invalid_dates() -> None:
    body = {
        "timeseries": {
            "result": [
                {
                    "meta": {"type": ["annualTotalRevenue"]},
                    "annualTotalRevenue": [
                        {
                            "asOfDate": "not-a-date",
                            "reportedValue": {"raw": 1},
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


def test_parse_dividends_uses_exchange_civil_date() -> None:
    timestamp = int(datetime(2024, 7, 24, 2, tzinfo=UTC).timestamp())
    body = {
        "chart": {
            "result": [
                {
                    "meta": {"exchangeTimezoneName": "America/New_York"},
                    "events": {
                        "dividends": {
                            str(timestamp): {"amount": 0.25},
                        }
                    },
                }
            ]
        }
    }

    df = parsing.parse_dividends(body, "AAPL")

    assert df.loc[0, "ts"] == date(2024, 7, 23)


def test_parse_dividends_without_events() -> None:
    without_events = parsing.parse_dividends({"chart": {"result": [{}]}}, "AAPL")
    invalid_chart = parsing.parse_dividends({"chart": None}, "AAPL")

    assert list(without_events.columns) == ["ticker", "ts", "dividend"]
    assert without_events.empty
    assert invalid_chart.empty


def test_parse_dividends_skips_malformed_items() -> None:
    body = {
        "chart": {
            "result": [
                {
                    "events": {
                        "dividends": {
                            "invalid": {"amount": 0.25},
                            "1721826284": None,
                        }
                    }
                }
            ]
        }
    }

    df = parsing.parse_dividends(body, "AAPL")

    assert df.empty
