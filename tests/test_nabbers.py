from contextlib import contextmanager

import pytest

from dag.util import nabbers


TESTVAL = "val"

class MockDagmod:
	item = TESTVAL

	def return_a(self):
		return a

	def ret(self, arg):
		return arg


class MockNabber(nabbers.Nabber):
	def _nab(self):
		return getattr(self.dagmod, self.val)




@pytest.fixture
def md():
	return MockDagmod()

@pytest.fixture
def mn():
	return MockNabber


@pytest.mark.parametrize("item", ["STR", 2, {"K":"V"}, ("STR", 2, {"K":"V"}, [1,2])])
def test_nab_if_nabber_without_nabber(md, item):
	assert nabbers.nab_if_nabber(item) == item


@pytest.mark.parametrize("item", ["item", "return_a"])
def test_nab_if_nabber_wtih_nabber(mn, md, item):
	assert nabbers.nab_if_nabber(mn(item)) == getattr(md, item)

