"""Module with helpers for parsing API content returned by Yahoo API endpoints."""

import pandas as pd
from pandas import DataFrame

from yfdata import utils

_PRICE_COLUMNS = ["ts", "o", "h", "l", "c", "v"]
_FINANCIAL_COLUMNS = ["ticker", "metric", "freq", "date", "value"]
_DIVIDEND_COLUMNS = ["ticker", "ts", "dividend"]


def _empty_prices_frame(code_name: str, ticker_or_pair: str) -> DataFrame:
    df = DataFrame(columns=[*_PRICE_COLUMNS, code_name])
    df[code_name] = df[code_name].astype("object")
    df["ts"] = pd.to_datetime(df["ts"], unit="s")
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

    result = body.get("chart", {}).get("result")

    if not isinstance(result, list) or not result:
        return _empty_prices_frame("instrument", ticker_or_pair)

    data = result[0]
    metadata = data.get("meta", {})
    instrument_type = metadata.get("instrumentType")

    if instrument_type in ("EQUITY", "ETF"):
        code_name = "ticker"
    elif instrument_type == "CURRENCY":
        code_name = "pair"
    else:
        raise ValueError("Instrument type not supported.")

    if (
        not isinstance(data, dict)
        or "timestamp" not in data
        or "indicators" not in data
    ):
        return _empty_prices_frame(code_name, ticker_or_pair)

    quotes = data["indicators"].get("quote", [{}])[0]
    df = DataFrame(
        data={
            "ts": data["timestamp"],
            "o": quotes.get("open", []),
            "h": quotes.get("high", []),
            "l": quotes.get("low", []),
            "c": quotes.get("close", []),
            "v": quotes.get("volume", []),
        }
    )

    df[code_name] = ticker_or_pair.lower()
    df["ts"] = pd.to_datetime(df["ts"], unit="s")

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
    results = body.get("timeseries", {}).get("result", [])

    for result in results:
        yahoo_metric_names = result.get("meta", {}).get("type", [])
        if not yahoo_metric_names:
            continue

        yahoo_metric_name = yahoo_metric_names[0]
        metric = mapping.get(yahoo_metric_name)
        if metric is None:
            continue

        for item in result.get(yahoo_metric_name, []):
            if item is None:
                continue

            rows.append(
                {
                    "ticker": ticker.lower(),
                    "metric": metric,
                    "freq": freq,
                    "date": item["asOfDate"],
                    "value": float(item["reportedValue"]["raw"]),
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
    result = body.get("chart", {}).get("result")

    if isinstance(result, list) and result:
        data = result[0]
        dict_dividends = data.get("events", {}).get("dividends", {})

        for uts, dividend in dict_dividends.items():
            if "amount" in dividend:
                rows.append(
                    {
                        "ticker": ticker.lower(),
                        "ts": utils.timestamp2datetime(int(uts)),
                        "dividend": dividend["amount"],
                    }
                )

    df = DataFrame(rows, columns=_DIVIDEND_COLUMNS)
    df["ts"] = pd.to_datetime(df["ts"], unit="s").dt.date

    return df
