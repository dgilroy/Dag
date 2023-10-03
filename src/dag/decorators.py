import typing, math

import dag

with dag.dtprofiler("import decorators.dagcmds"):
	from dag import dagcmds

with dag.dtprofiler("import decorators.dagargs"):
	from dag import dagargs



class DagArgDecorator:
	module = dagargs

	def __init__(self, *names, **settings):
		self.names = names
		self.settings = settings


	def __call__(self, fn):
		fn, origfn = dagcmds.extract_fn(fn)

		fn = dagargs.maybe_add_dagargslist_to_fn(fn)

		dagarg = self._generate_dagarg(fn)

		with dag.catch() as e:
			fn.dagargs.add(dagarg)

		return origfn


	def __repr__(self):
		return f"<{self.names=} {object.__repr__(self)}"


	def _generate_dagarg(self, fn = None):
		# IF a fn has been passed in and it contains annotations: Modify settings
		if fn:
			with dag.catch() as e:
				names = [name.lstrip('-') for name in self.names if isinstance(name, str)]
				target = [self.settings.get('target')]

			if (annotations := dag.get_annotations(fn)):
				annotationname = set(annotations).intersection(set(names + target))

				if annotationname:
					annotationname = [*annotationname][0]
					annotationtype = annotations[annotationname]

					annosettings = dagargs.registered_arg_annotations.get(annotationtype)

					if annosettings:
						self.settings = annosettings.settings | self.settings # ARG'S KWARGS TAKE PRECEDENCE OVER ANNOSETTINGS

			# If this is a varargs dagarg: Make the dagarg's nargs default to inf
			if dag.argspec(fn).varargs and dag.argspec(fn).varargs in (names + target):
				self.settings.setdefault("nargs", math.inf)

		dagargclass = dagargs.get_dagarg_class(self.settings)
		return dagargclass(*self.names, **self.settings)




class DecoratorBuilder(dag.Nabber):
	def __call__(self, arg1 = None, *args, **kwargs):
		for attr in self._stored_attrs or []:
			if attr.attr_name in self.module.registered_settings:
				kwargs = self.module.registered_settings[attr.attr_name] | kwargs # KWARGS TAKES PRECEDENT OVER REGISTERED SETTINGS

		if callable(arg1):
			return self.buildtarget(**kwargs)(arg1)

		if arg1 is not None:
			args = (arg1,) + args

		return self.buildtarget(*args, **kwargs)



class DagArgDecoratorBuilder(DecoratorBuilder):	
	module = dagargs
	buildtarget = DagArgDecorator



arg = DagArgDecoratorBuilder()