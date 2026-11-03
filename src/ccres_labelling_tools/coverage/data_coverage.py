"""Process Coverage data."""

from collections import Counter
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd
import requests

from ccres_labelling_tools.coverage.plot import plot_data_coverage_v2
from ccres_labelling_tools.coverage.utils import round_to_last_complete_month

BASE = "https://cloudnet.fmi.fi/api"  # TODO: params

# L2 products derived from categorize: their validity is the one of categorize
L2_PRODUCTS = ["categorize", "classification"]  # TODO: add all L2 products ?

# Shared session: reuse the connection to the API instead of opening a new one
# (and doing a TLS handshake) for each request
SESSION = requests.Session()


def get_file(uuid: str) -> dict:
    """_summary_

    Parameters
    ----------
    uuid : str
        _description_

    Returns
    -------
    dict
        _description_
    """
    r = SESSION.get(f"{BASE}/files/{uuid}")
    r.raise_for_status()
    return r.json()


def normalize_pids(nominal: str) -> list:
    """str -> [str]"""
    if nominal is None:
        return []
    if isinstance(nominal, dict):
        return list(nominal.values())
    return [nominal]


def get_instrument_uuids(
    site: str,
    month_start: pd.Timestamp,
    month_end: pd.Timestamp,
    pids: list,
) -> set[str]:
    """Return the uuids of all the files (any product) produced by the instruments.

    Parameters
    ----------
    site : str
        cloudnet site
    month_start : pd.Timestamp
        start of the period
    month_end : pd.Timestamp
        end of the period
    pids : list
        instruments PIDs

    Returns
    -------
    set[str]
        uuids of the files
    """
    uuids = set()
    for pid in pids:
        # without product, all the products of the instrument are returned
        r = SESSION.get(
            f"{BASE}/files",
            params={
                "site": site,
                "dateFrom": month_start.strftime("%Y-%m-%d"),
                "dateTo": month_end.strftime("%Y-%m-%d"),
                "instrumentPid": pid,
            },
        )
        r.raise_for_status()
        uuids.update(f["uuid"] for f in r.json())
    return uuids


def get_categorize_validity(
    site: str,
    month_start: pd.Timestamp,
    month_end: pd.Timestamp,
    station: dict,
    params: ModuleType,
) -> dict[str, bool]:
    """Check for each day if categorize was produced with nominal radar and mwr.

    Parameters
    ----------
    site : str
        cloudnet site
    month_start : pd.Timestamp
        start of the period
    month_end : pd.Timestamp
        end of the period
    station : dict
        station configuration
    params : ModuleType
        parameters

    Returns
    -------
    dict[str, bool]
        validity of categorize per measurement date (YYYY-MM-DD)
    """
    radar_uuids = get_instrument_uuids(
        site,
        month_start,
        month_end,
        normalize_pids(station["nominal_instrument"]["radar"]),
    )
    mwr_uuids = get_instrument_uuids(
        site,
        month_start,
        month_end,
        normalize_pids(station["nominal_instrument"]["mwr"]),
    )

    resp = SESSION.get(
        params.url_geophysical.format(
            site=site,
            date_start=month_start.strftime("%Y-%m-%d"),
            date_end=month_end.strftime("%Y-%m-%d"),
            product="categorize",
        )
    )
    resp.raise_for_status()

    validity = {}
    for categorize in resp.json():
        sources = set(get_file(categorize["uuid"]).get("sourceFileIds") or [])
        validity[categorize["measurementDate"]] = bool(
            sources & radar_uuids and sources & mwr_uuids
        )
    return validity


def define_request_and_call(product: str, station: dict) -> tuple[str, str]:
    """_summary_

    Parameters
    ----------
    product : str
        _description_
    station : dict
        _description_

    Returns
    -------
    _type_
        _description_
    """
    # Define request & call
    # -----------------------------------------------------
    if product in ["mwr-l1c", "mwr-single", "mwr-multi"]:
        product_request = "mwr"
        product_call = product
    elif (product == "weather-station") & (
        station["nominal_instrument"]["weather-station"]
        == station["nominal_instrument"]["mwr"]
    ):
        product_request = "mwr"
        product_call = "mwr-l1c"  # use weather station from mwr hatpro
    # elif product in ["doppler-lidar", "doppler-lidar-wind"]:  # noqa: ERA001
    #     product_request = "doppler-lidar"  # noqa: ERA001
    #     product_call = product  # noqa: ERA001
    else:
        product_request = product
        product_call = product
    return product_request, product_call


