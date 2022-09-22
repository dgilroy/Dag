import abc

class DagView(abc.ABC):
	@abc.abstractmethod
	def prompt_input(self):
		"""The function that calls for user input. Implemented by child"""

		raise NotImplementedError


	@abc.abstractmethod
	def get_line_buffer(self):
		"""The way the view sends its inputted text. Implemented by child"""

		raise NotImplementedError


	@abc.abstractmethod
	def echo(self, text: str) -> str:
		"""The way the view formats/outputs text. Also returns the outputted text. Implemented by child"""
		
		raise NotImplementedError