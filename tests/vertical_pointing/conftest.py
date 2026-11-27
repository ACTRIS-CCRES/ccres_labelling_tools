"""Fixtures for the vertical pointing tests.

The input files are downloaded from Cloudnet on the first run and kept in
tests/data/inputs/vertical_pointing (cached by the CI): a file already there is
not downloaded again.
"""

from pathlib import Path

import pytest

from ccres_labelling_tools.cloudnet import API_URL, SESSION, TIMEOUT

DATES = ["2026-10-30", "2026-10-31"]

# (site, product, instrument pid)
INSTRUMENTS = [
    # juelich
    ("juelich", "radar", "https://hdl.handle.net/21.12132/3.0366fa69504f4bd6"),
    ("juelich", "radar", "https://hdl.handle.net/21.12132/3.f7e002664a7a4e4e"),
    ("juelich", "radar", "https://hdl.handle.net/21.12132/3.cd8c566efe7346e0"),
    ("juelich", "mwr-l1c", "https://hdl.handle.net/21.12132/3.1668271e8d364263"),
    ("juelich", "mwr-l1c", "https://hdl.handle.net/21.12132/3.f51736b5923b483c"),
    # palaiseau
    ("palaiseau", "radar", "https://hdl.handle.net/21.12132/3.643b7b5b43814e6f"),
    ("palaiseau", "mwr-l1c", "https://hdl.handle.net/21.12132/3.770aaf228a974dd6"),
    # payerne
    ("payerne", "radar", "https://hdl.handle.net/21.12132/3.37a71c75789f47c3"),
]


def get_file_from_cloudnet(
    site: str, date: str, product: str, instrument_pid: str, local_dir: Path
) -> Path:
    """Download a file from Cloudnet if it is not already in local_dir.

    Parameters
    ----------
    site : str
        The site where the file was recorded.
    date : str
        The date when the file was recorded. format %Y-%m-%d.
    product : str
        The Cloudnet product (e.g. "radar", "mwr-l1c").
    instrument_pid : str
        The pid of the instrument that recorded the file.
    local_dir : Path
        The directory where the file should be downloaded.

    Returns
    -------
    Path
        The path to the downloaded file.

    """
    response = SESSION.get(
        f"{API_URL}/files",
        params={
            "site": site,
            "date": date,
            "product": product,
            "instrumentPid": instrument_pid,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    metadata = response.json()
    if not metadata:
        msg = f"No {product} file on Cloudnet for {site} {date} ({instrument_pid})"
        raise FileNotFoundError(msg)

    local_file = local_dir / metadata[0]["filename"]
    if local_file.is_file():
        return local_file

    file_url = metadata[0]["downloadUrl"]
    print(f"Downloading {file_url} into {local_file}")
    # write to a temporary file so that an interrupted download is not cached
    tmp_file = local_file.with_suffix(".part")
    with SESSION.get(file_url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with tmp_file.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                file.write(chunk)
    tmp_file.rename(local_file)

    return local_file


@pytest.fixture
def vertical_pointing_files(data_input_dir):
    """Download the radar and mwr files used by the tests.

    Returns a list of dict with the site, date, product, pid and path of each file.
    """
    path = data_input_dir / "vertical_pointing"
    path.mkdir(parents=True, exist_ok=True)

    return [
        {
            "site": site,
            "date": date,
            "product": product,
            "pid": pid,
            "path": get_file_from_cloudnet(site, date, product, pid, path),
        }
        for site, product, pid in INSTRUMENTS
        for date in DATES
    ]
