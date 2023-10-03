import dag
import inspect, copy
from inspect import FullArgSpec
from typing import Mapping, Any, Callable



def copy_argspec(fn: Callable[..., Any]) -> FullArgSpec:
	return copy.copy(inspect.getfullargspec(fn))


def kwonlyargspec(fn: Callable[..., Any]) -> FullArgSpec:
	def _emptyfn() -> None: pass # Here to provide an empty argspec
	
	fnargspec = copy_argspec(fn) # Copied so that original fn's argspec doens't get manipulated
	kwargspec = copy_argspec(_emptyfn)
	kwargspec.kwonlyargs.extend(fnargspec.kwonlyargs)
	kwargspec = kwargspec._replace(kwonlydefaults = fnargspec.kwonlydefaults)

	fnannotations = fnargspec.annotations
	for argname, value in fnannotations.items():
		if argname in kwargspec.kwonlyargs:
			kwargspec.annotations[argname] = value

	return kwargspec


def map_argspec_to_locals(argspec: FullArgSpec, locals_dict: Mapping) -> dict[str, Any]:
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
				
		argspec_argnames = argspec.args + argspec.kwonlyargs

		for argname, argval in locals_dict["kwargs"].items():
			if argname in argspec_argnames:
				argspec_args[argname] = argval
			elif argspec.varkw:
				breakpoint()
				argspec_args.setdefault(argspec.varkw, {})[argname] = argval		

		#argspec_args |= locals_dict["kwargs"] This was adding non-argspec local kwargs to argspec_args
			
		if argspec.varargs:
			total_fn_args = len(argspec.args[start_idx:])
			argspec_args[argspec.varargs] = tuple(locals_dict["args"][total_fn_args:])

		return argspec_args


def map_argspec_to_parsed(argspec: FullArgSpec, parsed: Mapping[str, object]) -> dict[str, object]:
	return map_argspec_to_locals(argspec, {"args": (), "kwargs": parsed})


def get_default_values(argspec: FullArgSpec) -> dict[str, object]:
	return dict(zip(argspec.args[::-1], (argspec.defaults or ())[::-1])) | (argspec.kwonlydefaults or {})