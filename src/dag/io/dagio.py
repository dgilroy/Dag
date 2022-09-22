import copy
from functools import partial
from contextlib import contextmanager

import dag
from dag.lib import concurrency
from dag.persistence import CacheFile
from dag.responses import registered_parsers, parse_response_item


class IOMethodSettingsAttr:
	def __init__(self, setting, value):
		self.setting = setting
		self.value = value

	def __get__(self, obj, cls):
		new_iomethod = copy.copy(obj)
		new_iomethod.settings[self.setting] = self.value
		return new_iomethod


class IOMethod:
	def __init__(self, action, action_name = "", group = "", session_class = None, **settings):
		self.action = action
		self.action_name = action_name
		self.group = group
		self.session_class = session_class or IOSession # Done this way bc IOSession is defined below IOmethod
		self.settings = settings # Settings to be passed into sessions
		self.settings.setdefault("concurrency_map", concurrency.multiprocess_map)

		for parsername, parser in registered_parsers.items():
			self.set_settings_attr(parsername, "response_parser", parser, no = dag.Response)

		self.set_settings_attr("CACHE", "cache", True)
		self.set_settings_attr("BYTES", "bytes", True)
		self.set_settings_attr("RAW", "raw", True)
		self.set_settings_attr("MULTIPROCESS", "concurrency_map", concurrency.multiprocess_map, no = concurrency.multithread_map)
		self.set_settings_attr("MULTITHREAD", "concurrency_map", concurrency.multithread_map, no = concurrency.multiprocess_map)



	def set_settings_attr(self, attrname, settingname, value, no = None):
		# Creates setting so iomethod.ATTRNAME makes iomethod.kwargs.settingname = value
		setattr(type(self), attrname, IOMethodSettingsAttr(settingname, value))

		# Creates setting so iomethod.NOATTRNAME undoes iomethod.ATTRNAME
		setattr(type(self), "NO" + attrname, IOMethodSettingsAttr(settingname, no or not value))



	def __call__(self, target = "", *args, **kwargs):
		return self.session_class(self, **self.settings).call(target, *args, **kwargs)




class IOSession:
	def __init__(self, iomethod, **settings):
		self.iomethod = iomethod
		self.action = iomethod.action
		self.action_name = iomethod.action_name
		self.group = iomethod.group or ""

		self.settings = self.process_settings(settings)
		self.is_str = None
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
		except AttributeError:
			yield None


	def io_session(self):
		return


	def process_action(self):
		pass


	def get_active_dagmod_name(self):
		return dag.ctx.active_dagcmd.dagmod.name.lower()


	def read_from_cachefile(self, dagmod_name, target):
		return CacheFile.read(dagmod_name, target)


	def run_action(self, target, *args, **kwargs):
		runsettings = args[-1] if args else {} # Since multiprocess map doesn't do kwargs, they are passed as a dict to the last arg
		self.settings |= runsettings # NOTE, KWARGS DOESN'T WORK BECAUSE CONCURRENCY ONLY PASSES ARGS, SO KWARGS ARE PASSED AS A DICT INTO ARGS
		args = args[:-1] # Remove the runsettings from the args

		dagmod_name = self.get_active_dagmod_name()
		if self.settings.get("cache") and not dag.ctx.directives.update_all_caches and CacheFile.exists(dagmod_name, target):
			return self.read_from_cachefile(dagmod_name, target)

		self.process_action()

		print(f"{dag.words.gerund(self.action_name).upper()} {target}\n")
		response = self.do_action(target, *args, **runsettings)

		if self.settings.get("raw"): 
			pass # Skip turning response into DagResponse
			
		if self.settings.get("attr"):
			response = getattr(response, self.settings['attr'])
			
		if self.settings.get("bytes"):
			response = self.process_bytes(response)
		else:
			response_parser = dag.ctx.active_dagcmd.settings.response_parser or self.settings.get("response_parser")
			if response_parser:
				response = self.prepare_response_for_parsing(response)
				response = parse_response_item(response, response_parser)

		self.after_action_hooks(response)

		# Write to cache
		CacheFile.exists(dagmod_name, target)
		if self.settings.get("cache") and (dag.ctx.directives.update_all_caches or not CacheFile.exists(dagmod_name, target)):
			CacheFile.write(response, dagmod_name, target)

		return response


	def do_action(self, target, *args, **kwargs):
		return self.action(target, *args, **kwargs)


	def process_bytes(self, response):
		return bytes(response)

	def prepare_response_for_parsing(self, response):
		return response


	def process_response(self):
		return self.response[0] if self.response and self.is_str else self.response


	def __call__(self, target, *args, **kwargs):
		return self.call(target, *args, **kwargs)


	def after_action_hooks(self, response):
		pass


	def process_args(self, *args, **kwargs):
		return args, kwargs


	def call(self, target, *args, **kwargs):
		self.is_str = isinstance(target, str)
		target = [target] if self.is_str else target
		self.targets = target or [""]

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
		newiomethod = copy.copy(self)

		for setting, value in settings.items():
			setattr(newiomethod, setting, value)

		return newiomethod

iomethod = IOMethodGenerator()