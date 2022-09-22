import pytest

from dag.lib import proxy_descriptor


TESTATTR = "test_attr"
TESTVAL = "test_val"

class InternalObj:
	def __init__(self):
		setattr(self, TESTATTR, TESTVAL)

class ExternalObj:
	def __init__(self):
		self.storage = InternalObj()

		setattr(self.__class__, TESTATTR, proxy_descriptor.ProxyDescriptor("storage", TESTATTR))


@pytest.fixture
def pd():
	return proxy_descriptor.ProxyDescriptor

@pytest.fixture
def eo():
	return ExternalObj()


def test_proxydescriptor(eo):
	assert getattr(eo, TESTATTR) == TESTVAL