import sys, os, pathlib, io, builtins, shutil
from pathlib import Path
from contextlib import contextmanager
from typing import Union, NoReturn, Optional

import dag


Pathable = Union[Path, str]



def is_inside_dag(filepath: Pathable) -> bool:
	"""
	Checks whether a given filepath is located inside the dag project's root path

	:param filepath: The filepath to be checked
	:returns: A boolean indicating whether the file is located within the dag root directory
	"""

	filepath = Path(filepath)

	return dag.ROOT_PATH in filepath.absolute().parents


def force_inside_dag(filepath: Pathable) -> Path:
	"""
	Takes a filepath and ensures it exists inside the dag root directory

	:param filepath: The filepath to force into the dag root directory
	:returns: The filepath, possibly modified so that it is inside the dag root directory
	"""

	# if filepath is already in the dag ROOT_DIR, return filepath
	if is_inside_dag(filepath):
		return filepath

	# Strip any leading slashes that may have indicated Unix root folder
	filepath = str(filepath).lstrip("/")

	filepath = Path(filepath)

	return dag.ROOT_PATH / filepath


def touch(filepath: Pathable) -> NoReturn:
	"""
	Perform unix-style touch on a file

	:param filepath: The filepath to touch
	"""

	filepath = pathlib.Path(filepath)

	directory = filepath if filepath.is_dir() else filepath.parents[0]
	
	directory.mkdir(parents=True, exist_ok=True) 

	try:
		filepath.touch()
	except Exception as e:
		breakpoint()
		pass

do_touch = touch # Done so that if "touch" is a kwarg, can still call touch()


def filename_avoid_overwrite(path: Pathable) -> Path:
	"""
	Takes in a filepath and modifies the filename so that it is unique in its directory

	If given "wow.py" and "wow.py" already exists in directory, returns "wow(1).py"
	If "wow(1).py" also already exists, returns "wow(2).py"
	etc...

	:param path: The path to make Unique
	:returns: A Path object with a filename unique to the directory
	"""

	path = Path(path)

	if path.exists():
		i = 1
		stem = path.stem
		newpath = path.with_stem(f"{stem}({i})")

		while newpath.exists():		
			i += 1
			newpath = path.with_stem(f"{stem}({i})")

		return newpath

	return path


def file_exists(filepath: Pathable, inside_dag: bool = False) -> bool:
	"""
	Checks whether a given filepath already exists

	:param filepath: The filepath to check
	:param inside_dag: Whether to force filepath into dag
	:returns: Whether the given filepath already exists
	"""

	filepath = Path(filepath)

	if inside_dag:
		filepath = force_inside_dag(filepath)

	return filepath.exists()


file_exists_in_dag = lambda filename, *args, **kwargs: DagFileOpener(filename, *args, **(kwargs | {"inside_dag": True}))


@contextmanager
def open(filepath: Pathable, permissions: str = "r", opener = None, touch: bool = True, inside_dag: bool = False, **kwargs):
	"""
	A file opener utility for files in dag. Acts as a context manager wrapper for builtins.open

	:param filepath: The path of the file being opened
	:param permissions: The file permissions for the file being opened
	:param opener: The function that will open the file. Defaults to builtins.open, but another possibility is gzip.open
	:param touch: Whether or not to touch the file before opening
	:param inside_dag: Whether ot not to force the file into the root dag folder
	:param kwargs: Any other args to be passed into the opener
	"""

	raw_filepath = filepath # May eventually use DagPlatform to convert paths Win<->Unix. Store original path here
	filepath = pathlib.Path(filepath)

	if inside_dag:
		filepath = force_inside_dag(filepath)

	permissions = permissions
	opener = opener or builtins.open
	touch = touch
	kwargs = kwargs

	file = None

	if touch:
		do_touch(filepath)
		
	file = opener(filepath, permissions, **kwargs)
	
	yield file

	try:
		file.close()
	except AttributeError as e:
		breakpoint()
		pass



open_in_dag = lambda filepath, *args, **kwargs: open(filepath, *args, **(kwargs | {"inside_dag": True}))


#@dag.iomethod(group = "file")
def read(filepath, opener = open, *args, **kwargs):
	with open(filepath, "r", *args, **kwargs) as file:
		return file.read()


def read_in_dag(*args, **kwargs):
	return read(*args, **(kwargs | {"inside_dag": True}))


def append(filepath, text, opener = open, *args, **kwargs):
	with opener(filepath, "a+", *args, **kwargs) as file:
		file.write(text)

def append_line(filepath, text, opener = open, *args, **kwargs):
	text = text if text.endswith("\n") else text + "\n"
	append(filepath, text, opener, *args, **kwargs)


def iterlines(filepath, opener = open, *args, **kwargs):
	with opener(filepath, "r", *args, **kwargs) as f:
		for line in f:
			yield line