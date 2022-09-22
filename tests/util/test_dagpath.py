import pytest

from dag.util import dagpath

@pytest.fixture
def dp():
	return dagpath.DagPath


def test_contains(dp):
	assert dp("/wow") in dp("/")