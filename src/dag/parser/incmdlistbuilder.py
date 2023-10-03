import copy

import dag
from dag.parser import Token, WORD
from dag.parser.commalists import CommaList
from dag.parser.incmds import InputCommandBuilder
from dag.parser.incmdlists import InputCommandList
from dag.parser.lexer import DagLexer

from dag.exceptions import DagContinueLoopException, DagMultipleCommaListException


class InputCommandListBuilder:
	def __init__(self):
		self.token_buffer = []
		self.comma_list = CommaList()


	def process_commalist(self, token):
		match token:
			# If token is a comma: Attempt to put into comma_list
			case Token.COMMA:
				self.process_comma(token)
			# elif token is WORD: Maybe put it into comma_list
			case WORD():
				self.maybe_put_into_comma_list(token)


	def process_comma(self, token):
		if self.comma_list.closed:
			raise DagMultipleCommaListException("Can't have multiple Comma-Lists in a single Input Command")

		if not self.comma_list:
			last_word = self.token_buffer.pop()
			self.comma_list.append(last_word)
			self.token_buffer.append(self.comma_list)

		self.comma_list.listening = True
		raise DagContinueLoopException()


	def maybe_put_into_comma_list(self, token):
		# If comma_list has been populated already: Maybe append, maybe close list
		if self.comma_list and not self.comma_list.closed:
			# If comma list is listening for next word: Append word to comma_list, turn of listening, and continue
			if self.comma_list.listening:
				self.comma_list.append(token.value)
				self.comma_list.listening = False
				raise DagContinueLoopException()
			# Else, comma list isn't listening for next word: indicate comma list is finished
			else:
				self.comma_list.closed = True


	def build_incmds_from_tokens(self, tokens):
		tokens = iter(tokens)

		incmdlist = InputCommandList()

		while token := next((t for t in tokens if isinstance(t, WORD)), None):
			self.token_buffer = [token.value]

			while (token := next(tokens, None)) and (isinstance(token, WORD) or token in [Token.COMMA]):
				try:
					self.process_commalist(token)

				except DagContinueLoopException:
					continue

				self.token_buffer.append(token.value)

			incmdlist.incmdbuilders.append(InputCommandBuilder(self.token_buffer, token, incmdlist = incmdlist))
			# Reset commalist for next incmd
			
			self.comma_list = CommaList()

		if not incmdlist:
			incmdlist.append(InputCommandBuilder([""], ";", incmdlist = incmdlist))

		return incmdlist