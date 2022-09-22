import pytest
from dag.lib import strtools

@pytest.fixture
def st():
	return strtools

@pytest.fixture
def qs():
	return strtools.is_valid_quoted_string


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