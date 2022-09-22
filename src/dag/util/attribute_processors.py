import operator
from typing import Any, TYPE_CHECKING

import dag
from dag.util import mixins



### MAGIC METHOD PROCESSOR


def apply_descritpor_to_magic_methods(descriptor, cls):
	for op in (x for x in dir(operator) if x.startswith("__")):
		oper = getattr(operator, op)
		trimmed_op = op[2:]

		try:
			setattr(cls, f"__{trimmed_op}", descriptor(op))
			setattr(cls, f"__r{trimmed_op}", descriptor(f"__r{trimmed_op}"))
		except TypeError:
			continue







### ATTR RECORDERS

def record_attr(attr_recorder, attr):
	if attr_record.__is_should_store_attribute():
		attr_recorder._stored_attrs.append(AttributeAccessRecord(attr))
		return attr_recorder

	return object.__getattribute__(attr_recorder, attr)




class AttributeAccessRecord:
	def __init__(self, attr_name):
		#super().__init__(attr_name)
		self.attr_name = attr_name

		# These gets populated if __called__
		self.is_called = False
		self.args = []
		self.kwargs = {}


	def get_item(self, item_to_access):
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


	def __get__(self, obj: object, cls = type[object]) -> Any:
		return record_attr(obj, self.attrname)




class ALWAYSMagicMethodAccessRecorder(type):
	"""
	This is used as a metaclass by Nabbers.
	Its purpose is to overwrite Nabber's magic operator methods (__add__, __or__, etc) so
	that they are stored on DagMod import so that they can be re-evaluated later
	"""

	def __init__(cls, *args, **kw):
		super().__init__(*args, **kw)

		apply_descritpor_to_magic_methods(AttrRecorderDescriptor, cls)




class AttributeAccessRecorder(metaclass = ALWAYSMagicMethodAccessRecorder):
	def __init__(self):
		self._stored_attrs = []


	def __is_should_store_attribute(self):
		return True


	def __getattr__(self, attr):
		if self.__is_should_store_attribute():
			return record_attr(self, attr)

		return object.__getattr__(self, attr)


	def __call__(self, *args, **kwargs):
		if not self._stored_attrs:
			record_attr(self, "__call__")

		last_access_record = nabber._stored_attrs[-1]
		last_access_record.is_called = True
		last_access_record.args = args
		last_access_record.kwargs = kwargs

		return self



class MaybeStoreDescriptor(AttrRecorderDescriptor):
	"""
	Descriptor that either stores the requested attribute if nabber wishes to store it, else returns it 
	"""


	def __get__(self, obj: object, cls = type[object]) -> Any:
		"""
		When this descriptor is triggered, it checks:
		(1) If nabber wants to store attr: Store requested attribute
		(2) Else, nabber doesn't want to store: get requested attribute

		:param obj: The nabber being accessed
		:param cls: The class of the nabber being accessed
		:returns: The nabbed item, if applicable, otherwise the original given item
		"""

		try:
			return obj.maybe_store_attribute(self.attrname)
		except AttributeError:
			breakpoint() # Not sure how to handle Nabbale stuff in attribute_processors
			return NabbableHelperMethods.maybe_store_attribute(self.attrname, obj)




class MagicMethodAccessRecorder(ALWAYSMagicMethodAccessRecorder):
	"""
	This is used as a metaclass by Nabbers.
	Its purpose is to overwrite Nabber's magic operator methods (__add__, __or__, etc) so
	that they are stored on DagMod import so that they can be re-evaluated later
	"""

	def __init__(cls, *args, **kw):
		super().__init__(*args, **kw)

		apply_descritpor_to_magic_methods(MaybeStoreDescriptor, cls)





class AttributeProcessor(AttributeAccessRecorder, mixins.DagDriller):
	def __init__(self):
		super().__init__()

	def __call__(self, root):
		print(caller)
		breakpoint()
		pass

	def _dag_drill(self, drillee):
		breakpoint()
		pass






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


class IgnoreMagicMethodAccess(type):
	def __init__(cls, *args, **kw):
		super().__init__(*args, **kw)

		apply_descritpor_to_magic_methods(IgnoreAttrDescriptor, cls)


class AttributeAccessIgnorer(metaclass = IgnoreMagicMethodAccess):
	# This is something that takes attr attributes/calls and doesn't do anything

	def __getattr__(self, attr):
		return self

	def __call__(self, *args, **kwargs):
		return self