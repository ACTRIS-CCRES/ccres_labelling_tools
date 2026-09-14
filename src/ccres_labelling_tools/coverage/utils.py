"""Utility functions for coverage analysis and plotting."""

import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def extract_short_pid(full_pid: str) -> str:
    """Extracts the short pid from cloudnet instrument (8 hexadecimal characters after the last '.')

    From a full pid in the format 'https://hdl.handle.net/.../3.442ec2ea9a24440e'.

    Args:
        full_pid (str): The full pid (e.g., "https://hdl.handle.net/21.12132/3.442ec2ea9a24440e").

    Returns:
        str: The short pid (e.g., "442ec2ea").

    Raises:
        ValueError: If the full pid format is invalid.
    """  # noqa: E501
    match = re.search(r"\.([a-f0-9]{8})", full_pid)
    if match:
        return match.group(1)
    raise ValueError("Invalid full pid format.")  # noqa: EM101 TRY003


def round_to_last_complete_month(ts: pd.Timestamp | None = None) -> pd.Timestamp:
    """Return the last day of the last 'complete' month.

    * If ts is the last day of the current month -> return that day (current month).
    * Otherwise -> return the last day of the previous month.
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
    # Otherwise, go to the first day of current month, subtract 1 day
    # -> gives the last day of the previous month
    return (ts.replace(day=1) - pd.Timedelta(days=1)).normalize()


def check_vars_in_df(df: pd.DataFrame, list_vars: list) -> pd.DataFrame:
    """Check if all variables are in the dataframe, if not add them with NaN values."""
    # check if all columns are in
    missing_col = [miss_col for miss_col in list_vars if miss_col not in df.columns]

    print("Missing columns :", missing_col)

    # Add missing columns with NaN
    for miss_col in missing_col:
        df[miss_col] = np.nan

    # reshape
    df = df[list_vars]

    return df


def add_logo(
    logo_name: str = "CCRES_logo.png",
    left: float = 0.75,
    bottom: float = 0.925,
    width: float = 0.15,
    height: float = 0.08,
) -> None:
    """add logos to the current plot on top right corner

    Parameters
    ----------
    dirname: str
        directory name
    station: str
        station name
    """
    plt.axes([left, bottom, width, height])
    plt.axis("off")

    try:
        logo = plt.imread(f"assets/logo/{logo_name}")
        plt.imshow(logo, origin="upper")
    except OSError:
        print("PLOT: Impossible to include the logo")
