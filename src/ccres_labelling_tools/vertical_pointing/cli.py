#!/usr/bin/env python
"""Script to get Doppler Cloud Radar and Miwrowave Radiometer
vertical pointing time percentages from Cloudnet's products (radar, mwr l1c)
for different National Facilities on a monthly time basis
"""  # noqa: D205

import datetime as dt
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import click
import pandas as pd

from ccres_labelling_tools.vertical_pointing import check_vertical_pointing

__author__ = "jean-francois.ribaud@ipsl.fr"


@click.command()
@click.option(
    "--site",
    type=str,
    required=True,
    multiple=True,
    help="List of sites (e.g., --site bucharest --site palaiseau --site munich)",
)
@click.option(
    "--date",
    type=(
        click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
        click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    ),
    required=True,
    nargs=2,
    help="Date start and date end (e.g., --date 20260101 20261231)",
)
@click.option(
    "--conf-nfs",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
    required=True,
    help="Path to the configuration file for the national facility",
)
@click.option(
    "--conf-params",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
    required=True,
    help="Path to the configuration file for the parameters",
)
@click.option(
    "--input_dir",
    "-i",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        path_type=Path,
    ),
    required=True,
    help="input directory",
)
@click.option(
    "--output_dir",
    "-o",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        writable=True,
        path_type=Path,
    ),
    required=True,
    help="output directory",
)
def main(
    site: tuple[str, ...],
    date: tuple[dt.datetime, dt.datetime],
    conf_nfs: Path,
    conf_params: Path,
    input_dir: Path,
    output_dir: Path,
) -> int:
    """Calculate the vertical pointing for the given sites and date range"""
    # 1 - Get conf & params
    # --------------------------------------------------
    conf_spec = spec_from_file_location("conf", conf_nfs)
    conf = module_from_spec(conf_spec)
    conf_spec.loader.exec_module(conf)

    params_spec = spec_from_file_location("params", conf_params)
    params = module_from_spec(params_spec)
    params_spec.loader.exec_module(params)

    # 2 - Define output directory
    # --------------------------------------------------
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3 - get site(s)
    # --------------------------------------------------
    sites = [s.lower() for s in site]
    invalid_sites = [s for s in sites if s not in conf.sites]
    for s in invalid_sites:
        print(f"WARNING: '{s}' SITE DOES NOT BELONG TO CONFIG FILE ! (ignored)")
    # keep only valid sites
    sites = [s for s in sites if s in conf.sites]
    if not sites:
        msg = f"none of the sites belong to {conf_nfs}"
        raise click.BadParameter(msg, param_hint="--site")

    # 4 - get dates
    # --------------------------------------------------
    new_date_start, new_date_end = (pd.Timestamp(d) for d in date)

    # 5 - main loop
    # --------------------------------------------------
    check_vertical_pointing.instruments(
        sites, new_date_start, new_date_end, input_dir, output_dir, conf, params
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