def get_most_present_pid(
    site: str,
    month_start: pd.Timestamp,
    month_end: pd.Timestamp,
    product_call: str,
    pids: pd.DataFrame,
    params: ModuleType,
) -> str | None:
    """Return the PID that yields the most valid results from the instrument API."""
    pid_counts = Counter()

    for pid in pids.values():
        resp = SESSION.get(
            params.url_instrument.format(
                site=site,
                date_start=month_start.strftime("%Y-%m-%d"),
                date_end=month_end.strftime("%Y-%m-%d"),
                product=product_call,
                pid=pid,
            )
        )

        prod_data = resp.json()
        if prod_data:
            for d in prod_data:
                pid_found = d.get("instrument", {}).get("pid")
                if pid_found:
                    pid_counts[pid_found] += 1

    # Choose the PID with the highest count
    return pid_counts.most_common(1)[0][0] if pid_counts else None


def get_pid(
    product_request: str,
    product_call: str,
    month_start: pd.Timestamp,
    month_end: pd.Timestamp,
    site: str,
    station: dict,
    params: ModuleType,
) -> str:
    """_summary_

    Parameters
    ----------
    product_request : str
        _description_
    product_call : str
        _description_
    month_start : pd.Timestamp
        _description_
    month_end : pd.Timestamp
        _description_
    site : str
        _description_
    station : dict
        _description_
    params : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    # If multiple successive instruments
    # -----------------------------------------------------
    if isinstance(
        station["nominal_instrument"][product_request],
        dict,
    ):
        pid = get_most_present_pid(
            site,
            month_start,
            month_end,
            product_call,
            station["nominal_instrument"][product_request],
            params,
        )  # TODO: crappy: find better solution
    else:
        pid = station["nominal_instrument"][product_request]
    return pid


def define_analysis_period(
    new_date_start: pd.Timestamp | None,
    new_date_end: pd.Timestamp,
    station: dict,
) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """_summary_

    Parameters
    ----------
    new_date_start : _type_
        _description_
    new_date_end : _type_
        _description_
    station : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    if new_date_start is not None:
        months_start = pd.date_range(new_date_start, new_date_end, freq="1MS")
        months_end = pd.date_range(new_date_start, new_date_end, freq="1ME")
    else:
        date_start = station["date_start_1b"]
        date_end = round_to_last_complete_month()
        months_start = pd.date_range(date_start, date_end, freq="1MS")
        months_end = pd.date_range(date_start, date_end, freq="1ME")
    return months_start, months_end


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


