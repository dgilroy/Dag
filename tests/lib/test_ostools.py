import pytest, os
from dag.lib import ostools

@pytest.fixture
def cwdman():
	return ctx.cwdmanager


### TEST CWDMANAGER ###

def test_cwdmanager(cwdman, tmp_path):
	cwd = os.getcwd()

	with cwdman(tmp_path):
		assert os.getcwd() == str(tmp_path)

	assert cwd == os.getcwd()