import os
from contextlib import contextmanager

from dag.lib import encoding


### ENV VARIABLES ###
# Check ENV variable exists
def has_env(var_name):
	return os.environ.get(var_name) is not None


def env(var_name):
	try:
		return os.environ[var_name]
	except KeyError:
		raise AttributeError(f"No token with name {var_name} found")


### ENV ###
def env64(var_name, codec = "utf-8"):
	return encoding.B64.encode(env(var_name), codec)


class _EnvGetter:
	def __getattr__(self, attr):
		return env(attr)

	def __call__(self, key):
		return env(attr)

EnvGetter = _EnvGetter()






@contextmanager
def cwdmanager(path) -> None:
	"""
	A simple context manager that allows to safely temporarily change the CWD
	"""

	oldcwd=os.getcwd()
	os.chdir(path)
	try:
		yield
	finally:
		os.chdir(oldcwd)

