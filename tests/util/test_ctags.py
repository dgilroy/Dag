import pytest

from dag.lib import term, colors
from dag.util import ctags


@pytest.fixture
def ct():
	yield ctags
	print("\x1b[0m") # Closes any straggling styles

@pytest.fixture
def ctag():
	yield ctags.CTag
	print("\x1b[0m") # Closes any straggling styles


@pytest.fixture
def ctf():
	yield ctags.CTagFormatter
	print("\x1b[0m") # Closes any straggling styles

@pytest.fixture
def ctf8():
	yield ctags.CTagFormatter8Bit
	print("\x1b[0m") # Closes any straggling styles

@pytest.fixture
def ctf24():
	yield ctags.CTagFormatter24Bit
	print("\x1b[0m") # Closes any straggling styles

@pytest.fixture
def sys24b(mocker):
	# Including this as a test parameter makes the system report that it's 24b color
	mocker.patch("dag.lib.platforms.Platform.is_24b_color", return_value = True)




@pytest.mark.parametrize("use24b", [True, False])
def test_ctag_formatter_xterm(ct, use24b):
	formatted = ct.format("<c red>TEST</c>", use_24b = use24b)
	assert formatted == "\x1b[38;5;9mTEST\x1b[0m"

	formatted = ct.format("<c bold red>TEST</c>", use_24b = use24b)
	assert formatted == "\x1b[1m\x1b[38;5;9mTEST\x1b[0m"

	formatted = ct.format("<c bold red>TEST</c red> ENDTAG</c>", use_24b = use24b)
	assert formatted == "\x1b[1m\x1b[38;5;9mTEST\x1b[0m\x1b[1m ENDTAG\x1b[0m"

	formatted = ct.format("<c INVALIDCOLOR>TEST</c>", use_24b = use24b)
	assert formatted == "TEST\x1b[0m"

	formatted = ct.format("<c bg-red>TEST</c>", use_24b = use24b)
	assert formatted == "\x1b[48;5;9mTEST\x1b[0m"


@pytest.mark.parametrize("hexval", ["#F00", "#FF0000"])
def test_ctag_formatter_hex(ct, hexval):
	formatted = ct.format(f"<c {hexval}>TEST</c>", use_24b = False)
	assert formatted == "\x1b[38;5;196mTEST\x1b[0m"

	formatted = ct.format(f"<c {hexval}>TEST</c>", use_24b = True)
	assert formatted == "\x1b[38;2;255;0;0mTEST\x1b[0m"

	formatted = ct.format(f"<c bg-{hexval}>TEST</c>", use_24b = False)
	assert formatted == "\x1b[48;5;196mTEST\x1b[0m"

	formatted = ct.format(f"<c bg-{hexval}>TEST</c>", use_24b = True)
	assert formatted == "\x1b[48;2;255;0;0mTEST\x1b[0m"


def test_ctag_formatter_2term_hex(ct):
	formatted = ct.format("<c #80>TEST</c>", use_24b = False)
	assert formatted == "\x1b[38;5;244mTEST\x1b[0m"

	formatted = ct.format("<c #80>TEST</c>", use_24b = True)
	assert formatted == "\x1b[38;2;128;128;128mTEST\x1b[0m"

	formatted = ct.format("<c bg-#80>TEST</c>", use_24b = False)
	assert formatted == "\x1b[48;5;244mTEST\x1b[0m"

	formatted = ct.format("<c bg-#80>TEST</c>", use_24b = True)
	assert formatted == "\x1b[48;2;128;128;128mTEST\x1b[0m"


def test_get_xterm_color_code_xterm_color(ctf):
	# Xterm Numbers
	assert ctf.get_xterm_color_code("1") == "1"
	assert ctf.get_xterm_color_code("11") == "11"
	assert ctf.get_xterm_color_code("111") == "111"
	assert ctf.get_xterm_color_code("1111") == ""


def test_get_xterm_color_code_hex(ctf8, ctf24):
	# Hex Strings
	assert ctf8.get_xterm_color_code("#00") == "16"
	assert ctf24.get_xterm_color_code("#00") == "0;0;0"
	assert ctf24.get_xterm_color_code("#FE0000") == "254;0;0"
	assert ctf24.get_xterm_color_code("#fe0000") == "254;0;0"


