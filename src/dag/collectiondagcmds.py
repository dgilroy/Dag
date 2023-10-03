import inspect, json

import dag
from dag.util import nabbers
from dag.util.argspectools import map_argspec_to_parsed

from dag import dagargs
from dag.builders import ResourcesBuilder
from dag.dagcmd_exctx import DagCmdExecutionContext
from dag.cachefiles import cachefiles
from dag.dagcmds import DagCmd, FilteredDagCmd, register_cmdsettings
from dag.dagcmdbuilders import DagCmdBuilder 
from dag.dagcmd_executors import CollectionDagCmdExecutor


#>>>> COLLECTION DAGCMD
class CollectionDagCmd(DagCmd):
	dagcmd_executor = CollectionDagCmdExecutor

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.resource_name = "resource"

		self.resources_dagarg = dagargs.CollectionResourceDagArg(self.resource_name, collectioncmd = self) # This gets inserted into incmd

		self._settings.setdefault("_cmd_type", type(self))
		self._settings.setdefault("label_ignore_chars", [])

		self._settings._resource_settings = self.resources_dagarg.settings

		self.resource_argname = ""


	@property
	def is_labelled(self):
		return self.settings.label or self.settings._resource_settings.label


	def get_cached_choices(self, incmd, parsed):
		with dag.ctx("skip_make_collection"):
			response = self.run_with_parsed(parsed)

		origparsed, parsed = parsed, map_argspec_to_parsed(self.argspec, parsed)
		exctx = DagCmdExecutionContext(self, parsed)

		folder, filename = cachefiles.get_folder_filename_from_dagcmd_exctx(exctx)
		filename = "ITEMS-" + filename

		if cachefiles.exists(folder, filename):
			return cachefiles.read(folder, filename)

		return []


	def write_cached_choices(self, response): # This is here so that it's with companion get_cached_choices. This could also go onto collection itself
		folder, filename = cachefiles.get_folder_filename_from_dagcmd_exctx(response.to_exctx)
		filename = "ITEMS-" + filename
		cachefiles.write(response.choices(), folder, filename)


	def load_aliases(self):
		from dag.dagcollections import collection

		with self.file.open(collection.ALIAS_FILENAME, "r") as file: # Have to read then write bc r+ appends file and w+ clears file before reading is possible
			aliases = json.loads(file.read() or "{}")
			return aliases


	def filter(self, *filters):
		return FilteredDagCmd(self, *filters)


	@property
	def resources(self):
		return ResourcesBuilder(self)


	@property
	def op(self, **settings):
		with dag.catch() as e:
			callframeinfo = dag.callframeinfo(inspect.currentframe())

			if not self.resource_argname:
				raise ValueError("To create an op, collection must have a defined resource_argname")

			dagCmdBuilder = OpDagCmdBuilder(self, self.root, callframeinfo, is_default_cmd = False, **settings)
			
			#resourcearg = self.arg(self.resource_argname)
			#resourcearg.process_fn(self.fn)
			#dagCmdBuilder.add_dagarg(resourcearg, argspec = True)

			dagCmdBuilder.add_dagarg(self.arg(self.resource_argname)._generate_dagarg(self.fn), argspec = True)
			return dagCmdBuilder


	# for creating an arg based on this collection
	def arg(self, *names, **settings):
		return self.root.arg(*names, _arg_type = dagargs.OpResourceDagArg, collectioncmd = self, is_collection_arg = True, **settings)


	def get_resource_dagcmds(self):
		return self.root.collectioncmds.get_resource_dagcmds(self)


	def process_incmd(self, incmd):
		super().process_incmd(incmd)

		if not self.resources_dagarg in incmd.dagargs:
			incmd.dagargs.add(self.resources_dagarg)

		incmd.dagargs.add(dagargs.CollectionResourceMethodDagArg("ResourceMethod", collectioncmd = self))
			
		return incmd


	def prompt_for_resource(self):
		# This was ported from DagMod. It was never finished.
		# This will prompt for parents to drill into this collection

		ancestors = [self]
		ancestor = self

		ancestors = ancestors.reverse()
			
		breakpoint()
#<<<< CollectionDagCmd



