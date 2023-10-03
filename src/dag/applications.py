import inspect, sys, json
from contextlib import contextmanager

import dag
from dag import r_

from dag import applists
from dag.dagcmds import DagCmd
from dag.collectiondagcmds import CollectionDagCmd
from dag.identifiers import Identifier
from dag import dagargs
from dag.responses import ResponseParserAttrSettings


parentcmds = []


#>>>> Used by DagApp to register parent cmds
def dagcmd(*names, **settings):
	def decorated(fn):
		if names:
			for name in names:
				cmd = DagCmd(settings, fn = fn, name = name)
				parentcmds.append(cmd)
		else:
			cmd = DagCmd(settings, fn = fn)
			parentcmds.append(cmd)

		return cmd

	return decorated
#<<<< Used by DagApp to register parent cmds



#>>>> DagApp
class DagApp(Identifier, dag.DotAccess):
	def __init__(self, name: str, callframeinfo, **settings):
		with dag.dtprofiler("dagapp_init") as tp:
			Identifier.__init__(self, callframeinfo = callframeinfo, settings = settings)
			self.name = name

			self.dagapp = self
			self.root = self

			self._cmd_root = self

			self.dagargs = dagargs.DagArgsList()

			self.default_dagcmd = None
			self.applists = applists.AppListManager(self)

			self.templist = applists.TempListManager(self.applists)

			self.setup_parent_cmds()



	def extend(self, **settings):
		settings = self.settings | settings
		callframeinfo = dag.callframeinfo(inspect.currentframe())
		newapp = type(self)(self.name, callframeinfo, settings)
		return newapp


	def __repr__(self):
		main_format = "white bg-#3A0B62"
		objrepr = object.__repr__(self)

		return dag.format(f'<<c {main_format}>"{self.name}": {objrepr}</c>>')


	def token(self, fn):
		return fn


	def add_dagcmd(self, dagcmd: DagCmd, is_default_cmd: bool = False) -> DagCmd:
		with dag.ctx(adding_dagcmd = True):
			names = dag.listify(dagcmd.settings.aka, tuple) if dagcmd.settings.aka else ()
			names += (dagcmd.name,)

			for name in names:
				self.dagcmds.add(dagcmd, name)
				try:
					if name in dir(self): # Used hasattr, but it was triggering @properties
						try:
							if not isinstance(getattr(type(self), name), (dag.Identifier)): # For commands like "setting", don't override what's already there. type(self) prevents @property's from triggering
								continue
						except AttributeError:
							pass

					# If dagcmd is regexcmd: don't set as an application attributes
					if dagcmd.is_regexcmd:
						continue

					setattr(self, name, dagcmd)
				except Exception as e: # Exception happens when @property is above @dagcmd and no setter
					pass

			if is_default_cmd:
				self.default_dagcmd = dagcmd

			return dagcmd


	def __setattr__(self, name, value):
		if not dag.ctx.adding_dagcmd and isinstance(value, DagCmd):
			cmd = value
			cmd._name = name
			self.add_dagcmd(cmd)
			return

		super().__setattr__(name, value)


	@dag.arg.Flag("--collection", target = "is_collection")
	@dag.arg.Flag("--raw", target = "is_raw")
	@dagcmd(parentcmd_onlyif = r_.settings.baseurl)
	def get(self, url = "", *, is_collection = False, is_raw = False):
		'''Do a HTTP GET request with module's base URL'''
		if is_raw:
			return dag.get.RAW(url)

		response = dag.get(url)

		if is_collection and not is_raw:
			response = dag.responses.to_collection(response)

		return response


	#@dagcmd(parentcmd_onlyif = r_.collectioncmds) -> Doesn't work because when parentcmds is being loaded no collectioncmds have been registered yet
	@dagcmd()
	@property
	def collectionnames(self):
		return self.collectioncmds.get_collection_names()


	@property
	@dagcmd()
	def collectiondagcmds(self):
		return [dagcmd for dagcmd in self.dagcmds.values() if isinstance(dagcmd, CollectionDagCmd)]


	@dagcmd()
	def update_collections(self):
		return self.collectioncmds.update_collections()


	@dag.arg("setting", complete = dag.nab.ctx.active_dagcmd.root.settings)
	@dagcmd("settings", parentcmd_onlyif = r_.settings)
	def _settings(self, setting = None):
		return self.settings if not setting else self.settings.get(setting, f"Setting <c bu/ {setting}> not found in <c bu/ {self.cmdpath()}>")


	@dagcmd(is_resource_method = True, resourcemethod_onlyif = r_.settings._resource_settings.baseurl, aka = "l")
	def launch(self, item):
		return dag.launch(item)


	@dagcmd(is_resource_method = True, resourcemethod_onlyif = r_.settings._resource_settings.label)
	def alias(self, item = None, name = None, *, unset: bool = False, list: bool = False):
		if list:
			return item._dag.collection.load_aliases()

		assert item and name, "Must provide a resource and name to create an alias"

		item._dag.collection.set_alias(item, name)


	@dag.arg("item")
	@dagcmd(is_resource_method = True, resourcemethod_onlyif = r_.settings._resource_settings.label)
	def unset_alias(item):
		aliasnames = dag.ctx.active_incmd.raw_parsed.get("item") # NOTE: I tried using a raw arg but I still needed access to the collection. 
		collection = item._dag.collection

		for name in aliasnames:
			if collection.has_alias(name):
				collection.unset_alias(name)
				dag.echo(f"Alias \"<c b u>{name}</c b u>\" removed")
			else:
				dag.echo(f"Alias \"<c b u>{name}</c b u>\" is not an alias of <c bu>{collection.collectioncmd.cmdpath()}</c bu>")


	@dagcmd()
	def aliases(self):
		aliasesdict = {}

		for dagcmd in self.collectiondagcmds:
			if aliasdict := dagcmd.load_aliases():
				aliasesdict[dagcmd.name] = aliasdict

		return aliasesdict or f"No aliases found for <c bu / {self.name}>"


	@dagcmd("breakpoint", "bb")
	def do_breakpoint(self, testarg: bool = False):
		'''Set a breakpoint inside module'''
		breakpoint()
		pass


	@dagcmd(parentcmd_onlyif = r_.settings.doc)
	def documentation(self):
		if self.settings.doc:
			return dag.launch(self.settings.doc)
		
		return f"No documentation found for dagapp: <c u b>{self.name}</c>"


	#@dag.arg("setting", choices = app.nab.settings.keys())
	#def dagappsettings(self, setting):
	#	return


	def setup_parent_cmds(self):
		if dag.ctx.init_defaultapp:
			return

		for dagcmd in parentcmds:
			if "parentcmd_onlyif" in dagcmd.settings:
				if not bool(dagcmd.settings.parentcmd_onlyif(self)):
					continue

			newdagcmd = dagcmd.copy_to_app(self)
			self.add_dagcmd(newdagcmd)

#<<<< DagApp





#>>>> App Builder
class AppBuilder(ResponseParserAttrSettings):
	def __init__(self, root):
		super().__init__()
		self.root = root

	def __call__(self, name, **settings):
		callframeinfo = dag.callframeinfo(inspect.currentframe())
		app = DagApp(name, callframeinfo, **(self.settings | settings))

		# IF this is a root dagapp and appamanager is active: Register the app with the appmanager
		if self.root is dag.defaultapp and dag.ctx.active_appmanager:
			dag.ctx.active_appmanager.process_identifier(app)

		self.root.dagcmds.maybe_register_child("dagapps").add(app, name)
		return app
#<<<< App Builder


