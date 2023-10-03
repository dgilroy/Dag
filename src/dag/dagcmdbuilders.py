import inspect, functools, ast, sys
from typing import Self

import dag

from dag import dagargs
from dag.responses import ResponseParserAttrSettings



#>>>> DagCmdBuilder
class DagCmdBuilder(ResponseParserAttrSettings):
	def __init__(self, app, callframeinfo: tuple, is_default_cmd: bool = False, **settings):
		from dag.dagcmds import registered_cmdsettings

		super().__init__(**settings)

		for name, settings in registered_cmdsettings.items():
			self.set_settings_attr_dict(name, settings)

		self.app = app
		self.callframeinfo = callframeinfo

		self.names = ()
		self.is_default_cmd = is_default_cmd

		self.added_dagargs = []
		self.added_argspec_args = []


	@property
	def collection(self):
		from dag.collectiondagcmds import CollectionBuilder
		return duplicate_builder_as(self, CollectionBuilder)


	@property
	def cmd(self):
		return duplicate_builder_as(self, DagCmdBuilder)


	@property
	def DEFAULT(self) -> Self:
		self.is_default_cmd = True
		return self


	@property
	def is_oneliner(self) -> bool:
		"""
		Checks whether or not this dagcmdbuilder is a 1-liner dagcmd
		:returns: True/False indicating whether this is a 1-liner dagcmd
		"""

		# Sometimes "callframeinfo.line" is blank. Don't treat as a 1liner if so
		return self.callframeinfo.line and not self.callframeinfo.line.startswith("@")
		#return self.names and "value" in self.settings


	def get_oneliner_name(self):
		name = ""
		try:
			astmodule = ast.parse(self.callframeinfo.line)
		except IndentationError as e:
			raise dag.DagError("Error parsing dagcmd") from e

		with dag.catch() as e:

			if not astmodule.body:
				breakpoint()
				pass
				
			if astmodule.body and isinstance(astmodule.body[0], ast.Assign):
				target = astmodule.body[0].targets[0]

				# IF multiple dagcmds are being made at once: Determine which name to use via callframeinfo
				if isinstance(target, ast.Tuple):
					varnames = [n.id for n in astmodule.body[0].targets[0].elts]
					values = [n for n in astmodule.body[0].value.elts]
					currentvalue = [d for d in dag.asttools.get_nodes_at(astmodule.body[0].value, self.callframeinfo.coll_offset) if d in values]
					name = varnames[values.index(currentvalue[0])]
				# ELIF, this is a value (e.g.: an object property): Get the assignment name
				if isinstance(target, ast.Attribute):
					name = astmodule.body[0].targets[0].value.id
				# ELSE, this is a singular assignment: Get the assignment name
				else:
					name = astmodule.body[0].targets[0].id

		return name


	def maybe_build_oneliner(self):
		"""
		If this is a 1-liner dagcmd, generate the dagcmd(s)
		:returns: The dagcmd if built, else this dagcmd builder
		"""

		dagcmd = None

		if self.is_oneliner:
			if not self.names:
				with dag.passexc(SyntaxError), dag.dtprofiler("astparse"), dag.catch() as e:
					name = self.get_oneliner_name()

					if not name:
						return self

					self.names = [name]

			for name in self.names: # If this has names, assume it's a 1liner and build the dagcmds
				dagcmd = self.add_dagcmd(name, self.settings)

				for dagarg in self.added_dagargs:
					dagargs.maybe_add_dagargslist_to_fn(dagcmd.fn)
					dagcmd.fn.dagargs.add(dagarg)

		return dagcmd if dagcmd else self


	def LAUNCH(self, url, *args, **kwargs):
		"""
		Sets the dagcmd so that it launches a given URL
		:param url: The object to launch
		:param args: Any args to be passed into the launcher
		:param kwargs: Any kwargs to be passed into the launcher
		:returns: The dagcmd if built, else this dagcmd builder
		"""

		self.settings.value = dag.nab.launch(url, *args, **kwargs)

		return self.maybe_build_oneliner()


	def _set_iomethod_value(self, methodname, target = "", drill = None, **kwargs):
		"""
		Processes a given iomethod, including possibly turning dagcmd into a 1-liner
		"""

		iomethod = dag.dagio.registered_iomethods[methodname]
		self.settings.value = dag.nab(iomethod)(target, drill = drill, **kwargs)
		self.settings.raw_value = target

		return self.maybe_build_oneliner()


	def __getattr__(self, attr: str) -> functools.partial | None:
		if attr.isupper():
			if attr.lower() in dag.dagio.registered_iomethods:
				return functools.partial(self._set_iomethod_value, attr.lower())

			# Set arbitrary settings if uppercased
			name, value = dag.evaluate_name(attr)
			self.settings[name.lower()] = value
			return self


	def add_dagcmd(self, name: str, settings, fn = None):
		from dag.dagcmds import DagCmd

		with dag.catch() as e:
			cmdclass = settings.get("_cmd_type", DagCmd)
			dagcmd = cmdclass(settings, fn = fn, dagapp = self.app, name = name, added_argspec_args = self.added_argspec_args, callframeinfo = self.callframeinfo)

			cmdmodule = self.callframeinfo.module

			if cmdmodule:
				if not hasattr(cmdmodule, "_dag_dagcmds_"):
					setattr(cmdmodule, "_dag_dagcmds_", [])

				cmdmodule._dag_dagcmds_.append(dagcmd)

			return self.app.add_dagcmd(dagcmd, is_default_cmd = self.is_default_cmd)


	def add_dagarg(self, dagarg, argspec: bool = False) -> None:
		"""
		Adds the given dagarg to the DagCmdBuilder

		:param dagarg: The dagarg to add
		:param argspec: Whether or not to eventually add the dagarg to the future dagcmd's fn
		"""

		self.added_dagargs.append(dagarg)

		# IF argspec: setup the dagarg to be added to the future dagcmd's argspec
		if argspec:
			with dag.catch() as e:
				self.added_argspec_args.append(dagarg.name)


	def __call__(self, arg1 = None, *names, **settings):
		from dag.dagcmds import extract_fn

		with dag.dtprofiler("dagcmd_builder_call") as tp:
			self.settings |= settings

			if callable(arg1):
				fn, origfn = extract_fn(arg1)

				if self.added_dagargs:
					fn = dagargs.maybe_add_dagargslist_to_fn(fn)

					for dagarg in self.added_dagargs:
						fn.dagargs.add(dagarg)

				if self.names:
					names += self.names				
				else:
					names += tuple([fn.__name__])

				for name in names:
					dagcmd = self.add_dagcmd(name, self.settings, fn = fn)

				return dagcmd

			if arg1 is not None:
				self.names += (arg1,) + names

			# 1-line dagcmd if names are defined and "value" is in settings
			if self.is_oneliner:
				#breakpoint("value" not in self.settings) <- find 1liners still inserting name
				if self.is_oneliner:
					name = self.get_oneliner_name()

					# IF not name: Then this isn't being assigned to a value. just return self
					if not name:
						return self
						
					self.names = [name]

					
				cfi = dag.callframeinfo(inspect.currentframe(), 1)
			
				for name in self.names:
					dagcmd = self.add_dagcmd(name, self.settings)

					if self.added_dagargs:
						dagargs.maybe_add_dagargslist_to_fn(dagcmd.fn)

						for dagarg in self.added_dagargs:
							dagcmd.fn.dagargs.add(dagarg)

					return dagcmd

			return self
