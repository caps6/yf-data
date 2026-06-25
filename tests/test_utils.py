from datetime import datetime, timedelta

from yfdata import constants, utils


def test_past_dt() -> None:
    dt = datetime(2024, 7, 24, 13, 4, 44)

    assert utils.eval_past_dt(constants.T1W, date_ref=dt) == dt - timedelta(days=7)
    assert utils.eval_past_dt(constants.T1M, date_ref=dt) == dt - timedelta(days=30)
    assert utils.eval_past_dt(constants.T5Y, date_ref=dt) == dt - timedelta(days=1826)


def test_conversion() -> None:
    ts = 1721826284
    dt = datetime(2024, 7, 24, 13, 4, 44)

    assert utils.datetime2timestamp(utils.timestamp2datetime(ts)) == ts
    assert utils.timestamp2datetime(utils.datetime2timestamp(dt)) == dt
