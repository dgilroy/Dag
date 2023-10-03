import pytest

from dag.lib.attribute_access_recorder import *

@pytest.fixture
def aar():
	return AttributeAccessRecorder()


class TestClass:
	testattr = "testattr"
	testdict = {"testdictkey": "testdictval"}

	def testcall(self, *args, **kwargs):
		return args, kwargs

	def __getitem__(self, idx):
		return self.testdict[idx]


@pytest.fixture
def tc():
	return TestClass()



def test_aar_attribute(aar):
	aar.test_get

	assert len(aar.stored_attrs) == 1
	assert aar.stored_attrs[0].access_recorder == aar
	assert aar.stored_attrs[0].value == "test_get"
	assert len(aar.stored_attrs) == 1


def test_aar_multi_attribute(aar):
	aar.test_get1.test_get2

	assert len(aar.stored_attrs) == 2
	assert aar.stored_attrs[0].access_recorder == aar
	assert aar.stored_attrs[0].value == "test_get1"

	assert aar.stored_attrs[1].access_recorder == aar
	assert aar.stored_attrs[1].value == "test_get2"
	assert len(aar.stored_attrs) == 2


def test_aar_call(aar):
	aar.test_call()

	assert len(aar.stored_attrs) == 2
	assert aar.stored_attrs[0].access_recorder == aar
	assert aar.stored_attrs[0].value == "test_call"

	assert aar.stored_attrs[1].access_recorder == aar
	assert aar.stored_attrs[1].value == tuple()

	assert len(aar.stored_attrs) == 2


def test_aar_call_with_args(aar):
	aar.test_call(1, "bit")

	assert len(aar.stored_attrs) == 2
	assert aar.stored_attrs[0].access_recorder == aar
	assert aar.stored_attrs[0].value == "test_call"

	assert aar.stored_attrs[1].access_recorder == aar
	assert aar.stored_attrs[1].value == (1, "bit")

	assert len(aar.stored_attrs) == 2


def test_aar_index(aar):
	aar[1]

	assert len(aar.stored_attrs) == 1
	assert aar.stored_attrs[0].access_recorder == aar
	assert aar.stored_attrs[0].value == 1

	aar["book"]

	assert aar.stored_attrs[1].access_recorder == aar
	assert aar.stored_attrs[1].value == "book"

	assert len(aar.stored_attrs) == 2


def test_aar_all_types(aar):
	aar.attr("arg")()[1]["book"]

	assert len(aar.stored_attrs) == 5

	assert aar.stored_attrs[0].access_recorder == aar
	assert aar.stored_attrs[0].value == "attr"

	assert aar.stored_attrs[1].access_recorder == aar
	assert aar.stored_attrs[1].value == ("arg",)

	assert aar.stored_attrs[2].access_recorder == aar
	assert aar.stored_attrs[2].value == ()

	assert aar.stored_attrs[3].access_recorder == aar
	assert aar.stored_attrs[3].value == 1

	assert aar.stored_attrs[4].access_recorder == aar
	assert aar.stored_attrs[4].value == "book"


def test_recorded_val(aar, tc):
	with pytest.raises(TypeError):
		rv = RecordedVal(aar, "testval")


def test_recorded_attr(aar, tc):
	testattr = "testattr"

	ra = RecordedAttr(aar, testattr)

	assert ra.get(tc) == testattr


def test_recorded_attr(aar, tc):
	testattr = "testattr"

	ra = RecordedAttr(aar, testattr)

	assert ra.get(tc) == getattr(tc, testattr)


def test_recorded_item(aar, tc):
	testdictkey = "testdictkey"

	ri = RecordedItem(aar, testdictkey)

	assert ri.get(tc) == tc[testdictkey]
	assert ri.get(tc.testdict) == tc.testdict[testdictkey]


def test_recorded_call(aar, tc):
	rc = RecordedCall(aar, "arg1", "arg2", kwarg1 = "kwarg1")
	assert rc.get(tc.testcall) == (("arg1", "arg2"), {"kwarg1": "kwarg1"})

	rc = RecordedCall(aar, "arg1", "arg2")
	assert rc.get(tc.testcall) == (("arg1", "arg2"), {})

	rc = RecordedCall(aar, kwarg1 = "kwarg1")
	assert rc.get(tc.testcall) == ((),{"kwarg1": "kwarg1"})