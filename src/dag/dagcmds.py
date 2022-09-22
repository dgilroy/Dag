import re, traceback, inspect
from copy import deepcopy
from collections.abc import Sequence, Mapping
from typing import Any

import dag
from dag.lib import dot
from dag.util import nabbers


from dag import dagargs
from dag.exceptions import DagPlaceholderError
from dag.dagcmd_exctx import DagCmdExecutionContext
from dag.persistence import CacheFile

from dag.tempcache import TempCacheFile
from dag.identifiers import DagCmdBase



class DagArgable:
	def __init__(self, dagargs_settings_dicts = None):
		pass


class DagCmd(DagCmdBase):
	def __init__(self, fn, settings, dagmod = None, dagargs_settings_dicts = None, name = None):
		super().__init__()

		# The module this DagCmd belongs to
		self.dagmod = dagmod or dag.ctx.active_dagcmd
		self.rootcmd = dagmod or self
		self._parent_dagcmd = self.dagmod
		
		self.settings = dagmod.settings | nabbers.NabbableSettings(dagmod.settings | settings)
		self.settings.setdefault("catch", DagPlaceholderError)
		self.settings.setdefault("subcmds", {})
		
		self.subcmdtable.register_child("subcmds").populate(self.settings.subcmds)
		
		# The function that this DagCmd wraps
		self.fn = fn
		self.fninfo = self.FnInfo(fn)
		self.name = name or self.fninfo.name

		# The list of @dag.arg decorators over the DagCmd
		self.dagargs_settings_dicts = dagargs_settings_dicts or {}
		self.dagargs = self.DagArgsList(self)
		
		self.update_dagcmd_cache = False

		self.locals = {} # Used by PartialDagCmd


	class FnInfo:
		def __init__(self, fn):
			self.fn = fn
			self.name = self.fn.__name__
			self.argspec = inspect.getfullargspec(self.fn)

			defaults = dict(zip(self.argspec.args[::-1], (self.argspec.defaults or ())[::-1]))
			self.arg_defaults = defaults | (self.argspec.kwonlydefaults or {})



	def _get_subcmd(self, subcmdname, subcmdtable_val):
		return subcmdtable_val

		
	@property
	def fn(self):
		return self._fn


	@fn.setter
	def fn(self, fn):
		self._fn = fn
		# The name of the function this DagCmd wraps
		self.fn_name = self.settings.fn_name or fn.__name__
		# The argspec of the function
		self.fn_argspec = inspect.getfullargspec(fn)
		# The argspec of the DagCmd which may be modified
		self.argspec = inspect.getfullargspec(fn)


		
	# The default values of the kwargs belonging to the function
	# This is set as a property because the argspec can be updated
	@property
	def fn_arg_defaults(self):
		defaults = dict(zip(self.fn_argspec.args[::-1], (self.fn_argspec.defaults or ())[::-1]))
		return dag.nab_if_nabber(defaults | (self.fn_argspec.kwonlydefaults or {}))


	@property
	def defaults(self):
		return self.fn_arg_defaults


	def __repr__(self):
		main_format = "white bg-lightseagreen"
		objrepr = object.__repr__(self)

		return dag.format(f'<<c {main_format}>{self.dagmod.name} "{self.name}": {objrepr}</c>>')
		
			
	# Runs the DagCmd				
	## Call DagCmd as a function
	def __call__(self, *args, **kwargs):
		parsed = associate_args_to_names(self.argspec, locals())

		with dag.ctx(parsed = parsed):
			return self.run_with_parsed(parsed)


	## Update the DagCmd cache as a function
	def update(self, *args, **kwargs):
		try:
			self.update_dagcmd_cache = True
			return self(*args, **kwargs)
		finally:
			self.update_dagcmd_cache = False


	def update_with_parsed(self, parsed):
		try:
			self.update_dagcmd_cache = True
			return self.run_with_parsed(parsed)
		finally:
			self.update_dagcmd_cache = False


	## THE dagcmd runner
	def run_with_parsed(self, parsed):
		with dag.ctx(active_dagcmd = self, active_parsed = parsed):
			dagcmd_exctx = DagCmdExecutionContext(self, parsed)

			with dag.ctx(parsed = parsed, active_dagcmd = self, dagcmd_execution_ctx = dagcmd_exctx):
				try:
					response = self.run_dagcmd(parsed, dagcmd_exctx)

					with dag.ctx(active_response = response):
						if "testbool" in self.settings:
							print(self.settings.testbool)

						if self.settings.cache and (dag.ctx.directives.update_all_caches or self.update_dagcmd_cache or not self.is_cached_from_exctx(dagcmd_exctx)):
							CacheFile.write_from_dagcmd_exctx(response, dagcmd_exctx)

						if self.settings.tempcache and not TempCacheFile.exists_from_dagcmd_exctx(dagcmd_exctx):
							TempCacheFile.write_from_dagcmd_exctx(response, dagcmd_exctx)						

						return response

				except self.settings.catch as e:
					print(f"\n\033[1mDagCmd: Caught anticipated error:\033[0m\n")
					return traceback.print_exc()


	def is_cached(self, **kwargs):
		exctx = DagCmdExecutionContext(self, kwargs)
		return self.is_cached_from_exctx(exctx)


	def is_cached_from_exctx(self, exctx):
		return CacheFile.exists_from_dagcmd_exctx(exctx)


	# Used by CollectionDagCmd for further processing
	def run_dagcmd(self, parsed, dagcmd_exctx):
		with dag.ctx(parsed = parsed):
			return self.get_response(parsed, dagcmd_exctx)



	def get_response(self, parsed, dagcmd_exctx):
		response = None

		# Returns contents of a cachefile/tempcachefile instead of running the fn
		if not dag.ctx.directives.update_all_caches and not self.update_dagcmd_cache:
			# Check tempcache first
			if self.settings.tempcache and TempCacheFile.exists_from_dagcmd_exctx(dagcmd_exctx):
				response = TempCacheFile.read_from_dagcmd_exctx(dagcmd_exctx)

			elif self.settings.cache and self.is_cached_from_exctx(dagcmd_exctx):
				response = self.read_from_cachefile(dagcmd_exctx)

			if response is not None:
				return response

		try:
			dag.hooks.do("before_evaulate_dagcmd")

			# If "value" setting is set, grab that as response
			if "value" in self.settings:
				response = self.get_dagcmd_value()
				
			# Runs the function if no cache or value setting found
			if response is None:
				response = self.run_fn_with_parsed(parsed)
		finally:
			dag.hooks.do("after_evaulate_dagcmd")

		return self.process_response_type(response)


	def process_response_type(self, response):
		if self.settings.get("type") and isinstance(response, str):
			return self.settings.type(response)

		return response


	def partial(self, *args, **kwargs):
		return PartialDagCmd(self, locals())


	def read_from_cachefile(self, dagcmd_exctx):
		with dag.ctx(cachefile_reading = True):
			dag.hooks.do("dagcmd_before_cachefile_read")
			response = CacheFile.read_from_dagcmd_exctx(dagcmd_exctx)
			dag.hooks.do("dagcmd_after_cachefile_read", response)
			return response


	def get_dagcmd_value(self):
		response = None

		try:
			dag.hooks.do("dagcmd_before_value")
			response = self.settings.value
			return response
		except:
			raise
		finally:
			if response is not None:
				dag.hooks.do("dagcmd_after_value", response)
			

	def run_fn_with_parsed(self, parsed):
		args, kwargs = self.translate_parsed_to_fn_args(parsed)
		
		try:
			dag.hooks.do("dagcmd_before_fn")
			response = self.fn(self.dagmod, *args, **kwargs)
			dag.hooks.do("dagcmd_after_fn", response)
			return response
		except TypeError as e:
			breakpoint()
			return self.fn(self.dagmod)
			

	# Used to make sure parsed dagargs.kwargs conform to internal callable argspec
	def translate_parsed_to_fn_args(self, parsed):
		args = []
		for arg in self.fn_argspec.args[1:]:
			if arg in parsed:
				args.append(parsed.get(arg))
					
		if self.fn_argspec.varargs:
			argval = parsed.get(self.fn_argspec.varargs, [])
			if isinstance(argval, (list, tuple)):
				args.extend(argval)
			else:
				args.append(argval)
				
		kwargs = {name:val for name,val in parsed.items() if name in self.fn_argspec.kwonlyargs}
			
		if self.fn_argspec.varkw:
			argnames = [*filter(None, (self.fn_argspec.args[1:] + self.fn_argspec.kwonlyargs) + [self.fn_argspec.varargs])]
			kwargs.update({name:val for name,val in parsed.items() if name not in argnames})

		return (args, kwargs)


	@property
	def __doc__(self): return self.fn.__doc__
	
	@property
	def __name__(self): return self.fn.__name__


	
	class DagArgsList(Sequence):
		def __init__(self, dagcmd):
			self.dagcmd = dagcmd
			self.dagargs_settings_dicts = dagcmd.dagargs_settings_dicts

			self._dagargs = []
			self.dagargs_dict = {argname: {} for argname in self.argnames}

			# Process any passed-in arg settings
			self.process_dagargs_dicts()
				
			# For any dagargs.in the cmd fn that weren't specified in an @dag.arg, build them here
			for arg_name in self.dagcmd.argspec.args:
				if arg_name == "self":
					continue

				if self.get(arg_name) is None:
					self.add_dagarg(dagargs.DagArg(arg_name, dagcmd, {}))

			if vararg := self.dagcmd.argspec.varargs:
				self.add_dagarg(dagargs.DagArg(vararg, dagcmd, {"nargs": -1, "required": False, "nargs_join": None}))

			# For any dagargs.in the cmd fn that weren't specified in an @dag.arg, build them here
			for arg_name in self.dagcmd.argspec.kwonlyargs:
				if self.get(arg_name) is None:
					self.add_dagarg(dagargs.DagArg(f"--{arg_name}", dagcmd, {}))
			
		def __getitem__(self, idx): return self._dagargs[idx]
		def __len__(self): return len(self._dagargs)


		@property
		def argnames(self):
			argspec = self.dagcmd.argspec
			# [1:] is to remove 'self'
			return argspec.args[1:] + ([argspec.varargs] if argspec.varargs else []) + argspec.kwonlyargs + ([argspec.varkw] if argspec.varkw else [])


			
		@property
		def dagargs(self):
			return self._dagargs
			

		@property
		def names(self):
			return [dagarg.name for dagarg in self._dagargs]
			

		def process_dagargs_dicts(self):
			for dagarg_name, dagarg_settings_dict in self.dagargs_settings_dicts.items():
				dagargclass = dagarg_settings_dict.get("_arg_type", dagargs.DagArg)

				# Remove name and argtype from settings dict
				# "pop" allows for removing withouot try/keyerror
				#dagarg_settings_dict.pop("_arg_type", None) Removed because it was breaking commands with multiple @dag.cmd's (see V _ticket)
				#dagarg_settings_dict.pop("_name", None)
				
				dagarg = dagargclass(dagarg_name, self.dagcmd, dagarg_settings_dict)

				self.add_dagarg(dagarg)


		def add_dagarg(self, dagarg):
			if dagarg.is_positional_dagarg and dagarg.clean_name not in self.dagcmd.argspec.args:
				self.dagcmd.argspec.args.append(dagarg.clean_name)

			elif dagarg.is_named_dagarg and dagarg.clean_name not in self.dagcmd.argspec.kwonlyargs:
				self.dagcmd.argspec.kwonlyargs.append(dagarg.clean_name)

			self._dagargs.append(dagarg)
				
			ordered_args = [self.get(arg_name) for arg_name in self.dagcmd.argspec.args if arg_name != "self" and self.get(arg_name) is not None]

			if self.dagcmd.argspec.kwonlyargs and dagarg not in ordered_args:
				ordered_args += [self.get(kwarg_name) for kwarg_name in self.dagcmd.argspec.kwonlyargs if self.get(kwarg_name) is not None]
				
			self._dagargs = ordered_args

			
		def pop(self, idx = -1):
			return self._dagargs.pop(idx)
			
		def get(self, name):
			return next((dagarg for dagarg in self._dagargs if name in (dagarg.name, dagarg.clean_name)), None)
			
		def get_named_dagargs_names(self):
			return [dagarg.name for dagarg in self._dagargs if dagarg.is_named_dagarg]
			
		def get_positional_dagargs(self):
			return [dagarg for dagarg in self._dagargs if dagarg.is_positional_dagarg]
						
		def __str__(self): return str(self._dagargs)

		def __repr__(self): return f"DagArgs: {self._dagargs}"
			
		"""
		def __getitem__(self, idx):
			try:
				return self.dagargs[idx]
			except IndexError as e:
				return None
		"""
			
		"""def copy(self): return self.__class__(self.dagcmd, deepcopy(self.dagargs_settings_dicts))"""
		
		

