import numpy as np
import pandas as pd
import requests

from collections import Counter

from analysis.utils import round_to_last_complete_month


def define_request_and_call(product: str, station: dict):
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
    # elif product in ["doppler-lidar", "doppler-lidar-wind"]:
    #     product_request = "doppler-lidar"
    #     product_call = product
    else:
        product_request = product
        product_call = product
    return product_request, product_call


def get_most_present_pid(site, month_start, month_end, product_call, pids, params):
    """Return the PID that yields the most valid results from the instrument API."""
    pid_counts = Counter()

    for pid in pids.values():
        resp = requests.get(
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
    if pid_counts:
        best_pid = pid_counts.most_common(1)[0][0]
    else:
        best_pid = None

    return best_pid  # dict(pid_counts)


def get_pid(
    product_request: str,
    product_call: str,
    month_start: pd.Timestamp,
    month_end: pd.Timestamp,
    site: str,
    station: dict,
    params,
):
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
        # print(
        #     month_start,
        #     month_end,
        #     product_call,
        #     station["nominal_instrument"][product_request],
        # )
        pid = get_most_present_pid(
            site,
            month_start,
            month_end,
            product_call,
            station["nominal_instrument"][product_request],
            params,
        )  # TODO: crappy: find better solution
        # print("\t\t\tmost frequent pid", pid)
    else:
        pid = station["nominal_instrument"][product_request]
    return pid


def define_analysis_period(new_date_start, new_date_end, station):
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
        months_end = pd.date_range(new_date_start, new_date_end, freq="1M")
    else:
        date_start = station["date_start_1b"]
        date_end = round_to_last_complete_month()
        months_start = pd.date_range(date_start, date_end, freq="1MS")
        months_end = pd.date_range(date_start, date_end, freq="1M")
    return months_start, months_end


def define_list_sites(new_sites, conf):
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
    if new_sites is not None:
        sites_to_analyzed = new_sites
    else:
        sites_to_analyzed = conf.sites.keys()
    return sites_to_analyzed


def cloudnet(new_sites, new_date_start, new_date_end, output_dir, conf, params):
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
        #
        months_start, months_end = define_analysis_period(
            new_date_start, new_date_end, station
        )
        # Loop over whole period
        # -------------------------------------
        for month_start, month_end in zip(months_start, months_end):
            print(site)
            print(
                "\tfrom",
                month_start.strftime("%Y-%m-%d"),
                "to",
                month_end.strftime("%Y-%m-%d"),
            )
            dfs = []  # list df per product
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
                        resp = requests.get(
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
                        resp = requests.get(
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
                        resp_backup = requests.get(
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
                    resp = requests.get(
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
            # print(final_df)
            # print("\n\n")
            filename = (
                output_dir
                / f"{month_start.strftime('%Y%m%d')}_{month_end.strftime('%Y%m%d')}_{site}_cloudnet_data_coverage.csv"
            )
            # print("\t\t", filename, "saved")
            final_df.to_csv(filename, float_format="%.2f")


def process_data(
    data,
    product_name,
    perfect_month_dates,
    sites,
    site,
    product_request,
    is_backup=False,
):
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
