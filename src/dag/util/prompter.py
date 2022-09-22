import readline, importlib, sys
import dag


def prompt(message = "", complete_list = None, display_choices = True, prefill = "", style = "b #F00"):
	
	def completer(text, state):
		if text:
			options = [i for i in complete_list if i and i.startswith(text)]

			if not options:
				options = [i for i in complete_list if text in i]
		else:
			options = []
		if state < len(options):
			return options[state]
		else:
			return None


	def hook():
		readline.insert_text(prefill)
		readline.redisplay()
		
		
	old_completer = readline.get_completer()
	
	try:		
		if complete_list is not None:
			complete_list.sort()
			readline.parse_and_bind("tab: complete")
			readline.set_completer(completer)
	
		lineend = "\n" # Have to keep this because python is bad about backspacing to end of line due to <c red>
		if display_choices and complete_list is not None:
			message = message + f" <c b>{complete_list} (press Tab to see all)</c>"
			lineend = "\n"

		if prefill:
			readline.set_pre_input_hook(hook)

		postmsg = "" if message.endswith(": ") else (" " if message.endswith(":") else ": ")

		return input(dag.format("\n<c b>" + message + postmsg + f"</c><c {style}>" + lineend)).strip()

	except TypeError as e:
		print("DagMod.prompt Error: ", e)		

	finally:
		print(dag.format("</c>"))
		readline.set_completer(old_completer)
		readline.set_pre_input_hook()
		lastcommand = readline.remove_history_item(readline.get_current_history_length()-1)