class PartialDagCmd(DagCmd):
	def __init__(self, dagcmd, locals = None):
		super().__init__(dagcmd.fn, dagcmd.settings, dagmod = dagcmd.dagmod, dagargs_settings_dicts = dagcmd.dagargs_settings_dicts, name = dagcmd.name)
		self.dagcmd = dagcmd
		self.locals = associate_args_to_names(self.argspec, locals or {})

	def run_with_parsed(self, parsed):
		parsed |= self.locals
		return super().run_with_parsed(parsed)
		

		
		
class CollectionDagCmd(DagCmd):		
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.resource_name = "resource"

		resources_dagarg = self.dagargs.get(self.resource_name)

		if resources_dagarg is None:
			resources_dagarg = dagargs.CollectionResourceArg(self.resource_name, self, {"collection": self}) # Settings are left empty here and filled belofw becuase of how the @dag.resources decorator works
			self.dagargs.add_dagarg(resources_dagarg)
		else:
			resources_dagarg.settings.collection = self
			resources_dagarg.settings.args = [dag.decorators.arg(dagarg.clean_name) for dagarg in self.dagargs.get_positional_dagargs() if dagarg.clean_name != self.resource_name]
			#resources_dagarg = dagargs.CollectionResourceArg(self.fn_name, self, resources_dagarg.settings | {"collection": self, "args": [dag.decorators.arg(dagarg.clean_name) for dagarg in self.dagargs.get_positional_dagargs() if dagarg.clean_name != self.resource_name],})


		self.resources_dagarg = resources_dagarg
	
		self.settings.setdefault("_cmd_type", type(self))
		self.settings.setdefault("cache", bool(self.settings.label or self.resources_dagarg.settings.label))
		self.settings.setdefault("launch", "")
		self.settings.setdefault("label", "")
		self.settings.setdefault("label_ignore_chars", [])
		self.settings.setdefault("id", "")

		self.settings._resource_settings = self.settings | self.resources_dagarg.settings
		
		
	def get_resource_from_parsed(self, collection, parsed):
		argvalue = self.resources_dagarg.settings.get("value")
		resource = parsed[self.resource_name]

	 	# Collection is here for things like regex r/.*/
		if isinstance(resource, (dag.Resource, dag.Collection)):
			return resource
			
		# NOTE: Getting used by XML stuff
		parsed_no_resource = {k:v for k,v in parsed.items() if k is not self.resource_name}
		return self.run_with_parsed(parsed_no_resource).find(parsed[self.resource_name])

	

	def run_dagcmd(self, parsed, dagcmd_exctx):
		parsed_no_resource = {k: v for k, v in parsed.items() if k != self.resource_name}

		response = super(type(self), self).run_dagcmd(parsed_no_resource, dagcmd_exctx)
		
		if not isinstance(response, (dag.Response, dag.Collection)):
			response = dag.Response(response)

		if not isinstance(response, dag.Collection):
			response = dag.Collection(response, settings = self.settings, parsed = parsed_no_resource, name = self.cmdpath())

		if self.resource_name in parsed:
			return self.get_resource_from_parsed(response, parsed)
			
		return response



	def prompt_for_resource(self):
		# This was ported from DagMod. It was never finished.
		# This will prompt for parents to drill into this collection
		# Used, for example, by M

		ancestors = [self]
		ancestor = self

		while ancestor.settings.parent:
			ancestor = getattr(self, ancestor.settings.parent.name[0])
			ancestors.append(ancestor)

		ancestors = ancestors.reverse()
			
		breakpoint()





