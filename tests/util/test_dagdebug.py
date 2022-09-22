import traceback, sys, subprocess, cmd
import pytest
from dag.exceptions import DagError
from dag.util import dagdebug, historyfile, editors


@pytest.fixture
def dagpdb():
	return dagdebug.DagPdb()


def test_mocker(mocker):
	pass


def test_tb(dagpdb, mocker):
	mocker.patch("traceback.print_exception")

	exc_info = sys.exc_info()

	dagpdb.do_tb("")

	traceback.print_exception.assert_called_once_with(*exc_info)

	try:
		raise DagError
	except DagError:
		exc_info = sys.exc_info()

		dagpdb.do_tb("")

		traceback.print_exception.assert_called_with(*exc_info)


def test_read_dagpdb_historyfile(dagpdb, mocker):
	mocker.patch("dag.util.historyfile.HistoryFile.load_into_readline")

	dagpdb.read_dagpdb_historyfile()

	historyfile.HistoryFile.load_into_readline.assert_called_once()


def test_do_tb(dagpdb, mocker):
	mocker.patch("traceback.print_exception")

	exc_info = sys.exc_info()

	dagpdb.do_tb("")

	traceback.print_exception.assert_called_once_with(*exc_info)

	try:
		raise DagError
	except DagError:
		exc_info = sys.exc_info()

		dagpdb.do_tb("")

		traceback.print_exception.assert_called_with(*exc_info)


def test_do_tb(dagpdb, mocker):
	mocker.patch("cmd.Cmd.onecmd")

	TESTLINE = "testline"
	dagpdb.onecmd(TESTLINE)

	cmd.Cmd.onecmd.assert_called_once_with(dagpdb, TESTLINE)


def test_set_trace(mocker):
	mocker.patch("dag.util.dagdebug.DagPdb.set_trace")

	dagdebug.set_trace()
	dagdebug.DagPdb.set_trace.assert_called_once()


def test_set_trace_optional_skipping_no_debugmode(mocker, monkeypatch):
	mocker.patch("dag.util.dagdebug.DagPdb.set_trace")

	monkeypatch.setattr(dagdebug, "DEBUG_MODE", False)
	assert dagdebug.set_trace(0) == False

	monkeypatch.setattr(dagdebug, "DEBUG_MODE", True)
	assert dagdebug.set_trace(0)


def test_set_trace_debugmode_only(mocker, monkeypatch):
	mocker.patch("dag.util.dagdebug.DagPdb.set_trace")

	monkeypatch.setattr(dagdebug, "DEBUG_MODE", False)
	assert dagdebug.set_trace(debugmode_only = True) == False

	monkeypatch.setattr(dagdebug, "DEBUG_MODE", True)
	assert dagdebug.set_trace(debugmode_only = True)
