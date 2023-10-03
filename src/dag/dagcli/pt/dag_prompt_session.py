from functools import partial

from prompt_toolkit import PromptSession
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document

import dag



def modified_go_to_completion(self, index: int | None) -> None:
	# If completing and only one completion: Select that completion and disable completions menu
	Buffer.go_to_completion(self, index)

	if len(self.complete_state.completions) == 1:
		self.complete_state = None
		self.text = self.text.rstrip(" ") + " "




class DagPromptSession(PromptSession):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.default_buffer.go_to_completion = partial(modified_go_to_completion, self.default_buffer)