from __future__ import annotations

import operator, abc, os, copy, sys
from typing import Any, TYPE_CHECKING

import dag
from dag.util import attribute_processors




def nab_if_nabber(item: object) -> object:
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

	origitem = item

	if isinstance(item, Nabber):
		return nab_if_nabber(item.nab())

	elif isinstance(item, (list, tuple)):
		tempitems = []

		for el in item:
			tempitems.append(nab_if_nabber(el))

		# Done so that normal lists return themselves so that they can be appended, etc
		if item == tempitems:
			return item

		return item.__class__(tempitems)

	elif isinstance(item, (dict)):
		item = item.copy()
		for k, v in item.items():
			item[k] = nab_if_nabber(v)

	return item



class Nabber(attribute_processors.AttrCallframeRecorder):
	"""
	Nabbers allow for lazy evaluation of items while dagapps are being imported
	Lazily-stored items are evaluated when called later while program is running

	:abstractmethod: _nab
	"""

	def nab(self) -> Any:
		"""
		Initiates nabbing sequence

		:returns: The nabbed item
		"""

		item = self._nab()
		return self._process_stored_attrs(item)


	def _process_stored_attrs(self, item: object) -> object:
		return attribute_processors.process_stored_attrs(self, item)


	def _process_root(self):
		return self._nab()


	def _nab(self): 
		return self	# Allows for mixins to more-easily incorporate



class SimpleNabber(Nabber):
	def __init__(self, item):
		self.item = item

	def _nab(self):
		return self.item



#class DagNabber(Nabber):
class DagNabber(Nabber):
	nabbed_item = dag.UnfilledArg


	def _is_skip_store_attribute_on_call(self):
		# If no stored args and nabbed_item is unfilled, then assume this is being used as dag.nab(BLAH) for storing the BLAH
		return not self._stored_attrs and self.nabbed_item == dag.UnfilledArg


	def _do_call(self, *args, **kwargs):
		if args and not self._stored_attrs and self.nabbed_item == dag.UnfilledArg:
			nabber = copy.copy(self)
			nabber.nabbed_item = args[0]
			return nabber

		return super().do_call(*args, **kwargs)


	def _nab(self):
		if self.nabbed_item == dag.UnfilledArg:
			return dag

		return self.nabbed_item


	def __bool__(self):
		return bool(self.nabbed_item) if self.nabbed_item != dag.UnfilledArg else True


	def __dir__(self):
		return dir(dag)



class ResponseNabber(Nabber):
#class ResponseNabber(Nabber):
	def _nab(self):
		if "active_response" in dag.ctx:
			return dag.ctx.active_response

		return attribute_processors.AttributeAccessIgnorer() # This is done so that calls like response.blah.blah() don't complain like it would if this were returning True


class ArgsNabber(Nabber):
	argsval = dag.UnfilledArg

	def _nab(self):
		match self.argsval:
			case int():
				return list(dag.ctx.parsed.values())[self.argsval]
			case str():
				return dag.ctx.parsed[self.argsval]
			case _:
				return dag.DotDict(dag.ctx.parsed or {})


	def __call__(self, *args, **kwargs):
		if len(args) == 1 and isinstance(args[0], int) and not self._stored_attrs:
			newnabber = copy.copy(self)
			newnabber.argsval = args[0]
			return newnabber

		with dag.ctx(callframe_nback = 5):
			return super().__call__(*args, **kwargs)



class ResourcesNabber(ResponseNabber):
	def _process_stored_attrs(self, item):
		if "active_response" in dag.ctx or "active_resource" in dag.ctx:
			if not dag.ctx.active_resource: # Currently assumes active_resource isn't set when all resources need to be processed
				responses = []

				for resources in item:
					responses.append(super()._process_stored_attrs(resources))

				return all(responses)

			else: # TO BE USED for more complex label creation
				return super()._process_stored_attrs(dag.ctx.active_resource)

		return item


	def _nab(self):
		return dag.ctx.active_resource or super()._nab()


	def __call__(self, *args, **settings):
		#breakpoint("final" in args, trigger = "nhlgames")
		with dag.ctx(callframe_nback = 5):
			return super().__call__(*args, **settings)



# list of nabbers
nab = DagNabber()
response = ResponseNabber()
args = ArgsNabber()
resources = ResourcesNabber()





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