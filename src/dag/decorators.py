import inspect, types

import dag
from dag.util import attribute_processors, nabbers

from dag import dagcmds, dagargs


class DagCmdBuilderDescriptor:
	def __init__(self, dagcmd_name, dagcmd_settings, decorator):
		self.dagcmd_name = dagcmd_name
		self.dagcmd_settings = dagcmd_settings
		self.dagargs_settings = decorator.processed_settings["args_settings"].copy()
		self.base_fn = decorator.base_fn


	# Build the DagCmd when called
	def __get__(self, dagmod_obj, dagmod_cls):
		with dag.ctx(active_dagcmd = dagmod_obj):
			dagcmd_class = self.dagcmd_settings.get("_cmd_type", dagcmds.DagCmd)
			dagcmd = dagcmd_class(self.base_fn, self.dagcmd_settings.copy(), dagmod = dagmod_obj, dagargs_settings_dicts = self.dagargs_settings.copy(), name = self.dagcmd_name)

			setattr(dagmod_obj, self.dagcmd_name, dagcmd)
			return dagcmd


class RegisteredTypeGetter(type):
	def __getattr__(cls, attr):
		if dag.ctx.DAG_DECORATOR_ACTIVE:
			if attr in cls.module.registered_settings:
				return lambda *names, **settings: cls(*names, **(cls.module.registered_settings[attr] | settings))

		return cls.__getattribute__(cls, attr)


class MetaDecorator(RegisteredTypeGetter, attribute_processors.MagicMethodAccessRecorder):
	pass


class DagDecoratorBase:
	pass


class DagDecorator(metaclass = MetaDecorator):
	def __init__(self, *names, **settings):
		super().__init__()
		self.names = names
		self.settings = settings
		self.is_name_set = False
		self.is_fn_set = False

		# Filled when __call__ed
		self.base_fn = None
		self.processed_settings = {}


	def process_settings(self):
		if not getattr(self, "processed_settings"):
			self.processed_settings = {
				"cmds_settings": {},
				"args_settings": {},
			}

		for name in self.names:
			self.processed_settings[self.settings_dict_name][name] = self.settings
			self.processed_settings[self.settings_dict_name][name]["_name"] = name


	def __call__(self, fn = None, *args, **kwargs):
		if isinstance(fn, (DagDecorator, types.FunctionType)):
			if isinstance(fn, DagDecorator):
				self.base_fn = fn.base_fn
				self.processed_settings = fn.processed_settings
			elif isinstance(fn, types.FunctionType):
				dag.ctx.DAG_DECORATOR_ACTIVE = False
				self.is_fn_set = True

				if not dag.ctx.IS_IMPORTING_DAGMOD and dag.ctx.active_dagcmd:
					dag.ctx.active_dagcmd.subcmdtable.children.dagcmds.add(fn, fn.__name__)

				self.base_fn = fn
				if not self.names:
					self.names = [self.base_fn.__name__]

			self.process_settings()

			return self

		elif not self.is_name_set:	# Otherwise, use the function as a Resource arg where the base_fn is the collection
			with dag.ctx(DAG_DECORATOR_ACTIVE = True):
				return dag.arg(*((fn,) + args), collection = getattr(dag.this, self.base_fn.__name__), _arg_type = dagargs.ResourceArg, **kwargs)



	def __set_name__(self, dagmod_class, dagcmd_name):
		self.is_name_set = True
		#dag.ctx.DAG_DECORATOR_ACTIVE = False

		# If no cmd decorator was used: Use normal function with no extra settings 
		if not self.processed_settings.get("cmds_settings"):
			self.processed_settings["cmds_settings"][self.base_fn.__name__] = {}

		if not "registered_dagcmds" in dagmod_class.__dict__:
			if hasattr(dagmod_class, "registered_dagcmds"):
				dagmod_class.registered_dagcmds = dagmod_class.registered_dagcmds.copy()
			else:
				dagmod_class.registered_dagcmds = {}


		for dagcmdname, dagcmdsettings in self.processed_settings["cmds_settings"].items():
			breakpoint(dagcmdname == "@", True)
			setattr(dagmod_class, dagcmdname, DagCmdBuilderDescriptor(dagcmdname, dagcmdsettings.copy(), self))
			dagmod_class.registered_dagcmds[dagcmdname] = dagcmdname



