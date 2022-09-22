import sys, readline

import dag
from dag.util import dagdebug

from dag import dag_view



# This class requests input and feeds to Controller, then displays output
class DagCLIView(dag_view.DagView):
	def __init__(self, controller_class, startup_args, style_formatter = None, is_silent = False):
		with dag.ctx(view = self):
			self.controller_class = controller_class
			self.startup_args = [*filter(None, startup_args)]
			self.style_formatter = style_formatter or dag.format
			self.is_silent = is_silent

			# Process directives passed when initializing Dag
			self.process_startup_args()

			# Parses and runs the input
			self.controller = self.controller_class(self)



	def process_startup_args(self):
		# Window Resizing
		if not "==w" in self.startup_args:				# If started with "=w", don't resize the window
			dag.get_terminal().resize_window(rows = dag.config.WINDOW_ROWS, cols = dag.config.WINDOW_COLS)
		else:
			self.startup_args.remove("==w")

		if "==d" in self.startup_args:				# If started with "=w", don't resize the window
			dagdebug.DEBUG_MODE = True
			self.startup_args.remove("==d")


	def format(self, text):
		return self.style_formatter(text) # Currently pointing to DagForatter, but could be changed later. using getattr bc child sometimes calls formatter


	def echo(self, text):
		formatted_text = self.format(text)

		if not self.is_silent:
			print(formatted_text)

		return formatted_text
		

	# Called by DagInstance when starting the program
	def run_prompt_loop(self):
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




	################# PRINTS INCMD RESPONSE #########################


	# Takes a fully-run incmd and processes how it's displayed in terminal
	def print_incmd_response(self, ic_response):
		# Print response to Terminal
		self.echo(ic_response.response)



	################# OUTPUT UTILITIES #########################

	## Format Message
	def print_incmd_message_if_valid(self, incmd):
		if incmd.dagcmd.settings.get("message") is not None:
			items = incmd.parsed.copy()

			for argname, arg in items.items():
				if isinstance(arg, dag.DTime):
					items[argname] = arg.format("%Y-%m-%d")

			message = incmd.dagcmd.settings.message.format(**{k: v for k, v in items.items() if v is not None})
			return self.echo(f"\n{message}")