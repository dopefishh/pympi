import pathlib

import pytest


@pytest.fixture
def test_dir():
    return pathlib.Path(__file__).parent
