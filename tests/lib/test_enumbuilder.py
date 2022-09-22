import pytest

from dag.lib import enumbuilder


@pytest.fixture
def de():
	return enumbuilder.build_enum("cow", "pig", bird = "CAW")


def test_build_enum(de):
	assert de.COW.name == "COW"
	assert de.COW.value == 0

	assert de.PIG.name == "PIG"
	assert de.PIG.value == 1

	assert de.BIRD.name == "BIRD"
	assert de.BIRD.value == "CAW"

	with pytest.raises(AttributeError):
		de.BANANA

	with pytest.raises(AttributeError):
		de.cow