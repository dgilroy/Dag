import pytest

from dag.lib import comparison


@pytest.fixture
def cr():
	return comparison.ComparisonRecorder()


@pytest.fixture
def sl():
	return comparison.sortlist



def test_is_should_record_comparison(cr):
	assert cr.is_should_record_comparison()


@pytest.mark.parametrize("val", [2, "teststr", 5.5])
def test_comparison_recorder_true(cr, val):
	assert (cr == val).do_stored_comparisons_against(val)


@pytest.mark.parametrize("val", [2, "teststr", 5.5])
def test_comparison_recorder_false(cr, val):
	assert not (cr == 2).do_stored_comparisons_against(val + type(val)(1))


def test_comparison_recorder_multiple(cr):
	cr < 2
	cr < 3

	assert cr.do_stored_comparisons_against(1)
	assert not cr.do_stored_comparisons_against(100)


def test_comparison_recorder_multiple_types(cr):
	cr != 2
	cr != "woof"

	assert cr.do_stored_comparisons_against(1)



def test_comparison_recorder_multiple_one_line(cr):
	1 < cr < 5

	assert cr.do_stored_comparisons_against(4)
	assert not cr.do_stored_comparisons_against(100)


def test_comparison_recorder_empty(cr):
	assert not cr.do_stored_comparisons_against(4)


def test_is_storing_comparisons(cr):
	for op in comparison.operators:
		op(cr, 1)
		assert op in cr.stored_comparisons


def test_do_comparison_lt(cr):
	assert cr.do_comparison(3, [4,5,6,7,8], comparison.cmp_operator_names['lt'])
	assert not cr.do_comparison(3, [1,4,5,6,7,8], comparison.cmp_operator_names['lt'])

def test_do_comparison_ne(cr):
	assert cr.do_comparison(3, [4,5,6,7,8], comparison.cmp_operator_names['ne'])
	assert not cr.do_comparison(3, [3], comparison.cmp_operator_names['ne'])

def test_do_comparison_eq(cr):
	assert cr.do_comparison(3, [3,3,3], comparison.cmp_operator_names['eq'])
	assert not cr.do_comparison(3, [1, 3,3,3], comparison.cmp_operator_names['eq'])

def test_do_comparison_ge(cr):
	assert cr.do_comparison(3, [1,2,3], comparison.cmp_operator_names['ge'])
	assert not cr.do_comparison(3, [1,2,3,100.5], comparison.cmp_operator_names['ge'])



### SORTLIST ###


def test_sortlist_1_elem(sl):
	assert sl([None]) == [None]

	assert sl([True]) == [True]
	assert sl([False]) == [False]

	assert sl([5]) == [5]
	assert sl([5.5]) == [5.5]


	assert sl([""]) == [""]
	assert sl(["a"]) == ["a"]



def test_sortlist_many_homog_elems(sl):
	assert sl([None, None, None]) == [None]
	assert sl([True, False]) == [False, True]
	assert sl([True, False]*2) == [False, False, True, True]
	assert sl([9,11,7]) == [7,9,11]
	assert sl([5.5, 7.5, 3.5]) == [3.5, 5.5, 7.5]
	assert sl(["m", "a", "z"]) == ["a", "m", "z"]
	assert sl(["ac", "aa", "ab"]) == ["aa", "ab", "ac"]

	assert sl(["ac", "ac", "ac"]) == ["ac", "ac", "ac"]



def test_sortlist_many_hetero_elems(sl):
	assert sl([None, True, False]) == [None, False, True]
	assert sl([5, 4.5, 5.5, 7, 6.5, 8.6, 3, 2.5]) == [2.5, 3, 4.5, 5, 5.5, 6.5, 7, 8.6]
	assert sl(["f", "s", 3]) == [3, "f", "s"]
	assert sl(["f", "s", 3, None]) == [None, 3, "f", "s"]
	assert sl(["f", "s", 3, None, True]) == [None, True, 3, "f", "s"]
	assert sl(["f", "s", 3, None, True, False]) == [None, False, True, 3, "f", "s"]
	assert sl(["f", "s", 3, None, True, False, 3.5]) == [None, False, True, 3, 3.5, "f", "s"]