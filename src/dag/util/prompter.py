import readline, importlib, sys
import dag
from dag.util import historyfiles


class Prompter:
	def __init__(self, message = "", complete_list = None, display_choices = True, prefill = "", style = "b #F00", id = "", killdelims = ""):
		self.message = message
		self.complete_list = complete_list or []
		self.display_choices = display_choices
		self.prefill = prefill
		self.style = style
		self.id = id
		self.killdelims = killdelims


class ReadLinePrompter(Prompter):
	def completer(self, text, state):
		if text:
			options = [i for i in self.complete_list if i and i.startswith(text)]

			if not options:
				options = [i for i in self.complete_list if text in i]
		else:
			options = []
		if state < len(options):
			return options[state]
		else:
			return None

	def hook(self, ):
		readline.insert_text(self.prefill)
		readline.redisplay()

		for ch in self.killdelims:
			with dag.passexc(KeyError):
				self.delims.remove(ch)

		readline.set_completer_delims("".join(self.delims))


	def prompt(self):		
		olddelims = set(readline.get_completer_delims())
		self.delims = olddelims.copy()
		old_completer = readline.get_completer()
		message = self.message # Done this way so that message can be modified further
		
		try:		
			if self.complete_list is not None:
				self.complete_list.sort()
				readline.parse_and_bind("tab: complete")
				readline.set_completer(self.completer)
		
			lineend = "\n" # Have to keep this because python is bad about backspacing to end of line due to <c red>
			if self.display_choices and self.complete_list is not None:
				message = message + f" <c b>{self.complete_list} (press Tab to see all)</c>"
				lineend = "\n"

			if self.prefill:
				readline.set_pre_input_hook(self.hook)

			postmsg = "" if message.endswith(": ") else (" " if message.endswith(":") else ": ")

			histfile = None

			if self.id:
				histfile = dag.directories.STATE / "prompters" / self.id

			with historyfiles.temphistory(histfile):
				return input(dag.format("\n<c b>" + message + postmsg + f"</c><c {self.style}>" + lineend)).strip()

		except TypeError as e:
			dag.echo("Dag prompt Error: ", e)

		finally:
			dag.echo(dag.format("</c>"))
			readline.set_completer(old_completer)
			readline.set_pre_input_hook()
			readline.set_completer_delims("".join(olddelims))
			
			if not self.id:
				lastcommand = readline.remove_history_item(readline.get_current_history_length()-1)