"""
script to get daily data coverage info associated to Cloudnet's products
for different National Facilities on a monthly time basis
"""

from pathlib import Path
import sys
from importlib.util import spec_from_file_location, module_from_spec

from analysis import data_coverage

import click

__version__ = "0.0.1"
__author__ = "jean-francois.ribaud@ipsl.fr"

# TODO: add logger


@click.command()
@click.option(
    "--site",
    type=str,
    multiple=True,
    help="List of sites (e.g., --site bucharest --site palaiseau --site munich)",
)
@click.option(
    "--date",
    type=(
        click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
        click.DateTime(formats=["%Y%m%d", "%Y-%m-%d"]),
    ),
    nargs=2,
    help="Date start and date end (e.g., --date 20260101 20261231)",
)
@click.option(
    "--output_dir",
    "-o",
    default=Path(__file__).parent / "outputs",
    help="output directory",
)
def main(site, date, output_dir):
    # 1 - Get conf & params
    # --------------------------------------------------
    conf_dir = Path(__file__).parent / "conf"
    conf_path = conf_dir / "conf_nf_ccres.py"
    conf_spec = spec_from_file_location("conf", conf_path)
    conf = module_from_spec(conf_spec)
    conf_spec.loader.exec_module(conf)

    params_path = conf_dir / "params.py"
    params_spec = spec_from_file_location("params", params_path)
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

    # 4 - get dates (if any)
    # --------------------------------------------------
    if date:
        new_date_start, new_date_end = date
    else:
        new_date_start, new_date_end = None, None

    # 5 - main loop
    # --------------------------------------------------
    data_coverage.cloudnet(
        sites, new_date_start, new_date_end, output_dir, conf, params
    )


if __name__ == "__main__":
    sys.exit(main())
