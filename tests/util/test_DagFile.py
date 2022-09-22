import pathlib, builtins
import pytest, _pytest

from dag.util import dagfile
from dag.definitions import ROOT_PATH


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


def test_is_inside_dag(tmp_path, homeslash, mocker):
	assert not dagfile.is_inside_dag(homeslash / tmp_path), "non-dag file was considered to be inside Dag"

	indag = ROOT_PATH / "testfile"
	assert dagfile.is_inside_dag(indag), "file inside ROOT_PATH was not considered to be inside Dag"

	with mocker.patch("os.getcwd", return_value = ROOT_PATH):
		relpath = pathlib.Path("testpath")
		assert dagfile.is_inside_dag(relpath), "Relative path created while CWD was ROOT_PATH was not considered to be inside Dag"



def test_force_inside_dag(tmp_path):
	forced_path = dagfile.force_inside_dag(tmp_path)
	assert dagfile.is_inside_dag(forced_path), "File wasn't successfully forced into Dag"


def test_touch(tmp_path, mockPath):
	testfile = tmp_path / "dagfile_test_touch"

	dagfile.touch(testfile)
	pathlib.Path.touch.assert_called_once()


def test_file_exists(tmp_path, mocker):
	mocker.patch("pathlib.Path.exists", return_value = False)
	assert not dagfile.file_exists(tmp_path), "File that shouldn't exist is being marked as existing"

	mocker.patch("pathlib.Path.exists", return_value = True)
	assert dagfile.file_exists(tmp_path), "File that should exist si being marked as not existing"


def test_dag_file_opener(tmp_path, mocker, mockPath, mockopen):
	testpath = tmp_path / "dag_file_opener_test"
	dagtestpath = dagfile.force_inside_dag(testpath)

	with dagfile.open(testpath, touch = True) as file:
		pathlib.Path.touch.assert_called_once()
		mockopen.assert_called_with(testpath, mocker.ANY)


def test_dag_file_open_in_dag_param(tmp_path, mocker, mockPath, mockopen):
	testpath = tmp_path / "dag_file_opener_test"
	dagtestpath = dagfile.force_inside_dag(testpath)

	with dagfile.open(testpath, touch = True, inside_dag = True) as file:
		mockopen.assert_called_with(dagtestpath, mocker.ANY)


def test_dag_file_open_in_dag(tmp_path, mocker, mockPath, mockopen):
	testpath = tmp_path / "dag_file_opener_test"
	dagtestpath = dagfile.force_inside_dag(testpath)

	with dagfile.open_in_dag(testpath) as file:
		mockopen.assert_called_with(dagtestpath, mocker.ANY)


def test_read(tpath, mocker, mockopen):
	testpath = tpath / "dag_file_reader_test"
	testcontent = "test read content"

	mo = mocker.mock_open(read_data = str(testcontent))
	mocker.patch("builtins.open", mo)

	assert dagfile.read(testpath) == testcontent, "File's contents do not match what was supposed to have been written"

	with dagfile.open_in_dag(testpath, "w+") as file:
		file.write(testcontent)

	assert dagfile.read_in_dag(testpath) == testcontent, "File wasn't created in Dag or its content doesnt match what was supposed to have been written"
