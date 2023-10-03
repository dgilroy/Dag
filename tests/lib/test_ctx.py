import pytest

from dag.lib import ctxmanagers


@pytest.fixture
def cx():
	return ctx.Context()


testval = "TESTVAL"
testval2 = 2

def test_ctx_manager(cx):
	with cx.manager(testvar = testval):
		assert cx.testvar == testval
		assert cx.Invalid is None

	assert cx.testvar is None


def test_ctx_manager_many(cx):
	with cx.manager(testvar = testval, testvar2 = 5):
		assert cx.testvar == testval
		assert cx.testvar2 == 5
		assert cx.Invalid is None


def test_ctx_manager_depth(cx):
	with cx.manager(testvar = testval, testvar2 = 5):
		with cx.manager(testvar3 = 2.2):
			assert cx.testvar == testval
			assert cx.testvar2 == 5
			assert cx.testvar3 == 2.2
			assert cx.Invalid is None

		assert cx.testvar3 is None
		assert testvar == testval


def test_ctx_manager_replacements(cx):
	with cx.manager(testvar = testval):
		assert cx.testvar == testval

		with cx.manager(testvar = testval2):
			assert cx.testvar == testval2

		assert cx.testvar == testval
