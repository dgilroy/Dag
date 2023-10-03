import subprocess, abc, pathlib

import dag


def process_filepath(filepath = ""):
	if not filepath:
		return ""

	return dag.get_platform().path_to_native(filepath)


class Editor(abc.ABC):
	cli_name = None

	@classmethod
	@abc.abstractmethod
	def open_file(cls, filepath = "", lineno = ""):
		raise NotImplementedError("'open_file' not implemented")


class NOTEPADPP(Editor):
	cli_name = "notepad++.exe"

	@classmethod
	def open_file(cls, filepath = "", lineno = ""):
		subprocess.run((cls.cli_name, process_filepath(filepath), f"-n{lineno}"))


class VIM(Editor):
	cli_name = "vim"

	@classmethod
	def open_file(cls, filepath = "", lineno = ""):
		subprocess.run((cls.cli_name, process_filepath(filepath), f"+{lineno}"))



class SUBLIME(Editor):
	cli_name = "subl.exe"

	@classmethod
	def open_file(cls, filepath = "", lineno = ""):
		filename = process_filepath(f"{filepath}:{lineno}") if filepath else "" # allows for opening current subl on its active tab
		subprocess.run((cls.cli_name, f"{filename}"))



class VSCODE(Editor):
	cli_name = "code"

	@classmethod
	def open_file(cls, filepath = "", lineno = ""):
		subprocess.run((cls.cli_name, "-g", f"{filepath}:{lineno}"))



registered_editors = {}

registered_editors["NOTEPAD++"] = NOTEPADPP
registered_editors["SUBL"] = SUBLIME
registered_editors["VIM"] = VIM
registered_editors["VSCODE"] = VSCODE


def get_editor(editor = None):
	if editor is None:
		editor = dag.settings.EDITOR or dag.getenv.EDITOR or ""

	name = pathlib.Path(editor).name.removesuffix(".exe").upper()

	return registered_editors.get(name, VIM)