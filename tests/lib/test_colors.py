from fractions import Fraction
from decimal import Decimal

import pytest
from dag.lib import colors


def test_to255():
	assert colors.to255(.5) == 127
	assert colors.to255(0) == 0
	assert colors.to255(1) == 255
	assert colors.to255(Fraction(1,2)) == 127
	assert colors.to255(Decimal(0.5)) == 127


@pytest.mark.parametrize("prefix", ["", "#"])
def test_ctags_expand_hexstr(prefix: str) -> None:
	assert colors.expand_hexstr(f"{prefix}F") == "FFFFFF"
	assert colors.expand_hexstr(f"{prefix}f") == "FFFFFF"
	assert colors.expand_hexstr(f"{prefix}F0") == "F0F0F0"
	assert colors.expand_hexstr(f"{prefix}F00") == "FF0000"
	assert colors.expand_hexstr(f"{prefix}FF00FF") == "FF00FF"

	with pytest.raises(AttributeError):
		assert colors.expand_hexstr("faoiwejf")

	with pytest.raises(AttributeError):
		assert colors.get_valid_hex(f"{prefix}8888")