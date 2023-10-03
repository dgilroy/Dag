from __future__ import annotations
import sys, inspect
from functools import cached_property
from types import TracebackType
from typing import NoReturn, Generator

from dag.lib import dot
from typing import Any
from contextlib import contextmanager



class Context(dot.DotDict):
	"""
	A context manager AND context for dagmodules that stores information about variables

	Use:
		with ctx(key = val):
			*DO_OPS*

		While doing *DO_OPS*, any check against ctx.key returns val
	"""

	def __init__(self):
		"""
		An instance of Context, which maintains the states of given variables and allows access to those variables via object attr access
		"""
		super().__init__()

		# Used to temporarily store context variables
		object.__setattr__(self, '_data', self._dict)


	def __setattr__(self, attr, value):
		self._data[attr] = value


	@contextmanager
	def __call__(self, *args, **kwargs):
		try:
			stored_settings = {}

			for arg in args:
				name, value = evaluate_name(arg)
				stored_settings[name] = value

			stored_settings |= kwargs
			
			for setting, value in stored_settings.items():
				old_value = self._data.get(setting, CtxSettingNotSet())
				self._data[setting] = value
				stored_settings[setting] = old_value

			yield

		finally:
			for setting, old_value in stored_settings.items():
				if isinstance(old_value, CtxSettingNotSet):
					try:
						del self._data[setting]
					except KeyError:
						pass
				else:
					self._data[setting] = old_value



	def __getattr__(self, attr: str, default: Any = None) -> Any:
		"""
		ContextManager will directly set object attributes to match those in _settings

		This is done so that vars() on Context object will show those attributes

		Any non-set attribute access will return default (None), so that searching context vars doesn't require a try statement

		:param attr: The attribute name being queried
		:param default: What to return if the attr isn't found in the object
		:returns: The default
		"""
		if attr in self._data:
			return self._data[attr]

		return None
		#return CtxSetter(self, attr)


	def __dir__(self):
		return [*self._data.keys()]


	def __repr__(self):
		return f"<Dag Context: {self._data}>"


	def __contains__(self, attr: str) -> bool:
		return attr in self._data



class CtxSettingNotSet:
	pass


@contextmanager
def base_ctx_manager():
	yield



class SkipExecution:
	class SkipWithBlock(Exception):
		pass

	def __init__(*args, **kwargs):
		pass


	def __enter__(self) -> None:
		sys.settrace(lambda *args, **keys: None)
		frame = sys._getframe(1)
		frame.f_trace = self.trace


	def trace(self, frame, event, arg) -> NoReturn:
		raise self.SkipWithBlock()


	def __exit__(self, type: type[BaseException] | None, value: BaseException | None, traceback: TracebackType | None) -> bool | None:
		if type is None:
			return  # No exception
		if issubclass(type, self.SkipWithBlock):
			return True  # Suppress special SkipWithBlock exception




def evaluate_name(name):
	name = name.lower()
	value = not (name.startswith("no-") or name.startswith("no_"))
	name = name.removeprefix("no-").removeprefix("no_")
	return name, value




class CtxSetter:
	def __init__(self, ctxmanager, name):
		self.ctxmanager = ctxmanager
		self.rawname = name	
		self.name, self.value = evaluate_name(name)
		self.oldvalue = None
		self.is_use_rawname = False
		self.is_used_name = False


	def __enter__(self):
		# IF use rawname: "==" was previously used to set a value, so these calcs have already been done
		if self.is_use_rawname:
			return self

		self.is_used_name = True
		self.oldvalue = self.ctxmanager._data.get(self.name)
		self.ctxmanager._data[self.name] = self.value
		return self.value


	def __exit__(self, type, value, traceback):
		name = self.rawname if self.is_use_rawname else self.name
		self.ctxmanager._data[name] = self.oldvalue


	def __bool__(self):
		return self.value


	def __eq__(self, value):
		if self.is_used_name:
			self.is_used_name = False
			self.ctxmanager._data[self.name] = self.oldvalue

		self.is_use_rawname = True
		self.value = value
		self.oldvalue = self.ctxmanager._data.get(self.rawname)
		self.ctxmanager._data[self.rawname] = value # Rawname bc don't need to strip no_ prefix if value is getting set manually
		return self