class DagArgDecorator(nabbers.Nabbable, DagDecorator):
	settings_dict_name = "args_settings"
	module = dagargs

	#@nabbers.nabval(argname = "names[0]") #-> This drills into self.names[0] and formats the val. DOESN"T WORK BC NEED THE DAGMOD
	#def _nab(self, dagmod, argname):
	def _nab(self):
		argname = self.names[0]
		argname = nabbers.format_val(argname)

		key = argname

		if isinstance(argname, int):
			try:
				key = [*dag.ctx.parsed][argname]
			except KeyError:
				return None

		try:
			return dag.ctx.parsed[key]
		except (TypeError, KeyError) as e:
			breakpoint()
			raise KeyError(f"Key \"<c u>{argname}</c u>\" not found in line args")


			
class DagCmdDecorator(DagDecorator, nabbers.Nabbable):
	settings_dict_name = "cmds_settings"
	module = dagcmds

	def _nab(self):
		collections = dag.nab_if_nabber(self.names[0])
		args = self.names[1:]
		kwargs = self.settings
		breakpoint()
		pass





arg = DagArgDecorator
cmd = DagCmdDecorator


	
def collection(*names, **settings):
	return cmd(*names, **(settings | {"_cmd_type": dagcmds.CollectionDagCmd}))



class ResourcesNabber(nabbers.Nabber, nabbers.ResponseNabbable):
	def __getattr__(self, attr):
		return super().__getattr__(attr)

		
	def process_stored_attrs(self, collection, stored_attrs):
		if not dag.ctx.active_resource: # Currently assumes active_resource isn't set when all resources need to be processed
			responses = []

			for res in collection:
				responses.append(super().process_stored_attrs(res, stored_attrs))

			return all(responses)

		else: # TO BE USED for more complex label creation
			response = super().process_stored_attrs(dag.ctx.active_resource, stored_attrs)
			return response


	def _nab(self):
		if dag.ctx.active_resource:
			return dag.ctx.active_resource

		return nabbers.ResponseNabbable._nab(self)


	def is_should_store_attribute(self):
		return True


	def is_should_process_stored_args(self, item):
		return "active_response" in dag.ctx or "active_resource" in dag.ctx


	def store_attribute(self, attr):
		if dag.ctx.IS_IMPORTING_DAGMOD:
			return super().store_attribute(attr)

		return getattr(dag.dagcollections.resource.ResourcesAttributeProcessor(dag.ctx.resources_call_frame), attr)


	def __getattr__(self, attr):
		frame = inspect.stack()[1]

		with dag.ctx(resources_call_frame = frame):
			return super().__getattr__(attr)
		pass


	def __call__(name = None, **settings):
		return arg("resource", **(settings | {"_arg_type": dagargs.CollectionResourceArg}))


resources = ResourcesNabber()







class DagmodImporter(DagDecoratorBase):
	def __init__(self, dagmod_name = None, **settings):
		self.old_is_importing_dagmod = dag.ctx.IS_IMPORTING_DAGMOD
		self.old_dagmod_importer = dag.ctx.active_dagmod_importer

		dag.ctx.IS_IMPORTING_DAGMOD = True
		dag.ctx.active_dagmod_importer = self


		self.dagmod_name = dagmod_name
		self.settings = settings

		self.hooks = {}


	def __call__(self, dagmod_cls):
		try:
			dag.ctx.IS_IMPORTING_DAGMOD = self.old_is_importing_dagmod

			# If no name registered: ignore the dagmod
			if not self.dagmod_name:
				return dagmod_cls

			for hookname, hookactions in self.hooks.items(): # Handles @hooks
				self.settings.setdefault(f"hook_{hookname}", {}).update(hookactions)

			self.settings["dagmod_name"] = self.dagmod_name.lower()

			dagmod_cls.settings = nabbers.NabbableSettings(getattr(dagmod_cls, "settings", {}) | self.settings)

			# Checks if module name is duplicated from another module
			if self.dagmod_name in dag.default_dagcmd.imported_cmds:
				# If this class is a duplicate, return normal class and skip
				if dagmod_cls in dag.default_dagcmd.imported_cmds.values():
					return dagmod_cls

				# If not dupliate, raise error due to module name duplication	
				if not dag.ctx.is_reloading_dagmod:
					raise ValueError(f"Dagmod Duplicate Error: Duplicate module name \"{self.dagmod_name}\"")
			
			dag.default_dagcmd.imported_cmds[self.dagmod_name] = dagmod_cls
				
			return dagmod_cls
		finally:
			self.active_dagmod_importer = self.old_dagmod_importer

dagmod = DagmodImporter