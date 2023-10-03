import abc

import dag



class OutputProcessor(abc.ABC):
	def __init__(self, incmd):
		self.incmd = incmd

	@abc.abstractmethod
	def process_output(self, ic_response):
		raise NotImplementedError



class StandardOutputProcessor(OutputProcessor):
	def process_output(self, ic_response, icexecutor):
		if not self.incmd.is_piped:
			dag.instance.view.print_incmd_response(ic_response)

		return None



def make_response_plaintext(response: str) -> str:
	response = dag.ctags.strip_ctags(response) or ""
	return dag.get_terminal().strip_escape_codes(response or "")



class ClipboardOutputProcessor(OutputProcessor):
	def __init__(self, incmd, echo: bool = True):
		super().__init__(incmd)

		self.echo = echo

	def process_output(self, ic_response, icexecutor):
		response = make_response_plaintext(ic_response.response_no_multicol or ic_response.response or "")

		dag.copy_text(response, echo = self.echo) or ""



class FileOutputProcessor(OutputProcessor):
	filemode = "w"

	def __init__(self, incmd, filename):
		super().__init__(incmd)

		self.filename = filename

	def process_output(self, ic_response, icexecutor):
		response = make_response_plaintext(ic_response.response_no_multicol or ic_response.response or "")

		with open(self.filename, self.filemode) as file:
			file.write(response + "\n")

		return ic_response.response_no_multicol or ""



class FileAppendOutputProcessor(FileOutputProcessor):
	filemode = "a"



class SilentOutputProcessor(OutputProcessor):
	def process_output(self, ic_response, icexecutor):
		return ic_response # ICExecutor checks that "not None" is returned to do stuff. hence, the silent OP returns the icresponse"