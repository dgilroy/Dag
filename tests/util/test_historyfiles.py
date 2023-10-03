import builtins
import pytest
from dag.util import historyfiles
from dag.io import files


@pytest.fixture
def histfile(tmp_path):
	return historyfiles.HistoryFile(tmp_path / "test-historyfile")


@pytest.fixture()
def mockout(mocker, request):
	mo = mocker.mock_open(read_data = request.param)
	mocker.patch("builtins.open", mo)
	mocker.patch("dag.io.files.open", mo)
	return mo



TESTLINE = "testline"

@pytest.mark.parametrize("mockout", [TESTLINE], indirect=["mockout"])
def test_read(histfile, mockout, mocker):
	#TESTLINE = "testline"

	#mo = mocker.mock_open(read_data = TESTLINE)
	#mocker.patch("builtins.open", mo)

	assert histfile.read() == TESTLINE
	assert mockout.mock_calls[0] == mocker.call(histfile.filepath, "r")



def test_is_line_valid(histfile):
	assert histfile.is_line_valid("") is False
	assert histfile.is_line_valid("TEST")
	assert histfile.is_line_valid("EOF") is False
	assert histfile.is_line_valid("eof") is False


@pytest.mark.parametrize("mockout", [TESTLINE], indirect=["mockout"])
def test_is_line_valid_duplicate_line(histfile, mockout):
	assert histfile.is_line_valid(TESTLINE) is False, "histfile considered a duplicate line to be valid"
	assert histfile.is_line_valid("line2")


@pytest.mark.parametrize("mockout", ["", "eof", "EOF", "line1"], indirect=["mockout"])
def test_add_if_valid(histfile, mockout):
	histfile.add_if_valid("line3")
	mockout().write.assert_called_once_with("line3\n")


@pytest.mark.parametrize("mockout", ["line1\nline2"], indirect=["mockout"])
def test_last_line(histfile, mockout):
	histfile.add_if_valid("line1\nline2")
	assert histfile.last_line() == "line2"