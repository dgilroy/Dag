import pytest
from dag.lib import colors

@pytest.fixture
def ctf():
	return colors


@pytest.mark.parametrize("prefix", ["", "#"])
def test_ctags_expand_hexstr(ctf, prefix):
	assert ctf.expand_hexstr(f"{prefix}F") == "FFFFFF"
	assert ctf.expand_hexstr(f"{prefix}f") == "FFFFFF"
	assert ctf.expand_hexstr(f"{prefix}F0") == "F0F0F0"
	assert ctf.expand_hexstr(f"{prefix}F00") == "FF0000"
	assert ctf.expand_hexstr(f"{prefix}FF00FF") == "FF00FF"

	with pytest.raises(AttributeError):
		assert ctf.expand_hexstr("faoiwejf")

	with pytest.raises(AttributeError):
		assert ctf.get_valid_hex(f"{prefix}8888")