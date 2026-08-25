"""Module for utility functions."""

from datetime import UTC, datetime, timedelta

from .constants import T1M, T1W, T5Y


def eval_past_dt(timeframe: str, date_ref: datetime | None = None) -> datetime:
    """Computes a datetime in the past according to a given timeframe or to
    given number of minutes. All datetimes are in UTC zone.

    Allowed values for timeframe are:
    - '1D' (1 day ago),
    - '1M' (1 month ago),

    """

    if date_ref is None:
        date_ref = datetime.now(UTC)
    elif date_ref.tzinfo is None:
        date_ref = date_ref.replace(tzinfo=UTC)
    else:
        date_ref = date_ref.astimezone(UTC)

    if timeframe is not None:
        if timeframe == T1W:
            dt = date_ref - timedelta(days=7)
        elif timeframe == T1M:
            dt = date_ref - timedelta(days=30)
        elif timeframe == T5Y:
            dt = date_ref - timedelta(days=1826)
        else:
            raise ValueError("Timeframe not supported.")

    else:
        raise ValueError("A value for timeframe or minutes must be defined.")

    return dt


def datetime2timestamp(date_ref: datetime | None = None) -> int:
    """Convert a datetime to a Unix timestamp, interpreting naive values as UTC."""

    if date_ref is None:
        date_ref = datetime.now(UTC)
    elif date_ref.tzinfo is None:
        date_ref = date_ref.replace(tzinfo=UTC)
    else:
        date_ref = date_ref.astimezone(UTC)

    return int(date_ref.timestamp())


def timestamp2datetime(timestamp: int) -> datetime:
    """Convert a Unix timestamp to a timezone-aware UTC datetime."""

    return datetime.fromtimestamp(timestamp, tz=UTC)
