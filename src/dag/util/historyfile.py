import readline
from typing import NoReturn

import dag


class HistoryFile:
	def __init__(self, filename: str = dag.config.HISTORY_FILE_NAME, inside_dag = True):
		"""
		A file that maintains lines of input commands

		:param filename: The filename of thie historyfile
		"""

		if inside_dag:
			filename = dag.file.force_inside_dag(dag.config.LOG_PATH / f"history/{filename}")

		self.filepath = filename


	def read(self) -> str:
		"""
		Return the contents of the historyfile

		:returns: The contents of the historyfile
		"""

		return dag.file.read_in_dag(self.filepath)


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
			self.add(line)


	def add(self, line: str) -> str:
		"""
		Append line to historyfile

		:param line: The line to check and append to historyfile
		:returns: The line that was written
		"""

		with dag.file.open_in_dag(self.filepath, "a+") as file:
			file.write(line + "\n")

		return line


	def load_into_readline(self) -> NoReturn:
		"""	Load historyfile into readline """

		readline.read_history_file(self.filepath)


	def last_line(self) -> str:
		"""	Return the latest entry to thie historyfile	"""

		return self.read().strip().split("\n")[-1].strip()




dag_historyfile = HistoryFile()