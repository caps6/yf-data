# -*- coding: utf-8 -*-
import unittest

from datetime import datetime, timedelta, timezone
from yfdata import constants, utils


class TestUtils(unittest.TestCase):

    def setUp(self):

        self.ts = 1721826284
        self.dt = datetime(2024, 7, 24, 13, 4, 44)

    def test_past_dt(self) -> None:

        dt_1W = utils.eval_past_dt(constants.T1W, date_ref=self.dt)
        dt_1M = utils.eval_past_dt(constants.T1M, date_ref=self.dt)
        dt_5Y = utils.eval_past_dt(constants.T5Y, date_ref=self.dt)

        self.assertEqual(dt_1W, self.dt - timedelta(days=7))
        self.assertEqual(dt_1M, self.dt - timedelta(days=30))
        self.assertEqual(dt_5Y, self.dt - timedelta(days=1826))

    def test_conversion(self) -> None:

        ts = utils.datetime2timestamp(utils.timestamp2datetime(self.ts))
        self.assertEqual(ts, self.ts)

        dt = utils.timestamp2datetime(utils.datetime2timestamp(self.dt))
        self.assertEqual(dt, self.dt)
