"""Fixtures for pytest."""

from pathlib import Path

import pytest


@pytest.fixture
def root_dir(request):
    path = request.config.rootdir
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return Path(path)


@pytest.fixture
def data_dir(root_dir):
    path = root_dir / "tests" / "data"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return path


@pytest.fixture
def data_input_dir(data_dir):
    path = data_dir / "inputs"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return path


@pytest.fixture
def data_output_dir(data_dir):
    path = data_dir / "outputs"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    return path


@pytest.fixture
def conf_dir(root_dir):
    return root_dir / "conf"


@pytest.fixture
def conf_coverage_dir(conf_dir):
    return conf_dir / "coverage"
