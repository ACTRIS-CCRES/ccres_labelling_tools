import pandas as pd


def round_to_last_complete_month(ts=None):
    """
    Return the last day of the last 'complete' month.
    - If ts is the last day of the current month -> return that day (current month).
    - Otherwise -> return the last day of the previous month.
    If ts is None, pd.Timestamp.now() is used.
    """
    ts = pd.Timestamp.now() if ts is None else pd.Timestamp(ts)
    # Normalize to midnight (keeps timezone if present)
    ts_norm = ts.normalize()

    # Last day of the current month
    last_day_current = (ts + pd.offsets.MonthEnd(0)).normalize()

    if ts_norm == last_day_current:
        # Today is the last day of the current month -> return it
        return last_day_current
    else:
        # Otherwise, go to the first day of current month, subtract 1 day
        # -> gives the last day of the previous month
        last_day_prev = (ts.replace(day=1) - pd.Timedelta(days=1)).normalize()
        return last_day_prev
