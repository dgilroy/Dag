import os, pytest, builtins

import dag
import dag.exceptions
from dag.dagcli import instance


@pytest.fixture
def instance_cwdfile(tmp_path):
	cwdpath = os.fspath(tmp_path) + "/cwdfile"
	yield cwdpath
	try:
		os.remove(cwdpath)
	except FileNotFoundError:
		pass




@pytest.fixture
def instance_reloadfile(tmp_path):
	reloadpath = os.fspath(tmp_path) + "/reloadfile"
	yield reloadpath
	try:
		os.remove(reloadpath)
	except FileNotFoundError:
		pass


#@pytest.fixture(params = [None, [], [""],["false"]])
@pytest.fixture(params = [None])
def inputdagargs(request):
	return request.param


@pytest.fixture
def instance(instance_cwdfile, instance_reloadfile, inputdagargs):
	instance = instance.DagCLIInstance(inputdagargs, instance_cwdfile, instance_reloadfile, is_silent = False)
	yield instance
	instance.shutdown()


@pytest.fixture
def newdir(tmp_path):
	newdir = tmp_path / "newdir"
	os.mkdir(newdir)

	return newdir

@pytest.fixture
def cwdmocker(newdir, mocker):
	mocker.patch("os.getcwd", return_value = str(newdir))
	return mocker

@pytest.fixture
def cwdfilemockopen(mocker):
	mo = mocker.mock_open(read_data = os.getcwd())
	mocker.patch("builtins.open", mo)

	return mo



class TestDagCLIInstance:
	def test_cwd_change_changefile(self, instance, cwdmocker, cwdfilemockopen):
		"""Tests whether instance records the new CWD to cwdfile"""
		instance.shutdown()

		cwdfilemockopen().write.assert_called_once_with(os.getcwd())

		with open(instance.cwdfile) as file:
			assert file.read() == os.getcwd()



	def test_no_cwd_change_changefile(self, instance, cwdfilemockopen):
		"""Tests that instance does not record the CWD to cwdfile if the CWD was not changed"""
		instance.shutdown()

		with pytest.raises(AssertionError):
			cwdfilemockopen().write.assert_called_with(os.getcwd())


	def test_cwd_write(self, instance, cwdmocker, mocker):
		"""Tests whether instance records the new CWD to cwdfile"""
		mo = mocker.mock_open(read_data = os.getcwd())
		mocker.patch("builtins.open", mo)

		instance.record_cwd()

		mo().write.assert_called_once_with(os.getcwd())

		with open(instance.cwdfile) as file:
			assert file.read() == os.getcwd()


	@pytest.mark.parametrize("reloadargs", [None, "", "test"])
	def test_reload(self, instance, reloadargs, mocker):
		"""Triggers a reload and tests whether it's properly recorded"""

		mo = mocker.mock_open(read_data = str(reloadargs))
		mocker.patch("builtins.open", mo)

		try:
			instance.view.controller.reload(reloadargs)
		except dag.exceptions.DagReloadException as e:
			instance.process_reload_exception(e)

		instance.shutdown()

		mo().write.assert_called_once_with(str(reloadargs))

		with open(instance.reloadfile) as file:
			assert file.read() == str(reloadargs)


	@pytest.mark.parametrize("reloadargs", [None, "", "test"])
	def test_reload_write(self, instance, reloadargs, mocker):
		"""Tests whether instance records the reload args to reloadfile"""

		mo = mocker.mock_open(read_data = str(reloadargs))
		mocker.patch("builtins.open", mo)

		try:
			instance.view.controller.reload(reloadargs)
		except dag.exceptions.DagReloadException as e:
			instance.process_reload_exception(e)

		instance.record_reload_args()

		mo().write.assert_called_once_with(str(reloadargs))

		with open(instance.reloadfile) as file:
			assert file.read() == str(reloadargs)

