"""Process vertical pointing data."""

from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import xarray as xr

from ccres_labelling_tools import cloudnet
from ccres_labelling_tools.utils import extract_short_pid


def get_instrument_filename(
    site: str,
    date: pd.Timestamp,
    instrument_type: str,
    spid: str,
    input_dir: Path,
    params: ModuleType,
    radar_id: str | None = None,
) -> Path | None:
    """Return the instrument filename if an existing file is found.

    Parameters
    ----------
    site : str
        _description_
    date : pd.Timestamp
        _description_
    instrument_type : str
        _description_
    spid : str
        _description_
    input_dir : Path
        _description_
    params : ModuleType
        _description_
    radar_id : str | None, optional
        _description_, by default None

    Returns
    -------
    Path | None
        _description_

    Raises
    ------
    ValueError
        _description_
    ValueError
        _description_
    """
    file_patterns = []

    if instrument_type == "radar":
        if radar_id is None:
            msg = "radar_id must be provided for radar instruments"
            raise ValueError(msg)

        if "rpg" in radar_id and "94" in radar_id:
            file_patterns = [
                params.RPG_94_FILE1.format(date_file=date, station_name=site),
                params.RPG_94_FILE2.format(date_file=date, station_name=site, pid=spid),
            ]

        elif "rpg" in radar_id and "35" in radar_id:
            file_patterns = [
                params.RPG_35_FILE1.format(date_file=date, station_name=site),
                params.RPG_35_FILE2.format(date_file=date, station_name=site, pid=spid),
            ]

        elif "mira" in radar_id and "35" in radar_id:
            file_patterns = [
                params.MIRA_35_FILE1.format(date_file=date, station_name=site),
                params.MIRA_35_FILE2.format(
                    date_file=date, station_name=site, pid=spid
                ),
                params.MIRA_35_FILE3.format(
                    date_file=date, station_name=site, pid=spid
                ),
            ]

        elif "basta" in radar_id:
            file_patterns = [
                params.BASTA_FILE1.format(date_file=date, station_name=site),
                params.BASTA_FILE2.format(date_file=date, station_name=site, pid=spid),
            ]

    elif instrument_type == "mwr":
        file_patterns = [
            params.MWR_L1C_FILE1.format(date_file=date, station_name=site),
            params.MWR_L1C_FILE2.format(date_file=date, station_name=site, pid=spid),
        ]

    else:
        msg_0 = f"Unsupported instrument type: {instrument_type}"
        raise ValueError(msg_0)

    # Return the first existing file, following the pattern priority
    for file in file_patterns:
        full_path = input_dir / file

        if full_path.is_file():
            return full_path

    return None


def get_radar_time_resolution(ds: xr.Dataset) -> int:
    """_summary_

    Parameters
    ----------
    ds : xr.Dataset
        _description_

    Returns
    -------
    float
        _description_
    """
    time_diffs = ds.time.values[1:] - ds.time.values[:-1]  # noqa: PD011
    time_diffs_seconds = time_diffs.astype("float64") / 1e9

    return round(np.median(time_diffs_seconds))


def create_empty_df(
    perfect_day_dates: pd.DatetimeIndex, params: ModuleType
) -> pd.DataFrame:
    """_summary_

    Parameters
    ----------
    perfect_day_dates : pd.DatetimeIndex
        _description_
    params : ModuleType
        _description_

    Returns
    -------
    pd.DataFrame
        _description_
    """
    return pd.DataFrame.from_dict(
        {
            "time": perfect_day_dates,
            "percentage_vertical_pointing": np.ones([params.NB_HOURS_PER_DAY]) * np.nan,
        }
    ).set_index("time")