def test_get_xterm_color_code_xterm_name(ctf):
	# Xterm name
	assert ctf.get_xterm_color_code("black") == "0"
	assert ctf.get_xterm_color_code("GREY") == "8"


def test_get_xterm_color_code_invalid(ctf):
	# Invalid Strings
	assert ctf.get_xterm_color_code("bbb") == ""
	assert ctf.get_xterm_color_code("#jx") == ""
	assert ctf.get_xterm_color_code("#FFF000000") == ""


def test_get_style_sequence_xterm_style(ctf):
	for style in term.get_terminal().stylemap:
		assert ctf.get_style_sequence(style) == term.get_terminal().stylemap[style]


def test_get_style_sequence_xterm_number(ctf, ctf8, ctf24):
	# Xterm Numbers
	assert ctf.get_style_sequence("1") == "\x1b[38;5;1m"
	assert ctf.get_style_sequence("11") == "\x1b[38;5;11m"
	assert ctf.get_style_sequence("111") == "\x1b[38;5;111m"
	assert ctf.get_style_sequence("1111") == ""


def test_get_style_sequence_hex(ctf, ctf8, ctf24):
	# Hex Strings
	assert ctf8.get_style_sequence("#00") == "\x1b[38;5;16m"
	assert ctf24.get_style_sequence("#00") == '\x1b[38;2;0;0;0m'
	assert ctf24.get_style_sequence("#FE0000") == '\x1b[38;2;254;0;0m'
	assert ctf24.get_style_sequence("#fe0000") == '\x1b[38;2;254;0;0m'


def test_get_style_sequence_xterm_color(ctf, ctf8, ctf24):
	# Xterm name
	assert ctf.get_style_sequence("black") == "\x1b[38;5;0m"
	assert ctf.get_style_sequence("GREY") == "\x1b[38;5;8m"


def test_get_style_sequence_invalid(ctf, ctf8, ctf24):
	# Invalid Strings
	assert ctf8.get_style_sequence("bbb") == ""
	assert ctf8.get_style_sequence("#jx") == ""
	assert ctf8.get_style_sequence("#FFF000000") == ""



teststr = " TEST "
teststr2 = " TEST2 "

def test_ctag_format_24b(ct, sys24b):
	assert ct.format(f"<c #FF0000>{teststr}</c>") == f"\x1b[38;2;255;0;0m{teststr}\x1b[0m"

def test_ctag_format_24b_2_styles(ct, sys24b):
	assert ct.format(f"<c #FF0000 bold>{teststr}</c>") == f"\x1b[38;2;255;0;0m\x1b[1m{teststr}\x1b[0m"

def test_ctag_format_24b_closing_style(ct, sys24b):
	assert ct.format(f"<c red bold>{teststr}</c red>{teststr2}</c>") == f"\x1b[38;5;9m\x1b[1m{teststr}\x1b[0m\x1b[1m{teststr2}\x1b[0m"

def test_ctag_format_24b_case_insensitive(ct, sys24b):
	assert ct.format(f"<c RED bold>{teststr}</c red>{teststr2}</c>") == f"\x1b[38;5;9m\x1b[1m{teststr}\x1b[0m\x1b[1m{teststr2}\x1b[0m"

def test_ctag_format_24b_no_closing_tag(ct, sys24b):
	assert ct.format(f"<c red bold>{teststr}</c red>{teststr2}") == f"\x1b[38;5;9m\x1b[1m{teststr}\x1b[0m\x1b[1m{teststr2}"

def test_ctag_format_24b_ignore_nonactive_closing_style(ct, sys24b):
	assert ct.format(f"<c red bold>{teststr}</c red BLUE>{teststr2}") == f"\x1b[38;5;9m\x1b[1m{teststr}\x1b[0m\x1b[1m{teststr2}"

def test_ctag_format_24b_non_xterm_hex(ct, sys24b):
	assert ct.format(f"<c #FE0000>{teststr}</c>") == f"\x1b[38;2;254;0;0m{teststr}\x1b[0m"

