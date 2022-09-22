from __future__ import annotations

import operator, abc, os
from typing import Any, TYPE_CHECKING

import dag
from dag.util.attribute_processors import MagicMethodAccessRecorder, AttributeAccessIgnorer, AttributeAccessRecord




def nab_if_nabber(item: Any) -> Any:
	"""
	This nabs any nabbable elements, and ignores them otherwise

	Given the item:
		(1) If it's a Nabber, Nab the item
		(2) If it's a tuple/list, iterate through and nab any nabbers
		(3) If it's a dict, iterate through the values and nab any nabbers
		(4) Else: Return as normal

	This can handle nested lists/tuples/dicts

	:param item: The item to nab, if it's a nabber
	:returns: The nabbed item, if applicable, otherwise the original given item
	"""

	if isinstance(item, Nabber):
		return nab_if_nabber(item.nab())
	elif isinstance(item, Nabbable):
		return NabbableHelperMethods.nab_nabbable(item)

	elif isinstance(item, (list, tuple)):
		tempitems = []
		for el in item:
			tempitems.append(nab_if_nabber(el))

		return item.__class__(tempitems)

	elif isinstance(item, (dict)):
		item = item.copy()
		for k, v in item.items():
			item[k] = nab_if_nabber(v)

	return item




class NabbableHelperMethods:
	"""
	This is to help keep the attribute footprint of nabbables small
	"""

	@classmethod
	def maybe_store_attribute(cls, attr, nabbable):
		if is_should_store_attribute():
			return cls.store_attribute(attr, nabbable)

		return object.__getattribute__(nabbable, attr)


	@classmethod
	def store_attribute(cls, attr, nabbable):
		accesslist_nabber = AttrAccessListNabber(root = nabbable)
		accesslist_nabber.append_access_record(attr)
		return accesslist_nabber


	@staticmethod
	def nab_nabbable(nabbable: Nabbable, stored_attrs = None):
		nabber = Nabber()
		nabber._nab = nabbable._nab
		return nabber.nab(stored_attrs or [])


def is_should_store_attribute():
	return dag.ctx.DAG_DECORATOR_ACTIVE


def format_val(val):
	val = nab_if_nabber(val)

	try:
		for arg in dag.ctx.parsed.values():	
			if isinstance(arg, dag.DTime) and (formatstr := dag.ctx.active_dagcmd.settings.dateformat) and arg.formatstr == dag.DTime.default_formatstr:
				arg.formatstr = formatstr

		return val.format(**(dag.ctx.parsed or {}))
	except (AttributeError, TypeError) as e:
		return val



class NabberBase:
	pass



class Nabbable(NabberBase, metaclass = MagicMethodAccessRecorder):
	"""
	A lightweight mixin for nabbers that don't need to modify Nabber internal mechanics
	This stores attrs into an AttrAccessList, and implements a _nab method that handles nabbing
	"""

	def __getattr__(self, attr):
		return NabbableHelperMethods.maybe_store_attribute(attr, self)

	def _nab(self):
		return self



