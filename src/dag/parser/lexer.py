import re
from typing import NoReturn

import dag
from dag.exceptions import DagContinueLoopException, DagMultipleCommaListException
from dag.parser import commalists, Token, WORD, tokentypes



def token_split(text, punct, groupings = None):
	with dag.bbtrigger("tokensplit"):
		dl = DagLexer(wordseparators = [punct], groupings = groupings)
		tokens = dl.lex(text)
		if tokens and tokens[-1].value == punct:
			tokens.append(WORD(""))
		return [t.value for t in tokens if not t.value == punct]
		return tokens


def is_pipe(token) -> bool:
	return token in [Token.PIPE, Token.ATPIPE]




class DagLexer:
	def __init__(self, wordseparators = None, groupings = None, ignore = None):
		self.wordseparators = wordseparators or [";", ";;", ",", " ", "|", ">", ">>", "@|", "||", "&&"]  # Chars that dont need spaces before them to become tokens
		self.groupings = groupings or {"(": ")", "{": "}", "r/": "/", '"': '"', "'": "'", "[": "]"}
		self.ignore = ignore or [">="] # preventing ">=" from being split into "> ="

		self.openpunctuation = (self.wordseparators + self.ignore) | self.groupings.keys()

		self.reset()


	def reset(self):
		self.tokens = []
		self.buffer = ""
		self.escape_char_active = False

		self.active_punctuation = ""
		self.active_grouping = ""
		self.active_grouping_count = 0
		

	def add_token(self, text):
		text = text.strip()

		if not text:
			return

		if text in tokentypes:
			self.tokens.append(tokentypes[text])
		else:
			self.tokens.append(WORD(text))


	def process_punctuation(self):
		def get_candidates(punctuation):
			nonlocal trimmedbuffer, ch

			candidates = [p for p in initial_candidates if p.startswith(punctuation)]

			if candidates:
				return candidates
			else:
				if self.active_punctuation:
					sorted_candidates = sorted([p for p in initial_candidates if p.startswith(self.active_punctuation)], key = lambda x: len(x))
					trimmedbuffer = self.buffer[:-1]

					for candidate in sorted_candidates:
						if dag.strtools.text_ends_with_punctuation(trimmedbuffer, candidate):
							candidates = [candidate]

					if candidates:
						ch = ""
						return candidates

					self.active_punctuation = ""
					return get_candidates(ch)

			return []


		if not self.buffer:
			return

		ch = self.buffer[-1]

		initial_candidates = self.openpunctuation

		if self.active_grouping:
			initial_candidates = list(set([self.groupings[self.active_grouping], self.active_grouping]))

		trimmedbuffer = self.buffer

		candidates = get_candidates(self.active_punctuation + ch)

		if candidates:
			self.active_punctuation += ch

		if len(candidates) == 1 and dag.strtools.text_ends_with_punctuation(trimmedbuffer, candidates[0]):
			self.add_punctuation_token(candidates[0], trimmedbuffer)


	def add_punctuation_token(self, punctuation, trimmedbuffer = None):
		trimmedbuffer = trimmedbuffer or self.buffer
		self.active_punctuation = "" #We've found the punctuation so turn off search

		if self.active_grouping:
			# IF punctuation closes the group: Close the group
			if punctuation == self.groupings[self.active_grouping]:
				self.active_grouping_count -= 1

				# IF not nested: Turn off active grouping
				if self.active_grouping_count == 0:
					self.active_grouping = ""
			else:
				self.active_grouping_count += 1
		else:
			if punctuation in self.wordseparators:
				if prepunctuation := trimmedbuffer[:-len(punctuation)]:
					self.add_token(prepunctuation)

				self.add_token(punctuation)
				punctidx = self.buffer.rfind(punctuation)
				punctlen = len(punctuation)
				self.buffer = self.buffer[punctidx + punctlen:]
				self.process_punctuation()

			if punctuation in self.groupings:
				self.active_grouping = punctuation
				self.active_grouping_count += 1


	def lex(self, text):
		self.reset()

		for ch in text:
			if self.escape_char_active:
				self.buffer += ch
				self.escape_char_active = False
				continue

			elif ch == "\\": # note: does not push the \ into buffer, but if there's \\, the 2nd will get put into buffer
				self.escape_char_active = True
				self.active_punctuation = ""
			elif self.active_grouping:
				pass

			self.buffer += ch
			self.process_punctuation()

		if self.buffer:
			for i in range(len(self.buffer)):
				if self.buffer[i:] in self.wordseparators:
					self.add_punctuation_token(self.buffer[i:])

		if self.buffer:
			self.add_token(self.buffer)

		# If text ends with space, append an empty word (it implies the start of a new argy)
		if text.endswith(" "):
			self.tokens.append(WORD(""))

		return PostLexer(self.tokens).process()


class PostLexer:
	def __init__(self, tokens):
		self.tokens = tokens
		self.proctokens = tokens[:]
		self.commalist = commalists.CommaList()

		self.processedtokens = [] # Token that are done being processed
		self.token_buffer = [] # Token who are still being processed


	def process_commalist(self, token: Token) -> None:
		"""
		Checks whether the token should be placed into the commalist

		:param token: The token to analyze
		:returns: Nothing
		"""

		match token:
			# If token is a comma: Attempt to put into commalist
			case Token.COMMA:
				self.process_comma(token)
			# elif token is WORD: Maybe put it into commalist
			case WORD():
				self.maybe_put_into_commalist(token)


	def process_comma(self, token: Token) -> NoReturn:
		"""

		"""
		if self.commalist.closed:
			raise DagMultipleCommaListException("Can't have multiple Comma-Lists in a single Input Command")

		if not self.commalist:
			last_word = self.processedtokens.pop()
			self.commalist.append(last_word)

		self.commalist.listening = True
		raise DagContinueLoopException()


	def maybe_put_into_commalist(self, token: Token):
		# If commalist has been populated already and hasn't been closed: Maybe append or maybe close list
		if self.commalist and not self.commalist.closed:
			# If comma list is listening for next word: Append word to commalist, turn of listening, and continue
			if self.commalist.listening:
				self.commalist.append(token)
				self.commalist.listening = False
				raise DagContinueLoopException()
			# Else, comma list isn't listening for next word: indicate comma list is finished
			else:
				self.commalist.closed = True
				self.processedtokens.append(self.commalist)
				self.processedtokens.append(token)
				raise DagContinueLoopException()



	def process(self):
		if not dag.ctx.commalist_active:
			return self.tokens

		while self.proctokens:
			try:
				token = self.proctokens.pop(0)
				self.process_commalist(token) # <- Raises Contine if word put into commalist
				self.processedtokens.append(token)
			except DagContinueLoopException:
				continue

		# If command has trailing comma (e.g.: "1,2,3,"): Add the commalist
		if self.commalist and self.commalist.listening:
			self.processedtokens.append(self.commalist)

		return self.processedtokens


@dag.oninit
def _():
	@dag.cmd
	def commalist(text = "surprise 1, 2,3,4, 5 6"):
		with dag.bbtrigger("commalist"), dag.ctx("commalist_active"):
			dag.echo(text)
			return DagLexer().lex(text)