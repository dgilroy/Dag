import sys, traceback, subprocess, fnmatch, pathlib
from typing import NoReturn

import dag
from dag.util.historyfiles import HistoryFile

from dag.dagcli import helpformatter
from dag.dagcli import filts # Needs to be imported from somewhere, so controller was chosen
from dag.dagcli.alists import Alist
from dag.parser import inputscripts, lexer
from dag.dag_controller import DagController
from dag.exceptions import DagError, DagFalseException, DagMultipleCommaListException, DagReloadException

with dag.dtprofiler("import root dag.modules") as tp:
	#from dag import pathmanager_dagmod
	#from dag import config_module
	#from dag.dagcli import bash_dagapp
	#from dag.dagcli import base_cli_dagmod
	pass


class DagCLIController(DagController):
	def __init__(self, is_interactive = False):
		dag.instance.controller = self

		self.is_interactive = is_interactive

		from dag import appmanager
		with dag.ctx("silent"):
			self.appmanager = appmanager.AppManager()
			self.appinfo = self.appmanager.appinfo

		self.last_inputscript = None
		self.last_incmd = None
		self.last_ic_response = None
		self.last_exception = None

		self.alist = Alist()
		self.templist = []
		self.vars = {"dag": dag}
		
		#self.historyfile = HistoryFile(dag.settings.HISTORY_FILE_NAME)
		#self.maybe_load_history()


	#def maybe_load_history(self):
	#	if self.is_interactive:
	#		self.historyfile.load_into_readline()


	#def maybe_add_history(self, line):
	#	if self.is_interactive:
	#		# Add input to history file
	#		self.historyfile.add_if_valid(line)

		
		
	def run_input_line(self, line: str):
		"""
		Runs the line and records the line in history

		:param line: The line to be executed
		"""
		
		return self.run_line(line, store_history = True)


	def run_line(self, line: str, store_history: bool = False):
		# If no line, reload Dag

		if not line.strip():
			dag.instance.view.echo("<c magenta2 u>Blank Line Detected:</c>")
			self.reload()

		# If EOF, end session
		if line.lower().strip() in ["eof"]:
			return self.eof()

		#if store_history:
			#self.maybe_add_history(line)

		# Parse line into incmds
		input_script = inputscripts.generate_from_text(line, strip_trailing_spaces = True)
		return self.run_inputscript(input_script)



	def run_inputscript(self, inputscript):
		try:
			incmd = None
			ic_response = inputscript.execute()

			if inputscript.executor.last_exception:
				self.last_exception = inputscript.executor.last_exception
		except Exception as e:
			self.last_exception = e
			dag.print_traceback(e)
			dag.echo("\n")

			if not isinstance(e, (dag.DagError, DagReloadException)):
				dag.instance.view.echo(f"\n<c red>{e}</c>")
				dag.debug.postmortem(e)
			return

			incmd = inputscript.executor.last_incmd

			if incmd and incmd.is_should_store_input_info: # If "store_ic_response = False" on dagcmd, 
				self.last_incmd = inputscript.executor.last_incmd
				self.last_ic_response = ic_response

			return ic_response
		except EOFError as e:
			dag.instance.view.echo(f"EOF Error: {e}")
			dag.exit()
		except DagMultipleCommaListException as e:
			return dag.instance.view.echo(f"<c b>Error: </c> {e}")
		except RuntimeError as e:
			dag.instance.view.echo(f"<c bold>RuntimeError: execution halted:</c>\n\n")
			dag.print_traceback()
			dag.instance.view.echo(f"\n<c red>{e}</c>")
		except DagReloadException as e: # Can't let base "Exception" eat this if it's being fired from a dagcmd such as "reload"
			raise e
		except DagError as e:
			dag.echo(f"<c red>{e}</c red>")
		except (Exception, SyntaxError) as e:
			dag.print_traceback()
			dag.instance.view.echo(f"<c bold>Exception: {e}</c>")
		finally:
			if incmd and incmd.settings.store_inputscript:
				self.last_inputscript = inputscript


	@dag.arg.InputObject("command")
	@dag.cmd(aka = "man")
	def help(command):
		if command.name in dag.get_dagcmd("bash").get_dagcmd_names():
			return subprocess.run(['man', command], capture_output = True).stdout.decode("utf-8")
		else:
			return helpformatter.generate_help_text(command)


	def process_dagcmd_response_for_cli(self, icresponse, icexecutor):
		incmd = icresponse.incmd
		
		if icresponse.formatter.idxitemslist:
			try:
				icresponse.raw_response = icresponse.raw_response.create_subcollection(icresponse.formatter.idxitemslist) # Dont use sum: It's too slow
				self.alist.set(icresponse)
			except:
				pass

		self.templist = icresponse.formatter.templist # Either gets the templist or resets it back to empty

		# Handle callback
		if incmd.settings.get("callback") is not None:
			callback_incmd = incmd.get_callback_incmd()
			callback_incmd.directives = incmd.directives | (callback_incmd.directives or {})
			type(icexecutor)(icexecutor.iclistexecutor, callback_incmd).execute()






