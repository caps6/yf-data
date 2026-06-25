import os

import pytest
from pandas import DataFrame

from yfdata import YahooProvider, constants

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("YFDATA_RUN_INTEGRATION") != "1",
        reason="Set YFDATA_RUN_INTEGRATION=1 to run Yahoo Finance integration tests.",
    ),
]


@pytest.fixture
def provider() -> YahooProvider:
    return YahooProvider()


def test_prices(provider: YahooProvider) -> None:
    df = provider.get_prices(["aapl", "msft"], freq=constants.FREQ_DAILY)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0

    df = provider.get_prices(["aapl", "msft"], freq=constants.FREQ_MINUTE)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0


def test_rates(provider: YahooProvider) -> None:
    df = provider.get_rates("usd", "eur", freq=constants.FREQ_DAILY)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0

    df = provider.get_rates("usd", "eur", freq=constants.FREQ_MINUTE)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0


def test_income(provider: YahooProvider) -> None:
    df = provider.get_income(["aapl", "msft"], constants.FREQ_QUARTERLY)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0

    df = provider.get_income(["aapl", "msft"], constants.FREQ_ANNUAL)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0

    df = provider.get_income(["aapl", "msft"], constants.TTM)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0


def test_balance(provider: YahooProvider) -> None:
    df = provider.get_balance(["aapl", "msft"], constants.FREQ_QUARTERLY)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0

    df = provider.get_balance(["aapl", "msft"], constants.FREQ_ANNUAL)
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0


def test_dividends(provider: YahooProvider) -> None:
    df = provider.get_dividends(["aapl", "msft"])
    assert isinstance(df, DataFrame)
    assert df.shape[0] > 0
