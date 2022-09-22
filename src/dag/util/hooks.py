import uuid, inspect, functools
from contextlib import contextmanager

import dag


def generate_uuid():
	return uuid.uuid4



class HooksAPI:
	def __init__(self):
		self.hooks = Hooks()
		self.hookbuilder = HookBuilderAPI(self) # Used by dag API


	def add(self, hook_name, hook_action):
		if not dag.ctx.IS_IMPORTING_DAGMOD:
			return self.hooks.add_hook(hook_name, hook_action)
		else:
			uuid = generate_uuid()
			dag.ctx.active_dagmod_importer.hooks.setdefault(hook_name, {})[uuid] = hook_action
			return uuid



	def do(self, hook_name, *args, **kwargs):
		return self.hooks.do_hook(hook_name, *args, **kwargs)


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


class Hooks:
	def __init__(self):
		self.hooks = {}


	def add_hook(self, hookname, action, dagcmd = None):
		hookid = generate_uuid()

		#self.hooks.setdefault(dagcmd or dag.ctx.active_dagcmd, {}).setdefault(hookname, {})[hookid] = action
		dag.ctx.active_dagcmd.settings.setdefault(f"hook_{hookname}", {})[hookid] = action

		return hookid


	def remove_hook(self, hookname, hookid):
		#self.hooks.setdefault(dag.ctx.active_dagcmd, {}).setdefault(hookname, {}).pop(hookid, None)
		if f"hook_{hookname}" in dag.ctx.active_dagcmd.settings:
			dag.ctx.active_dagcmd.settings[f"hook_{hookname}"].pop(hookid, None)



	def do_hook(self, hookname, *args, **kwargs):
		value = None

		# Run hooks valid to all commands in module
		#for hook_action in self.hooks.get(None, {}).get(hookname, {}).values():
		#	total_fnargs = len(inspect.getfullargspec(hook_action).args) - 1 # Minus one for self arg
		#	value = hook_action(*args[:total_fnargs])
		
		# Run hooks specific to current command
		dagcmd = dag.ctx.active_dagcmd

		for hookuuid, hookaction in dagcmd.settings.getnab(f"hook_{hookname}", {}).items():
			total_fnargs = len(inspect.getfullargspec(hookaction).args)

			if len(args) <= total_fnargs:
				if not inspect.ismethod(hookaction):
					args = (dag.ctx.active_dagcmd.dagmod,) + args  # needed for @dag.hook decorators to pass "self" into the fn
				else:
					pass

			value = hookaction(*args[:total_fnargs])

		return value


	def __repr__(self):
		msg = f"<c b>Dag Hooks Object</c>\n<c b orchid>Hooks</c>{self.hooks}"
		return dag.format(msg)



class HookBuilderAPI:
	def __init__(self, hooksinstance):
		self.hooksinstance = hooksinstance

	def __call__(self, name = "", **hooks):
		return HookBuilder(self.hooksinstance, name, **hooks)

	def __getattr__(self, attr):
		return HookBuilder(self.hooksinstance, attr)


class HookBuilder:
	def __init__(self, hooksinstance, name, **hooks):
		self.hooksinstance = hooksinstance
		self.name = name
		self.hooks = hooks
		self.hookids = {}

	def __call__(self, fn):
		uuid = generate_uuid()
		dag.ctx.active_dagmod_importer.hooks.setdefault(self.name, {})[uuid] = fn
		return fn

	def __enter__(self):
		for hookname, hookaction in self.hooks.items():
			hookid = self.hooksinstance.add(hookname, hookaction)
			self.hookids.setdefault(hookname, []).append(hookid)


	def __exit__(self, type, value, traceback):
		for hookname, hookidlist in self.hookids.items():
			for hookid in hookidlist:
				self.hooksinstance.hooks.remove_hook(hookname, hookid)


instance_hooks = HooksAPI()