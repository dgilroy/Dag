from collections.abc import Sequence
from collections import UserList

import dag

class IdxList(UserList):
	def __getitem__(self, idx):
		match idx:
			case str():
				idx = dag.strtools.strtoint(idx)
			case float():
				idx = int(idx)
				
		return self.data[idx]