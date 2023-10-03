import dag
from dag.idxlists import IdxList


ALIST_REGEX = r"_|(?:-*\d+)"
ALISTS_RSLASH = f"r/{ALIST_REGEX}/"



class Alist(IdxList):
	ic_response = None
	collection_dagcmd = None
	formatted_response = ""
	dagmod = None
	formatter = ""
	name = ""
	current_id = ""
	parsed = {}

	stored_responses = {}
	
	
	def set(self, ic_response):
		incmd = ic_response.incmd

		with dag.dtprofiler(f"{incmd.dagcmd.cmdpath()}-alist-set"):
			response = ic_response.raw_response

			try:
				collection_dagcmd = ic_response.raw_response.collectioncmd or self.incmd.dagcmd
			except AttributeError:
				collection_dagcmd = incmd.dagcmd

			self.formatted_response = ic_response.formatted_response or response

			if self.data is not response:
				self.incmd = incmd
				self.ic_response = ic_response
				self.stored_responses[incmd.dagcmd.cmdpath().split(".")[0]] = (self.ic_response, self.incmd)
				self.data = dag.listify(response) # Listify, because previously 1-resource collections weren't treated as a sequence
				self.current_id = ""
				
			if self.collection_dagcmd is not collection_dagcmd:
				self.set_collectioncmd(collection_dagcmd)


	def set_collectioncmd(self, collectioncmd):
		self.collection_dagcmd = collectioncmd
		self.name = collectioncmd.name
		self.current_id = ""

		self.set_alist_commands(collectioncmd)


	def set_alist_commands(self, collectioncmd):
		dag.defaultapp.dagcmds.maybe_register_child("alist_dagcmds").clear()
		alist_dagcmds = collectioncmd.dagapp.collectioncmds.get_resource_dagcmds(self.collection_dagcmd)

		for dagcmd in alist_dagcmds:
			if dagcmd.name in dag.defaultapp.dagcmds.names():
				continue
			
			dag.defaultapp.dagcmds.children.alist_dagcmds.add(dagcmd)


	@property
	def stored_dagcmd_names(self):
		return self.stored_responses.keys()
		return {k.split(".")[0]: r for k, r in self.stored_responses.items()}


	def restore_from(self, key):
		self.set(*self.stored_responses[key])

			
	def __getitem__(self, idx):
		if idx == "_":
			if self.current_id != "":
				idx = self.current_id
			else:
				return "<c b>ALIST ERROR:</c> Alist has no current index"
		try:
			response = super().__getitem__(idx)
			self.current_id = idx
			return response
		except TypeError:
			return "<c b>ALIST ERROR:</c> Alist not yet generated"

	def __str__(self):
		return str(self.collection_dagcmd) #So that just the Alist can be returned and still get shown properly in console


def isidx(text):
	return dag.strtools.isint(text) or text == "_"




@dag.arg("item", complete = dag.nab.instance.controller.alist.stored_dagcmd_names)
@dag.cmd
def alist(item = None):
	alist = dag.instance.controller.alist

	if item and item in {k.split(".")[0] for k in alist.stored_responses.keys()}:
		alist.restore_from(item)
		return alist.formatted_response

	if item:
		dag.settings.noformat = True
		if dag.strtools.isint(item):
			return alist[int(item)]

	return alist


@dag.arg.Resource("idx", collectioncmd = dag.nab.instance.controller.alist.collection_dagcmd)
@dag.cmd(ALISTS_RSLASH, display = None)
def alist_item(idx):
	return idx

@dag.cmd("_")
def current_list_item():
	return dag.instance.controller.alist["_"]


@alist.display
def display_alist(alist, formatter):
	if isinstance(alist, str):
		return alist
		
	return alist.formatted_response or alist
