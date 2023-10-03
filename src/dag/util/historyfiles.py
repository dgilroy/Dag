import readline, pathlib, tempfile
from contextlib import contextmanager
from typing import NoReturn

import dag


class HistoryFile:
	def __init__(self, filename: str):
		"""
		A file that maintains lines of input commands

		:param filename: The filename of thie historyfile
		"""

		self.filepath = dag.directories.STATE / filename
		self.size = dag.settings.HISTORY_LENGTH


	def read(self) -> str:
		"""
		Return the contents of the historyfile

		:returns: The contents of the historyfile
		"""

		if not self.filepath.exists():
			self.filepath.touch()

		with open(self.filepath) as file:
			return file.read()
			#return dag.file.read(self.filepath)


	def is_line_valid(self, line: str) -> bool:
		"""
		Checks whether line is valid to add to historyfile. It checks that it isn't:
			(1) empty,
			(2) a duplicate of the last line,
			(3) end of file (EOFd)

		:param line: The line to test
		:returns: Whether or not the line is valid
		"""

		line = line and line.strip() or ""

		return bool(line and line != self.last_line() and line.lower() != "eof")


	def add_if_valid(self, line: str) -> NoReturn:
		"""
		Appends line to historyfile, provided that it isn't:
			(1) empty,
			(2) a duplicate of the last line,
			(3) end of file (EOFd)

		:param line: The line to check and append to historyfile
		"""

		if self.is_line_valid(line):
			self.add_line(line)


	def add_line(self, line: str) -> str:
		"""
		Append line to historyfile

		:param line: The line to check and append to historyfile
		:returns: The line that was written
		"""

		lines = (self.read().strip().split("\n") + [line])[-self.size:]
		lines = "\n".join(lines)
		with open(self.filepath, "w+") as file:
			file.write(lines + "\n")

		return line


	def load_into_readline(self) -> NoReturn:
		"""	Load historyfile into readline """

		try:
			readline.read_history_file(str(self.filepath))
		except FileNotFoundError:
			return ""


	def last_line(self) -> str:
		"""	Return the latest entry to thie historyfile	"""

		return self.read().strip().split("\n")[-1].strip()



@contextmanager
def temphistory(histfile = None):
	if histfile:
		dag.file.touch(histfile)

		with tempfile.NamedTemporaryFile(mode = "r") as fp:
			try:
				readline.write_history_file(fp.name)	# Store current history into tempfile
				readline.clear_history()				# Erease current history
				readline.read_history_file(histfile)	# Load temporary history
				yield									# Yield until CTX is done
				readline.write_history_file(histfile)	# Store the loaded history plus any new user input to the history file
			finally:
				readline.clear_history()				# Remove the temporary history
				readline.read_history_file(fp.name)		# Load the original history back into readline
	else:
		yield

