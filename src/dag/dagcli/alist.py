from collections.abc import Sequence

import dag

class _Alist(Sequence):
	ic_response = None
	response = []
	collection_dagcmd = None
	formatted_response = ""
	dagmod = None
	formatter = ""
	name = ""
	current_id = ""
	parsed = {}

	stored_responses = {}
	
	
	def set(self, ic_response):
		response = ic_response.raw_response
		collection_dagcmd = ic_response.incmd.dagcmd
		formatted_response = ic_response.formatted_response

		if self.response is not response:
			self.stored_responses[ic_response.incmd.dagcmd.cmdpath()] = ic_response
			self.ic_response = ic_response
			self.response = response
			self.formatted_response = formatted_response or response
			self.current_id = ""
			
		if self.collection_dagcmd is not collection_dagcmd:
			self.collection_dagcmd = collection_dagcmd
			self.name = collection_dagcmd.fn_name
			self.current_id = ""

			self.set_alist_commands(ic_response)

			
	def set_alist_commands(self, ic_response):
		dag.default_dagcmd.subcmdtable.maybe_register_child("alist_dagcmds").clear()

		arglist_dagcmds = ic_response.incmd.dagcmd.dagmod.collections.get_resource_dagcmds(self.collection_dagcmd)

		for dagcmd in arglist_dagcmds:			
			if dagcmd.name in dag.default_dagcmd.subcmdtable.names():
				continue
			
			dag.default_dagcmd.subcmdtable.children.alist_dagcmds.add(dagcmd)






	def restore_from(self, key):
		self.set(self.stored_responses[key])

			
	def __getitem__(self, idx):
		if idx == "_":
			if self.current_id:
				idx = self.current_id
			else:
				return "<c b>ALIST ERROR:</c> Alist has no current index"
		try:
			response = self.response[int(idx)]
		except TypeError:
			return "<c b>ALIST ERROR:</c> Alist not yet generated"
		except IndexError as e:
			breakpoint()
			return "<c b>ALIST ERROR:</c> Index not in Alist"
			
		self.current_id = idx
		return response


	def __len__(self):
		return len(self.response)


	def __str__(self):
		return str(self.collection_dagcmd) #So that just the Alist can be returned and still get shown properly in console
		
		
		
		
		
Alist = _Alist()