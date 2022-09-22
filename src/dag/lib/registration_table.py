import inspect
from collections.abc import MutableMapping

from typing import Optional, Any

class RegistrationTable(MutableMapping):
	"""
	A wrapped dict that keeps track of identifiable elements contained within its containing object
	"""

	def __init__(self, owner: Optional[Any] = None, items: Optional[dict] = None):
		self.owner = owner
		self.items = items or {}

		self.parent_items = [*self.items.keys()]


	def __getitem__(self, idx):
		if isinstance(idx, int):
			name = self.items.keys()[idx]
			return self[name]

		item = getattr(self.owner, idx) if self.owner else None

		return item or self.items[idx]


	def __setitem__(self, idx, value):
		if idx in self.items and not idx in self.parent_items:
			raise IndexError(f"Item named {idx} already registered {'in ' + self.owner if self.owner else ''}");
		if isinstance(idx, int):
			raise IndexError("Cannot set integer index of RegistrationTable")

		#self.items[idx] = None if self.owner else value
		self.items[idx] = value


	def __delitem__(self, idx):
		del self.items[idx]


	def __iter__(self):
		return iter(self.items)


	def __len__(self):
		return len(self.items)


	def names(self):
		return [*self.items.keys()]


	def __getattr__(self, value, default = None):
		return self.items.get(value, default)


	def copy(self, owner = None):
		return self.__class__(owner or self.owner, self.items.copy())


	def get_by_type(self, cls):
		return {k:v for k,v in self.items.items() if isinstance(v, cls) or (inspect.isclass(v) and issubclass(v, cls))}


	def __repr__(self): return f"RegistrationTable: {sorted(self.names())}"