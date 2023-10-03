import sys, os, pathlib, io, builtins, shutil
from pathlib import Path
from contextlib import contextmanager
from typing import NoReturn

import dag


Pathable = Path | str


class FileManager:
	def __init__(self, root: Pathable = ""):
		self.root = dag.Path(root)


	def process_filepath(self, filepath: Pathable) -> dag.Path:
		filepath = dag.Path(filepath)

		if self.root in filepath.parents:
			return filepath

		return self.root / filepath


	def touch(self, filepath: Pathable) -> NoReturn:
		"""
		Perform unix-style touch on a file

		:param filepath: The filepath to touch
		"""

		filepath = self.process_filepath(filepath)

		directory = filepath if filepath.is_dir() else filepath.parents[0]
		
		directory.mkdir(parents=True, exist_ok=True) 

		try:
			filepath.touch()
		except Exception as e:
			breakpoint()
			pass


	def filename_avoid_overwrite(self, path: Pathable) -> dag.Path:
		"""
		Takes in a filepath and modifies the filename so that it is unique in its directory

		If given "wow.py" and "wow.py" already exists in directory, returns "wow(1).py"
		If "wow(1).py" also already exists, returns "wow(2).py"
		etc...

		:param path: The path to make Unique
		:returns: A Path object with a filename unique to the directory
		"""

		path = self.process_filepath(path)

		if path.exists():
			i = 1
			stem = path.stem
			newpath = path.with_stem(f"{stem}({i})")

			while newpath.exists():		
				i += 1
				newpath = path.with_stem(f"{stem}({i})")

			return newpath

		return path


	def exists(self, filepath: Pathable) -> bool:
		"""
		Checks whether a given filepath already exists

		:param filepath: The filepath to check
		:returns: Whether the given filepath already exists
		"""

		filepath = self.process_filepath(filepath)

		return filepath.exists()



	@contextmanager
	def do_open(self, filepath: Pathable, mode: str = "r", opener = None, touch: bool = True, **kwargs):
		"""
		A file opener utility for files in dag. Acts as a context manager wrapper for builtins.open

		:param filepath: The path of the file being opened
		:param mode: The file mode for the file being opened
		:param opener: The function that will open the file. Defaults to builtins.open, but another possibility is gzip.open
		:param touch: Whether or not to touch the file before opening
		:param kwargs: Any other args to be passed into the opener
		"""

		raw_filepath = filepath # May eventually use DagPlatform to convert paths Win<->Unix. Store original path here
		filepath = self.process_filepath(filepath)

		opener = opener or builtins.open

		file = None

		if touch:
			self.touch(filepath)
			
		file = opener(filepath, mode, **kwargs)
		
		yield file

		try:
			file.close()
		except AttributeError as e:
			breakpoint()
			pass


	open = do_open


	@dag.iomethod(name = "read", group = "file")
	def read(self, filepath: Pathable, opener = None, *args, **kwargs) -> str:
		opener = opener or self.do_open

		filepath = self.process_filepath(filepath)
		with self.open(filepath, "r", *args, **kwargs) as file:
			return file.read()


	@dag.iomethod(name = "readlines", group = "file")
	def readlines(self, filepath: Pathable, opener = None, *args, **kwargs) -> list[str]:
		opener = opener or self.do_open

		filepath = self.process_filepath(filepath)
		with self.open(filepath, "r", *args, **kwargs) as file:
			return file.read().splitlines()


	def append(self, filepath: Pathable, text: str, opener = None, *args, **kwargs) -> None:
		opener = opener or self.do_open
		filepath = self.process_filepath(filepath)

		with opener(filepath, "a+", *args, **kwargs) as file:
			file.write(str(text))


	def appendline(self, filepath: Pathable, text: str, opener = None, *args, **kwargs) -> None:		
		maybenewline = "\n" if not text.endswith("\n") else ""
		return self.append(filepath, text + maybenewline)


	def append_if_new(self, filepath: Pathable, item: str, opener = None, *args, **kwargs) -> None:
		opener = opener or self.do_open
		filepath = self.process_filepath(filepath)

		with opener(filepath, "a+", *args, **kwargs) as file:
			file.seek(0)
			
			for line in file:
				line = line.strip("\n")

				if item == line:
					return

			file.write(item + "\n")


	def append_line(self, filepath: Pathable, text: str, opener = None, *args, **kwargs) -> None:
		opener = opener or self.do_open
		filepath = self.process_filepath(filepath)

		text = text if text.endswith("\n") else text + "\n"
		self.append(filepath, text, opener, *args, **kwargs)


	def iterlines(self, filepath: Pathable, opener = None, *args, **kwargs):
		opener = opener or self.do_open
		filepath = self.process_filepath(filepath)

		with opener(filepath, "r", *args, **kwargs) as f:
			for line in f:
				yield line


	def rmdir(self, dirpath: Pathable, force: bool = False) -> str | None:
		dirpath = self.process_filepath(dirpath)

		if not dirpath.exists():
			return f"Directory <c b u>{dirpath}</c b u> not found"

		assert dirpath.is_dir(), "Path must be a directory"

		if force:
			confirm = True
		else:
			confirm = dag.cli.confirm(f"Delete directory: <c #F00>{dirpath}</c #F00>?")

		if confirm:
			shutil.rmtree(dirpath)
			dag.echo(f"Removed directory <c b u>{dirpath}</c b u>")


	def delete(self, path: Pathable, force: bool = False) -> bool:
		path = self.process_filepath(path)

		if not path.exists():
			return False

		if path.is_dir():
			return self.rmdir(path, force)

		with dag.cli.confirmer(f"Delete directory: <c #F00>{path}</c #F00>?	", force = force) as confirm:
			if confirm:
				path.unlink()
				return True

		return False