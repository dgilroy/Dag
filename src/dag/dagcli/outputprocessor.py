import abc

class OutputProcessor(abc.ABC):

	@abc.abstractmethod
	def process_output(self, output):
		raise NotImplementedError


class OutputFilt(OutputProcessor):
	def process_output(self, output):
		pass


class OutputDriller(OutputProcessor):
	def process_output(self, output):
		pass