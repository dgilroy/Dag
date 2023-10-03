from prompt_toolkit.completion import Completer, Completion

import dag
from dag.dagcli import completers


class DagPTCLICompleter(Completer):
	def get_completions(self, document, complete_event):
		with dag.ctx("completer_active"):
			line = document.text
			word = document.text.split(" ")[-1]

			appinfo = dag.instance.controller.appinfo

			try:
				compincmd = completers.get_completion_incmd(line)

				with dag.ctx(active_incmd = compincmd, skip_breakpoint = not dag.ctx.completeline_active, complain_breakpoint_skip = not dag.ctx.completeline_active):
					for item in completers.complete_completion_incmd(compincmd, word):
						item += "" if item.endswith(" ") else " "
						completion = Completion(item,
							display = item,
							start_position = -len(word),
							style="bold bg:#000000 fg:#FFFFFF",
							selected_style = "bold bg:#000000 fg:#BBBBBB",
						)

						if " " not in line:
							completion = dag.defaultapp.pt_process_completion(completion)
						else:
							completion = dag.ctx.active_incmd.active_inputobject.pt_process_completion(completion)

						yield completion
			except Exception: # Silence errors during completion bc they are too jarring
				dag.bb.completeline()
				return
