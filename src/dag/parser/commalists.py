import collections

import dag
from dag.exceptions import DagMultipleCommaListException


def expand_commalist(tokens):
	commalists = [t for t in tokens if isinstance(t, CommaList)]

	if len(commalists) > 1:
		raise DagMultipleCommaListException("Can't have multiple Comma-Lists in a single Input Command")
	elif len(commalists) == 1:
		coml = commalists[0]
		clidx = tokens.index(coml)

		tokenlists = []

		for token in coml:
			newtokens = [*tokens]
			newtokens[clidx] = token
			tokenlists.append(newtokens)

		return tokenlists

	else:
		return [tokens]


class CommaList(collections.UserList):
	def __init__(self):
		super().__init__()
		self.listening = False
		self.closed = False

	def __repr__(self): return dag.format(f"<c b u>CommaList: <c #EE>{self.data}</c>")