import operator, copy, inspect, re
from typing import Any, TYPE_CHECKING, Sequence, Self

import dag
from dag.lib import comparison



### MAGIC METHOD PROCESSOR

def apply_descritpor_to_magic_methods(descriptor, cls):
	for op in (x for x in dir(operator) if x.startswith("__")):
		if op == "__call__": # for python 3.11
			continue

		oper = getattr(operator, op)
		trimmed_op = op[2:]

		try:
			setattr(cls, f"__{trimmed_op}", descriptor(op))
			setattr(cls, f"__r{trimmed_op}", descriptor(f"__r{trimmed_op}"))
		except TypeError:
			continue




### ATTR RECORDERS

class AttributeAccessRecord:
	def __init__(self, attr_name, attr_recorder):
		#super().__init__(attr_name)
		self.attr_name = attr_name
		self.attr_recorder = attr_recorder
		self.root = attr_recorder # Redundant bc sometimes I look for "root instead of attr_recorder"

		# These gets populated if __called__
		self.is_called = False
		self.args = []
		self.kwargs = {}


	def get_item(self, item_to_access):
		from dag.util.lambdabuilders import LambdaBuilder

		item_to_access = dag.nab_if_nabber(item_to_access)
		gotten_item = getattr(item_to_access, self.attr_name, None)

		if self.is_called or self.args or self.kwargs:
			args = dag.nab_if_nabber(self.args)
			args = list(args)
			for i, arg in enumerate(args):
				try:
					args[i] = arg.format(**dag.ctx.parsed)
				except Exception as e:
					continue

			kwargs = dag.nab_if_nabber(self.kwargs)
			for k, v in kwargs.items():
				try:
					kwargs[k] = v.format(**dag.ctx.parsed)
				except:
					continue

			# Hacky because strings don't have __radd__
			if gotten_item is None and self.attr_name == "__radd__":
				return args[0] + item_to_access

			match self.attr_name:
				case "__or__":
					return item_to_access or args[0]
				case "__ior__":
					return args[0] or item_to_access
				case "__and__":
					return item_to_access and args[0]
				case "__iand__":
					return args[0] and item_to_access
				case "__invert__" | "__inv__":
					return not item_to_access

			with dag.catch() as e:
				for i, arg in enumerate(args):
					# If two lambdabuilders are being used in the same expression, evaulate here. (e.g.: r_.site_id + r_.id)
					if isinstance(self.attr_recorder, LambdaBuilder) and isinstance(arg, LambdaBuilder) and dag.ctx.active_lambdabuilder_root:
						args[i] = args[i](dag.ctx.active_lambdabuilder_root)

				return gotten_item(*args, **kwargs)

		return gotten_item


	def __repr__(self):
		return f"<{self.attr_name =} {object.__repr__(self)}>"


	# Generates a new instance so that nabbers built off AttriuteAccessNabber don't all have the same args as eachother after one is called
	def __call__(self, *args, **kwargs):
		new_nabber = type(self)(self.attr_name)
		new_nabber.is_called = True
		new_nabber.args = args
		new_nabber.kwargs = kwargs

		return new_nabber



class AttrRecorderDescriptor:
	def __init__(self, attrname: str):
		"""
		An instance of the descriptor, keeping track of the attr name

		:param attrname: The name of the attr to store
		"""

		self.attrname = attrname


	def __get__(self, recorder: object, recordercls = type[object]) -> Any:
		return getattr(recorder, self.attrname)
		if recorder._is_should_store_attribute():
			recorder = maybe_setup_recorder(recorder)
			return record_attr(recorder, self.attrname)

		return object.__getattribute__(recorder, self.attrname)		



def record_attr(attr_recorder, attr):
	if attr_recorder._stored_attrs is None:
		attr_recorder._stored_attrs = []

	attr_recorder._stored_attrs.append(AttributeAccessRecord(attr, attr_recorder))
	return attr_recorder


def maybe_setup_recorder(recorder):
	if recorder._stored_attrs is None:
		recorder = copy.copy(recorder) # Generate a new Attr Recorder for each new attempted attr
		recorder._stored_attrs = []

	return recorder


def process_stored_attrs(recorder, item):
	return get_stored_attrs(item, recorder._stored_attrs)


def get_stored_attrs(root, attrs):
	item = root

	for record in (attrs or []):
		item = record.get_item(item)

	return item




