import copy

from dag.parser.comma_list import CommaList
from dag.parser.InputCommand import InputCommand
from dag.parser.InputCommandList import InputCommandList
from dag.parser.lexer import DagLexer, WORD, Tokens

from dag.exceptions import DagContinueLoopException, DagMultipleCommaListException


DO_CONTINUE = True
DO_NOT_CONTINUE = False

class InputCommandListBuilder:
	def __init__(self):
		self.token_buffer = []
		self.space_buffer = ""
		self.comma_list = CommaList()


	def process_commalist(self, token):
		# If token is a comma: Attempt to put into comma_list
		if isinstance(token, Tokens.COMMA): 
			self.process_comma(token)
		# elif token is WORD: Maybe put it into comma_list
		elif isinstance(token, WORD):
			self.maybe_put_into_comma_list(token)


	def process_comma(self, token):
		if self.comma_list.closed:
			raise DagMultipleCommaListException("Can't have multiple Comma-Lists in a single Input Command")

		if not self.comma_list:
			last_word = self.token_buffer.pop()
			self.comma_list.append(last_word)
			self.comma_list.token_position = len(self.token_buffer)
			self.token_buffer.append(self.comma_list)

		self.comma_list.listening = True
		raise DagContinueLoopException()


	def maybe_put_into_comma_list(self, token):
		# If comma_list has been populated already: Maybe append, maybe close list
		if self.comma_list:
			# If comma list is listening for next word: Append word to comma_list, turn of listening, and continue
			if self.comma_list.listening:
				self.comma_list.append(token.value)
				self.comma_list.listening = False
				raise DagContinueLoopException()
			# Else, comma list isn't listening for next word: indicate comma list is finished
			else:
				self.comma_list.closed = True



	def process_space(self, token):
		if isinstance(token, Tokens.SPACE): 
			self.space_buffer += " "

			raise DagContinueLoopException()




	def build_incmds_from_tokens(self, tokens):
		tokens = iter(tokens)

		incmd_list = InputCommandList()

		while token := next((t for t in tokens if isinstance(t, WORD)), None):
			self.token_buffer = [token.value]
			self.space_buffer = ""

			while (token := next(tokens, None)) and isinstance(token, (WORD, Tokens.COMMA, Tokens.SPACE)):
				try:
					self.process_space(token)
					self.process_commalist(token)

				except DagContinueLoopException:
					continue

				self.token_buffer.append(token.value)
				self.space_buffer = ""

			# If space after last word, append empty string to indicate new empty arg
			if self.space_buffer:
				self.token_buffer += [""]


			tokenbuffers = []
			# If comma_list has been filled, process it
			if self.comma_list:
				if self.comma_list.listening:
					self.comma_list.append("")

				for citem in self.comma_list:
					tbuff = copy.deepcopy(self.token_buffer)
					tbuff[self.comma_list.token_position] = citem
					tokenbuffers.append(tbuff)
		

			tokenbuffers = tokenbuffers or [self.token_buffer]

			for tokenbuffer in tokenbuffers:
				ic = InputCommand(tokenbuffer, token or None, incmd_list = incmd_list)

				# space_suffix is used by completer to keep track of what should be completed
				ic.space_suffix = self.space_buffer

				incmd_list.append(ic)

		return incmd_list