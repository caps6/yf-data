from datetime import UTC, datetime, timedelta, timezone

from yfdata import constants, utils


def test_past_dt() -> None:
    dt = datetime(2024, 7, 24, 13, 4, 44, tzinfo=UTC)

    assert utils.eval_past_dt(constants.T1W, date_ref=dt) == dt - timedelta(days=7)
    assert utils.eval_past_dt(constants.T1M, date_ref=dt) == dt - timedelta(days=30)
    assert utils.eval_past_dt(constants.T5Y, date_ref=dt) == dt - timedelta(days=1826)


def test_conversion() -> None:
    ts = 1721826284
    dt = datetime(2024, 7, 24, 13, 4, 44, tzinfo=UTC)

    assert utils.datetime2timestamp(utils.timestamp2datetime(ts)) == ts
    assert utils.timestamp2datetime(utils.datetime2timestamp(dt)) == dt


def test_naive_datetime_is_interpreted_as_utc() -> None:
    naive = datetime(1970, 1, 1, 0, 0, 1)

    assert utils.datetime2timestamp(naive) == 1


def test_aware_datetime_is_normalized_to_utc() -> None:
    utc_plus_two = timezone(timedelta(hours=2))
    date_ref = datetime(1970, 1, 1, 2, 0, 1, tzinfo=utc_plus_two)

    assert utils.datetime2timestamp(date_ref) == 1
    assert utils.timestamp2datetime(1) == datetime(1970, 1, 1, 0, 0, 1, tzinfo=UTC)
