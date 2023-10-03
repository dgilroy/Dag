import dag

class Builder(dag.DotAccess):
	def __init__(self, cmd):
		self.cmd = cmd
		self.active_attr = None


	def __getattr__(self, attr):
		self.active_attr = attr.lower() # lets attr names be UPPERCASE but the setting is saved as lowercase
		return self


class SettingsBuilder(Builder):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.settings = dag.DotDict()


	def __getattr__(self, attr):
		"""
		This is set up so that getting the ATTR sets the value to TRUE/FALSE, but if it's called later the new value will be set
		E.G.: item.ATTR1 will have ATTR1=TRUE, while ATTR1("wow") will set ATTR1="wow" 
		"""

		name, value = dag.evaluate_name("attr")
		self._set_setting(name, value)

		self.active_attr = attr.lower() # This is set for if the attr gets called with a new value
		return self


	def _get_settings(self):
		"""
		This is here because different settingsbuilders use different settings configurations.
		"""
		return self.settings


	def _set_setting(self, name, value):
		settings = self._get_settings()
		settings[self.active_attr] = value


	def __call__(self, value = True):
		if self.active_attr:
			self._set_setting(self.active_attr, value)
			self.active_attr = None

		return self


# >>>> DisplayBuilder
class DisplayBuilder(Builder):
	# Decorator used to set display fn
	def __call__(self, *args, **kwargs):
		assert args or kwargs, "At least one arg must be filled out"

		args = args[0] if len(args) == 1 else args

		if self.active_attr:
			self.cmd._display_settings[self.active_attr] = args
			self.active_attr = None
		elif kwargs:
			self.cmd._display_settings = dag.nabbers.NabbableSettings(kwargs)
		else:
			# here, args is the fn being passed in
			fn = args
			self.cmd._settings.display = fn
			return fn

		return self
# <<<< DisplayBuilder


#>>>> Resources Builder
class ResourcesBuilder(Builder):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.hooks = dag.util.hooks.HooksAPI(parentsettings = self.cmd.settings._resource_settings)
		self.hook = self.hooks.hookbuilder


	def __call__(self, *args):
		assert args, "At least one arg must be filled out"

		args = args[0] if len(args) == 1 else args

		# If Builder is listening to an attr: Set the attr's value to the given args
		if self.active_attr:
			if self.active_attr == "label":
				self.cmd._settings.setdefault("cache", True)
			self.cmd.settings._resource_settings[self.active_attr] = args
			self.active_attr = None
		# Else, no listener is active: Treat resource argname as given args	
		else:
			self.cmd.resource_argname = args

		#if callable(args): -> This works when used as a decorator, but not when used as: {collection}.resources().label(...).id(some callable)....
			#import inspect
			#callframeinfo = inspect.currentframe().f_back
			#breakpoint()
			#return args

		return self
#<<<< Resources Builder