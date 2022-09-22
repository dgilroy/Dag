from dag.exceptions import DagContinueLoopException

class Token:
	value: str = ""
	def __repr__(self): return f"<{self.__class__.__name__}>"


class WORD(Token):
	def __init__(self, value): self.value = value
	def __repr__(self): return f"<{self.__class__.__name__} {self.value}>"


# List that holds the text value of tokens defined in Tokens
tokentypes = {}

def create_token_type(name, value):
	tokentype = type(name, (Token,), {"value": value})
	tokentypes[value] = tokentype
	globals()[name] = tokentype # This is necessary to make multiprocess pickling work
	return tokentype

class Tokens:
	AND_IF = create_token_type("AND_IF", "&&")
	OR_IF = create_token_type("OR_IF", "||")
	PIPE = create_token_type("PIPE", "|")
	SEMICOLON = create_token_type("SEMICOLON", ";")
	COMMA = create_token_type("COMMA", ",")
	SPACE = create_token_type("SPACE", " ")
	#UNDERSCORE = create_token_type("UNDERSCORE", "_") -> Setting this as a token means "l _" won't work beacuse "_" is considered the op




class DagLexer:
	def __init__(self, strip_trailing_spaces = False):
		self.punctuation_chars = [";", ","]  # Chars that dont need spaces before them to become tokens
		self.quote_chars = ['"', "'"]
		self.container_chars = {"(": ")", "{": "}"}

		self.strip_trailing_spaces = strip_trailing_spaces

		self.arglist_active = False
		self.reset()


	def reset(self):
		self.tokens = []
		self.buffer = ""
		self.escape_char_active = False
		self.active_quote = ""
		self.active_container = ""
		

	def add_token(self, text):
		if text in tokentypes:
			self.tokens.append(tokentypes[text]())
		else:
			self.tokens.append(WORD(text))


	def handle_escape_char_active(self):
		self.escape_char_active = False

	def handle_escape_slash(self):
		self.escape_char_active = True

	def handle_open_grouping(self):
		pass

	def handle_space(self):
		if self.buffer:
			self.add_token(self.buffer)

			if not self.strip_trailing_spaces:
				self.add_token(" ")

			self.buffer = ""

	def handle_punctuation(self, c):
		if self.buffer:	# In case there are multipe punct marks in a row
			self.add_token(self.buffer)
			self.buffer = ""
		self.add_token(c)

	def handle_quotechar(self, c):
		if self.active_quote:
			self.active_quote = ""
			if self.buffer:
				self.add_token(self.buffer + c)
				self.buffer = ""
				raise DagContinueLoopException()
		else:
			self.active_quote = c

	def handle_containerchar(self, c):
		if self.active_container:
			self.active_container = ""
			if self.buffer:
				self.add_token(self.buffer + c)
				self.buffer = ""
				raise DagContinueLoopException()
				return True
		else:
			self.active_container = self.container_chars[c]


	def lex(self, text):
		self.reset()

		for c in text:
			skip = False

			try:
				if self.escape_char_active:
					self.handle_escape_char_active()
				elif c == "\\": # note: does not push the \ into buffer, but if there's \\, the 2nd will get put into buffer
					self.handle_escape_slash()
				elif (self.active_quote and c != self.active_quote) or (self.active_container and c != self.active_container):
					self.handle_open_grouping()
				elif c == " ":
					self.handle_space()
					continue
				elif c in self.punctuation_chars:
					self.handle_punctuation(c)
					continue
				elif c in self.quote_chars:
					self.handle_quotechar(c)
				elif c in self.container_chars or c == self.active_container:
					self.handle_containerchar(c)
			except DagContinueLoopException:
				continue


			self.buffer += c

		if self.buffer:
			self.add_token(self.buffer)

		return self.tokens
