import sys, readline, os, pathlib
from datetime import datetime

import dag
from dag.util import dagdebug

from dag import dag_view
from dag.dagcli import outputprocessors



# This class requests input and feeds to Controller, then displays output
class DagCLIView(dag_view.DagView):
	def __init__(self, style_formatter = None, is_silent = False):
		with dag.ctx(view = self):
			self.style_formatter = style_formatter or dag.format
			self.is_silent = is_silent



	def format(self, text: str) -> str:
		return self.style_formatter(text) # Currently pointing to DagForatter, but could be changed later. using getattr bc child sometimes calls formatter


	def echo(self, *args: tuple[str]) -> str:
		formatted_text = [self.format(text) for text in args]

		if not (self.is_silent or dag.settings.silent or dag.ctx.silent):
			print(*formatted_text)

		return formatted_text



	def get_dir_git_branch(self):
		cwd = pathlib.Path.cwd() / ".git" / "HEAD"

		paths = [cwd] + [*cwd.parents]
		content = ""

		for path in paths:
			headpath = path / ".git" / "HEAD"
			if headpath.exists():
				with headpath.open("r") as f:
					content = f.read().splitlines()
				break

		if content:
			for line in content:
				if line[0:4] == "ref:":
					return line.partition("refs/heads/")[2]

		return ""
		

	# Called by DagInstance when starting the program
	def run_prompt_loop(self) -> None:
		while True:
			try:

				self.prompt_input()
			except KeyboardInterrupt:			# IF Ctrl-C
				self.handleKeyboardInterrupt()


	# An attempt at making async Dag
	async def run_async_command_loop(self):
		while True:
			try:
				await self.prompt_input()
			except KeyboardInterrupt:
				self.handleKeyboardInterrupt()


	# Used by the command loops when Ctrl+C is pressed
	def handleKeyboardInterrupt(self):
		self.echo("\n")

		if self.get_line_buffer():		# If there's text in the line, rerun with blank line
			return

		sys.exit()						# If there's no text in the line, exit




	# Text that appears with every prompt
	def prompt(self):
		dag.debug.IGNORE_BREAKPOINTS = False
		dag.debug.TRIGGERS = []
		
		if dag.settings.PROMPT:
			return self.format(dag.settings.PROMPT)

		prompt = ""


		templist = dag.instance.controller.templist

		if templist:
			prompt += f"\n<c #F8F bg-#222>Temp list: </c #848><c #848 bold><c #F00 / {templist.manager.app.name}> {templist.name}</c>"

		dagvars = dag.instance.controller.vars

		if dagvars:
			varnames = ", ".join([f"${v}" for v in dagvars])
			prompt += f"\n<c bg-#600 black / Vars:> <c #800 bg-#200 / {varnames}>"


		alist = dag.instance.controller.alist

		if alist.name and not dag.settings.PROMPT_HIDE_ALIST:
			alist_id = f":{alist.current_id}" if alist.current_id != "" else ""
			cmdpath = alist.collection_dagcmd.cmdpath(until = -1)
			prompt += f"\n<c white bg-#222>Active list: </c white><c #F00 bold>{cmdpath} </c #F00><c yellow>{alist.name}<c pink1>{alist_id}</c>"


		settings = dag.settings.session_settings

		if settings:
			prompt += "\n<c bg-#128> " + ", ".join([f"=={k} {v}" for k,v in settings.items()]) + "</c>"

		prompt += f"\n<c bold>"

		if not dag.settings.PROMPT_HIDE_TIME:
			tformat = '%m/%d/%y %I:%M:%S %p'

			if dag.settings.show_milliseconds:
				tformat = '%m/%d/%y %I:%M:%S.%f %p'

			prompt += f"<c #27C5DC>§ {datetime.now().strftime(tformat)}</c>"

		if not dag.settings.PROMPT_HIDE_CWD:
			prompt += f"<c #27C5DC>   --   {os.getcwd()}</c>"

		if not dag.settings.PROMPT_HIDE_GIT_BRANCH:
			prompt += f" <c #F22>{self.get_dir_git_branch()}</c>"
	
		# Bold and color are split up because Windows 10 Ubuntu shell doesn't like it
		prompt += f"\n<c #EC5100>§ DAG)<c #FFF> " # New line is placed where it is 
		
		return self.format(prompt)




	################# PRINTS INCMD RESPONSE #########################


	# Takes a fully-run incmd and processes how it's displayed in terminal
	def print_incmd_response(self, ic_response):
		# Print response to Terminal

		if ic_response.incmd.is_piped:
			return

		self.echo(ic_response.response)



	################# OUTPUT UTILITIES #########################
	def pre_incmd_execute(self, incmd, parsed):
		if incmd.is_piped:
			return

		if isinstance(incmd.outputprocessor, outputprocessors.StandardOutputProcessor):
			self.print_incmd_message_if_valid(incmd, parsed)


	## Format Message
	def print_incmd_message_if_valid(self, incmd, parsed):
		if incmd.dagcmd.display_settings.get("message") is not None:
			items = parsed.copy()

			for argname, arg in items.items():
				if isinstance(arg, dag.DTime):
					items[argname] = arg.format("%Y-%m-%d")

			message = str(incmd.dagcmd.display_settings.message).format(**{k: v for k, v in items.items() if v is not None})
			return self.echo(f"\n{message}")