#<<<< DagCmdBuilder




#>>>> DagCmdBuiderGenerator
class DagCmdBuilderGenerator:
	is_default_dagcmd = False

	@property
	def cmd(self):
		callframeinfo = dag.callframeinfo(inspect.currentframe())

		with dag.catch() as e:
			return DagCmdBuilder(self._cmd_root, callframeinfo, is_default_cmd = self.is_default_dagcmd, **self._cmd_settings)


	@property
	def collection(self):
		from dag.collectiondagcmds import CollectionDagCmd, CollectionBuilder
		callframeinfo = dag.callframeinfo(inspect.currentframe())
		return CollectionBuilder(self._cmd_root, callframeinfo, is_default_cmd = self.is_default_dagcmd, _cmd_type = CollectionDagCmd, **self._cmd_settings)


	@property
	def _cmd_settings(self):
		# This is here so that applications and templates can be a subclass of this class
		return {}


	def cmdtemplate(self, **settings):
		return DagCmdTemplate(root = self, **settings)


	@property
	def arg(self):
		return dag.arg


	@property
	def DEFAULT(self):
		dbuilder = DefaultDagCmdBuilderGenerator()
		dbuilder._cmd_root = self._cmd_root
		return dbuilder
#<<<< DagCmdBuilderGenerator


#>>>> DefaultDagCmdBuilderGenerator
class DefaultDagCmdBuilderGenerator(DagCmdBuilderGenerator):
	is_default_dagcmd = True
#<<<< DefaultDagCmdBuilderGenerator




#<<<< DagCmd Templates
class DagCmdTemplate(DagCmdBuilderGenerator):
	def __init__(self, root = None, **settings):
		self.root = root
		self.settings = settings
		self._cmd_root = root

	@property
	def _cmd_settings(self):
		return self.settings

	def template(self, **settings):
		return type(self)(root = self.root, **(self.settings | settings))

	def __call__(self, **settings):
		return self.template(**settings)
#<<<< DagCmd Templates



def duplicate_builder_as(builder, buildercls: type[DagCmdBuilder]) -> DagCmdBuilder:
	newbuilder = buildercls(app = builder.app, callframeinfo = builder.callframeinfo, is_default_cmd = builder.is_default_cmd, **builder.settings)
	newbuilder.names = builder.names
	newbuilder.added_dagargs = builder.added_dagargs
	newbuilder.added_argspec_args = builder.added_argspec_args
	return newbuilder