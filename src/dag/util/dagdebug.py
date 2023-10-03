import sys, readline, signal, traceback, pdb, rlcompleter, re
from contextlib import contextmanager
from io import TextIOWrapper
from typing import NoReturn, Any, Optional
from collections.abc import Iterable

import dag
from dag import settings
from dag.lib.dot import DotDict
from dag.util import historyfiles, drill, editors
#from dag.util.editors import registered_editors as editors


DEBUG_MODE = False
IGNORE_BREAKPOINTS = False
TRIGGERS = []

class DagPdb(pdb.Pdb):
	def __init__(
					self,
					completekey: str = 'tab',
					stdin: Optional[TextIOWrapper] = None,
					stdout: Optional[TextIOWrapper] = None,
					skip: Optional[Iterable[str]] = None,
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
		"""

		super().__init__(completekey, stdin, stdout, skip)

		# Stores dagpdb command history
		self.historyfile = historyfiles.HistoryFile(settings.DAGPDB_HISTORY_FILE_NAME)

		# Loads dagpdb command history into readline
		self.read_dagpdb_historyfile()

		# String displayed before every command
		self.prompt = "(DAGPDB)"

		# The editor with which to open code
		self.editor = editors.get_editor()

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


	def do_dd(self, line: str) -> NoReturn: # dir
		scopevars = dag.DotDict(self.get_scope_vars())

		if line:
			print(dir(drill.drill(scopevars, line)))
		else:
			print(scopevars)


	def do_tt(self, line: str) -> NoReturn: # type 
		scopevars = dag.DotDict(self.get_scope_vars())

		if line:
			print(type(drill.drill(scopevars, line)))


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

		self.open_in_editor(editors.get_editor("NOTEPAD++"))


	def do_sublime(self, line: str) -> NoReturn:
		"""
		Opens the current debugger line of code in Sublime

		:param line: The line being executed
		"""

		self.open_in_editor(editors.get_editor("SUBL"))


	# Aliases for do_sublime
	do_subl = do_sub = do_sss = do_ss = do_sublime


	def do_vscode(self, line: str) -> NoReturn:
		"""
		Opens the current debugger line of code in Sublime

		:param line: The line being executed
		"""

		self.open_in_editor(editors.get_editor("VSCODE"))


	# Aliases for do_sublime
	do_vv = do_vscode


	# Open in default editor
	def open_in_editor(self, editor: Optional[editors.Editor] = None) -> NoReturn:
		"""
		Opens the current debugger line in the given editor

		:param editor: The editor with which to open the code
		"""

		editor = editor or self.editor

		filepath, lineno = self.get_current_filepath_lineno()
		editor.open_file(filepath, lineno)


	def do_exc(self, line: str):
		exc = sys.exception()

		if exc is None:
			traceback.print_exc()
		else:
			traceback.print_exception(exc)


	def do_ee(self, line: str) -> None:
		"""
		Opens the current debugger line in the default editor

		:param line: The line being executed
		"""

		self.open_in_editor()


	def do_nn(self, line: str) -> None:
		"""
		Advances the debugger and opens in editor

		:param line: The line being executed
		"""

		self.do_next(line)
		self.open_in_editor()


	def get_scope_vars(self):
		curframe_locals = self.curframe.f_locals

		if "dag" in self.curframe.f_globals.keys(): # "dag" is a special global value that I want completeable if it's in scope
			import dag
			curframe_locals |= {"dag": dag}

		return curframe_locals


	def do_n(self, *args) -> None:
		curframe_locals = self.get_scope_vars()

		super().do_next(0)

		if args:
			args = args[0].split()
			typedargs = [curframe_locals.get(a) for a in args]
			printfn = dag.echo if "dag" in curframe_locals else print
			[printfn(f"<c bg-#0F0 black bu / {name}>\t", a.__repr__()) for name, a in zip(args, typedargs)]

		return 1



	def do_bb(self, line):
		breakpoint()
		pass


	def do_ignorebreakpoints(self, line):
		global IGNORE_BREAKPOINTS
		IGNORE_BREAKPOINTS = True
		return self.resume()

	do_ii = do_ignorebreakpoints


	def postloop(self) -> None:
		"""
		Once command loop ends,
			(1) remove all input debug commands from readline history and replace Dag's historyfile
			(2) Revert the completer delims to what they were before debugging
		"""

		#if dag.instance and hasattr(dag.instance, "controller"):
		#	dag.instance.controller.historyfile.load_into_readline()
			
		readline.set_completer_delims(self.original_delims)


	def emptyline(self) -> int:
		print("DAGPDB Blank Line: Continuing...")
		return self.resume()


	def resume(self) -> int:
		"""
		If a blank line is entered, stop debugging and continue code execution
		"""

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

			self.completer = DagPdbCompleter(curframe_locals)
			self.completion_matches = [prefix + i for i in compfunc(text, line, begidx, endidx) + [l for l in curframe_locals_names if l.startswith(text)] + drilled_args]

		try:
			return self.completer.complete(text, state)
			return self.completion_matches[state]
		except IndexError:
			return None




class DagPdbCompleter(rlcompleter.Completer):
	def complete(self, text, state):
		"""Return the next possible completion for 'text'.
		This is called successively with state == 0, 1, 2, ... until it
		returns None.  The completion should begin with 'text'.

		MODIFIED BY DAG: Doesn't tab when no text entered
		"""

		if self.use_main_ns:
			self.namespace = __main__.__dict__

		if not text.strip():
			if state == 0:
				self.matches = self.global_matches(text)
			try:
				return self.matches[state]
			except IndexError:
				return None

		with dag.catch() as e:
			if state == 0:
				if "." in text:
					self.matches = self.attr_matches(text)
				else:
					self.matches = self.global_matches(text)
			try:
				return self.matches[state]
			except IndexError:
				return None


	def attr_matches(self, text):
		"""Compute matches when text contains a dot.
		Assuming the text is of the form NAME.NAME....[NAME], and is
		evaluable in self.namespace, it will be evaluated and its attributes
		(as revealed by dir()) are used as possible completions.  (For class
		instances, class members are also considered.)
		WARNING: this can still invoke arbitrary C code, if an object
		with a __getattr__ hook is evaluated.
		"""
		m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)

		if "." not in text:
			return []

		from dag.parser.lexer import token_split #-> This was done so that function calls could be completed, but that was too risky because the fuctnions were getting called
		attrs = token_split(text, ".")

		# If the conditions are true: This is a called function. Set it up so that the function isn't called. Check to see later whether fn has a return type and complete against that
		if len(attrs) >= 2 and not attrs[-2][0] in dag.strtools.QUOTEMARKS and attrs[-2].endswith(")") and "(" in attrs[-2]:
			delims = set(readline.get_completer_delims())
			delims.remove("(") #-> This was done so that function calls could be completed, but that was too risky because the fuctnions were getting called
			delims.remove(")")
			readline.set_completer_delims("".join(delims))

			attrs = attrs[:-2] + [attrs[-2].split("(")[0], attrs[-1]]

		expr, attr = ".".join(attrs[:-1]), attrs[-1]
		#expr, attr = m.group(1, 3)
		try:
			thisobject = eval(expr, self.namespace)
		except Exception:
			return []

		try:
			returntype = thisobject.__annotations__["return"]
		except (AttributeError, IndexError, KeyError, TypeError):
			pass

		# get the content of the object, except __builtins__
		words = set(dir(thisobject))
		words.discard("__builtins__")

		if hasattr(thisobject, '__class__'):
			words.add('__class__')
			words.update(rlcompleter.get_class_members(thisobject.__class__))
		matches = []
		n = len(attr)

		if attr == '':
			noprefix = '_'
		elif attr == '_':
			noprefix = '__'
		else:
			noprefix = None

		with dag.catch() as e:
			while True:
				for word in words:
					if (word[:n] == attr and
						not (noprefix and word[:n+1] == noprefix)):
						match = "%s.%s" % (expr, word)
						if isinstance(getattr(type(thisobject), word, None),
									  property):
							# bpo-44752: thisobject.word is a method decorated by
							# `@property`. What follows applies a postfix if
							# thisobject.word is callable, but know we know that
							# this is not callable (because it is a property).
							# Also, getattr(thisobject, word) will evaluate the
							# property method, which is not desirable.
							matches.append(match)
							continue
						if (value := getattr(thisobject, word, None)) is not None:
							try:	# TRY/EXCEPT ADDED BY DAG: _callable_postfix seems to not play well with janky getattrs
								matches.append(self._callable_postfix(value, match))
							except TypeError:
								matches.append(match)
						else:
							matches.append(match)
				if matches or not noprefix:
					break
				if noprefix == '_':
					noprefix = '__'
				else:
					noprefix = None
			matches.sort()

		return matches


	def global_matches(self, text):
		"""Compute matches when text is a simple name.
		Return a list of all keywords, built-in functions and names currently
		defined in self.namespace that match.

		DAG CHANGE: Only current namespace gets searched. Previously, also returned keywords and builtins
		"""
		matches = []
		seen = {"__builtins__"}
		n = len(text)
		
		for nspace in [self.namespace]:
			for word, val in nspace.items():
				if word[:n] == text and word not in seen:
					seen.add(word)
					matches.append(self._callable_postfix(val, word))
		return matches






class TraceSetter:
	def __call__(self, is_set_trace: object = True, debugmode_only: object = False, *args, framesback: int = 0, trigger = None, show: object = dag.UnfilledArg, line = None, **kwargs) -> bool:
		"""
		Activates DagPDB debugger

		:param is_set_trace: A param that, if it resolves to False while not in DEBUG_MODE, skips debugging
		:param debugmode_only: A param that, if it resolves to True while not in DEBUG_MODE, skips debugging if DEBUG_MODE is false
		:returns: Whether or not the debugger ran
		"""

		global TRIGGERS

		if dag.ctx.skip_breakpoint:
			if not dag.ctx.complain_breakpoint_skip:
				dag.echo("Skipping breakpoint because dag.ctx.skip_breakpoint is set")
			return False

		if trigger is not None and trigger.lower() not in TRIGGERS and not dag.ctx.get(trigger.lower()):
			return False

		if IGNORE_BREAKPOINTS:
			return False

		if debugmode_only and not DEBUG_MODE:
			return False

		if not is_set_trace and not DEBUG_MODE:
			return False

		if show is not dag.UnfilledArg:
			dag.echo("DagPDB Show:", f"<c bu/{show}>")

		frame = sys._getframe().f_back

		for i in range(framesback):
			frame = frame.f_back

		if line:
			#Hoping someodaoy that breakpoint(line = "filename:lineno") can virtually set a breakpoint at that point to be executed during dagcmcd call
			pass

		DagPdb().set_trace(frame)
		return True



set_trace = TraceSetter()



@contextmanager
def set_trigger(name, condition = True, trigger = ""):
	global TRIGGERS

	name = name.lower()
	try:
		if trigger and not trigger in TRIGGERS:
			pass
		elif condition:
			TRIGGERS.append(name)
		yield
	finally:
		try:
			TRIGGERS.remove(name)
		except ValueError:
			pass


class DebugTriggerer:
	gotten_attr = None

	def __init__(self):
		self._debugger = None


	@property
	def debugger(self):
		#Don't initiate a DagPpdb session until needed. Prevents random "DAGPDB" from being printed
		if self._debugger is None:
			self._debugger = DagPdb()

		return self._debugger


	def __getattr__(self, attr):
		self.gotten_attr = attr
		return self


	def __call__(self, *args, **kwargs):
		kwargs["framesback"] = kwargs.get("framesback",0)+1
		attr = self.gotten_attr
		self.gotten_attr = None
		TraceSetter()(*args, trigger = attr, **kwargs)


	def set_breakpoint_at(self, item):
		breakpoint()
		pass


	def __matmul__(self, item):
		return self.at(item)



def postmortem(tb):
	"""Taken from python pdb module"""
	match tb:
		case BaseException():
			tb = tb.__traceback__

	# handling the default
	if tb is None:
		# sys.exc_info() returns (type, value, traceback) if an exception is
		# being handled, otherwise it returns None
		t = sys.exc_info()[2]
	if tb is None:
		raise ValueError("A valid traceback must be passed if no "
						 "exception is being handled")

	dagpdb = DagPdb()
	dagpdb.reset()
	dagpdb.interaction(None, tb)