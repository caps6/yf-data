import random
from collections.abc import Callable, Sequence
from typing import Any

import pandas as pd
from curl_cffi import requests
from pandas import DataFrame

from yfdata import urls

from . import parsing
from .constants import (
    BROWSERS,
    FREQ_DAILY,
    MAPPING_BALANCE_METRICS,
    MAPPING_INCOME_METRICS,
)


class YahooProvider:
    """Provide normalized market and company data from Yahoo Finance.

    Data include OHLC values for stocks and exchange rates, and dividends and
    financial (income and balance) data of companies.

    Minute prices and exchange rates use timezone-aware UTC timestamps. Daily
    stock prices, financial reporting periods, and dividends use
    :class:`datetime.date` values. No public method returns naive datetimes.

    Args:
        http_get: HTTP callable compatible with ``curl_cffi.requests.get``.
        browsers: Browser profiles available for request impersonation.
        timeout: HTTP timeout in seconds; it must be greater than zero.

    Available metrics for the income statement are:
        - total_revenue
        - cost_of_revenue
        - gross_profit
        - operating_expense
        - operating_income
        - non_operating_interest_income_expense
        - other_income_expense
        - basic_eps
        - diluted_eps
        - basic_average_shares
        - total_expense
        - normalized_income
        - ebit
        - ebitda

    Available metrics for balance sheet are:
        - total_assets
        - total_liabilities_net_minority_interest
        - total_equity_gross_minority_interest
        - total_capitalization
        - common_stock_equity
        - capital_lease_obligations
        - net_tangible_assets
        - working_capital
        - invested_capital
        - tangible_book_value
        - total_debt
        - net_debt
        - share_issued
        - ordinary_shares_number

    Examples:
        Create the provider and get some daily stock prices.

        >>> from yfdata import YahooProvider
        >>> yp = YahooProvider()
        >>> df = yp.get_prices(["aapl"], "1D")

        Get exchange rates with frequency of 1 minute.
        >>> df = yp.get_rates("usd", "eur", freq="1m")

        Get company dividends.
        >>> df = yp.get_dividends(["aapl", "msft"])

        Get annual income data.
        >>> df = yp.get_income(["aapl", "msft"], freq="A")

        Get quarterly balance data.
        >>> df = yp.get_balance(["aapl", "msft"], freq="Q")

        Define specific income metrics to retrieve.
        >>> metrics = ["total_revenue", "ebitda"]
        >>> df = yp.get_income(["aapl", "msft"], freq="A", metrics=metrics)

    """

    def __init__(
        self,
        http_get: Callable[..., Any] = requests.get,
        browsers: Sequence[str] = BROWSERS,
        timeout: float = 30.0,
    ) -> None:
        if not browsers:
            raise ValueError("At least one browser must be provided.")
        if timeout <= 0:
            raise ValueError("Timeout must be greater than zero.")

        self._http_get = http_get
        self._browsers = tuple(browsers)
        self._timeout = timeout

    def _request_json(self, url: str) -> dict:
        response = self._http_get(
            url,
            impersonate=random.choice(self._browsers),
            timeout=self._timeout,
        )
        response.raise_for_status()
        body = response.json()

        if not isinstance(body, dict):
            raise ValueError("Yahoo Finance returned a non-object JSON response.")

        return body

    @staticmethod
    def _normalize_tickers(tickers: str | Sequence[str]) -> list[str]:
        if isinstance(tickers, str):
            return [tickers]

        tickers = list(tickers)
        if not tickers:
            raise ValueError("At least one ticker must be provided.")

        return tickers

    @staticmethod
    def _concat_frames(frames: list[DataFrame]) -> DataFrame:
        if not frames:
            raise ValueError("At least one dataframe must be provided.")

        return pd.concat(frames, ignore_index=True)

    @staticmethod
    def _build_financial_mapping(
        available_metrics: dict,
        freq: str,
        metrics: Sequence[str] | None,
    ) -> tuple[dict, dict]:
        if metrics is None:
            metrics = list(available_metrics.keys())

        unknown_metrics = set(metrics) - set(available_metrics)
        if unknown_metrics:
            formatted_metrics = ", ".join(sorted(unknown_metrics))
            raise ValueError(f"Unknown financial metrics: {formatted_metrics}")

        mapping = {}
        for metric in metrics:
            if freq not in available_metrics[metric]:
                raise ValueError(f"Frequency {freq!r} is not supported for {metric!r}.")
            mapping[metric] = available_metrics[metric][freq]

        inv_mapping = {v: k for k, v in mapping.items()}
        return mapping, inv_mapping

    def get_prices(
        self,
        tickers: str | Sequence[str],
        freq: str = FREQ_DAILY,
    ) -> DataFrame:
        """Get OHLC price data for one or more tickers.

        Daily observations use :class:`datetime.date` values in ``ts``. Minute
        observations use timezone-aware UTC timestamps.

        Args:
            tickers: A company ticker or a sequence of tickers.
            freq: Data sampling, can be ``1D`` (daily) or ``1m`` (1 minute).

        Returns:
            A DataFrame with columns ``ticker``, ``ts``, ``o``, ``h``, ``l``,
            ``c`` and ``v``. The type of ``ts`` follows the requested frequency.

        """

        dfs = []
        for ticker in self._normalize_tickers(tickers):
            url = urls.build_url_prices(ticker, freq)
            body = self._request_json(url)
            df = parsing.parse_prices_or_rates(body, ticker, freq)
            dfs.append(df)

        return self._concat_frames(dfs)

    def get_rates(self, base: str, quote: str, freq: str = FREQ_DAILY) -> DataFrame:
        """Get OHLC exchange rates for a currency pair.

        The ``ts`` column always contains timezone-aware UTC timestamps, for
        both daily and minute observations.

        Args:
            base: Base currency code, for example ``usd``.
            quote: Quote currency code, for example ``eur``.
            freq: Data sampling, can be ``1D`` (daily) or ``1m`` (1 minute).

        Returns:
            A DataFrame with columns ``pair``, ``ts``, ``o``, ``h``, ``l``,
            ``c`` and ``v``. ``pair`` is formatted as ``quote/base`` and values
            express units of the quote currency per unit of the base currency.

        """

        pair = f"{quote}/{base}"
        url = urls.build_url_rates(base, quote, freq)
        body = self._request_json(url)
        return parsing.parse_prices_or_rates(body, pair, freq)

    def get_income(
        self,
        tickers: str | Sequence[str],
        freq: str,
        metrics: Sequence[str] | None = None,
    ) -> DataFrame:
        """Get income data for one or more companies.

        Reporting periods are represented by :class:`datetime.date` values in
        the ``date`` column.

        Args:
            tickers: A company ticker or a sequence of tickers.
            freq: Period of data, can be quarterly (Q), annual (A) or trailing
                twelve months (TTM).
            metrics: Specific metrics to retrieve. All available income metrics
                are returned when omitted.

        Returns:
            A DataFrame with columns ``ticker``, ``metric``, ``freq``, ``date``
            and ``value``.

        """

        return self._get_financials(tickers, freq, MAPPING_INCOME_METRICS, metrics)

    def get_balance(
        self,
        tickers: str | Sequence[str],
        freq: str,
        metrics: Sequence[str] | None = None,
    ) -> DataFrame:
        """Get balance-sheet data for one or more companies.

        Reporting periods are represented by :class:`datetime.date` values in
        the ``date`` column.

        Args:
            tickers: A company ticker or a sequence of tickers.
            freq: Period of data, can be quarterly (Q) or annual (A).
            metrics: Specific metrics to retrieve. All available balance-sheet
                metrics are returned when omitted.

        Returns:
            A DataFrame with columns ``ticker``, ``metric``, ``freq``, ``date``
            and ``value``.

        """

        return self._get_financials(tickers, freq, MAPPING_BALANCE_METRICS, metrics)

    def _get_financials(
        self,
        tickers: str | Sequence[str],
        freq: str,
        available_metrics: dict,
        metrics: Sequence[str] | None,
    ) -> DataFrame:
        mapping, inv_mapping = self._build_financial_mapping(
            available_metrics,
            freq,
            metrics,
        )
        dfs = []

        for ticker in self._normalize_tickers(tickers):
            url = urls.build_url_financials(ticker, freq, mapping)
            body = self._request_json(url)
            df = parsing.parse_financials(body, ticker, freq, inv_mapping)
            dfs.append(df)

        return self._concat_frames(dfs)

    def get_dividends(self, tickers: str | Sequence[str]) -> DataFrame:
        """Get dividend data for one or more companies.

        Dividend events are represented by :class:`datetime.date` values in the
        ``ts`` column, using the exchange timezone reported by Yahoo when
        available and the UTC date as fallback.

        Args:
            tickers: A company ticker or a sequence of tickers.

        Returns:
            A DataFrame with columns ``ticker``, ``ts`` and ``dividend``.

        """

        dfs = []

        for ticker in self._normalize_tickers(tickers):
            url = urls.build_url_dividends(ticker)
            body = self._request_json(url)
            df = parsing.parse_dividends(body, ticker)
            dfs.append(df)

        return self._concat_frames(dfs)
