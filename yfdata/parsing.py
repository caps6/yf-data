"""Module with helpers for parsing API content returned by Yahoo API endpoints."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
from pandas import DataFrame

from yfdata import utils

from .constants import FREQ_DAILY

_PRICE_COLUMNS = ["ts", "o", "h", "l", "c", "v"]
_FINANCIAL_COLUMNS = ["ticker", "metric", "freq", "date", "value"]
_DIVIDEND_COLUMNS = ["ticker", "ts", "dividend"]


def _price_code_name(ticker_or_pair: str, instrument_type: object = None) -> str:
    if instrument_type in ("EQUITY", "ETF"):
        return "ticker"
    if instrument_type == "CURRENCY":
        return "pair"
    if instrument_type is not None:
        raise ValueError(f"Instrument type {instrument_type!r} is not supported.")

    return "pair" if "/" in ticker_or_pair else "ticker"


def _as_civil_dates(values, timezone_name: object = None):
    """Convert UTC timestamps to civil dates in an optional IANA timezone."""

    timestamps = pd.to_datetime(values, errors="coerce", utc=True)
    if isinstance(timezone_name, str):
        try:
            timestamps = timestamps.dt.tz_convert(ZoneInfo(timezone_name))
        except (ValueError, ZoneInfoNotFoundError):
            pass
    return timestamps.dt.date


def _empty_prices_frame(
    code_name: str,
    ticker_or_pair: str,
    *,
    dates_only: bool,
) -> DataFrame:
    df = DataFrame(columns=[*_PRICE_COLUMNS, code_name])
    df[code_name] = df[code_name].astype("object")
    if dates_only:
        df["ts"] = df["ts"].astype("object")
    else:
        df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    df[code_name] = ticker_or_pair.lower()
    return df[[code_name, *_PRICE_COLUMNS]]


def parse_prices_or_rates(body: dict, ticker_or_pair: str, freq: str) -> DataFrame:
    """Parse OHLC data for stock prices and exchange rates.

    Minute prices and exchange rates use timezone-aware UTC timestamps. Daily
    stock prices use the civil date of the trading session in the exchange
    timezone reported by Yahoo, falling back to the UTC date when unavailable.

    Args:
        body: Body response from API.
        ticker_or_pair: Ticker or currency pair.
        freq: Data sampling frequency, ``1D`` (daily) or ``1m`` (1 minute).

    Returns:
        DataFrame with OHLC data. The ``ts`` column contains
        :class:`datetime.date` values for daily stock prices and timezone-aware
        UTC timestamps for minute prices and exchange rates.

    """

    chart = body.get("chart", {})
    result = chart.get("result") if isinstance(chart, dict) else None
    code_name = _price_code_name(ticker_or_pair)
    dates_only = code_name == "ticker" and freq == FREQ_DAILY

    if not isinstance(result, list) or not result:
        return _empty_prices_frame(
            code_name,
            ticker_or_pair,
            dates_only=dates_only,
        )

    data = result[0]
    if not isinstance(data, dict):
        return _empty_prices_frame(
            code_name,
            ticker_or_pair,
            dates_only=dates_only,
        )

    metadata = data.get("meta", {})
    if not isinstance(metadata, dict):
        metadata = {}
    instrument_type = metadata.get("instrumentType")
    code_name = _price_code_name(ticker_or_pair, instrument_type)
    dates_only = code_name == "ticker" and freq == FREQ_DAILY

    timestamps = data.get("timestamp")
    indicators = data.get("indicators")
    if not isinstance(timestamps, list) or not isinstance(indicators, dict):
        return _empty_prices_frame(
            code_name,
            ticker_or_pair,
            dates_only=dates_only,
        )

    quote_items = indicators.get("quote")
    if (
        not isinstance(quote_items, list)
        or not quote_items
        or not isinstance(quote_items[0], dict)
    ):
        return _empty_prices_frame(
            code_name,
            ticker_or_pair,
            dates_only=dates_only,
        )

    quotes = quote_items[0]
    row_count = len(timestamps)

    def values_for(name: str) -> list:
        values = quotes.get(name)
        if not isinstance(values, list):
            return [None] * row_count
        return (values + [None] * row_count)[:row_count]

    df = DataFrame(
        data={
            "ts": timestamps,
            "o": values_for("open"),
            "h": values_for("high"),
            "l": values_for("low"),
            "c": values_for("close"),
            "v": values_for("volume"),
        }
    )

    df[code_name] = ticker_or_pair.lower()
    df["ts"] = pd.to_datetime(df["ts"], unit="s", errors="coerce", utc=True)
    if dates_only:
        df["ts"] = _as_civil_dates(
            df["ts"],
            metadata.get("exchangeTimezoneName"),
        )

    # Reorder the columns.
    return df[[code_name, *_PRICE_COLUMNS]]


def parse_financials(body: dict, ticker: str, freq: str, mapping: dict) -> DataFrame:
    """Parse financials data of a company.

    Financial reporting periods are civil dates, not instants in time, so the
    returned ``date`` column contains :class:`datetime.date` values.

    Args:
        body: Body response from API.
        ticker: Ticker of the company.
        freq: Reporting frequency: ``Q`` (quarterly), ``A`` (annual), or
            ``TTM`` (trailing twelve months).
        mapping: Mapping from Yahoo metric names to their canonical names.

    Returns:
        DataFrame with retrieved financial data and a ``date`` column containing
        :class:`datetime.date` values.

    """

    rows = []
    timeseries = body.get("timeseries", {})
    results = timeseries.get("result", []) if isinstance(timeseries, dict) else []
    if not isinstance(results, list):
        results = []

    for result in results:
        if not isinstance(result, dict):
            continue

        metadata = result.get("meta", {})
        if not isinstance(metadata, dict):
            continue

        yahoo_metric_names = metadata.get("type", [])
        if not isinstance(yahoo_metric_names, list) or not yahoo_metric_names:
            continue

        yahoo_metric_name = yahoo_metric_names[0]
        if not isinstance(yahoo_metric_name, str):
            continue

        metric = mapping.get(yahoo_metric_name)
        if metric is None:
            continue

        items = result.get(yahoo_metric_name, [])
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            reported_value = item.get("reportedValue")
            if (
                "asOfDate" not in item
                or not isinstance(reported_value, dict)
                or "raw" not in reported_value
            ):
                continue

            try:
                value = float(reported_value["raw"])
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "ticker": ticker.lower(),
                    "metric": metric,
                    "freq": freq,
                    "date": item["asOfDate"],
                    "value": value,
                }
            )

    df = DataFrame(rows, columns=_FINANCIAL_COLUMNS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    return df.dropna(subset=["date"]).reset_index(drop=True)


def parse_dividends(body: dict, ticker: str) -> DataFrame:
    """Parse dividend data of a company.

    Dividend timestamps are exposed as civil dates because the event is tied to
    a market date rather than to a meaningful time of day. The exchange timezone
    reported by Yahoo is used when available, with the UTC date as fallback.

    Args:
        body: Body response from API.
        ticker: Ticker of company.

    Returns:
        DataFrame with dividend data and a ``ts`` column containing
        :class:`datetime.date` values.

    """

    rows = []
    timezone_name = None
    chart = body.get("chart", {})
    result = chart.get("result") if isinstance(chart, dict) else None

    if isinstance(result, list) and result and isinstance(result[0], dict):
        data = result[0]
        metadata = data.get("meta", {})
        if isinstance(metadata, dict):
            timezone_name = metadata.get("exchangeTimezoneName")
        events = data.get("events", {})
        dict_dividends = events.get("dividends", {}) if isinstance(events, dict) else {}

        if isinstance(dict_dividends, dict):
            for uts, dividend in dict_dividends.items():
                if not isinstance(dividend, dict) or "amount" not in dividend:
                    continue

                try:
                    timestamp = utils.timestamp2datetime(int(uts))
                except (TypeError, ValueError, OverflowError, OSError):
                    continue

                rows.append(
                    {
                        "ticker": ticker.lower(),
                        "ts": timestamp,
                        "dividend": dividend["amount"],
                    }
                )

    df = DataFrame(rows, columns=_DIVIDEND_COLUMNS)
    df["ts"] = _as_civil_dates(df["ts"], timezone_name)

    return df
