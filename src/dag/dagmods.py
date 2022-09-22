import copy

import dag
from dag.util.nabbers import this, NabbableSettings

from dag.decorators import arg, cmd

from dag import dagcmds
from dag.dagargs import CollectionResourceArg
from dag.identifiers import DagCmdBase
from dag.dagcmds import DagCmd



with dag.ctx(IS_IMPORTING_DAGMOD = True):
	# Base class for dag modules, which handles i/o for various tools
	class DagMod(DagCmdBase):
		def __init__(self):
			#self._parent_dagcmd = dag.ctx.active_dagcmd -> Was making the active_dagcmd pickled, which isn't useful
			self._parent_dagcmd = None
			super().__init__() # outside ctx change so it can set _parent_dagcmd (for a dagmod, likely to be default_dagcmd)

			with dag.ctx(active_dagcmd = self):
				self.dagmod = self # Used for identifiers

				# Initialization
				self.initialize()
				self._init() # Hook for subclasses
				self.dagmod_settings = copy.copy(self.settings)

				self.settings.setdefault("default_cmd", self._get_resource) # Needs to be here for dagmod_settings

				# Manage dagcmds
				self.subcmdtable.register_child("dagcmds").populate(self.registered_dagcmds)


				self.collections = DagModCollections(self)


				# DagCmd stuff
				self.dagargs = getattr(self.settings.default_cmd, "dagargs", {})
				self.name = self.settings.dagmod_name


		# Can be overridden by subclasses so it doesn't have to bother with __init__
		def _init(self):
			pass


		def initialize(self, *args):
			with dag.ctx(initializing_dagmod = True):
				# Sets defaults
				self.settings = NabbableSettings(getattr(self, "settings", {}).copy())
				self.name = self.settings.dagmod_name
				self.settings.setdefault("baseurl", "")
				self.settings.setdefault("help", "")
				self.settings.setdefault("dateformat", "%Y-%m-%d")
				self.settings.setdefault("enable_tempcache", True)
				self.settings._dag_thisref = self

				dag.hooks.do("post_dagmod_setup")


		def __repr__(self):
			return f"{super().__repr__()} -> {self.name}"		



		def __call__(self, *args, **kwargs):
			with dag.ctx(active_dagcmd = self):
				return self.settings.default_cmd(*args, **kwargs)


		def _get_subcmd(self, subcmdname, subcmdtable_val):
			return getattr(self, subcmdtable_val)


		@dag.cmd.Parent()
		def _get_resource(self, *args, **kwargs):
			"""The thought here is that this will search all labelled, cached no-arg collections to see if they contain a given arg"""
			breakpoint()
			pass

			
				

		@dag.cmd.Parent()
		def documentation(self):
			if self.settings.doc:
				return dag.launch(self.settings.doc)

			return f"No documentation found for dagmod: <c u b>{self.name}</c>"


		@dag.arg("setting", choices = this.settings.keys())
		@dag.cmd.Parent("@", value = this.settings.get(dag.arg("setting")))
		def __settings(self, setting):
			return


		@dag.cmd.Parent(value = this.collections.update_collections())
		def update_collections(self):
			pass


		@dag.arg("url")
		@dag.cmd.Parent("get", "head")
		def _call_api(self, url = ""):
			"""Do a HTTP GET request with module's base URL"""
			return getattr(dag, f"{dag.ctx.active_dagcmd.name}")(url)


		@dag.arg("url")
		@dag.cmd.Parent()
		def get_raw(self, url = ""):
			"""Do a raw HTTP GET request with module's base URL"""
			response = dag.get.RAW(url)
			breakpoint()
			return response


		@dag.arg("url")
		@dag.cmd.Parent()
		def get_collection(self, url = ""):
			"""Do a HTTP GET request and return a collection"""
			response = dag.get(url)
			return response.to_collection()

			
		@dag.cmd.Parent("breakpoint", "bb")
		def breakpoint(self):
			"""Set a breakpoint inside module"""
			breakpoint()


		@dag.cmd.Parent("collectionnames", value = this.collections.get_collection_names())
		def collectionnames(self):
			pass

			

	class DagModCollections:
		def __init__(self, dagmod):
			self.dagmod = dagmod

		
		def get_resource_dagcmds(self, collection_dagcmd):
			resource_dagcmds = []

			for dagcmd in self.dagmod.subcmdtable.values():
				if dagcmd.dagargs:
					try:
						candidate_dagarg = dagcmd.dagargs[0]
						collections = getattr(candidate_dagarg, "collection_cmds", [])

						if not collections:
							continue

						if (collection_dagcmd in collections or collections[0] is None) and not isinstance(candidate_dagarg, CollectionResourceArg):
							resource_dagcmds.append(dagcmd)
					except (AttributeError, IndexError):
						continue

			return resource_dagcmds



		def get_collection_names(self):
			return [name for name, val in self.dagmod.subcmdtable.items() if val.get('_cmd_type') and issubclass(val.get('_cmd_type'), dagcmds.CollectionDagCmd)]



		# Used by Help Formater
		def get_collections(self):
			collection_names = self.get_collection_names()
			return [getattr(self.dagmod, name) for name in collection_names]



		def update_collections(self):
			collections = self.get_collections()
			for coll in collections:
				if coll.settings.cache:
					coll.update()


		def __call__(self):
			return self.get_collection_names()
