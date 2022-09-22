import sys, readline, signal, traceback, pdb
from io import TextIOWrapper
from typing import NoReturn, Any, Optional
from collections.abc import Iterable

from dag import config as _config
from dag.lib.dot import DotDict
from dag.util import historyfile, editors, drill


DEBUG_MODE = False

class DagPdb(pdb.Pdb):
	def __init__(
					self,
					completekey: str = 'tab',
					stdin: Optional[TextIOWrapper] = None,
					stdout: Optional[TextIOWrapper] = None,
					skip: Optional[Iterable[str]] = None,
					editor: Optional[editors.Editor] = None
				):
		"""
		A wrapper for PDB with added utilitly, incuding:
			(1) tab-completion of elements in scope, dict keys, and object values
			(2) the ability to open the current line of code in npp or sublime
			(3) Pressing "enter" on an empty line continues the execution of the code
			(4) "tb" command that lists the details of the last raised exception
			(5) Maintins history of debug commands and separates from other CLI commands

		:param completekey: The key pressed to activate text completion
		:param stdin: The stdin to be passed into Cmd
		:param stdout: The stdout to be passed into Cmd
		:param skip: The skip to be passed ito Bdb. An iterable collection of module names for pdb to ignore
		:param editor: The editor to use when opening code
		"""

		super().__init__(completekey, stdin, stdout, skip)

		# Stores dagpdb command history
		self.historyfile = historyfile.HistoryFile(_config.DAGPDB_HISTORY_FILE_NAME)

		# Loads dagpdb command history into readline
		self.read_dagpdb_historyfile()

		# String displayed before every command
		self.prompt = "(DAGPDB)"

		# The editor with which to open code
		self.editor = editor or _config.DEFAULT_EDITOR

		# A reminder that we're in dagpdb
		print("DAGPDB")

		# Storing current completer delims for when dagpdb is done
		self.original_delims = readline.get_completer_delims()

		# New delims for dagpdb. Allows for completion inside of list/dict brackets
		delims = set(readline.get_completer_delims())
		delims.remove("[")
		delims.remove("]")

		readline.set_completer_delims("".join(delims))


	def read_dagpdb_historyfile(self) -> NoReturn:
		"""
		Loads DagPDB's command history
		"""

		self.historyfile.load_into_readline()


	def do_tb(self, line: str) -> NoReturn:
		"""
		Typing "tb" into dagdebugger will print a traceback of the latest exception

		:param line: The line of code being executed by dagdebug
		"""

		traceback.print_exception(*sys.exc_info())
	

	def onecmd(self, line: str) -> bool:
		"""
		Actions to be performed before each line is executed

		:param line: The line to be executed
		:returns: A flag indicating whether the prompt loop should end
		"""

		self.historyfile.add_if_valid(line = line)
		return super().onecmd(line)


	def get_current_filepath_lineno(self) -> tuple[str, int]:
		"""
		Gets the filepath and line number of the current line of code being debugged

		:returns: A tuple with (the filepath to the current line of code, the line number of the current line of code)
		"""

		frame, lineno = self.stack[self.curindex]
		filepath = frame.f_code.co_filename

		return filepath, lineno



	def do_npp(self, line: str) -> NoReturn:
		"""
		Opens the current debugger line of code in Notepad++

		:param line: The line being executed
		"""

		self.open_in_editor(editors.NOTEPADPP)


	def do_sublime(self, line: str) -> NoReturn:
		"""
		Opens the current debugger line of code in Sublime

		:param line: The line being executed
		"""

		self.open_in_editor(editors.SUBLIME)


	# Aliases for do_sublime
	do_subl = do_sub = do_sss = do_ss = do_sublime


	# Open in default editor
	def open_in_editor(self, editor: Optional[editors.Editor] = None) -> NoReturn:
		"""
		Opens the current debugger line in the given editor

		:param editor: The editor with which to open the code
		"""

		editor = editor or self.editor

		filepath, lineno = self.get_current_filepath_lineno()
		editor.open_file(filepath, lineno)


	def do_ee(self, line: str) -> NoReturn:
		"""
		Opens the current debugger line in the default editor

		:param line: The line being executed
		"""

		self.open_in_editor()


	def do_nn(self, line: str) -> NoReturn:
		"""
		Advances the debugger and opens in editor

		:param line: The line being executed
		"""

		self.do_next(line)
		self.open_in_editor()


	def postloop(self) -> NoReturn:
		"""
		Once command loop ends,
			(1) remove all input debug commands from readline history and replace Dag's historyfile
			(2) Revert the completer delims to what they were before debugging
		"""

		historyfile.dag_historyfile.load_into_readline()
		readline.set_completer_delims(self.original_delims)



	def emptyline(self) -> int:
		"""
		If a blank line is entered, stop debugging and continue code execution
		"""

		print("DAGPDB Blank Line: Continuing...")
		if not self.nosigint:
			try:
				pdb.Pdb._previous_sigint_handler = \
				signal.signal(signal.SIGINT, self.sigint_handler)
			except ValueError:
				# ValueError happens when do_continue() is invoked from
				# a non-main thread in which case we just continue without
				# SIGINT set. Would printing a message here (once) make
				# sense?
				pass
		self.set_continue()
		return 1


	def debug(self) -> NoReturn:
		"""
		Used to debug this debugger
		"""

		pdb.set_trace()


	def do_curframe(self, line: str) -> NoReturn:
		"""
		Displays the current frame's local variables
		:param line: the line being executed
		"""

		print(self.curframe_locals)


	def complete(self, text: str, state: int) -> list[str]:
		"""
		A modification of the original cmd.cmd completer to provide locals()

		Allows for nested completing, "so Obj1[0].dict['k" could complete the dict's keys. Obj1 must be in current frame's locals

		:param text: The text being completed
		:param state: Used by cmd when looping through completion options
		"""

		if state == 0:
			origline = readline.get_line_buffer()
			line = origline.lstrip()
			stripped = len(origline) - len(line)
			begidx = readline.get_begidx() - stripped
			endidx = readline.get_endidx() - stripped

			if begidx>0:
				cmd, args, foo = self.parseline(line)
				if cmd == '':
					compfunc = self.completedefault
				else:
					try:
						compfunc = getattr(self, 'complete_' + cmd)
					except AttributeError:
						compfunc = self.completedefault
			else:
				compfunc = self.completenames

			# Allows for completion when "!" in front of words
			prefixes = "!"
			prefix = ""

			if text and text[0] in prefixes:
				prefix = text[0]
				text = text[1:]


			#curframe_scoped_args = [*self.curframe_locals.keys()] + [*self.curframe.f_globals.keys()] -> Too many globals

			curframe_locals = self.curframe.f_locals
			curframe_locals_names = [*self.curframe.f_locals.keys()]

			if "dag" in self.curframe.f_globals.keys(): # "dag" is a special global value that I want completeable if it's in scope
				import dag
				curframe_locals |= {"dag": dag}
				curframe_locals_names += ["dag"]


			drilled_args = drill.drill_for_properties(DotDict(curframe_locals), text)

			self.completion_matches = [prefix + i for i in compfunc(text, line, begidx, endidx) + [l for l in curframe_locals_names if l.startswith(text)] + drilled_args]

		try:
			return self.completion_matches[state]
		except IndexError:
			return None


		
def set_trace(no_skip: Any = True, debugmode_only: Any = False, *args, **kwargs) -> bool:
	"""
	Activates DagPDB debugger

	:param no_skip: A param that, if it resolves to False while not in DEBUG_MODE, skips debugging
	:param debugmode_only: A param that, if it resolves to True while not in DEBUG_MODE, skips debugging if DEBUG_MODE is false
	:returns: Whether or not the debugger ran
	"""

	if debugmode_only and not DEBUG_MODE:
		return False

	if not no_skip and not DEBUG_MODE:
		return False

	DagPdb().set_trace(sys._getframe().f_back)
	return True
