import dag


class TOKEN:
	value: str = ""
	startpos: int = -1

	def __repr__(self): return f"<{self.__class__.__name__}>"

	def split(self, punct: str): # Implement so that it maintains groupings
		return token_split(self.value, punct)

	@property
	def is_quoted(self): # Only checks that first char is a quote, because this might be an open quotation (aka not yet finished)
		return self.value and self.value[0] in dag.strtools.QUOTEMARKS


class WORD(TOKEN):
	def __init__(self, value): self.value = value
	def __repr__(self): return f"<{self.__class__.__name__}: {self.value} >"


def is_pipe(token) -> bool:
	return token in [Token.PIPE, Token.DOTGT, Token.GTDOT, Token.ATPIPE]


# List that holds the text value of tokens defined in Token Enum
tokentypes = {}
Token = dag.enum.Token(AND_IF = "&&", OR_IF = "||", PIPE = "|", SEMICOLON = ";", COMMA = ",", DOTGT = ".>", GTDOT = ">.", ATPIPE = '@|', DOUBLE_SEMICOLON = ";;")

for token in Token:
	tokentypes[token.value] = token
	#globals()[token.name] = token # This is necessary to make multiprocess pickling work