def cloudnet(  # noqa:C901
    new_sites: list[str],
    new_date_start: pd.Timestamp,
    new_date_end: pd.Timestamp,
    output_dir: Path,
    makeplot: bool,  # noqa: FBT001
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
    output_dir : _type_
        _description_
    makeplot : bool
        _description_
    conf : _type_
        _description_
    params : _type_
        _description_
    """
    # Loop over sites
    # -------------------------------------
    sites_to_analyzed = define_list_sites(new_sites, conf)

    for site in sites_to_analyzed:
        station = conf.sites[site]  # get conf for a specific site

        # Do analysis per full year
        year_start = new_date_start.replace(month=1, day=1)
        year_end = new_date_end.replace(month=12, day=31)
        years_start = pd.date_range(year_start, year_end, freq="1YS")
        years_end = pd.date_range(year_start, year_end, freq="1YE")
        for ys, ye in zip(years_start, years_end):  # noqa: B905
            months_start, months_end = define_analysis_period(ys, ye, station)
            dfs_station = []

            # Loop over whole year
            # -------------------------------------
            for month_start, month_end in zip(months_start, months_end):  # noqa: B905
                if (month_start < new_date_start) or (month_end > new_date_end):
                    continue
                print(site)
                print(
                    "\tfrom",
                    month_start.strftime("%Y-%m-%d"),
                    "to",
                    month_end.strftime("%Y-%m-%d"),
                )
                dfs = []  # list df per product
                categorize_validity = None  # nominal instruments check for L2
                perfect_month_dates = pd.date_range(month_start, month_end, freq="1D")

                # Loop over products
                # -------------------------------------
                for product in params.all_products:
                    print("\t\t", product)
                    backup_data = None

                    # ------------------------------------------------------
                    # request instrumental products - wit pid
                    # ------------------------------------------------------
                    if product in params.instrument_products:
                        # 1 - get request & call for API
                        # ---------------------------------------
                        product_request, product_call = define_request_and_call(
                            product, station
                        )
                        if station["nominal_instrument"][product_request]:
                            # 2 - get relative PID
                            # ---------------------------------------
                            pid = get_pid(
                                product_request,
                                product_call,
                                month_start,
                                month_end,
                                site,
                                station,
                                params,
                            )

                            # 3 - Do request
                            # ---------------------------------------
                            resp = SESSION.get(
                                params.url_instrument.format(
                                    site=site,
                                    date_start=month_start.strftime("%Y-%m-%d"),
                                    date_end=month_end.strftime("%Y-%m-%d"),
                                    product=product_call,
                                    pid=pid,
                                )
                            )
                        # if instrument but any reason does not work
                        # ----------------------------------------------------
                        else:  # request as geophysical products -> without pid
                            resp = SESSION.get(
                                params.url_geophysical.format(
                                    site=site,
                                    date_start=month_start.strftime("%Y-%m-%d"),
                                    date_end=month_end.strftime("%Y-%m-%d"),
                                    product=product_call,
                                )
                            )

                        # 4 - Backup instrument (if any) request
                        # ------------------------------------------
                        if product_request in conf.sites[site]["additional_instrument"]:
                            print("\t\t+1 backup", product_request)
                            pid_backup = conf.sites[site]["additional_instrument"][
                                product_request
                            ]
                            resp_backup = SESSION.get(
                                params.url_instrument.format(
                                    site=site,
                                    date_start=month_start.strftime("%Y-%m-%d"),
                                    date_end=month_end.strftime("%Y-%m-%d"),
                                    product=product_call,
                                    pid=pid_backup,
                                )
                            )
                            backup_data = resp_backup.json()

                    # ------------------------------------------------------
                    # request geophysical products - without pid
                    # ------------------------------------------------------
                    elif product in params.geophysical_products:
                        product_request = product
                        resp = SESSION.get(
                            params.url_geophysical.format(
                                site=site,
                                date_start=month_start.strftime("%Y-%m-%d"),
                                date_end=month_end.strftime("%Y-%m-%d"),
                                product=product,
                            )
                        )
                    else:
                        print("\t\t\t--> PROBLEM with", product)
                        print("\t\t\t--> Please double check, something WRONG !")

                    # --------------------------------------
                    # Analyze resp json
                    # --------------------------------------
                    prod_data = resp.json()
                    if product in L2_PRODUCTS:
                        # computed once per month, shared by all L2 products
                        if categorize_validity is None:
                            categorize_validity = get_categorize_validity(
                                site, month_start, month_end, station, params
                            )

                        for d in prod_data:
                            if not categorize_validity.get(d["measurementDate"], False):
                                # remove coverage info -> to be not considered
                                d.pop("coverage", None)

                    df = process_data(
                        prod_data,
                        product,
                        perfect_month_dates,
                        conf.sites,
                        site,
                        product_request,
                    )
                    dfs.append(df)

                    if backup_data is not None:
                        backup_df = process_data(
                            backup_data,
                            product,
                            perfect_month_dates,
                            conf.sites,
                            site,
                            product_request,
                            is_backup=True,
                        )
                        dfs.append(backup_df)

                # --------------------------------------
                # Get final df & save
                # --------------------------------------
                final_df = pd.concat(dfs, axis=1)
                final_df.index.name = "dates"
                filename = (
                    output_dir
                    / site
                    / f"{month_start.strftime('%Y%m%d')}_{month_end.strftime('%Y%m%d')}_{site}_cloudnet_data_coverage.csv"  # noqa:E501
                )
                filename.parent.mkdir(parents=True, exist_ok=True)
                final_df.to_csv(filename, float_format="%.2f")
                dfs_station.append(final_df)

            # --------------------------------------
            # Plot
            # --------------------------------------
            if makeplot:
                df2plot = pd.concat(dfs_station).sort_index(ascending=True)
                plot_data_coverage_v2(
                    site, station, df2plot, months_start, output_dir, params
                )
                print("Plot saved")


def process_data(  # noqa: D103
    data: pd.DataFrame,
    product_name: str,
    perfect_month_dates: int,
    sites: dict,
    site: str,
    product_request: str,
    is_backup: bool = False,  # noqa: FBT001 FBT002
) -> pd.DataFrame:
    if data:
        measurement_dates, product_coverages = [], []
        for d in data:
            if d.get("coverage"):
                measurement_dates.append(pd.Timestamp(d["measurementDate"]))
                product_coverages.append(d["coverage"] * 100)
            else:
                measurement_dates.append(pd.Timestamp(d["measurementDate"]))
                product_coverages.append(np.nan)

        df = pd.DataFrame.from_dict(
            {
                "date": measurement_dates,
                f"{product_name}{'_backup' if is_backup else ''}": product_coverages,
            }
        ).set_index("date")
        df = df.loc[~df.index.duplicated(keep=False), :]
        df = df.reindex(perfect_month_dates)
    else:
        if product_request in sites[site]["nominal_instrument"]:
            if sites[site]["nominal_instrument"][product_request] is None:
                df = pd.DataFrame.from_dict(
                    {
                        "date": perfect_month_dates,
                        f"{product_name}{'_backup' if is_backup else ''}": np.ones(
                            len(perfect_month_dates)
                        )
                        * -1,
                    }
                ).set_index("date")
            else:
                df = pd.DataFrame.from_dict(
                    {
                        "date": perfect_month_dates,
                        f"{product_name}{'_backup' if is_backup else ''}": np.ones(
                            len(perfect_month_dates)
                        )
                        * np.nan,
                    }
                ).set_index("date")
        else:  # if no geophysical product outputs
            df = pd.DataFrame.from_dict(
                {
                    "date": perfect_month_dates,
                    f"{product_name}": np.ones(len(perfect_month_dates)) * np.nan,
                }
            ).set_index("date")
    return df
