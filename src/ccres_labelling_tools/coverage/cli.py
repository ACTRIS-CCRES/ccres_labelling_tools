#!/usr/bin/env python
"""Script to get daily data coverage from to Cloudnet's products.

Can for different National Facilities on a monthly time basis
"""

import datetime as dt
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import click

from ccres_labelling_tools.coverage import data_coverage

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
@click.option(
    "--makeplot",
    type=bool,
    default=False,
)
def main(
    site: str,
    date: dt.datetime,
    conf_nfs: Path,
    conf_params: Path,
    output_dir: Path,
    makeplot: bool = False,  # noqa: FBT001 FBT002
) -> int:
    """Calculate the data coverage for the given sites and date range, and optionally generate plots."""  # noqa: E501
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
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3 - get site(s)
    # --------------------------------------------------
    if site:
        sites = [s.lower() for s in site]
        invalid_sites = [s for s in sites if s not in conf.sites]
        if invalid_sites:
            for s in invalid_sites:
                print(f"WARNING: '{s}' SITE DOES NOT BELONG TO CONFIG FILE ! (ignored)")
        # keep only valid sites
        sites = [s for s in sites if s in conf.sites]
    else:
        sites = None
        return 0

    # 4 - get dates
    # --------------------------------------------------
    if date:
        new_date_start, new_date_end = date
    else:
        new_date_start, new_date_end = None, None
        return 0

    # 5 - main loop
    # --------------------------------------------------
    data_coverage.cloudnet(
        sites, new_date_start, new_date_end, output_dir, makeplot, conf, params
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
