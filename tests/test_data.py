# -*- coding: utf-8 -*-
import unittest

from yfdata import constants, urls, YahooProvider

from pandas import DataFrame


class TestData(unittest.TestCase):

    def setUp(self):

        self.yp = YahooProvider()
        self.tickers = ["aapl", "msft"]

    def test_prices(self) -> None:
        """Tests provider for prices."""

        df = self.yp.get_prices(["aapl", "msft"], freq=constants.FREQ_DAILY)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

        df = self.yp.get_prices(["aapl", "msft"], freq=constants.FREQ_MINUTE)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

    def test_rates(self) -> None:
        """Tests provider for exchange rates."""

        df = self.yp.get_rates("usd", "eur", freq=constants.FREQ_DAILY)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

        df = self.yp.get_rates("usd", "eur", freq=constants.FREQ_MINUTE)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

    def test_income(self) -> None:
        """Tests provider for income data."""

        df = self.yp.get_income(["aapl", "msft"], constants.FREQ_QUARTERLY)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

        df = self.yp.get_income(["aapl", "msft"], constants.FREQ_ANNUAL)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

        df = self.yp.get_income(["aapl", "msft"], constants.TTM)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

    def test_balance(self) -> None:
        """Tests provider for balance data."""

        df = self.yp.get_balance(["aapl", "msft"], constants.FREQ_QUARTERLY)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

        df = self.yp.get_balance(["aapl", "msft"], constants.FREQ_ANNUAL)
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)

    def test_dividends(self) -> None:
        """Tests provider for dividends."""

        df = self.yp.get_dividends(["aapl", "msft"])
        self.assertIsInstance(df, DataFrame)
        self.assertTrue(df.shape[0] > 0)
