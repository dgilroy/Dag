import subprocess, abc
from enum import Enum

import dag


def process_filepath(filepath):
	return dag.get_platform().path_to_native(filepath)


class Editor(abc.ABC):
	cli_name = None

	@classmethod
	@abc.abstractmethod
	def open_file(cls, filepath, lineno = None):
		raise NotImplementedError("'open_file' not implemented")


class NOTEPADPP(Editor):
	cli_name = "notepad++"

	@classmethod
	def open_file(cls, filepath, lineno = None):
		subprocess.run((cls.cli_name, process_filepath(filepath), f"-n{lineno}"))


class SUBLIME(Editor):
	cli_name = "subl"

	@classmethod
	def open_file(cls, filepath, lineno = None):
		subprocess.run((cls.cli_name, f"{process_filepath(filepath)}:{lineno}"))