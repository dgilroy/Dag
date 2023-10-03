import dag

from dag.parser import Token, WORD
from dag.parser.lexer import DagLexer
from dag.parser.incmdlistbuilder import InputCommandListBuilder
from dag.parser.incmds import InputCommand


class InputScript:
	def __init__(self, tokens):
		from dag.parser.inputexecutors import InputScriptExecutor
		
		self.incmd_lists = []
		self.tokens = tokens
		self.executor = InputScriptExecutor(self)


	def __repr__(self): return f"InputScript \n {self.incmd_lists}"


	def execute(self):
		return self.executor.execute()


	# Might eventually have logic to split different inputcommandlines (eg on non-string newline, if running from a file)
	def build_incmdlists(self):
		self.incmd_lists = []
		
		tokens = iter(self.tokens)

		incmd_list = InputCommandListBuilder().build_incmds_from_tokens(tokens)

		incmd_list.inscript = self

		self.incmd_lists.append(incmd_list)

		return self


	# Could be used in the future if there's logic controlling which list to use next
	def yield_incmdlists(self):
		self.build_incmdlists()

		for incmd_list in self.incmd_lists:
			yield incmd_list


	# Run this if you just want the next incmd without the list
	def yield_incmds(self):
		for incmd_list in self.yield_incmdlists():
			yield from incmd_list.yield_incmds()


	def get_last_incmd(self):
		incmd = None

		for ic in self.yield_incmds():
			incmd = ic

		return incmd or InputCommand([""])
		
		#*_, incmd = self.yield_incmds() -> This failed when text was empty


def generate_from_text(line = "", strip_trailing_spaces = False):
	if strip_trailing_spaces:
		line = line.strip()

	daglexer = DagLexer()
	tokens = daglexer.lex(line)

	inputscript = InputScript(tokens)
	inputscript.build_incmdlists()

	return inputscript



def yield_incmds_from_text(line = ""):
	inscript = generate_from_text(line)
	yield from inscript.yield_incmds()




def test_line(line = ""):
	text = ""
	text = "test multiarg eef wow moo\ cow banana eek eek eek"

	response = [incmd.initialize() for incmd in yield_incmds_from_text(line or text)]

	print(response)
	ic = response[-1]
	breakpoint()
	dag.echo(f"\n<c yellow b>{text}</c>")

	#return response






def test_argument_parser(line = ""):
	from dag.dagcli.arguments import CliArgumentParser

	line = line or "nhl teams ##venue.city Seattle"

	response = [CliArgumentParser(incmd).run() for incmd in yield_incmds_from_text(line)]

	print(response)
	breakpoint(response)
	pass