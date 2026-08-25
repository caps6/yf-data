"""Module with helpers for parsing API content returned by Yahoo API endpoints."""

import pandas as pd
from pandas import DataFrame

from yfdata import utils

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


def _empty_prices_frame(code_name: str, ticker_or_pair: str) -> DataFrame:
    df = DataFrame(columns=[*_PRICE_COLUMNS, code_name])
    df[code_name] = df[code_name].astype("object")
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    df[code_name] = ticker_or_pair.lower()
    return df[[code_name, *_PRICE_COLUMNS]]


def parse_prices_or_rates(body: dict, ticker_or_pair: str) -> DataFrame:
    """Parse OHLC data for stock prices and exchange rates.

    Args:
        body: Body response from API.
        ticker_or_pair: Ticker or currency pair.

    Returns:
        DataFrame with OHLC data.

    """

    chart = body.get("chart", {})
    result = chart.get("result") if isinstance(chart, dict) else None

    if not isinstance(result, list) or not result:
        return _empty_prices_frame(_price_code_name(ticker_or_pair), ticker_or_pair)

    data = result[0]
    if not isinstance(data, dict):
        return _empty_prices_frame(_price_code_name(ticker_or_pair), ticker_or_pair)

    metadata = data.get("meta", {})
    if not isinstance(metadata, dict):
        metadata = {}
    instrument_type = metadata.get("instrumentType")
    code_name = _price_code_name(ticker_or_pair, instrument_type)

    timestamps = data.get("timestamp")
    indicators = data.get("indicators")
    if not isinstance(timestamps, list) or not isinstance(indicators, dict):
        return _empty_prices_frame(code_name, ticker_or_pair)

    quote_items = indicators.get("quote")
    if (
        not isinstance(quote_items, list)
        or not quote_items
        or not isinstance(quote_items[0], dict)
    ):
        return _empty_prices_frame(code_name, ticker_or_pair)

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

    # Reorder the columns.
    return df[[code_name, *_PRICE_COLUMNS]]


def parse_financials(body: dict, ticker: str, freq: str, mapping: dict) -> DataFrame:
    """Parse financials data of a company.

    Args:
        body: Body response from API.
        ticker: Ticker of the company.
        freq: Period of data, can be quarterly or annual.
        mapping: Mapping from Yahoo metric names to their canonical names.

    Returns:
        DataFrame with retrieved financial data.

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

    return DataFrame(rows, columns=_FINANCIAL_COLUMNS)


def parse_dividends(body: dict, ticker: str) -> DataFrame:
    """Parse dividend data of a company.

    Args:
        body: Body response from API.
        ticker: Ticker of company.

    Returns:
        DataFrame with dividend data.

    """

    rows = []
    chart = body.get("chart", {})
    result = chart.get("result") if isinstance(chart, dict) else None

    if isinstance(result, list) and result and isinstance(result[0], dict):
        data = result[0]
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
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.date

    return df
