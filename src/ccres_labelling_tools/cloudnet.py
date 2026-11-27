"""Requests to the Cloudnet API."""

import pandas as pd
import requests

API_URL = "https://cloudnet.fmi.fi/api"
TIMEOUT = 30  # seconds

# Shared session: reuse the connection to the API instead of opening a new one
# (and doing a TLS handshake) for each request
SESSION = requests.Session()


def get_file(uuid: str) -> dict:
    """Return the metadata of a file.

    Parameters
    ----------
    uuid : str
        uuid of the file

    Returns
    -------
    dict
        metadata of the file (e.g. its "sourceFileIds")
    """
    r = SESSION.get(f"{API_URL}/files/{uuid}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_files(
    site: str,
    date_start: pd.Timestamp,
    date_end: pd.Timestamp,
    product: str | None = None,
    pid: str | None = None,
) -> list[dict]:
    """Return the metadata of the files of a site over a period.

    Parameters
    ----------
    site : str
        cloudnet site
    date_start : pd.Timestamp
        start of the period
    date_end : pd.Timestamp
        end of the period
    product : str | None, optional
        product, by default all the products
    pid : str | None, optional
        instrument PID, by default all the instruments

    Returns
    -------
    list[dict]
        metadata of the files
    """
    r = SESSION.get(
        f"{API_URL}/files",
        # requests leaves out the parameters set to None
        params={
            "site": site,
            "dateFrom": date_start.strftime("%Y-%m-%d"),
            "dateTo": date_end.strftime("%Y-%m-%d"),
            "product": product,
            "instrumentPid": pid,
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def get_instrument_ids() -> dict[str, str]:
    """Return the Cloudnet instrument id (e.g. "mira-35") of each instrument PID.

    All the instruments are fetched in a single request.

    Returns
    -------
    dict[str, str]
        instrument id for each instrument PID
    """
    r = SESSION.get(f"{API_URL}/instrument-pids", timeout=TIMEOUT)
    r.raise_for_status()
    return {item["pid"]: item["instrument"]["id"] for item in r.json()}
