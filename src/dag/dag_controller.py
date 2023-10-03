from typing import NoReturn
import dag
from dag.exceptions import DagReloadException

class DagController:
	def __init__(self, is_interactive):
		self.is_interactive = is_interactive

	def reload(self, text = "") -> NoReturn:
		# _reload and reload are separate so that "self.reload()" doesn't have to be run through a dagcmd
		if not dag.settings.skip_blank_line_reloads:
			raise DagReloadException(text)

	def process_dagcmd_response_for_cli(self, icresponse, icexecutor):
		return