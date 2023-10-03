import os, readline, cmd, pathlib, io, sys
from datetime import datetime

from prompt_toolkit import print_formatted_text, ANSI
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit import formatted_text
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.completion import ThreadedCompleter
from prompt_toolkit.history import FileHistory


import dag

from dag.dagcli import completers
from dag.dagcli.view import DagCLIView

from dag.dagcli.pt.dag_prompt_session import DagPromptSession
from dag.dagcli.pt.dag_base_prompter import DagPromptToolkitPrompter
from dag.dagcli.pt.dag_cli_completer import DagPTCLICompleter

from dag.parser import inputscripts



#Byte counter
#from pympler.tracker import SummaryTracker
#tracker = SummaryTracker()

bindings = KeyBindings()

sys.breakpointhook = dag.util.dagdebug.set_trace


def dag_on_completions_changed(buffer):
	if buffer.complete_state:
		completions = buffer.complete_state.completions

		if len(completions) == 1:
			completions[0].text += ' '



@bindings.add('escape')  # Bind the escape key
def _(event):
	buffer = event.app.current_buffer
	buffer.cancel_completion()



@bindings.add("enter")
def _accept_input(event) -> None:
	event.app.current_buffer.validate_and_handle()
	return
	if not event.app.current_buffer.complete_state or event.app.current_buffer.complete_state.current_completion is None:
		event.app.current_buffer.validate_and_handle()
	else:
		event.app.current_buffer.complete_state = None



class DagLexer(Lexer):
	def lex_document(self, document):
		def get_line(lineno):
			line = document.lines[lineno]

			firstword = line
			afterword = ""

			if line:
				try:
					spaceindex = line.index(" ")
					firstword = line[:spaceindex]
					afterword = line[spaceindex:]
				except ValueError:
					pass

				appinfo = dag.instance.controller.appinfo
				identifier_settings = appinfo.get(firstword, {})
				color = identifier_settings.get("color") or "#FFFFFF" # Need to use "or" or else empty colors strings might appear that annoy PT

				return [(color, firstword)] + [("#FFFFFF", afterword)]

			return []


		return get_line




#def process_changed_text(buffer):
#	pass



def process_changed_cursor(buffer):
	document = buffer.document
	cursor_position = document.cursor_position
	before_cursor = document.current_line_before_cursor
	after_cursor = document.current_line_after_cursor
	current_char = document.current_char
	current_line = document.current_line
	start_of_word = document.find_start_of_previous_word(cursor_position)
	is_end_of_line = after_cursor == ""

	if not dag.settings.showincmd:
		return

	with dag.ctx("parse_while_valid", "skip_validate_inputarg", "skip_breakpoint"):
		incmd = inputscripts.generate_from_text(before_cursor).get_last_incmd()
		pass

	if is_end_of_line:
		obj = incmd.active_inputobject
		autofill = obj.provide_autofill(incmd, obj)

		if autofill:
			buffer.insert_text(autofill)

			cursormove = obj.autofill_move_cursor(incmd, obj)
			buffer.cursor_position += cursormove

	dag.echo(incmd)
	dag.echo(before_cursor, " :: ", f"<c bg-#88 black>{current_char}</c bg-#88 black>", " :: ", f"<c bg-#88 black>{after_cursor}</c bg-#88 black>") #[1:] trims current char from after cursor
	dag.echo(before_cursor + f"<c bg-#88 black>{current_char or ' '}</c bg-#88 black>" + after_cursor[1:]) #[1:] trims current char from after cursor



# This is a child of python's Cmd.cmd. and DagCLIView.DagCLIView
class DagPromptToolkitCLIView(DagCLIView):
	def __init__(self, style_formatter = None, is_silent = False, **kwargs):
		with dag.dtprofiler("init DagPromptToolkitCLIView"):
			super().__init__(style_formatter = style_formatter, is_silent = is_silent)

			# Stores inputted kwargs for possible future use
			self.kwargs = kwargs

			with dag.dtprofiler("starting DagPromptSession"):
				self.session = DagPromptSession(
					enable_history_search = False,
					history = FileHistory(dag.directories.STATE / dag.settings.HISTORY_FILE_NAME),
					complete_style = CompleteStyle.MULTI_COLUMN,
					completer = ThreadedCompleter(DagPTCLICompleter()), # ThreadedCompleter prevents freezing on slower searches
					key_bindings = bindings,
					complete_while_typing = bool(dag.settings.complete_while_typing),
					color_depth = ColorDepth.DEPTH_24_BIT,
					lexer = DagLexer(),
				)

			#self.session.default_buffer.on_text_changed += process_changed_text
			self.session.default_buffer.on_cursor_position_changed += process_changed_cursor
			self.session.default_buffer.on_completions_changed += dag_on_completions_changed
			self.session.app.timeoutlen = 0.1 # Speeds up "escape" closing completions box (I also tried ttimeoutlen but it didn't seem to help)

			self.echo(f"\n<c b #2BA4B8>|</c><c b #1C7071>|</c><c b #259C58>/</c><c b #C49B3F>/</c><c b #E87136>_</c> <c b #FF>Something to tie together APIs:</c>")

			# Used by stand-alone prompters (not the main loop)
			self.promptclass = DagPromptToolkitPrompter


	def echo(self, *text, **kwargs):
		if not (dag.ctx.silent or dag.settings.silent):
			print_formatted_text(self.format(*text))
		
		
	def format(self, *text):
		text = " ".join([str(text) for text in text])
		return ANSI(dag.format(text))


	def prompt_input(self):
		try:
			while True:
				#with patch_stdout(): -> Currently Prevents proper printing of ctags in pdb
					line = self.session.prompt(self.prompt())
					dag.instance.controller.run_input_line(line)
		except EOFError as e:
			# Caught here to prevent PromptToolkit from complaining
			dag.exit()


	def get_line_buffer(self):
		return self.session.app.current_buffer.text




@dag.arg.Cmd("line", stripquotes = True)
@dag.cmd
def ptcompleteline(line = ""):
	from prompt_toolkit.completion import CompleteEvent
	from prompt_toolkit.document import Document

	document = Document(line)
	completeevent = CompleteEvent()
	completer = DagPTCLICompleter()

	return [*completers.get_completions(document, completeevent)]