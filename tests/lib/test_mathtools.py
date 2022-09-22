import pytest
from dag.lib import mathtools

@pytest.fixture
def mt():
	return mathtools

@pytest.fixture
def em():
	return mathtools.eval_math

def test_eval_math(em):
	assert em("3+3") == 6, "Addition didn't work"
	assert em("4-3") == 1, "Subtraction didn't work"
	assert em("4*3") == 12, "Multiplication didn't work"
	assert em("12/3") == 4, "True Division didn't work"
	assert em("12//5") == 2, "Floor Division didn't work"
	assert em("2**3") == 8, "Pow didn't work"
	assert em("-1") == -1, "Negation didn't work"
	assert em("12%5") == 2, "Modulus didn't work"