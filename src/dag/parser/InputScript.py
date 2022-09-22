import dag

from dag.parser.lexer import DagLexer, WORD, Tokens
from dag.parser.InputCommandListBuilder import InputCommandListBuilder

class InputScript:
	def __init__(self):
		self.incmd_lists = []


	def __repr__(self): return f"InputScript \n {self.incmd_lists}"


	# Might eventually have logic to split different inputcommandlines (eg on non-string newline, if running from a file)
	def build_incmdlists_from_tokens(self, tokens):
		tokens = iter(tokens)

		incmd_list = InputCommandListBuilder().build_incmds_from_tokens(tokens)

		incmd_list.inscript = self

		self.incmd_lists.append(incmd_list)

		return self


	# Could be used in the future if there's logic controlling which list to use next
	def yield_incmd_lists(self):
		for incmd_list in self.incmd_lists:
			yield incmd_list


	# Run this if you just want the next incmd without the list
	def yield_incmds(self):
		for incmd_list in self.yield_incmd_lists():
			yield from incmd_list.yield_incmds()


	def get_last_incmd(self):
		*_, incmd = self.yield_incmds()
		return incmd


	def execute(self):
		breakpoint()
		pass


def generate_from_text(line = "", strip_trailing_spaces = False):
	if strip_trailing_spaces:
		line = line.strip()

	daglexer = DagLexer(strip_trailing_spaces = strip_trailing_spaces)
	inputscript = InputScript()

	tokens = daglexer.lex(line)
	inputscript.build_incmdlists_from_tokens(tokens)

	return inputscript



def yield_incmds_from_text(line = ""):
	inscript = generate_from_text(line)
	yield from inscript.yield_incmds()




def test_line(line = ""):
	text = ""
	#text = "true && false; echo 'I am a man with a plan; & I (a man) have | a || plan'; echo \\ \;; ls | cat; nhl games yesterday; launch (nhl =b) ; nhl teams ##id 3; item woof, 3, 4"
	#text = "test flag --flag --message I am a fly; nhl games yesterday =t && ls ; nhl =b | launch; launch (nhl =b); nhl teams.city =u ##id 1; nba teams ##teamId '=u'; echo 'woof i dog (nhl) ##filt =g';"
	#text = "nhl teams blah ##id 12 \"=u\" ##division =u"
	#text = "git commmit -am \"yeehaw i am a log\" && git push"
	#text = "mr dog ; mr dog"
	#text = "nhl > ; nba > scores.txt"
	#text = "open file\ name\  "
	#text = "pokemon moves "
	#text = "nhl --dog woof"
	text = "test multiarg eef wow moo\ cow banana eek eek eek"

	response = [incmd.initialize() for incmd in yield_incmds_from_text(line or text)]

	print(response)
	ic = response[-1]
	breakpoint()
	dag.echo(f"\n<c yellow b>{text}</c>")

	#return response






def test_argument_parser(line = ""):
	from dag.dagcli.arguments import CliArgumentParser

	text = "nhl teams ##venue.city Seattle"

	response = [CliArgumentParser(incmd).run() for incmd in yield_incmds_from_text(line or text)]

	print(response)
	breakpoint(response)
	pass