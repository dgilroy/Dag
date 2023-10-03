from __future__ import annotations

import copy, functools
from collections import namedtuple
from collections.abc import Mapping, MutableMapping

import dag
from dag import dagargs
from dag.lib import ctxmanagers
from dag.util import hooks
from dag.builders import DisplayBuilder
from dag.identifiertables import IdentifierTable
from dag.dagcmdbuilders import DagCmdBuilderGenerator



class Identifier(DagCmdBuilderGenerator, dag.mixins.DagLaunchable, dag.mixins.CLIInputtable, dag.mixins.DagSettings):
	"""
	Anything identifiable will contain a table allowing for further searches
	"""

	name: str = ""

	def __init__(self, callframeinfo: tuple[str, int, str] | None, settings: Mapping = None):
		self._callframeinfo = callframeinfo
		self._settings = dag.util.nabbers.NabbableSettings(settings or {})
		self._identifier_settings = self._settings

		self.dagcmds = IdentifierTable(self)
		self._parent_dagcmd = None
		self._display_settings = dag.nabbers.NabbableSettings()
		self._display_builder = DisplayBuilder(self)

		self.collectioncmds = IdentifierCollectionCmds(self)

		self.is_regexcmd = False # Will be set to True by appropriate dagcmds

		self.ctx = ctxmanagers.Context()

		self.hooks = hooks.HooksAPI(parentsettings = self._settings)
		self.hook = self.hooks.hookbuilder




	@property
	def settings(self):
		return self._settings


	def _dag_get_settings(self):
		# Done this way so that a "settings" dagcmd doesn't make the underlying settings inaccessible
		return self._identifier_settings


	@settings.setter
	def settings(self, settings):
		self._settings = settings


	def run_with_parsed(self, *args, **kwargs):
		return f"{self.name} is a {type(self).__name__}, not a dagcmd"


	def _dag_launch_item(self):
		return self.settings.launch


	@property
	def display_settings(self):
		return self._display_settings or getattr(self.settings.display, "display_settings", dag.nabbers.NabbableSettings())


	def get_dagcmd(self, cmdname):
		if cmdname in self.dagcmds:
			return self.dagcmds[cmdname]

		if self.dagcmds.regexcmds:
			regexcmds = {k: self.dagcmds.regexcmds[k] for k in sorted([float(p) for p in self.dagcmds.regexcmds], reverse = True)}

			for priority, regexcmdlist in regexcmds.items():
				for regexcmd in regexcmdlist:
					if dag.rslashes.fullmatch_rslash(cmdname, regexcmd.name):
						return regexcmd

		raise ValueError(f"{cmdname} not found in {self.name}.dagcmds")
		pass


	def get_dagcmd_names(self):
		return self.dagcmds.names()


	def has_dagcmd(self, cmdname):
		return cmdname in self.get_dagcmd_names()


	@property
	def parents(self):
		parents = [self._parent_dagcmd]

		while hasattr(parents[-1], "_parent_dagcmd") and parents[-1]._parent_dagcmd:
			parent = parents[-1]._parent_dagcmd

			if parent == dag.defaultapp:
				break

			parents.append(parent)

		return [*filter(None, parents)]


	@property
	def parentnames(self):
		return [p.name for p in self.parents]


	@functools.cached_property
	def file(self):
		return dag.FileManager(root = dag.directories.DATA / self.cmdpath("/"))


	@functools.cached_property
	def cachefile(self):
		return dag.FileManager(root = dag.directories.CACHE / self.cmdpath("/"))


	def cmdpath(self, separator = ".", until = 0):
		parents = [self] + self.parents

		path = ""

		if until:
			parents = parents[abs(until):]

		for parent in parents:
			if parent == dag.defaultapp:
				break

			path = parent.name + separator + path

		return path.rstrip(separator)


	@property
	def auth(self):
		return AuthManager(self)


	@property
	def nab(self):
		return dag.nabbers.SimpleNabber(self)


	def names(self):
		name = dag.listify(self.name, list)
		aka = dag.listify(self.settings.aka, list) if self.settings.aka else []
		return name + aka



class AuthManager:
	def __init__(self, identifier):
		self.identifier = identifier

	def token(self, fn):
		self.identifier.settings.auth.raw_token = fn
		return fn



#>>>> Identifier CollectionCmds
class IdentifierCollectionCmds:
	def __init__(self, owner):
		self.owner = owner
		self.collectioncmds = {}


	def add(self, name, collection):
		self.collectioncmds[name] = collection


	def __bool__(self):
		return bool(self.collectioncmds)

	
	def get_resource_dagcmds(self, collection_dagcmd):
		resource_dagcmds = []

		with dag.ctx(active_collection_dagcmd = collection_dagcmd, is_getting_resource_methods = True):
			for dagcmd in self.owner.dagcmds.values():
				if dagcmd.settings.is_resource_method:
					resource_dagcmds.append(dagcmd)
					continue

				if dagcmd.dagargs.positionalargs:
					try:
						candidate_dagarg = dagcmd.dagargs.positionalargs[0]

						if not isinstance(candidate_dagarg, dagargs.ResourceDagArg):
							continue
							
						collectioncmds = getattr(candidate_dagarg, "collectioncmds", [])

						if not collectioncmds:
							continue

						#if (collection_dagcmd in collections or collections[0] is None) and not isinstance(candidate_dagarg, CollectionResourceDagArg):
						if (collection_dagcmd in collectioncmds) and not isinstance(candidate_dagarg, dagargs.CollectionResourceDagArg):
							resource_dagcmds.append(dagcmd)
					except (AttributeError, IndexError) as e:
						breakpoint(dagcmd.name == "pause")
						continue

		return resource_dagcmds


	def get_collection_names(self):
		return [*self.collectioncmds.keys()]


	# Used by Help Formater
	def get_collections(self):
		return [*self.collectioncmds.items()]


	def update_collections(self):
		for coll in self.collectioncmds.values():
			if coll.settings.cache:
				coll.update()


	def __call__(self):
		return self.get_collection_names()
#<<<< Identifier CollectionCmds
