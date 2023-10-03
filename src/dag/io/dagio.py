import copy
from functools import partial
from contextlib import contextmanager

import dag
from dag.lib import concurrency
from dag.cachefiles import cachefiles
from dag.responses import registered_parsers, parse_response_item, ResponseParserAttrSettings


registered_iomethods = dag.ItemRegistry()

class IOMethod(ResponseParserAttrSettings):
	def __init__(self, action, action_name = "", group = "", session_class = None, **settings):
		super().__init__(**settings)
		self.action = action
		self.action_name = action_name

		if self.action_name.lower() in registered_iomethods:
			raise ValueError(f"IO Method \"{self.action_name.lower()}\" already registered")

		registered_iomethods[self.action_name.lower()] = self

		self.group = group
		self.session_class = session_class or IOSession # Done this way bc IOSession is defined below IOmethod
		self.settings.setdefault("concurrency_map", concurrency.multiprocess_map)

		self.set_settings_attr("CACHE", "cache", True)
		self.set_settings_attr("BYTES", "bytes", True)
		self.set_settings_attr("RAW", "raw", True)
		self.set_settings_attr("MULTIPROCESS", "concurrency_map", concurrency.multiprocess_map, default = concurrency.multithread_map)
		self.set_settings_attr("MULTITHREAD", "concurrency_map", concurrency.multithread_map, default = concurrency.multiprocess_map)



	def __call__(self, target = "", *args, **kwargs):
		return self.session_class(self, **self.settings).call(target, *args, **kwargs)

	# Used when iomethod is a class method, (currently files.read())
	def __get__(self, instance, owner):
		newself = copy.copy(self)
		newself.action = partial(newself.action, instance)
		return newself




class IOSession:
	def __init__(self, iomethod, **settings):
		self.iomethod = iomethod
		self.action = iomethod.action
		self.action_name = iomethod.action_name
		self.group = iomethod.group or ""

		self.settings = self.process_settings(settings)
		self.multitarget = None
		self.targets = None
		self.io_sess = None
		self.response = None


	def process_settings(self, settings):
		return settings



	def process_targets(self):
		return self.targets


	def run_concurrent(self, action, targets, *args):
		return self.settings['concurrency_map'](action, targets, *args)


	@contextmanager
	def _io_session(self):
		try:
			with self.io_session() as sess:
				yield sess 		# Done this way because session.__enter__ can introduce a different variable, so "sess" may not equal "session"
		except (AttributeError, TypeError):
			yield None


	def io_session(self):
		return


	def process_action(self):
		pass


	def get_active_dagmod_name(self):
		try:
			return dag.ctx.active_dagcmd.dagapp.name.lower()
		except AttributeError:
			return "DAG_CACHE"


	def read_from_cachefile(self, dagmod_name, target):
		return cachefiles.read(dagmod_name, target)


	def run_action(self, target, *args, **kwargs):
		runsettings = args[-1] if args else {} # Since multiprocess map doesn't do kwargs, they are passed as a dict to the last arg
		self.settings |= runsettings # NOTE, KWARGS DOESN'T WORK BECAUSE CONCURRENCY ONLY PASSES ARGS, SO KWARGS ARE PASSED AS A DICT INTO ARGS
		args = args[:-1] # Remove the runsettings from the args

		dagmod_name = self.get_active_dagmod_name()

		if self.settings.get("cache") and not dag.settings.update_all_caches and cachefiles.exists(dagmod_name, target):
			return self.read_from_cachefile(dagmod_name, target)

		self.process_action()

		dag.echo(f"\n<c b #0F0 / {dag.words.gerund(self.action_name).upper()}:>\n<c u #FFF / {target}>\n")
		response = self.do_action(target, *args, **runsettings)

		if self.settings.get("raw"): 
			return response
			
		if self.settings.get("attr"):
			response = getattr(response, self.settings['attr'])

		if self.settings.get("bytes"):
			response = self.process_bytes(response)
		else:
			try:
				response_parser = self.settings.get("response_parser") or dag.ctx.active_dagcmd.settings.response_parser
			except AttributeError:
				response_parser = dag.responses.DagResponseParser()

			if response_parser:
				response = self.prepare_response_for_parsing(response)
				response = parse_response_item(response, response_parser)

		self.after_action_hooks(response)

		# Write to cache
		if self.settings.get("cache") and (dag.settings.update_all_caches or not cachefiles.exists(dagmod_name, target)):
			cachefiles.write(response, dagmod_name, target)

		if drillee := self.settings.get("drill"):
			response = dag.drill(response, drillee)

		return response


	def do_action(self, target, *args, **kwargs):
		with dag.catch() as e:
			return self.action(target, *args, **kwargs)


	def process_bytes(self, response):
		return bytes(response)

	def prepare_response_for_parsing(self, response):
		return response


	def process_response(self):
		return self.response[0] if self.response and self.multitarget else dag.Response(self.response)


	def __call__(self, target, *args, **kwargs):
		return self.call(target, *args, **kwargs)


	def after_action_hooks(self, response):
		pass


	def process_args(self, *args, **kwargs):
		return args, kwargs


	def call(self, target, *args, **kwargs):
		self.multitarget = not isinstance(target, (list, tuple))
		target = [target] if self.multitarget else target
		self.targets = target or [""]
		self.targets = [str(t) for t in self.targets]

		with self._io_session() as io_sess:
			self.io_sess = io_sess

			targets = self.process_targets()
			args, kwargs = self.process_args(*args, **kwargs)

			self.response = self.run_concurrent(self.run_action, targets, *(args + (kwargs,)))

			return self.process_response()



class IOMethodGenerator:
	def __init__(self, name = "", group = "", session_class = IOSession):
		self.name = name
		self.group = group
		self.session_class = IOSession


	def __call__(self, fn = None, **settings):
		if fn:
			if not callable(fn):
				raise ValueError("iomethod must be passed either (1) a function, or else (2) keyword settings args")

			name = self.name
			group = self.group
			session_class = self.session_class

			if not name:
				name = fn.__name__

			return IOMethod(action = fn, action_name = name, group = group, session_class = session_class)

		# If kwargs, this is a settings
		if settings:
			return self.replace_settings(**settings)

		return self



	def replace_settings(self, **settings):
		newiomethod = copy.deepcopy(self)

		for setting, value in settings.items():
			setattr(newiomethod, setting, value)

		return newiomethod

iomethod = IOMethodGenerator()