def associate_args_to_names(argspec: inspect.FullArgSpec, locals_dict: Mapping) -> dict["str", Any]:
	argspec_args = {}

	with dag.ctx(parsed = argspec_args):
		start_idx = 1 if (argspec.args and "self" == argspec.args[0]) else 0

		# Apply defaults
		if argspec.defaults:
			for argname, default in zip(argspec.args[start_idx:], argspec.defaults):
				argspec_args[argname] = dag.nab_if_nabber(default)
				
		# Apply values
		argspec_args |= dict(zip(argspec.args[start_idx:], locals_dict["args"]))

		# Apply kwarg defaults
		if argspec.kwonlydefaults:
			for argname, default in dict(argspec.kwonlydefaults).items():
				argspec_args[argname] = dag.nab_if_nabber(default)
				
		argspec_args |= locals_dict["kwargs"]
			
		if argspec.varargs:
			total_fn_args = len(argspec.args[start_idx:])
			argspec_args[argspec.varargs] = tuple(locals_dict["args"][total_fn_args:])

		return argspec_args


class MetaDagCmd(DagCmd):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.completion_cmdtable = dag.default_dagcmd.subcmdtable





registered_settings = {}


def register_cmd(name, **settings):
	registered_settings[name] = settings


register_cmd("Parent", parentcmd = True)
register_cmd("Collection", _cmd_type = CollectionDagCmd)
register_cmd("Meta", _cmd_type = MetaDagCmd)