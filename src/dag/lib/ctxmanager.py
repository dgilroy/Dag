from __future__ import annotations
from functools import cached_property

from dag.lib import dot
from typing import Any
from contextlib import contextmanager



class Context(dot.DotAccess):
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
		object.__setattr__(self, '_data', {})


	def __setattr__(self, attr, value):
		self._data[attr] = value


	@contextmanager
	def __call__(self, **kwargs):
		stored_settings = kwargs
		
		for setting, value in stored_settings.items():
			old_value = self._data.get(setting, CtxSettingNotSet())
			self._data[setting] = value
			stored_settings[setting] = old_value

		yield

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

		return self._data.get(attr, default)


	def __dir__(self):
		return [*self._data.keys()]


	def __repr__(self):
		return f"<Dag Context: {self._data}>"


	def __contains__(self, attr):
		return attr in self._data



class CtxSettingNotSet:
	pass


@contextmanager
def base_ctx_manager():
	yield