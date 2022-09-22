import pytest
from dag.lib import dot


TESTDICT = {"hello": "goodbye", "bool": False, "none": None, "int": 3, "float": 3.3}

TESTDICT2 = {"NEWKEY": "NEWVAL", "float": 4.4}

@pytest.fixture
def dd():
	return dot.DotDict(TESTDICT)

@pytest.fixture
def dd2():
	return dot.DotDict(TESTDICT2)



def test_dislikes_nonstring_key():
	with pytest.raises(ValueError):
		dot.DotDict({2,3})

@pytest.mark.parametrize("item", TESTDICT.keys())
def test_getitem(dd, item):
	assert dd[item] == TESTDICT[item]

def test_setitem(dd):
	dd["TEST"] = "TESTVAL"
	assert dd.TEST == "TESTVAL"

def test_delitem(dd):
	del dd['hello']
	assert 'hello' not in dd

def test_iter(dd):
	assert set(iter(dd)) == set(TESTDICT)

def test_len(dd):
	assert len(dd) == len(TESTDICT)

@pytest.mark.parametrize("item", TESTDICT.keys())
def test_getattr(dd, item):
	assert getattr(dd, item) == TESTDICT[item]

def test_getattr_none_default(dd):
	assert dd.NOT_A_VAL is None

def test_getattr_dot(dd):
	assert dd.hello == "goodbye"

def test_setattr(dd):
	dd.TEST = "TESTVAL"
	assert dd.TEST == "TESTVAL"

def test_dot_or(dd, dd2):
	dd3 = dd | dd2

	assert dd3.hello == "goodbye"
	assert dd3.NEWKEY == "NEWVAL"
	assert dd3.float == 4.4

def test_mapping_or(dd):
	dd3 = dd | TESTDICT2

	assert dd3.hello == "goodbye"
	assert dd3.NEWKEY == "NEWVAL"
	assert dd3.float == 4.4

def test_dot_ior(dd, dd2):
	dd |= dd2

	assert dd.hello == "goodbye"
	assert dd.NEWKEY == "NEWVAL"
	assert dd.float == 4.4

def test_mapping_ior(dd):
	dd |= TESTDICT2

	assert dd.hello == "goodbye"
	assert dd.NEWKEY == "NEWVAL"
	assert dd.float == 4.4

def test_mapping_ror(dd):
	dd3 = TESTDICT2 | dd

	assert dd3.hello == "goodbye"
	assert dd3.NEWKEY == "NEWVAL"
	assert dd3.float == 3.3
