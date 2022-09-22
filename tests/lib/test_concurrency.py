import time
import pytest

from dag.lib import concurrency

@pytest.fixture
def mpm():
	return concurrency.multiprocess_map


@pytest.fixture
def mtm():
	return concurrency.multithread_map


def retval(val, plus = 0):
	return val + plus


def test_multiprocess_map(mpm):
	assert mpm(retval, [1,2,3,4,5]) == [1,2,3,4,5]
	assert mpm(retval, range(1,6)) == [1,2,3,4,5]

	assert mpm(retval, [1,2,3,4,5], 1) == [2,3,4,5,6]
	assert mpm(retval, range(1,6), 1) == [2,3,4,5,6]

	assert mpm(retval, ["d", "a", "g"], ".") == ["d.", "a.", "g."]


def test_multithread_map(mtm):
	assert mtm(retval, [1,2,3,4,5]) == [1,2,3,4,5]
	assert mtm(retval, range(1,6)) == [1,2,3,4,5]

	assert mtm(retval, [1,2,3,4,5], 1) == [2,3,4,5,6]
	assert mtm(retval, range(1,6), 1.5) == [2.5,3.5,4.5,5.5,6.5]