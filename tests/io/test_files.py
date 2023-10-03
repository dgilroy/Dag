import pathlib, builtins
import pytest, _pytest

from dag.io import files
from dag.definitions import CODE_PATH


@pytest.fixture()
def df():
	return files

@pytest.fixture()
def tpath(tmp_path):
	return pathlib.Path(str(tmp_path).lstrip("/"))

@pytest.fixture()
def homeslash():
	return pathlib.Path("/")


@pytest.fixture()
def mockopen(mocker):
	mo = mocker.mock_open()
	mocker.patch("builtins.open", mo)
	return mo

@pytest.fixture()
def mockPath(mocker):
	mocker.patch("pathlib.Path.mkdir")
	mocker.patch("pathlib.Path.touch")
	return mocker



def test_touch(tmp_path, mockPath, df):
	testfile = tmp_path / "df_test_touch"

	df.touch(testfile)
	pathlib.Path.touch.assert_called_once()


def test_file_exists(tmp_path, mocker, df):
	mocker.patch("pathlib.Path.exists", return_value = False)
	assert not df.exists(tmp_path), "File that shouldn't exist is being marked as existing"

	mocker.patch("pathlib.Path.exists", return_value = True)
	assert df.exists(tmp_path), "File that should exist si being marked as not existing"


def test_dag_file_opener(tmp_path, mocker, mockPath, mockopen, df):
	testpath = tmp_path / "dag_file_opener_test"

	with df.open(testpath, touch = True) as file:
		pathlib.Path.touch.assert_called_once()
		mockopen.assert_called_with(testpath, mocker.ANY)


def test_read(tpath, mocker, mockopen, df):
	testpath = tpath / "dag_file_reader_test"
	testcontent = "test read content"

	mo = mocker.mock_open(read_data = str(testcontent))
	mocker.patch("builtins.open", mo)

	assert df.read(testpath) == testcontent, "File's contents do not match what was supposed to have been written"
