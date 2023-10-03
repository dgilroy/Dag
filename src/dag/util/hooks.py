import uuid, inspect, functools
from contextlib import contextmanager

import dag


def generate_uuid():
	return uuid.uuid4()





class HooksAPI:
	def __init__(self, parentsettings = None):
		self.parentsettings = parentsettings

		# Holds the hooks
		self.hooks = HooksContainer(parentsettings)

		# Generates new hooks
		self.hookbuilder = HookBuilderAPI(self) # Used by dag API


	def add(self, hook_name, hook_action):
		return self.hooks.add_hook(hook_name, hook_action)


	def do(self, hook_name, *args, items = None, **kwargs):
		return self.hooks.do_hook(hook_name, *args, items = items, **kwargs)


	@contextmanager
	def do_pre_post(self, hookname, *args, **kwargs) -> None:
		"""
		A simple context manager that runs "pre_{hookname}" on entry and "post_{hookname}" on exit
		"""
		try:
			self.do(f"pre_{hookname}", *args, **kwargs)
			yield
		finally:
			self.do(f"post_{hookname}", *args, **kwargs)


	@contextmanager
	def __call__(self, **hooks):
		hookids = {}
		for hookname, hookaction in hooks.items():
			hookid = self.add(hookname, hookaction)
			hookids.setdefault(hookname, []).append(hookid)

		yield

		for hookname, hookidlist in hookids.items():
			for hookid in hookidlist:
				self.hooks.remove_hook(hookname, hookid)


class HooksContainer:
	def __init__(self, parentsettings = None):
		self.parentsettings = parentsettings
		self.hooks = {}


	def add_hook(self, hookname, action, dagcmd = None):
		hookid = generate_uuid()

		#self.hooks.setdefault(dagcmd or dag.ctx.active_dagcmd, {}).setdefault(hookname, {})[hookid] = action

		settings = self.parentsettings or dag.ctx.active_dagcmd.settings
		settings.setdefault(f"hook_{hookname}", {})[hookid] = action

		return hookid


	def remove_hook(self, hookname, hookid):
		#self.hooks.setdefault(dag.ctx.active_dagcmd, {}).setdefault(hookname, {}).pop(hookid, None)
		settings = self.parentsettings or dag.ctx.active_dagcmd.settings

		if f"hook_{hookname}" in settings:
			settings[f"hook_{hookname}"].pop(hookid, None)



	def do_hook(self, hookname, *args, items = None, **kwargs):
		with dag.ctx(f"do_hook_{hookname}"):
			value = None

			# Run hooks valid to all commands in module
			#for hook_action in self.hooks.get(None, {}).get(hookname, {}).values():
			#	total_fnargs = len(inspect.getfullargspec(hook_action).args) - 1 # Minus one for self arg
			#	value = hook_action(*args[:total_fnargs])

			# List of possible items to run hooks on
			if not isinstance(items, (list, tuple)):
				items = [items]
			elif isinstance(items, tuple):
				items = [*items]

			hookitems = [dag.ctx.active_dagcmd] + items
			
			# Run hooks specific to current command
			#dagcmd = dag.ctx.active_dagcmd

			for item in dag.nonefilter(hookitems):
				for hookuuid, hookaction in dag.getsettings(item).getnab(f"hook_{hookname}", {}).items():
					actionargs = inspect.getfullargspec(hookaction).args
					total_fnargs = len(actionargs)

					if len(args) <= total_fnargs:
						if not inspect.ismethod(hookaction) and "self" in actionargs:
							args = (dag.ctx.active_dagcmd.root,) + args  # needed for @dag.hook decorators to pass "self" into the fn
						else:
							pass

					value = hookaction(*args[:total_fnargs])

			return value



	def __repr__(self):
		msg = f"<c b>Dag Hooks Object</c>\n<c b orchid>Hooks</c>{self.hooks}"
		return dag.format(msg)



# The public facing object that sets up hooks
class HookBuilderAPI(dag.DotAccess):
	def __init__(self, hooksinstance: HooksAPI):
		self.hooksinstance = hooksinstance

	def __call__(self, name = "", **hooks):
		return HookBuilder(self.hooksinstance, name, **hooks)

	def __getattr__(self, attr):
		return HookBuilder(self.hooksinstance, attr)


# 
class HookBuilder:
	def __init__(self, hooksinstance: HooksAPI, name, **hooks):
		self.hooksinstance = hooksinstance
		self.name = name
		self.hooks = hooks
		self.hookids = {}

	def __call__(self, fn):
		uuid = generate_uuid()
		parentsettings = self.hooksinstance.parentsettings
		parentsettings.setdefault("hook_" + self.name, {})[uuid] = fn
		return fn

	def __enter__(self):
		for hookname, hookaction in self.hooks.items():
			hookid = self.hooksinstance.add(hookname, hookaction)
			self.hookids.setdefault(hookname, []).append(hookid)


	def __exit__(self, type, value, traceback):
		for hookname, hookidlist in self.hookids.items():
			for hookid in hookidlist:
				self.hooksinstance.hooks.remove_hook(hookname, hookid)