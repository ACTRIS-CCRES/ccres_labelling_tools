"""Tests for vertical pointing (radar, mwr) script."""

import shutil

import pandas as pd
from click.testing import CliRunner

from ccres_labelling_tools.vertical_pointing.cli import (
    main as vertical_pointing_main,
)


def test_vertical_pointing(conf_pointing_dir, vertical_pointing_files, data_output_dir):
    """Test that the script computes the vertical pointing of each instrument."""
    input_dir = vertical_pointing_files[0]["path"].parent
    output_dir = data_output_dir / "vertical_pointing"
    # remove the outputs of a previous run so that they cannot hide a failure
    shutil.rmtree(output_dir, ignore_errors=True)

    runner = CliRunner()
    result = runner.invoke(
        vertical_pointing_main,
        [
            "--site",
            "Juelich",
            "--site",
            "Palaiseau",
            "--site",
            "Payerne",
            "--date",
            "20261001",
            "20261031",
            "--conf-nfs",
            str(conf_pointing_dir.parent / "conf_nf_ccres.py"),
            "--conf-params",
            str(conf_pointing_dir / "params.py"),
            "--input_dir",
            str(input_dir),
            "--output_dir",
            str(output_dir),
        ],
    )

    # Check that the command succeeded
    assert result.exit_code == 0, (
        f"Command failed with return code {result.exit_code}.\n"
        f"{result.output}\n{result.exception}"
    )

    # Check that each instrument has values on the days with a file
    for file in vertical_pointing_files:
        site, date = file["site"], file["date"]
        short_pid = file["pid"].split(".")[-1][:8]
        instrument_type = "mwr" if file["product"] == "mwr-l1c" else "radar"
        csv_files = list(
            (output_dir / site).glob(
                f"*_{short_pid}_{instrument_type}_vertical_pointing.csv"
            )
        )
        assert len(csv_files) == 1, f"No output for {site} {short_pid}"

        df = pd.read_csv(csv_files[0], index_col=0, parse_dates=True)
        day = df.loc[date, "percentage_vertical_pointing"]
        assert day.notna().any(), f"No value for {site} {short_pid} on {date}"
