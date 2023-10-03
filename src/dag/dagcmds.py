import inspect, copy, functools
from collections.abc import Mapping
from typing import Callable, Self

import dag
from dag.lib import dummies
from dag.util.argspectools import map_argspec_to_locals

from dag import dagargs
from dag.exceptions import DagPlaceholderError, DagError
from dag.identifiers import Identifier
from dag.builders import DisplayBuilder
from dag.dagcmd_executors import DagCmdExecutor



def extract_fn(fn: Callable) -> tuple[Callable, Callable]:
	origfn = fn

	match fn:
		case DagCmd():
			while isinstance(fn, DagCmd):
				fn = fn.fn
		case _:
			pass

	return fn, origfn





#>>>> DagCmd
class DagCmd(Identifier, dag.mixins.DagSettings, dag.DotAccess):
	dagcmd_executor = DagCmdExecutor

	def __init__(self, settings, fn = None, dagapp = None, name = None, added_argspec_args = None, callframeinfo = None):
		with dag.dtprofiler("dagcmd_init") as tp:
			super().__init__(callframeinfo = callframeinfo, settings = settings)

			# The function that this DagCmd wraps
			if isinstance(fn, property):
				fn = fn.fget

			self._fn = fn or settings.get("fn", dummies.DummyNoArgCallable())
			self._cmd_root = self # Being used by creating subcmds

			# The settings passed into the dagcmd
			self.set_root(dagapp or dag.ctx.active_dagcmd)

			# Cmd settings
			self._settings.setdefault("catch", DagPlaceholderError)
			self._settings.setdefault("prettyprint", True)
			self._settings.setdefault("sort_dict_response", True)
			self._settings.setdefault("store_ic_response", True)
			self._settings.setdefault("store_inputscript", True)
			self._settings.setdefault("enable_tempcache", True)

			try:
				self._settings.raw_value = self.settings['value']._stored_attrs[0].args[0]
			except Exception:
				pass
			
			self._name = name

			self.is_regexcmd = dag.rslashes.item_is_rslash(self._name)

			if self.is_regexcmd:
				self._settings.setdefault("regex_priority", 10)

			self._argspec = None
			self._dagargs = None
			self._added_argspec_args = added_argspec_args or {} # Used if no fn is passed into dagcmd. Used by ops


	def _dag_get_settings(self):
		return self.settings


	def _set_iomethod_value(self, methodname, target = "", drill = None, **kwargs):
		"""
		Processes a given iomethod, including possibly turning dagcmd into a 1-liner
		"""

		iomethod = dag.dagio.registered_iomethods[methodname]

		with dag.bbtrigger("iometh"):
			self._settings.value = dag.nab(iomethod)(target, drill = drill, **kwargs)
			self._settings.raw_value = target

		return self


	def __getattr__(self, attr: str) -> functools.partial | None:
		if attr.isupper():
			if attr.lower() in dag.dagio.registered_iomethods:
				return functools.partial(self._set_iomethod_value, attr.lower())

			# Set arbitrary settings if uppercased
			name, value = dag.evaluate_name(attr)
			self._settings[name.lower()] = value
			return self


	def LAUNCH(self, url, *args, **kwargs):
			"""
			Sets the dagcmd so that it launches a given URL
			:param url: The object to launch
			:param args: Any args to be passed into the launcher
			:param kwargs: Any kwargs to be passed into the launcher
			:returns: The dagcmd if built, else this dagcmd builder
			"""

			self._settings.value = dag.nab.launch(url, *args, **kwargs)
			return self


	@property
	def DEFAULT(self):
		self.root.default_dagcmd = self
		return self


	def copy(self):
		return copy.copy(self)


	def copy_to_app(self, app):
		return self.copy().set_root(app)


	def set_root(self, root):
		self.root = root
		self.dagapp = root
		self._parent_dagcmd = root # used by cmdpath
		return self


	@property
	def fn(self):
		return self._fn


	@property
	def name(self):
		if self.fn:
			return self._name or self.settings.fn_name or self.fn.__name__

		return self._name or self.settings.fn_name


	@property
	def settings(self):
		if self.root:
			return self.root.settings | self._settings # dagapp.settings is a NabbableSettings instance, so unioning will yield another NS instance 

		return self._settings


	@settings.setter
	def settings(self, key, value):
		self._settings[key] = value


	def add_dagcmd(self, dagcmd, is_default_cmd = False):
		self.dagcmds.add(dagcmd, dagcmd.name)

		if not dag.ctx.adding_dagcmd:
			with dag.ctx(adding_dagcmd = True):
				setattr(self, dagcmd.name, dagcmd)

		return dagcmd


	@property
	def add_dagarg(self):
		return DagArgAdder(self)

	add_arg = add_dagarg


	@property
	def argspec(self) -> inspect.FullArgSpec:
		if self._argspec is None:
			if self.fn:
				self._argspec = copy.copy(dag.argspec(self.fn))

			else:
				self._argspec = dummies.emptyargspec

			if self._added_argspec_args:
				for arg in self._added_argspec_args:
					if not arg in self._argspec.args:
						self._argspec.args.append(arg)

		return self._argspec


	@property
	def dagargs(self):
		if self._dagargs and self._dagargs.argspec == self.argspec:
			return self._dagargs

		self._dagargs = dagargs.DagArgsList.build_from_argspec(argspec = self.argspec, arglist = getattr(self.fn, "dagargs", None))

		return self._dagargs



	def process_incmd(self, incmd):
		# For any dagargs.in the cmd fn that weren't specified in an @dag.arg, build them here

		if self.settings.display:
			dagargslist = None

			if hasattr(self.settings.display, "dagargs"):
				dagargslist = self.settings.display.dagargs

			kwonlyargspec = dag.argspectools.kwonlyargspec(self.settings.display)

			kwonlydagargslist = dagargs.DagArgsList.build_from_argspec(kwonlyargspec)

			if dagargslist:
				[dagargslist.add(dagarg, overwrite = False) for dagarg in kwonlydagargslist]
			else:
				dagargslist = kwonlydagargslist


			for dagarg in dagargslist:
				if dagarg.is_positional_dagarg: # Only named dagargs allowed for display fns
					continue

				if dagarg.target in incmd.dagargs.targetdict:
					raise DagError(f"Duplicate dagarg registered ({dagarg.name}) in dagcmd \"{self.cmdpath()}\"")

				dagarg.settings.cacheable = False
				dagarg.settings.required = False
				incmd.dagargs.add(dagarg)

		return incmd
		
		
	# The default values of the kwargs belonging to the function
	# This is set as a property because the argspec can be updated
	@property
	def defaults(self) -> dict[str, object]:
		with dag.ctx(active_dagcmd = self):
			defaults = dag.argspectools.get_default_values(self.argspec)
			return dag.nab_if_nabber(defaults | (self.argspec.kwonlydefaults or {}))


	def __repr__(self) -> str:
		main_format = "white bg-lightseagreen"
		objrepr = object.__repr__(self)

		if self.root:
			return dag.format(f'<<c {main_format}>{self.root.name} "{self.name}": {objrepr}</c>>')

		return dag.format(f'<<c {main_format}> "{self.name}": {objrepr}</c>>')


	# Runs the DagCmd from a function call
	def __call__(self, *args, **kwargs) -> object:
		return self.run(*args, **kwargs)


	def run(self, *args, **kwargs):
		parsed = map_argspec_to_locals(self.argspec, locals())
		return self.run_with_parsed(parsed)


	def showcli(self, *args, **kwargs):
		results = self.run(*args, **kwargs)
		parsed = map_argspec_to_locals(self.argspec, locals())
		formatter = dag.formatter()
		self.settings.display(results, formatter, parsed)
		dag.echo(formatter)
		return results


	def run_with_parsed(self, parsed: Mapping, update_cache: bool = False):
		return self.dagcmd_executor(self, parsed, update_cache).run()


	## Update the DagCmd cache as a function
	def update(self, *args, **kwargs):
		parsed = map_argspec_to_locals(self.argspec, locals())
		return self.run_with_parsed(parsed, update_cache = True)


	def update_with_parsed(self, parsed: Mapping):
		return self.run_with_parsed(parsed, update_cache = True)


	def partial(self, *args, **kwargs):
		return PartialDagCmd(self, locals())


	# Decorator used to set display fn
	@property
	def display(self) -> DisplayBuilder:
		return self._display_builder


	@property
	def __doc__(self) -> str:
		if self.fn:
			return self.fn.__doc__

		return "NO DOC FOR NON-FN DAGCMD"
	
	@property
	def __name__(self) -> str:
		return self.name
