import os, readline, cmd
from datetime import datetime

import dag
from dag.dagcli.alist import Alist

from dag.dagcli.view import DagCLIView



#Byte counter
#from pympler.tracker import SummaryTracker
#tracker = SummaryTracker()


# This is a child of python's Cmd.cmd. and DagCLIView.DagCLIView
class DagPyCmdCLIView(DagCLIView, cmd.Cmd):
	
	def __init__(self, controllerClass, startup_args, styleformatter = None, is_silent = False, **kwargs):
		cmd.Cmd.__init__(self)
		DagCLIView.__init__(self, controllerClass, startup_args, styleformatter, is_silent = is_silent)

		# Stores inputted kwargs for possible future use
		self.kwargs = kwargs

		# Set up the unix stuff
		readline.set_completer_delims(' /\t\n')							# Complete on Tab or Newline only
		readline.parse_and_bind('set show-all-if-ambiguous on')			# Show all possible complete matches
		readline.parse_and_bind('set colored-completion-prefix on')		# Color parts of completion candidates that match needle
		readline.parse_and_bind('set bell-style none')					# Don't ring bell on errors
				
		# Intro Text (used by cmd.cmd)
		self.intro = self.format(f"\n<c bold #2BA4B8>|</c><c bold #1C7071>|</c><c bold #259C58>/</c><c bold #C49B3F>/</c><c bold #E87136>_</c> <c bold #FF>Something to tie together APIs:</c>")
				
		self.run_startup_args()


	def prompt_input(self):
		return self.cmdloop()


	# Treat any passed-in args as a line to be run
	def run_startup_args(self):
		# Run any input text
		if self.startup_args:						# Any other input text is immediately set to run
			self.controller.run_input_line(" ".join(self.startup_args))


	# Text that appears with every prompt
	@property
	def prompt(self):
		#prompt = f"{self.times}"
		#self.times += 1

		prompt = ""

		if Alist.name:
			alist_id = f":{Alist.current_id}" if Alist.current_id else ""
			cmdpath = Alist.collection_dagcmd.cmdpath(until = -1)
			prompt += f"\n<c white bg-#222>Active list: </c white><c #F00 bold>{cmdpath} </c #F00><c yellow>{Alist.name}<c pink1>{alist_id}</c>"

		prompt += f"\n<c bold><c #27C5DC>\u00A7 {datetime.now().strftime('%m/%d/%y %I:%M:%S %p')}   --   {os.getcwd()}</c>"
	
		# Bold and color are split up because Windows 10 Ubuntu shell doesn't like it
		prompt += f"\n<c #EC5100>\u00A7 DAG)</c> <c #FFF>" # New line is placed where it is 
		
		return self.format(prompt)


	def get_line_buffer(self):
		return readline.get_line_buffer()


	def completedefault(self, text, line, begidx, endidx):
		return self.controller.complete_line(line)
		
		
	# Modify completenames to handle upper-cased input
	def completenames(self, text, *ignored):
		return [f"{name} " for name in dag.default_dagcmd.subcmdtable.get_completion_names() if name.lower().startswith(text.lower())]


	# Turn off white coloring
	def precmd(self, line):
		print("\033[0m")
		return line


	def onecmd(self, line = ""):
		self.controller.run_input_line(line)