import os, readline, cmd, pathlib, sys

import dag

from dag.dagcli import completers
from dag.dagcli.view import DagCLIView
from dag.util import prompter



#Byte counter
#from pympler.tracker import SummaryTracker
#tracker = SummaryTracker()


def display_completion_matches(substring, matches, maxtotal):
	print(f"\n\nMatches for '{substring}':")
	for match in matches:
		print(f" - {match}")
	print("\n\n")

	print(self.prompt.rstrip(), readline.get_line_buffer(), sep='', end='')
	sys.stdout.flush()






# This is a child of python's Cmd.cmd. and DagCLIView.DagCLIView
class DagPyCmdCLIView(DagCLIView, cmd.Cmd):
	
	def __init__(self, style_formatter = None, is_silent = False, **kwargs):
		with dag.dtprofiler("init DagPyCmdCLIView"):
			cmd.Cmd.__init__(self)
			DagCLIView.__init__(self, style_formatter, is_silent = is_silent)

			# Stores inputted kwargs for possible future use
			self.kwargs = kwargs

			# Set up the unix stuff
			readline.set_completer_delims(' /\t\n')							# Complete on Tab or Newline only
			readline.parse_and_bind('set show-all-if-ambiguous on')			# Show all possible complete matches
			readline.parse_and_bind('set colored-completion-prefix on')		# Color parts of completion candidates that match needle
			readline.parse_and_bind('set bell-style none')					# Don't ring bell on errors
			#readline.set_completion_display_matches_hook(display_completion_matches)
					
			# Intro Text (used by cmd.cmd)
			self.intro = self.format(f"\n<c b #2BA4B8>|</c><c b #1C7071>|</c><c b #259C58>/</c><c b #C49B3F>/</c><c b #E87136>_</c> <c b #FF>Something to tie together APIs:</c>")

			self.promptclass = prompter.ReadLinePrompter


	def prompt_input(self):
		return self.cmdloop()


	# Text that appears with every prompt
	@property
	def prompt(self):
		return super().prompt()


	def get_line_buffer(self):
		return readline.get_line_buffer()


	def completedefault(self, text, line, begidx, endidx):
		return completers.complete_line(line)
		
		
	# Modify completenames to handle upper-cased input
	def completenames(self, text, *ignored):
		text = text.lower()
		return completers.complete_line(text)


	def complete(self, text, state):
		"""Return the next possible completion for 'text'.
		If a command has not been entered, then complete against command list.
		Otherwise try to call complete_<command> to get list of completions.
		"""
		if state == 0:
			import readline
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
			self.completion_matches = compfunc(text, line, begidx, endidx)
		try:
			return self.completion_matches[state]
		except IndexError:
			return None


	# Turn off white coloring
	def precmd(self, line):
		print("\033[0m")
		return line


	def onecmd(self, line = ""):
		dag.instance.controller.run_input_line(line)