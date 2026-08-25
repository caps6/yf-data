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
    """Provides data from Yahoo Finance.

    Data include OHLC values for stocks and exchange rates, and dividends and
    financial (income and balance) data of companies.

    Available metrics for income sheet are:
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
        Create the provider e get some daily stock prices.

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
        >>> metrics = ["revenue", "ebitda"]
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
        """Gets OHLC price data for multiple tickers.

        Args:
            tickers: List of company tickers.
            freq: Data sampling, can be ``1D`` (daily) or ``1m`` (1 minute).

        Returns:
            A DataFrame with OHLC data for prices.

        """

        dfs = []
        for ticker in self._normalize_tickers(tickers):
            url = urls.build_url_prices(ticker, freq)
            body = self._request_json(url)
            df = parsing.parse_prices_or_rates(body, ticker)
            dfs.append(df)

        return self._concat_frames(dfs)

    def get_rates(self, base: str, quote: str, freq: str = FREQ_DAILY) -> DataFrame:
        """Gets OHLC exchange rates for multiple tickers.

        Args:
            base: Currency base.
            quote: Currency quote.
            freq: Data sampling, can be ``1D`` (daily) or ``1m`` (1 minute).

        Returns:
            A DataFrame with OHLC data for exchange rates.

        """

        pair = f"{quote}/{base}"
        url = urls.build_url_rates(base, quote, freq)
        body = self._request_json(url)
        return parsing.parse_prices_or_rates(body, pair)

    def get_income(
        self,
        tickers: str | Sequence[str],
        freq: str,
        metrics: Sequence[str] | None = None,
    ) -> DataFrame:
        """Gets income data for a list of companies.

        Args:
            tickers: List of company tickers.
            freq: Period of data, can be quarterly (Q), annual (A) or trailing
                twelwe months (TTM).
            metrics: List of specific metrics to retrieve. If None, it returns
                all metrics available for income sheet.
        Returns:
            DataFrame with financial data.

        """

        return self._get_financials(tickers, freq, MAPPING_INCOME_METRICS, metrics)

    def get_balance(
        self,
        tickers: str | Sequence[str],
        freq: str,
        metrics: Sequence[str] | None = None,
    ) -> DataFrame:
        """Gets balance data for a list of companies.

        Args:
            tickers: List of company tickers.
            freq: Period of data, can be quarterly (Q) or annual (A).
            metrics: List of specific metrics to retrieve. If None, it returns
                all metrics available for balance sheet.
        Returns:
            DataFrame with financial data.

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
        """Gets dividend data of a company.

        Args:
            tickers: List of company tickers.

        Returns:
            DataFrame with dividend data.

        """

        dfs = []

        for ticker in self._normalize_tickers(tickers):
            url = urls.build_url_dividends(ticker)
            body = self._request_json(url)
            df = parsing.parse_dividends(body, ticker)
            dfs.append(df)

        return self._concat_frames(dfs)
