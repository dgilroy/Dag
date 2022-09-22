from __future__ import annotations

import copy
from collections.abc import MutableMapping, Mapping, Generator, Iterator
from typing import Any, NoReturn, Hashable, Union


class DotAccess:
	def __getstate__(self) -> dict:
		"""
		Used by pickling. Needed because of custom __getattr__ functionality
		"""

		return self.__dict__


	def __setstate__(self, d: Mapping) -> NoReturn:
		"""
		Used by pickling. Needed because of custom __getattr__ functionality
		"""

		self.__dict__.update(d)



class DotProxy(DotAccess):
	def __init__(self, obj):
		object.__setattr__(self, '___dot_object', obj)


	def __getattr__(self, attr, default = None):
		return getattr(object.__getattribute__(self, "___dot_object"), attr)


	def __dir__(self):
		return [*set(object.__dir__(self) + dir(object.__getattribute__(self, "___dot_object")))]



class DotNone(DotAccess):
	def __getattr__(self, attr):
		return None


def prep_dotdict(di): # Done outside of DotDict to prevent clogging the .namespace
	try:
		di = di.copy() if hasattr(di, "copy") else {}
	except Exception as e:
		breakpoint()
		pass

	# Checks to make sure keys are strings
	for key in di:
		try:
			assert isinstance(key, str)
		except AssertionError as e:
			raise ValueError(f"DotDict key must be a str (Given: {key})")

	return di


class DotDict(MutableMapping, DotAccess):
	"""
	A class that wraps a dictionary allowing for dot write/access

	If an attribute is not in the internal storage dict, return None

	So, with di = {"key": "val"}: di.key == "val"; dict.not_a_key is None
	"""

	def __init__(self, di = None):
		"""
		A DotDict instance containing a dictionary with values

		Keys must be strings

		:param dictionary: The dictionary to store in the DotDict instance
		:raises ValueError: Raised if one of the given dict keys is not a string
		"""

		di = prep_dotdict(di)

		# Applies the given dict into the DotDict
		object.__setattr__(self, '_dict', di or {})


	def __dir__(self):
		return object.__dir__(self) + [*self._dict.keys()]
		
		
	def __getitem__(self, idx: str) -> Any:
		"""
		Gets element from DotDict's internal storage dict

		:param idx: The element to get
		:returns: The associated element in the internal dict
		"""

		return self._dict[idx]


	def __setitem__(self, idx: str, value: Any) -> NoReturn:
		"""
		Sets the DotDict's internal storage dict key to a given value

		:param idx: The idx of the dict to set
		:param value: The value for the given idx
		:raises ValueError: Raised if the given idx is not a string
		"""

		if not isinstance(idx, str):
			raise ValueError(f"DotDict key must be a str (Given: {idx})")

		self._dict[idx] = value


	def __delitem__(self, idx: str) -> NoReturn:
		"""
		Removes element from storage dict at given index

		:param idx: The index to remove from the dict
		"""

		del self._dict[idx]


	def __iter__(self) -> Iterator:
		"""
		Iterates over internal storage dict

		:returns: An iterator of the internal storage dict
		"""

		return iter(self._dict)


	def __len__(self) -> int:
		"""
		Gets the length of the internal storage dict

		:returns: The length of the internal storage dict
		"""

		return len(self._dict)

	
	def __getattr__(self, attr: str, default: Any = None) -> Any:
		"""
		Get element from the internal storage dict via object attribute access

		:param attr: The attribute to access
		:param default: If the attribute doesn't exist, return this instead
		:returns: Either the element in the internal dict, or else the default value
		"""

		return self._dict.get(attr, default)
		

	def __setattr__(self, attr: str, value: Any) -> NoReturn:
		"""
		Set element in the internal storage dict via object attribute access

		:param attr: The name of hte attribute to set
		:param value: The value of the attribute being set
		"""

		if not isinstance(attr, str):
			raise ValueError(f"DotDict key must be a str (Given: {attr})")

		self._dict[attr] = value
		

	def __str__(self) -> str:
		"""
		Shows the internal storage dict

		:returns: The string representation of hte internal storage dict
		"""

		return str(self._dict)
		

	def __repr__(self) -> str:
		"""
		Shows the internal storage dict, prefixed by the name of the class

		:returns: The internal storage dict, prefixed by the name of the class
		"""

		return f"{self.__class__.__name__}:{self.__str__()}"
		

	def __or__(self, other: Mapping) -> DotDict:
		"""
		Provides a way for merging DotDicts via the "|" operator

		:param other: The mapping being merged into this DotDict
		:returns: A dot dict with this and other's dicts merged
		"""

		if isinstance(other, Mapping):
			return self.__class__({**self._dict, **other})

		return NotImplemented


	def __ior__(self, other: Mapping) -> DotDict:
		"""
		Provides a way for in-place merging of DotDicts via the "|=" operator

		:param other: The mapping being merged into this DotDict
		:returns: A dot dict with this and other's dicts merged
		"""

		return self.__or__(other)


	def __ror__(self, other: Mapping) -> DotDict:
		"""
		Provides a way for in-place merging of DotDicts via the "|=" operator when DotDict is to the right of the pipe

		:param other: The mapping this DotDict is being merged into
		:returns: A dot dict with other and this's dicts merged
		"""

		if isinstance(other, Mapping):
			return self.__class__(other | self._dict)

		return NotImplemented


	#def __copy__(self):
		#return self.__class__(copy.deepcopy(self._dict))