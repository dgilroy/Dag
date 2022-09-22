import tracemalloc, sys, importlib


import dag
from dag.lib import dtime
from dag.util import dagdebug

from dag.dagcli.alist import Alist

from dag import this

from dag.exceptions import DagFalseException, DagReloadException


@dag.mod("_base_cli_commands", base = True)
class BaseCLICommands(dag.DagMod):
	def __init__(self):
		super().__init__()
		# Used for key completion
		self._alist = Alist	


	@dag.arg("--echo", flag=True)
	@dag.arg("text", nargs=-1)
	@dag.cmd("copy", ">")
	def copy(self, text = "", echo = False):
		text = text or dag.ctx.controller.last_response_no_multicol or dag.ctx.controller.last_response
		return dag.copy_text(dag.format(text), echo)


	@dag.cmd()
	def memuse(self):
		snapshot = tracemalloc.take_snapshot()
		top_stats = snapshot.statistics('lineno')
		breakpoint()



	@dag.cmd("breakpoint", "bb")
	def breakpoint(self):
		return dag.ctx.controller.do_breakpoint()


	@dag.cmd("debugmode")
	def debugmode(self):
		newval = not dagdebug.DEBUG_MODE
		dagdebug.DEBUG_MODE = newval
		return f"Debug Mode: <c b>{newval}</c>"


	@dag.cmd()
	def slice(self):
		return dag.ctx.controller.run_line("test testcollection :::3")


	@dag.cmd("exit", "xx")
	def exit(self):
		return dag.ctx.controller.exit()


	@dag.cmd()
	def eof(self):
		return dag.ctx.controller.eof()


	@dag.cmd()
	def traceback(self):
		raise Exception(dag.ctx.controller.last_exception).with_traceback(dag.ctx.controller.last_exception.__traceback__)


	@dag.arg.Cmd("line")
	@dag.cmd.Meta()
	def completetest(self, line = ""):
		comp = "pokemon moves lee"
		#comp = "nhl teams hur"
		#comp "test nabberarg moo "
		#comp = "color "
		#comp = "nhl ==h"
		#comp = "test g"

		comp = line or comp

		with dag.tprofiler() as profiler:
			completion = dag.ctx.controller.complete_line(comp, debugmode = True)

		print(f"\"{comp}\"\n")
		print(completion)
		print(f"COMPLETION TIME: {profiler.diff}ms")
		print("jwoifjoiewf\033[2K") #clearline


	@dag.arg.DagCmd("command")
	@dag.cmd("man", "help")
	def man(self, command):
		return dag.ctx.controller.man(command)

	@dag.cmd()
	def false(self):
		raise DagFalseException("'false' entered into CLI")


	@dag.cmd()
	def true(self):
		return "true"


	@dag.arg("item", complete = dag.nab(Alist).stored_responses.keys())
	@dag.cmd(display = this._display_alist)
	def alist(self, item = None):
		if item and item in Alist.stored_responses:
			Alist.restore_from(item)
			return Alist.ic_response

		if item:
			if item.lstrip("-").isdigit():
				return Alist[int(item)]

		return Alist



	@dag.cmd()
	def commalist(self):
		return dag.ctx.controller.run_line("pokemon bulbasaur, magnemite")


	def _display_alist(self, alist, formatter):
		return alist.formatted_response or alist


	@dag.arg("text", nargs = -1)
	@dag.cmd()
	def parser(self, text = ""):
		return dag.ctx.controller.parser(text)



	@dag.arg("text", nargs = -1)
	@dag.cmd()
	def argparser(self, text = ""):
		return dag.ctx.controller.argparser(text)



	@dag.arg("item")
	@dag.cmd("l", "launch")
	def launch(self, item):
		#dag.ctx.active_incmd.directives.do_launch = True
		incmd = dag.ctx.active_incmd

		if item and isinstance(item, str):
			if item.isdigit():
				item = Alist[int(item)]
			elif item == "_":
				item = Alist[item]

		return dag.launch(item, incmd.directives.browser, incmd.directives.portalurl)


	@dag.cmd(store_ic_response = False)
	def last(self):
		if dag.ctx.controller.last_incmd:
			dag.ctx.controller.run_incmd(dag.ctx.controller.last_incmd)
			return

		return "No last incmd"
		

	@dag.cmd("r/\d/")
	def alist_item(self):
		pass

	@dag.arg.Cmd("text")
	@dag.cmd.Meta("dag", raw = True)
	def reload_dag(self, text = ""):
		raise DagReloadException(text)


	@dag.arg.Cmd("cmd", complete = dag.nab.default_dagcmd.subcmdtable.names())
	@dag.cmd.Meta("refresh", "swap", raw = True)
	def _reload_module(self, cmd = None):
		if cmd is None:
			if dag.ctx.controller.last_ic_response:
				dagcmd = dag.ctx.controller.last_incmd.dagcmd
				cmd = dagcmd.dagmod.name
				module = dagcmd.dagmod.__module__
			else:
				return "No Cmd provided"
		else:
			module = dag.get_dagcmd(cmd).__module__

		with dag.ctx(is_reloading_dagmod = True):
			importlib.reload(sys.modules[module])
			dag.load_dagcmd(cmd)

			return f"Reloaded module {cmd}"



	@dag.cmd()
	def dpdb(self):
		dp = dagdebug.DagPdb()
		dp.debug()


	@dag.cmd()
	def last_incmd(self):
		return dag.ctx.controller.last_incmd


	@dag.arg("text")
	@dag.cmd()
	def inlineparser(self, text = "test test_collection ##key val1 ##key2 =d"):
		from dag.parser import InputCommandParser, InputScript
		incmd = InputScript.generate_from_text(text).get_last_incmd()
		ilp = InputCommandParser.InputCommandParser(incmd)
		ilp.parse_incmd_tokens()


	@dag.arg.File("file")	
	@dag.cmd()
	def open(self, file):
		dag.get_platform().open(f"'{file}'")