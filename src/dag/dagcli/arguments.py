class CliArgument:
	def parse_name(self):
		pass

	def process_preparsed_cmd(self):
		pass

	def process_parsed_cmd(self):
		pass

	def process_cli_response(self):
		pass






class ArgToken(str):
	pass



class CliArgumentParserController:
	def __init__(self, incmd):
		self.incmd = incmd

	def parse(self):
		from dag.parser import DagDirective # This is currently causing circular import when outside this fn

		dagcmd = self.incmd.dagcmd

		for token in self.incmd.argtokens:

			breakpoint()
			pass




class CliArgumentParser:
	def __init__(self, incmd):
		self.incmd = incmd
		self.parser = CliArgumentParserController(self.incmd)

	def run(self):
		self.parser.parse()