def get_percentage_vertical_pointing_radar(
    ds: xr.Dataset,
    perfect_day_dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Calculate hourly vertical pointing coverage for a cloud radar."""
    time_hours = pd.to_datetime(ds["time"].values).floor("h")

    # Exclude the first timestamp (initialization / incomplete interval)
    df = pd.DataFrame({"hour": time_hours[1:]})

    hourly_counts = df.groupby("hour").size()

    expected_radar_time_res = get_radar_time_resolution(ds)
    expected_steps_per_hour = 3600 / expected_radar_time_res

    hourly_coverage = (hourly_counts / expected_steps_per_hour * 100).round(2)

    hourly_coverage = hourly_coverage.reindex(perfect_day_dates)

    return hourly_coverage.to_frame(name="percentage_vertical_pointing")


def get_percentage_vertical_pointing_mwr(
    ds: xr.Dataset,
    perfect_day_dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Calculate hourly vertical pointing percentage for a microwave radiometer."""
    pointing_flag = ds["pointing_flag"].to_series()

    # Group observations by hour
    hourly = pointing_flag.index.floor("h")

    total_obs_per_hour = pointing_flag.groupby(hourly).count()

    vertical_obs_per_hour = pointing_flag.eq(0).groupby(hourly).sum()

    # Calculate percentage of vertical pointing observations
    hourly_percentage = (vertical_obs_per_hour / total_obs_per_hour * 100).round(2)

    # Reindex to include all expected hours
    hourly_percentage = hourly_percentage.reindex(perfect_day_dates)

    return hourly_percentage.to_frame(name="percentage_vertical_pointing")


def define_list_sites(new_sites: str | None, conf: ModuleType) -> str:
    """_summary_

    Parameters
    ----------
    new_sites : _type_
        _description_
    conf : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    return new_sites if new_sites is not None else conf.sites.keys()


def get_month_starts(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """First day of each month between start and end."""
    start = pd.Period(start, freq="M")
    end = pd.Period(end, freq="M")
    return pd.period_range(start, end, freq="M").to_timestamp(how="start")


def get_month_ends(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Last day of each month between start and end."""
    start = pd.Period(start, freq="M")
    end = pd.Period(end, freq="M")
    return pd.period_range(start, end, freq="M").to_timestamp(how="end").normalize()


def get_instruments(config: dict, instrument_type: str) -> dict:
    """Return all instruments of a given type, ordered by category.

    Nominal instruments are listed first, followed by additional instruments.
    Instrument identifiers are renumbered sequentially, starting from "1".

    Args:
        config (dict): Station configuration dictionary.
        instrument_type (str): Instrument type (e.g. "radar", "mwr", "lidar").

    Returns:
        dict: Dictionary mapping sequential identifiers to instrument PIDs.
    """
    instruments = {}

    # Process nominal instruments first, then additional instruments
    for category in ("nominal_instrument", "additional_instrument"):
        instrument = config.get(category, {}).get(instrument_type)

        # Normalize instrument entries to a list of PIDs
        if isinstance(instrument, str):
            instrument = [instrument]
        elif isinstance(instrument, dict):
            instrument = list(instrument.values())
        else:
            continue

        # Assign sequential identifiers, skipping missing PIDs
        for pid in instrument:
            if pid is not None:
                instruments[str(len(instruments) + 1)] = pid

    return instruments


def instruments(  # noqa: C901
    new_sites: list[str],
    new_date_start: pd.Timestamp,
    new_date_end: pd.Timestamp,
    input_dir: Path,
    output_dir: Path,
    conf: ModuleType,
    params: ModuleType,
) -> None:
    """_summary_

    Parameters
    ----------
    new_sites : _type_
        _description_
    new_date_start : _type_
        _description_
    new_date_end : _type_
        _description_
    input_dir : _type_
        _description_
    output_dir : _type_
        _description_
    conf : _type_
        _description_
    params : _type_
        _description_
    """
    # Loop over sites
    # -------------------------------------
    sites_to_analyzed = define_list_sites(new_sites, conf)
    instrument_ids = cloudnet.get_instrument_ids()

    for site in sites_to_analyzed:
        print(site)
        station = conf.sites[site]  # get conf for a specific site

        for instrument_type in ["radar", "mwr"]:
            instruments = get_instruments(station, instrument_type)

            # Get PID-s
            pids = list(instruments.values())
            short_pids = [extract_short_pid(pid) for pid in instruments.values()]

            # Do monthly analysis per instrument (PID)
            for short_pid, pid in zip(short_pids, pids, strict=False):
                radar_id = instrument_ids.get(pid, "")
                if instrument_type == "radar" and not radar_id:
                    msg = f"Unknown instrument PID on Cloudnet: {pid}"
                    raise ValueError(msg)
                months_start = get_month_starts(new_date_start, new_date_end)
                months_end = get_month_ends(new_date_start, new_date_end)
                for month_start, month_end in zip(
                    months_start, months_end, strict=False
                ):
                    dfs_day = []
                    perfect_month_dates = pd.date_range(
                        month_start, month_end, freq="1D"
                    )
                    for date in perfect_month_dates:
                        perfect_day_dates = pd.date_range(
                            date, date + pd.Timedelta(hours=23, minutes=59), freq="1h"
                        )

                        # Get filename
                        # -------------------------------------------------
                        if instrument_type == "radar":
                            filename = get_instrument_filename(
                                site,
                                date,
                                instrument_type,
                                short_pid,
                                input_dir,
                                params,
                                radar_id,
                            )
                        elif instrument_type == "mwr":
                            filename = get_instrument_filename(
                                site,
                                date,
                                instrument_type,
                                short_pid,
                                input_dir,
                                params,
                            )

                        # manage no file
                        # -------------------------------------------------
                        if filename is None:
                            tmp_df = create_empty_df(perfect_day_dates, params)
                            dfs_day.append(tmp_df)
                            continue

                        # read file and calculate vertical pointing
                        # --------------------------------------------------
                        with xr.open_dataset(filename) as ds:
                            if instrument_type == "radar":
                                if ds.instrument_pid != pid:
                                    tmp_df = create_empty_df(perfect_day_dates, params)
                                else:
                                    tmp_df = get_percentage_vertical_pointing_radar(
                                        ds, perfect_day_dates
                                    )
                            elif instrument_type == "mwr":
                                if ds.instrument_pid != pid:
                                    tmp_df = create_empty_df(perfect_day_dates, params)
                                else:
                                    tmp_df = get_percentage_vertical_pointing_mwr(
                                        ds, perfect_day_dates
                                    )
                        dfs_day.append(tmp_df)
                    df_day = pd.concat(dfs_day, axis=0)

                    # Save
                    # --------------------------------------------------
                    if instrument_type == "radar":
                        filename = (
                            output_dir
                            / site
                            / f"{site}_{month_start.strftime('%Y%m%d')}_{month_end.strftime('%Y%m%d')}_{radar_id.lower()}_{short_pid}_radar_vertical_pointing.csv"  # noqa:E501
                        )
                    elif instrument_type == "mwr":
                        filename = (
                            output_dir
                            / site
                            / f"{site}_{month_start.strftime('%Y%m%d')}_{month_end.strftime('%Y%m%d')}_{short_pid}_mwr_vertical_pointing.csv"  # noqa:E501
                        )
                    filename.parent.mkdir(parents=True, exist_ok=True)
                    df_day.to_csv(filename, float_format="%.2f")