class Nabber(NabberBase, dag.dot.DotAccess, metaclass = MagicMethodAccessRecorder):
	"""
	Nabbers allow for lazy evaluation of items while dagmods are being imported
	Lazily-stored items are evaluated when called later while program is running

	:abstractmethod: _nab
	"""

	always_store_attr = False

	def __init__(self):
		"""
		An instance of a Nabber. Nabbers can be given values that will be formatted against parsed args
		So, if "date" is a parsed arg, and val is "{date}", then the val will be turned into that date arg value

		:param val: The value to evaluate before nabbing
		"""

		# Used for drilling later
		self.stored_attrs = []
		

	def nab(self, stored_attrs: Optional[list[AttributeAccessRecord]] = None) -> Any:
		"""
		Initiates nabbing sequence

		:returns: The nabbed item
		"""

		stored_attrs = stored_attrs or self.stored_attrs

		item = self._nab()

		if self.is_should_process_stored_args(item):
			return self.process_stored_attrs(item, stored_attrs)

		return item


	def is_should_store_attribute(self):
		return self.always_store_attr or is_should_store_attribute() # Done this way so subclasses may be able to override this in the future


	def is_should_process_stored_args(self, item):
		return True


	def process_stored_attrs(self, item, stored_attrs):
		for attr in stored_attrs:
			item = attr.get_item(item)

		return item


	def _nab(self): 
		return self	# Allows for mixins to more-easily incorporate


	def __getattr__(self, attr):
		return self.maybe_store_attribute(attr)

		
	def format_val(self, val):
		return format_val(val) # Done this way so that Nabber subclasses may be able to override this in the future

		
	def maybe_store_attribute(self, attr):
		if self.is_should_store_attribute():
			return self.store_attribute(attr)

		return object.__getattribute__(self, attr)


	def store_attribute(self, attr):
		nabber = self.get_nabber_for_storing()
		nabber.append_access_record(attr)
		return nabber	


	def append_access_record(self, attr):
		self.stored_attrs.append(AttributeAccessRecord(attr))


	def get_nabber_for_storing(self):
		return AttrAccessListNabber(root = self)


	def __call__(self, *args, **kwargs):
		if self.is_should_store_attribute():
			nabber = self

			if not self.stored_attrs:
				nabber = self.get_nabber_for_storing()
				nabber.append_access_record("__call__")

			last_access_record = nabber.stored_attrs[-1]
			last_access_record.is_called = True
			last_access_record.args = args
			last_access_record.kwargs = kwargs

			return nabber

		breakpoint()
		pass



class AttrAccessListNabber(Nabber):
	def __init__(self, root = None):
		super().__init__()
		self.root = root


	def _nab(self):
		if isinstance(self.root, Nabber):
			return self.root.nab(self.stored_attrs)
		elif isinstance(self.root, Nabbable):
			return NabbableHelperMethods.nab_nabbable(self.root, self.stored_attrs)

		raise ValueError("Root Nabber must be a Nabber")


	def get_nabber_for_storing(self):
		return self


	def process_stored_attrs(self, item, stored_attrs):
		# passing stored_attrs in nab() makes the root process handle this, so just return item
		return item
		




class DagNabber(MagicMethodAccessRecorder):
	def __getattr__(cls, attr):
		return getattr(nab(dag), attr)

	def __dir__(cls):
		return dir(dag)



class nab(Nabbable, metaclass = DagNabber):
	def __init__(self, value):
		self.value = value

	def __getattr__(self, attr):
		nabberlist = NabbableHelperMethods.store_attribute(attr, self)
		nabberlist.always_store_attr = True # make dag.nab special in that it generates nabbers whether or not @decorators active
		return nabberlist


	def __call__(self, *args, **kwargs):
		return self.__getattr__("__call__")(*args, **kwargs)


	def _nab(self):
		return format_val(self.value)

	def __bool__(self):
		return bool(self.value)




class _DagmodNabber(Nabber):
	def _nab(self):
		return dag.ctx.active_dagcmd.settings._dag_thisref



class ResponseNabbable(Nabbable):
	def _nab(self):
		if "active_response" in dag.ctx:
			return dag.ctx.active_response

		return AttributeAccessIgnorer() # This is done so that calls like response.blah.blah() don't complain like it would if this were returning True

		#breakpoint()
		#return True

	"""
	def process_stored_attrs(self, item, stored_attrs):
		if "active_response" not in dag.ctx:
			breakpoint()
			return True

		return super().process_stored_attrs(item, stored_attrs)
	"""


# list of nabbers
this = _DagmodNabber()
response = ResponseNabbable()











class NabbableSettings(dag.dot.DotDict):
	"""
	An extension of DotDict that triggers Nabbers whenver they are accessed via dot notation

	So, with settings['nabber'] being a Nabber: settings['nabber'] returns the nabber; settings.nabber runs the Nabber
	This allows for safer ways to check the dict's values without wasting time/network firing nabbers
	"""

	def __getattr__(self, attr):
		return self.getnab(attr)

	def getnab(self, attr, default = None):
		item = nab_if_nabber(self.get(attr))

		return item if item is not None else default

	def copy(self):
		return self.__class__(self._dict.copy())