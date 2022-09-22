import pytest
from dag.lib import words

@pytest.fixture
def st():
	return words

@pytest.fixture
def pl():
	return words.pluralize

@pytest.fixture
def pq():
	return words.pluralize_by_quantity

@pytest.fixture
def qt():
	return words.quantize

@pytest.fixture
def qi():
	return words.quantize_or_ignore



@pytest.mark.parametrize("quotemark", ["'", '"'])
def test_is_valid_quoted_string(qs, quotemark):
	qm = quotemark

	assert qs(f'{qm}Wow I am a valid string{qm}')
	assert qs(f'{qm}{qm}')
	assert not qs(f'{qm}')
	assert not qs(f'{qm}{qm}{qm}')
	assert qs(f'{qm}\\{qm}{qm}')
	assert not qs(f'{qm}\\\\{qm}{qm}')
	assert not qs(f'{qm}Wow I {qm}am not a valid string{qm}')
	assert qs(f'{qm}Wow I \\{qm}am a valid string{qm}')
	assert qs(f'{qm}Wow I \\{qm}am a valid string{qm}')
	assert not qs(f'{qm}Wow I \"am a valid string{qm}GGG')
	assert not qs(f'{qm}Wow I am not a valid string\\{qm}')
	assert not qs(f'\\{qm}Wow I am not a valid string\\{qm}')
	assert not qs(f'\\{qm}Wow I am a valid string\\\\{qm}')
	assert not qs(f'{qm}{qm}Wow I am not a valid string\\{qm}')


def test_pluralize(pl):
	assert pl("wow") == "wows"
	assert pl("bush") == "bushes"
	assert pl("bus") == "buses"
	assert pl("baby") == "babies"


def test_pluralize_by_quantity(pq):
	assert pq(0, "item") == "items"
	assert pq(1, "item") == "item"
	assert pq(1.5, "item") == "items"
	assert pq(2, "item") == "items"
	assert pq(2, "item", "itemz") == "itemz"

def test_quantize(qt):
	assert qt(-1, "item") == "-1 items"
	assert qt(0, "item") == "0 items"
	assert qt(1, "item") == "1 item"
	assert qt(1.5, "item") == "1.5 items"
	assert qt(2, "item") == "2 items"
	assert qt(2, "item", "itemz") == "2 itemz"

def test_quantize_or_ignore(qi):
	assert qi(0, "item") == ""
	assert qi(1, "item") == "1 item"
	assert qi(2, "item") == "2 items"
	assert qi(2, "item", "itemz") == "2 itemz"