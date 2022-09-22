import collections

from dag.parser.lexer import Tokens


class InputCommandList(collections.UserList):
	def __init__(self):
		super().__init__()
		self.incmds = self.data

		# Used by Command Executor to determine which incmd to run next
		self.active_exception = False
		self.last_response = None		

		# Filled out by calling InputScript
		self.inscript = None


	def __getitem__(self, idx):	return self.incmds[idx]
	def __setitem__(self, idx, data): self.incmds[idx] = data
	def __delitem__(self, idx):	del self.incmds[idx]
	def __len__(self): return len(self.incmds)
	def insert(self, idx, data): self.incmds.insert(idx, data)

	def __repr__(self): return f"InputCommandList \n {self.incmds}"


	def yield_incmds(self):
		#breakpoint()
		# Reset variables used for choosing how to run next comand in incmds_list
		self.active_exception = None
		self.last_response = None		

		# Run each InCmd and choose how to segue into next InCmd
		for incmd in self.incmds:
			op = incmd.op
			if op == Tokens.SEMICOLON:
				if self.active_exception:
					raise self.active_exception
				self.active_exception = None
			elif op == Tokens.AND_IF and self.active_exception:
				continue
			elif op == Tokens.OR_IF and not self.active_exception:
				continue
			elif op == Tokens.PIPE:
				breakpoint()
				line += f" {self.last_response}"
		
			self.active_exception = None
			yield incmd