class AttrRecorder(dag.dot.DotAccess):
	_stored_attrs = None # Done this way so don't need to call __init__, allowing for better mixing in. None so that class-level array won't accidentally get loaded with stuff


	def _is_should_store_attribute(self) -> bool:
		return True


	def _is_skip_store_attribute_on_call(self) -> bool:
		"""This is in place so that dag.nab(blah) properly stores the blah"""
		return False


	def __getattr__(self, attr: str) -> object:
		# If should store attributes: Store the attribute
		if self._is_should_store_attribute():
			recorder = maybe_setup_recorder(self)
			return record_attr(recorder, attr)

		# Else, should NOT store attributes: get the attribute like normal
		return object.__getattribute__(self._process_root(), attr)


	def _process_root(self) -> Self:
		return self


	def _isin_(self, lst: Sequence) -> bool:
		"""Used as the opposite of __contains__"""
		breakpoint()
		return self in lst


	def __call__(self, *args, **kwargs):
		# If this recorder is not a Lambda builder, has its last stored attr is a magic method, and the arg is a LambdaAbuilder: Swap this AttrRecorder with the LambdaBuilder
		# E.G. {nabber} > {r_...} will turn to {r_...} < {nabber}
		# This means that the call will return the lambdabuilder instead of the nabber
		from dag.util.lambdabuilders import LambdaBuilder

		if not isinstance(self, LambdaBuilder) and self._stored_attrs and args and self._stored_attrs[-1].attr_name.startswith("__") and isinstance(args[0], LambdaBuilder):
			lambdabuilder = args[0]
			attrname = self._stored_attrs.pop(-1).attr_name

			if attrname == "__contains__":
				attrname = "_isin_"
			else:
				attrname = comparison.opposites.get(attrname, attrname)

			record_attr(lambdabuilder, attrname)
			mark_last_access_record_as_called(lambdabuilder, self)
			return  lambdabuilder

		if self._is_should_store_attribute() and not self._is_skip_store_attribute_on_call():
			recorder = maybe_setup_recorder(self)

			if not recorder._stored_attrs:
				record_attr(recorder, "__call__")

			mark_last_access_record_as_called(recorder, *args, **kwargs)

			return recorder

		return self._do_call(*args, **kwargs)


	def _do_call(self, *args, **kwargs):
		return self

apply_descritpor_to_magic_methods(AttrRecorderDescriptor, AttrRecorder)


def mark_last_access_record_as_called(recorder, *args, **kwargs):
	last_access_record = recorder._stored_attrs[-1]
	last_access_record.is_called = True
	last_access_record.args = args
	last_access_record.kwargs = kwargs




def get_callframe(total = 2):
	frame = inspect.currentframe()

	for i in range(total):
		frame = frame.f_back

	filename = frame.f_code.co_filename
	lineno = frame.f_lineno

	#if filename == "<stdin>" and lineno == 1:
	#	return None

	return (filename, lineno)


def record_callframe(recorder):
	recorder = copy.copy(recorder)
	recorder.callframe = get_callframe(3)
	return recorder




class AttrRecorderDescriptorWithCallframe(AttrRecorderDescriptor):
	def __get__(self, recorder: object, recordercls = type[object]) -> object:
		if recorder._stored_attrs is None:
			recorder = record_callframe(recorder)

		if recorder._is_should_store_attribute(3):
			recorder = maybe_setup_recorder(recorder)
			recorder = record_attr(recorder, self.attrname)
			return recorder

		return object.__getattribute__(recorder, self.attrname)		



class AttrCallframeRecorder(AttrRecorder):
	callframe = None

	def _is_should_store_attribute(self, nback = 4):
		nback = dag.ctx.callframe_nback or nback
		callframe = get_callframe(nback)

		#while nback and 'frozen' in callframe[0]: # This is in place bc apps and mods need different nbacks
		#	nback -= 1
		#	callframe = get_callframe(nback)

		return callframe == self.callframe


	def __getattr__(self, attr):
		with dag.ctx(attr = attr):
			if self._stored_attrs is None:
				recorder = record_callframe(self)
				return AttrRecorder.__getattr__(recorder, attr)

			return super().__getattr__(attr)


	def __call__(self, *args, **kwargs):
		if self._stored_attrs is None:
			recorder = record_callframe(self)
			return AttrRecorder.__call__(recorder, *args, **kwargs)

		return super().__call__(*args, **kwargs)


apply_descritpor_to_magic_methods(AttrRecorderDescriptorWithCallframe, AttrCallframeRecorder)










### ATTR ACCESS IGNORERS
class IgnoreAttrDescriptor:
	def __init__(self, attrname: str):
		"""
		An instance of the descriptor, keeping track of the attr name

		:param attrname: The name of the attr to store
		"""

		self.attrname = attrname


	def __get__(self, obj: object, cls = type[object]) -> Any:
		return obj


class AttributeAccessIgnorer:
	# This is something that takes attr attributes/calls and doesn't do anything

	def __getattr__(self, attr):
		return self

	def __call__(self, *args, **kwargs):
		return self

apply_descritpor_to_magic_methods(IgnoreAttrDescriptor, AttributeAccessIgnorer)