from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles.named_colors import NAMED_COLORS
from prompt_toolkit.completion import Completion, WordCompleter, ThreadedCompleter
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

import dag
from dag.util import prompter

from dag.dagcli import completers





class PTPromptDagCompleter(WordCompleter):
	def get_completions(self, document, complete_event):
		line = document.text
		word = document.text.split(" ")[-1]
		yield from [Completion(i, start_position = -len(i)) for i in completers.dag_complete(word, self.words)]




class DagPromptToolkitPrompter(prompter.Prompter):
	def prompt(self):
		message = self.message
		completer = None

		if self.complete_list:
			completer = ThreadedCompleter(PTPromptDagCompleter(self.complete_list) if self.complete_list else None)

		if self.display_choices and completer:
			message = message + f" <c b>{self.complete_list if self.complete_list else ''} (press Tab to see all)</c>"

		histfile = None

		if self.id:
			histfilepath = dag.directories.STATE / "prompters" / self.id
			histfile = FileHistory(histfilepath)

		postmsg = "" if message.endswith(": ") else (" " if message.endswith(":") else ": ")

		return prompt(
			dag.instance.view.format("\n<c b>" + message + postmsg + f"</c>\n"),
			completer = completer, 
			default = self.prefill,
			history = histfile,
			lexer = RedLexer()).strip()




class RedLexer(Lexer):
	def lex_document(self, document):
		def get_line(lineno):
			return [(NAMED_COLORS['Red'], document.lines[lineno])]

		return get_line