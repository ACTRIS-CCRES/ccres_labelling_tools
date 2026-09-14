"""Tests for Cloudnet data coverage script."""

from click.testing import CliRunner

from ccres_labelling_tools.coverage.cli import main as cloud_coverage_main


def test_cloudnet_data_coverage(conf_coverage_dir, data_output_dir):
    """Test that the script runs successfully with the given arguments."""
    runner = CliRunner()
    result = runner.invoke(
        cloud_coverage_main,
        [
            "--site",
            "Bucharest",
            "--site",
            "Hyytiala",
            "--site",
            "Palaiseau",
            "--date",
            "20260401",
            "20260531",
            "--conf-nfs",
            str(conf_coverage_dir / "conf_nf_ccres.py"),
            "--conf-params",
            str(conf_coverage_dir / "params.py"),
            "--output_dir",
            str(data_output_dir),
            "--makeplot",
            "True",
        ],
    )

    # Check that the command succeeded
    assert result.exit_code == 0, (
        f"Command failed with return code {result.exit_code}.\n"
    )

    # Check that files were generated
    output_files = list(data_output_dir.glob("*"))
    assert len(output_files) > 0, f"No files generated in {data_output_dir}"