#<<<< DagCmd


	

		
#>>>> PARTIAL DAGCMD
class PartialDagCmd(dag.dot.DotProxy):
	def __init__(self, dagcmd, locals = None):
		super().__init__(dagcmd)
		self.dagcmd = dagcmd
		self.locals = map_argspec_to_locals(dagcmd.argspec, locals or {})
# <<<<<<< PARTIAL DAGCMD


# >>>> Filtered DagCmd
class FilteredDagCmd(dag.dot.DotProxy):
	def __init__(self, dagcmd, *filters):
		super().__init__(dagcmd)
		self.dagcmd = dagcmd
		self.filters = filters


	def run_with_parsed(self, parsed = None, *args, **kwargs):
		breakpoint()
		response = super().run_with_parsed(parsed, *args, **kwargs)

		items = []

		breakpoint()
		for filter in self.filters:
			# NOTE: IF THE FOLLOWING BREAKS ON A DAGRESPOSNE, INCORPORATE TYPE CHECK AND USE dag.responses.filter 
			response = response.filter(filter)

			if not response:
				break

		return response
# <<<< Filtered DagCmd




#>>>> AppCmd 
class AppCmd(dag.DotProxy):
	def __init__(self, root, dagcmd):
		super.__init__(dagcmd)
		self.dagcmd = dagcmd
		self.root = root
#<<<< AppCmd




#>>>> DagCmd DagArg Adder
class DagArgAdder:
	def __init__(self, dagcmd):
		self.dagcmd = dagcmd
		self.names = ()
		self.settings = {}


	def __getattr__(self, attr):
		if attr in dagargs.registered_settings:
			self.settings |= dagargs.registered_settings[attr]

		return self


	def __call__(self, *names, **settings):
		self.dagcmd.argspec #generates argspec
		dagargclass = dagargs.get_dagarg_class(self.settings)
		dagarg = dagargclass(*(self.names + names), **(self.settings | settings))
		dagarg(self.dagcmd.fn)

		if isinstance(self.fn, dummies.DummyNoArgCallable):
			self.fn = dummies.DummmyCallable()

		if dagarg.target not in self.dagcmd._argspec.args + (self.dagcmd._argspec.kwonlyargs or []):
			if dagarg.is_positional_dagarg:
				self.dagcmd._argspec.args.append(dagarg.target)
			else:
				## KWARG PROCESSINGe
				self.dagcmd._argspec.args.append(dagarg.target)
				#breakpoint() # SET THIS TO WOKR WITH KWARGS
				pass

		return self.dagcmd
#<<<< DagCmd DagArg Adder





registered_cmdsettings = dag.ItemRegistry()


def register_cmdsettings(name, **settings):
	registered_cmdsettings[name] = settings