#>>>> CollectionBuilder
class CollectionBuilder(DagCmdBuilder, nabbers.Nabber):
	def __init__(self, *args, **settings):
		settings["_cmd_type"] = CollectionDagCmd
		super().__init__(*args, **settings)

	def add_dagcmd(self, name, settings, fn = None):
		dagcmd = super().add_dagcmd(name, settings, fn = fn)

		with dag.catch() as e:
			self.app.collectioncmds.add(name, dagcmd)

		return dagcmd

	def _nab(self):
		return dag.ctx.active_collection_dagcmd
#<<<< CollectionBuilder



#>>>> OpDagCmd
class OpDagCmd(DagCmd):
	pass
#<<<< OpDagCmd



#>>>> MultiOpDagCmd
class MultiOpDagCmd(OpDagCmd):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.opcmds = []
		self.collectioncmds = []
		self.oppairs = {}


	def process_incmd(self, incmd): # This is done because incmd copies dagargslist and this makes ResourcesDagArg turn back into ResourceDagArg (which breaks processing)
		resourcesarg = incmd.dagargs[0]
		if type(resourcesarg) is dag.dagargs.ResourceDagArg: # Done this way because we don't wan't to match subclasses
			resourcesarg = dag.dagargs.ResourcesDagArg(*resourcesarg.names, **resourcesarg.settings)
			incmd.dagargs[0] = resourcesarg

		resourcesarg.settings.collectioncmd = self.collectioncmds
		return incmd


	def add_opcmd(self, opcmd):
		collectioncmd = opcmd.settings.op_collectioncmd
		self.opcmds.append(opcmd)
		self.add_collectioncmd(collectioncmd)
		self.oppairs[collectioncmd] = opcmd


	def add_collectioncmd(self, cmd):
		resourcesarg = self.dagargs[0]

		# IF resourcearg is exactly a ResourceDagArg (and not a ResourcesDagArg/subclass): Turn the first dagarg into a ResourcesDagArg
		if type(resourcesarg) is dag.dagargs.ResourceDagArg:
			resourcesarg = dag.dagargs.ResourcesDagArg(*resourcesarg.names, **resourcesarg.settings)
			resourcesarg.settings['collectioncmd'] = [] # Blanked out so that collectioncmd order is better preserved so that bottom one is first
			self.dagargs[0] = resourcesarg

		# IF cmd is not already registered by the multiop: Add as registered collectioncmd
		if cmd not in self.collectioncmds:
			self.collectioncmds.append(cmd)

		# IF cmd is not already registered as a collectioncmd by the resourcsearg: Add it to registered collectioncmds
		if cmd not in resourcesarg.settings.collectioncmd:
			resourcesarg.settings.collectioncmd.append(cmd)


	def run_with_parsed(self, parsed, *args, **kwargs):
		resourcekey = [*parsed][0] # The name of the op resource in parsed (simply searched for the first parsed arg's name)
		resourcecollcmd = parsed[resourcekey]().collection.collectioncmd # Get the resource's collectioncmd

		# IF resource collectioncmd is not a registered collectioncmd: Complain
		if not resourcecollcmd in self.collectioncmds:
			return f"Op not defined for collection {resourcecollcmd.name}"

		return self.oppairs[resourcecollcmd].run_with_parsed(parsed)
#<<<< MultiOpDagCmd



#>>>> OpDagCmdBuilder
class OpDagCmdBuilder(DagCmdBuilder):
	def __init__(self, op_collectioncmd, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.op_collectioncmd = op_collectioncmd


	def __call__(self, arg1 = None, *names, **settings):
		newdagcmd = super().__call__(arg1, *names, **settings)
		newdagcmd.settings.op_collectioncmd = self.op_collectioncmd

		if isinstance(arg1, DagCmd):
			dagcmd = arg1

			if isinstance(dagcmd, MultiOpDagCmd):
				dagcmd.add_opcmd(newdagcmd)
				return dagcmd

			multiopdagcmd = MultiOpDagCmd(settings = dag.DotDict(), fn = dagcmd.fn, dagapp = dagcmd.dagapp, name = dagcmd.name, callframeinfo = dagcmd._callframeinfo)
			multiopdagcmd.add_opcmd(dagcmd)
			multiopdagcmd.add_opcmd(newdagcmd)

			dagcmd.dagapp.add_dagcmd(multiopdagcmd)

			return multiopdagcmd

		return newdagcmd
#<<<< OpDagCmdBuilder

register_cmdsettings("ResourceMethod", is_resource_method = True)