def test_ctag_format_24b_two_opening_one_closing(ct, sys24b):
	# IF there are 2 red styles active and one closing red, only remove one of the red styles
	assert ct.format(f"<c red><c red>{teststr}</c red>{teststr2}</c>") == f"\x1b[38;5;9m\x1b[38;5;9m{teststr}\x1b[0m\x1b[38;5;9m{teststr2}\x1b[0m"

def test_ctag_format_24b_two_opening_two_closing(ct, sys24b):
	# IF there are 2 red styles active and two closing red, close both
	assert ct.format(f"<c red><c red>{teststr}</c red red>{teststr2}</c>") == f"\x1b[38;5;9m\x1b[38;5;9m{teststr}\x1b[0m{teststr2}\x1b[0m"

def test_ctag_format_24b_no_style(ct, sys24b):
	# If opening ctag has no style, ignore
	assert ct.format(f"<c>{teststr}</c>") == f"{teststr}\x1b[0m"
	assert ct.format(f"<c >{teststr}</c>") == f"{teststr}\x1b[0m"
	assert ct.format(f"<c   >{teststr}</c>") == f"{teststr}\x1b[0m"




def test_get_styles_from_ctag(ctag):
	assert ctag("<c red bold>").styles() == ["red", "bold"]
	assert ctag("</c red bold>").styles() == ["red", "bold"]
	assert ctag("</c>").styles() == []
	assert ctag("<c>").styles() == []
	assert ctag("<c BADSTYLE bold>").styles() == ["badstyle", "bold"]


def test_is_opening_ctag(ctag):
	assert ctag("<c>").is_opening_tag()
	assert ctag("<c red>").is_opening_tag()
	assert ctag("<c red bg-BOLD>").is_opening_tag()
	assert not ctag("</c>").is_opening_tag()	
	assert not ctag("</c red>").is_opening_tag()	
	assert not ctag("FFF").is_opening_tag()	
	

def test_is_closing_ctag(ctag):
	assert not ctag("<c>").is_closing_tag()
	assert ctag("</c>").is_closing_tag()
	assert ctag("</c RED>").is_closing_tag()
	assert ctag("</c RED bold>").is_closing_tag()
	assert not ctag("FFF").is_closing_tag()	


def test_expand_ctag(ctag):
	assert ctag("<c>").expand() == [ctag("<c>")]
	assert ctag("</c>").expand() == [ctag("</c>")]

	assert ctag("<c red>").expand() == [ctag("<c red>")]
	assert ctag("</c red>").expand() == [ctag("</c red>")]

	assert ctag("<c red blue>").expand() == [ctag("<c red>"), ctag("<c blue>")]
	assert ctag("</c red blue>").expand() == [ctag("</c red>"), ctag("</c blue>")]


def test_iter_ctags_in_text(ctf):
	assert [ct.group(0) for ct in ctf.iter_ctags_in_text("<c>")] == ["<c>"]
	assert [ct.group(0) for ct in ctf.iter_ctags_in_text("<c>"*3)] == ["<c>"]*3
	assert [ct.group(0) for ct in ctf.iter_ctags_in_text("</c>")] == ["</c>"]
	assert [ct.group(0) for ct in ctf.iter_ctags_in_text("</blue>")] == []
	assert [ct.group(0) for ct in ctf.iter_ctags_in_text("<c red>wow</c><c blue>WOW</c>")] == ["<c red>", "</c>", "<c blue>", "</c>"]
	assert [ct.group(0) for ct in ctf.iter_ctags_in_text("<c red blue>wow</c><c blue>WOW</c>")] == ["<c red blue>", "</c>", "<c blue>", "</c>"]
	assert [ct.group(0) for ct in ctf.iter_ctags_in_text("<c red blue>wow</c blue><c blue>WOW</c>")] == ["<c red blue>", "</c blue>", "<c blue>", "</c>"]


