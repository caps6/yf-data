"""Module for utility functions."""

from datetime import UTC, datetime, timedelta

from .constants import T1M, T1W, T5Y


def eval_past_dt(timeframe: str, date_ref: datetime | None = None) -> datetime:
    """Return a UTC datetime shifted backwards by a supported timeframe.

    Naive reference values are interpreted as UTC; aware values are normalized
    to UTC before applying the shift.

    Args:
        timeframe: ``1W`` (7 days), ``1M`` (30 days), or ``5Y`` (1826 days).
        date_ref: Reference datetime. Current UTC time is used when omitted.

    Returns:
        A timezone-aware UTC datetime.

    Raises:
        ValueError: If ``timeframe`` is unsupported.
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
    """Convert a datetime to an integer Unix timestamp.

    Naive values are interpreted as UTC and aware values are normalized to UTC.
    Current UTC time is used when ``date_ref`` is omitted.

    Args:
        date_ref: Datetime to convert. Current UTC time is used when omitted.

    Returns:
        Whole seconds since the Unix epoch.
    """

    if date_ref is None:
        date_ref = datetime.now(UTC)
    elif date_ref.tzinfo is None:
        date_ref = date_ref.replace(tzinfo=UTC)
    else:
        date_ref = date_ref.astimezone(UTC)

    return int(date_ref.timestamp())


def timestamp2datetime(timestamp: int) -> datetime:
    """Convert a Unix timestamp to a timezone-aware UTC datetime.

    Args:
        timestamp: Seconds since the Unix epoch.

    Returns:
        A timezone-aware UTC datetime.
    """

    return datetime.fromtimestamp(timestamp, tz=UTC)
