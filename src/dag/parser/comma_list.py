import collections

import dag

class CommaList(collections.UserList):
	def __init__(self):
		super().__init__()
		self.token_position = None
		self.listening = False
		self.closed = False

	def __repr__(self): return dag.format(f"<c b u>CommaList: <c #EE>{self.data}</c>")