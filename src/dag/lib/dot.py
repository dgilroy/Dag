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
	_dag_proxies = None

	def __init__(self, *args):
		for item in args:
			self._add_proxy(item)


	def _add_proxy(self, item):
		if self._dag_proxies is None:
			self._dag_proxies = []

		self._dag_proxies.append(item)

		try:
			cls = self.__class__
			currentbases = (cls,) + cls.__bases__

			itemtype = type(item)

			if itemtype in currentbases:
				return

			#self.__class__ = type(cls.__name__, currentbases + (itemtype,), {}) #<- Was leading to class properties overwriting item's instance properties
		except:
			pass


	def __getattr__(self, attr):
		if self._dag_proxies is None:
			self._dag_proxies = []

		for proxy in self._dag_proxies:
			try:
				return getattr(proxy, attr)
			except AttributeError:
				continue

		raise AttributeError(f"Attribute \"<c bu / {attr}>\" Not found")


	def __dir__(self):
		if self._dag_proxies is None:
			self._dag_proxies = []

		items = set(object.__dir__(self))

		for proxy in self._dag_proxies:
			items |= set(dir(proxy))

		return items


	def __instancecheck__(self, instance):
		if self._dag_proxies is None:
			self._dag_proxies = []

		return isinstance(instance, type(self)) or any(x for x in self._dag_proxies if isinstance(instance, type(x)))




class DotNone(DotAccess):
	def __getattr__(self, attr):
		return None


def prep_dotdict(di): # Done outside of DotDict to prevent clogging the .namespace
	di = di or {}

	try:
		#di = di.copy() if hasattr(di, "copy") else {}
		di = copy.copy(di)
	except Exception as e:
		breakpoint()
		pass

	# Checks to make sure keys are strings
	for key in di:
		try:
			assert isinstance(key, str)
		except AssertionError as e:
			raise ValueError(f"DotDict key must be a str (Given: {key})") from e

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
		"""
		Append internal dict's keys to this object's dir entries
		"""

		return object.__dir__(self) + [*self._dict.keys()]
		
		
	def __getitem__(self, idx: str) -> object:
		"""
		Gets element from DotDict's internal storage dict

		:param idx: The element to get
		:returns: The associated element in the internal dict
		"""

		return maybe_make_dotdict(self._dict[idx], self)


	def __setitem__(self, idx: str, value: object) -> None:
		"""
		Sets the DotDict's internal storage dict key to a given value

		:param idx: The idx of the dict to set
		:param value: The value for the given idx
		:raises ValueError: Raised if the given idx is not a string
		"""

		if not isinstance(idx, str):
			raise ValueError(f"DotDict key must be a str (Given: {idx})")

		self._dict[idx] = value


	def __delitem__(self, idx: str) -> None:
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

		return maybe_make_dotdict(self._dict.get(attr, default), self)
		

	def __setattr__(self, attr: str, value: Any) -> NoReturn:
		"""
		Set element in the internal storage dict via object attribute access

		:param attr: The name of hte attribute to set
		:param value: The value of the attribute being set
		"""

		if not isinstance(attr, str):
			raise ValueError(f"DotDict key must be a str (Given: {type(attr)} = {attr})")

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



def maybe_make_dotdict(item: object, dotdict: DotDict) -> object:
	"""
	If given item is a dict, turns it into the type of the given dotdict

	:param item: The item to maybe convert into a dotdict
	:param dotdict: The dotdict whose type the item should be derived from
	:returns: The item, possibly converted into a dotdict
	"""

	# IF is dict: Try turning into dotdict
	if isinstance(item, dict):
		try:
			return type(dotdict)(item)
		# EXCEPT ValueError: dict had a key that wasn't a string, so don't convert to dotdict
		except ValueError:
			pass

	return item