"""Tests for vertical pointing (radar, mwr) script."""

from click.testing import CliRunner

from ccres_labelling_tools.vertical_pointing.cli import (
    main as vertical_pointing_main,
)


def test_vertical_pointing(conf_pointing_dir, data_input_dir, data_output_dir):
    """Test that the script runs successfully with the given arguments."""
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
            str(data_input_dir / "vertical_pointing"),
            "--output_dir",
            str(data_output_dir / "vertical_pointing"),
        ],
    )

    print("Exit code:", result.exit_code)
    print("Output:", result.output)
    print("Exception:", result.exception)

    # Check that the command succeeded
    assert result.exit_code == 0, (
        f"Command failed with return code {result.exit_code}.\n"
    )

    # Check that files were generated
    output_files = list(data_output_dir.glob("*"))
    assert len(output_files) > 0, f"No files generated in {data_output_dir}"
