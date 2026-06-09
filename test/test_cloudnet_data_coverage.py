"""
Test for Cloudnet Data Coverage script
"""

from pathlib import Path
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent.parent
EXE = SCRIPT_DIR / "run_get_data_coverage_cloudnet.py"
TEST_DIR = SCRIPT_DIR / "test" / "output"


def test_cloudnet_data_coverage():
    """
    Test that the script runs successfully with the given arguments
    """
    # Build the command using Path and subprocess
    cmd_args = [
        sys.executable,  # Use the same Python interpreter as the test
        str(EXE),  # Convert Path to str
        "--site",
        "Bucharest",
        "--site",
        "Hyytiala",
        "--site",
        "Palaiseau",
        "--date",
        "20260401",
        "20260531",
        "--output_dir",
        str(TEST_DIR),
    ]

    # Print command for debugging
    print("\n--- Command executed ---")
    print(" ".join(cmd_args))
    print("------------------------\n")

    # Execute command
    result = subprocess.run(
        cmd_args,
        text=True,
        capture_output=True,  # Capture stdout and stderr
        check=False,  # Do not raise exception automatically
    )

    # Print outputs for debugging
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    # Check that the command succeeded
    assert result.returncode == 0, (
        f"Command failed with return code {result.returncode}.\n"
        f"STDERR: {result.stderr}\n"
        f"STDOUT: {result.stdout}"
    )

    # Check that files were generated
    output_files = list(TEST_DIR.glob("*"))
    assert len(output_files) > 0, f"No files generated in {TEST_DIR}"


if __name__ == "__main__":
    test_cloudnet_data_coverage()
