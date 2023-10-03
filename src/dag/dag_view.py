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
	def echo(self, *args: tuple[str]) -> str:
		"""The way the view formats/outputs text. Also returns the outputted text. Implemented by child"""
		
		raise NotImplementedError

	@abc.abstractmethod
	def print_incmd_response(self, ic_response):
		"""Outputs the contents of the ic_response"""

		raise NotImplementedError

	@abc.abstractmethod
	def pre_incmd_execute(self, incmd, parsed):
		"""prints any incmd info before its execution"""

		raise NotImplementedError



class NullDagView(DagView):
	def prompt_input(self):
		return

		
	def get_line_buffer(self):
		return


	def echo(self, *args: tuple[str]):
		return


	def print_incmd_response(self, ic_response):
		return

	def pre_incmd_execute(self, incmd, parsed):
		return
