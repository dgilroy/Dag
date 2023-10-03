import os
from contextlib import contextmanager
from collections.abc import Generator
from pathlib import Path
from typing import Any

from dag.lib import encoding



### ENV VARIABLES ###
# Check ENV variable exists
def has_env(var_name: str) -> bool:
	return os.environ.get(var_name) is not None

def environ() -> os._Environ:
	return os.environ


def getenv(var: str, default: Any = None) -> str:
	return environ().get(var, default)


def env(var_name: str) -> str:
	try:
		return environ()[var_name]
	except KeyError as e:
		raise AttributeError(f"No token with name {var_name} found") from e


### ENV ###
def env64(var_name: str, codec: str = "utf-8") -> str:
	return encoding.B64.decode(env(var_name), codec)


class EnvGetter:
	def __getattr__(self, attr: str) -> str:
		return env(attr)

	def __call__(self, attr: str) -> str:
		return env(attr)


class OptionalEnvGetter:
	def __getattr__(self, attr: str) -> str:
		return getenv(attr)

	def __call__(self, attr: str) -> str:
		return getenv(attr)




@contextmanager
def cwdmanager(path: str | Path) -> Generator[None, None, None]:
	"""
	A simple context manager that allows to safely temporarily change the CWD
	"""

	oldcwd=os.getcwd()
	os.chdir(path)
	try:
		yield
	finally:
		os.chdir(oldcwd)



def humanize(num: float, suffix: str ="B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}{suffix}"




def get_files(basepath: str = ".", dirs: bool = True, files: bool = True, filetype: str = "") -> list[str]:
	try:
		basefiles = next(os.walk(basepath))
	except Exception:
		return []

	items = []
	
	# Get directories
	if dirs:
		items += [f"{f}/" for f in basefiles[1]]
		
	# Get files
	if files:
		items += [f"{f}" for f in basefiles[2]]

	if filetype:
		items = [f for f in items if f.endswith(filetype)]

	return items