import sys, subprocess
import pytest, pyperclip
from dag.lib import platforms


@pytest.fixture
def cygwin():
	return platforms.Cygwin


@pytest.fixture
def windows():
	return platforms.Windows



def test_get_platform(monkeypatch):
	monkeypatch.setattr(sys, "platform", "win32")
	assert platforms.get_platform() == platforms.Windows, "Windows platform wasn't detected as windows"

	monkeypatch.setattr(sys, "platform", "cygwin")
	assert platforms.get_platform() == platforms.Cygwin, "Cygwin platform wasn't detected as cygwin"

	monkeypatch.setattr(sys, "platform", "FXF")
	assert platforms.get_platform() == platforms.Unix, "Unknown platform didn't default to unix"

	monkeypatch.setattr(sys, "platform", None)
	assert platforms.get_platform() == platforms.Unix, "Missing platform didn't default to unix"


def test_cygwin_path_to_windows(cygwin):
	test_dir = "/cygdrive/t/testdir/file.txt"

	winpath = cygwin.path_to_windows(test_dir) # Add test str to clipboard

	assert winpath == "T:/testdir/file.txt", "Cygwin path wasn't properly converted to windows path"