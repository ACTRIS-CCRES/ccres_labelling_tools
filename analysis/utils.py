import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def extract_short_pid(full_pid: str) -> str:
    """
    Extracts the short pid from cloudnet instrument (8 hexadecimal characters after the last '.')
    from a full pid in the format 'https://hdl.handle.net/.../3.442ec2ea9a24440e'.

    Args:
        full_pid (str): The full pid (e.g., "https://hdl.handle.net/21.12132/3.442ec2ea9a24440e").

    Returns:
        str: The short pid (e.g., "442ec2ea").

    Raises:
        ValueError: If the full pid format is invalid.
    """
    match = re.search(r"\.([a-f0-9]{8})", full_pid)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid full pid format.")


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


def check_vars_in_df(df: pd.DataFrame, vars: list) -> pd.DataFrame:
    # check if all columns are in
    missing_col = [miss_col for miss_col in vars if miss_col not in df.columns]

    print("Missing columns :", missing_col)

    # Add missing columns with NaN
    for miss_col in missing_col:
        df[miss_col] = np.nan

    # reshape
    df = df[vars]

    return df


def add_logo(
    logo_name="CCRES_logo.png",
    left=0.75,
    bottom=0.925,
    width=0.15,
    height=0.08,
):
    """
    add logos to the current plot on top right corner

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
    except IOError:
        print("PLOT: Impossible to include the logo")

    return