def test_iter_open_ctags_in_text(ctf):
	assert [ct.group(0) for ct in ctf.iter_open_ctags_in_text("<c red>wow</c><c blue>WOW</c>")] == ["<c red>", "<c blue>"]
	assert [ct.group(0) for ct in ctf.iter_open_ctags_in_text("<c red blue>wow</c><c blue>WOW</c>")] == ["<c red blue>", "<c blue>"]
	assert [ct.group(0) for ct in ctf.iter_open_ctags_in_text("<c red blue>wow</c blue><c blue>WOW</c>")] == ["<c red blue>", "<c blue>"]


def test_process_closing_ctags(ctf):
	assert ctf.process_closing_ctags("<c red><c blue>hi") == "<c red><c blue>hi"
	assert ctf.process_closing_ctags("<c red blue>hi</c>") == "<c red blue>hi</c>"

	assert ctf.process_closing_ctags("<c red blue>hi</c blue>wow") == "<c red blue>hi</c><c red>wow"
	assert ctf.process_closing_ctags("<c red blue bold>hi</c blue>wow") == "<c red blue bold>hi</c><c red><c bold>wow"


def test_replace_ctags(ctf):
	assert ctf.replace_ctags(f"<c red><c blue>{teststr}</c>") == f"\x1b[38;5;9m\x1b[38;5;12m{teststr}\x1b[0m"
	assert ctf.replace_ctags(f"<c red blue>{teststr}</c>") == f"\x1b[38;5;9m\x1b[38;5;12m{teststr}\x1b[0m"
	assert ctf.replace_ctags(f"<c red bold>{teststr}</c red>{teststr2}") == f"\x1b[38;5;9m\x1b[1m{teststr}</c red>{teststr2}"
	assert ctf.replace_ctags(f"<c red bold>{teststr}</c green>{teststr2}") == f"\x1b[38;5;9m\x1b[1m{teststr}</c green>{teststr2}"


def test_format(ctf):
	assert ctf.format(f"<c red bold>{teststr}</c red>{teststr2}") == f"\x1b[38;5;9m\x1b[1m{teststr}\x1b[0m\x1b[1m{teststr2}"
	assert ctf.format(f"<c red bold>{teststr}</c green>{teststr2}") == f"\x1b[38;5;9m\x1b[1m{teststr}\x1b[0m\x1b[38;5;9m\x1b[1m{teststr2}"


@pytest.mark.parametrize("prefix", ["", "#"])
def test_get_rgb_style_code_number(ctf, prefix):
	with pytest.raises(NotImplementedError):
		ctf.get_rgb_style_code_number(f"{prefix}00")


@pytest.mark.parametrize("prefix", ["", "#"])
def test_get_rgb_style_code_number_8bit(ctf8, prefix):
	assert ctf8.get_rgb_style_code_number(f"{prefix}00") == "16"
	assert ctf8.get_rgb_style_code_number(f"{prefix}000") == "16"
	assert ctf8.get_rgb_style_code_number(f"{prefix}000000") == "16"

	assert ctf8.get_rgb_style_code_number(f"{prefix}00005f") == "17"

	with pytest.raises(AttributeError):
		assert ctf8.get_rgb_style_code_number(f"{prefix}") == ""


@pytest.mark.parametrize("prefix", ["", "#"])
def test_get_rgb_style_code_number_24bit(ctf24, prefix):
	assert ctf24.get_rgb_style_code_number(f"{prefix}F0") == "240;240;240"
	assert ctf24.get_rgb_style_code_number(f"{prefix}F00") == "255;0;0"
	assert ctf24.get_rgb_style_code_number(f"{prefix}FF0000") == "255;0;0"

	assert ctf24.get_rgb_style_code_number(f"{prefix}00005f") == "0;0;95"

	with pytest.raises(AttributeError):
		assert ctf24.get_rgb_style_code_number(f"{prefix}") == ""


def test_get_closest_hex_value(ctf8):
	assert ctf8.get_closest_hex_value(colors.hexstr("FF0000")) == "#ff0000"
	assert ctf8.get_closest_hex_value(colors.hexstr("#FF0000")) == "#ff0000"

	assert ctf8.get_closest_hex_value(colors.hexstr("FF0001")) == "#ff0000"
	assert ctf8.get_closest_hex_value(colors.hexstr("FD0001")) == "#ff0000"
	assert ctf8.get_closest_hex_value(colors.hexstr("0000FE")) == "#0000ff"