@dag.cmd
def false() -> NoReturn:
	raise DagFalseException("'false' entered into CLI")






@dag.arg.Flag("--editor")
@dag.cmd("traceback", "tb")
def do_traceback(editor = False): 
	if dag.instance.controller.last_exception:
		if editor:
			tbinfo = traceback.extract_tb(dag.instance.controller.last_exception.__traceback__)[-1]
			lineno = tbinfo.lineno
			filename = tbinfo.filename
			return dag.get_editor().open_file(filename, lineno)


		raise Exception(dag.instance.controller.last_exception).with_traceback(dag.instance.controller.last_exception.__traceback__)

	return "No traceback found"


@dag.arg.Cmd("text")
@dag.cmd(aka = ("ii"), raw = True)
def reload(self, text = ""):
	"""
	Raises exception to exit Dag instance so that a new one will start

	:param reloadargs: the args to be passed into the new Dag instance
	:raises DagReloadException: Raises exception that triggers reload
	"""

	return dag.instance.controller.reload(text) # Done like this so that DagCmd isn't called while run_line detects blank line


@dag.cmd
def exit(self, code: int = 0):
	return dag.exit(code)


@dag.arg.Flag("--pdb", target = "do_pdb")
@dag.cmd("breakpoint", "bb")
def do_breakpoint(self, response: object = dag.UnfilledArg, do_pdb: bool = False):
	if response is not dag.UnfilledArg:
		print(response)
		
	if do_pdb:
		import pdb; pdb.set_trace()
		pass
	else:
		breakpoint()
		pass



true = dag.cmd(value = True)


@dag.arg("key", complete = dag.nab.dtresults.keys())
@dag.cmd
def dtresults(key: dag.Searcher = ""):
	results = {k: f"{v:08.4f} ms" for k,v in dag.dtresults.items()}
	return {k: v for k, v in sorted(results.items(), key=lambda item: item[1], reverse = True) if not key or key.search(k)}


@dag.arg.GreedyWords("text")
@dag.cmd
def lex(text):
	with dag.tprofiler() as c:
		lexed = lexer.DagLexer().lex(text)

	dag.instance.view.echo(f"Lexing took {c.diff}ms")
	return lexed



@dag.cmd
def lark(text = "wow; dog && cat", dodebug: bool = False):
	from dag.parser import lark

	parsed = lark.test_lark(text)
	breakpoint(dodebug)
	return parsed


@dag.cmd
def gerund(word):
	return dag.words.gerund(word)





@dag.arg("key", complete = dag.nab.instance.controller.appinfo.keys())
@dag.cmd("appinfo")
def _load_appinfo(key = None):
	appinfo = dag.instance.controller.appinfo

	if key:
		return appinfo.get(key)

	return appinfo


@dag.cmd()
def clear_appinfo():
	appmanager = dag.instance.controller.appmanager
	appmanager.clear_appinfo
	return "Appinfo cleared"


@dag.cmd()
def reload_appinfo():
	appmanager = dag.instance.controller.appmanager
	appmanager.clear_appinfo()
	appmanager.initialize_session()



@dag.cmd("register") # Done this way so that this core functionality doesn't have to go through dagcmd-execution process
def _register(filepath: pathlib.Path, updating: bool = False):
	appmanager = dag.instance.controller.appmanager
	appmanager.register(filepath, updating)
	dag.file.appendline(dag.PATHINFO_PATH, str(filepath))