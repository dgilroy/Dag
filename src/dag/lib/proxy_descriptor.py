from typing import Any

class ProxyDescriptor:
	"""
	Some objects hold important information within an internal storage object.

	This descriptor class provides a way to pretend that the internal object's
	values are part of the containing object. This is typically used to set
	the containing's object __dict__ with the internal object's keys/vals.
	This is used for tab-completion purposes in DagPDB

	So, with	(1) Containing object C holding internal object X
				(2) X.y == "z"
				(3) C.y is set to be this descriptor:
					Accessing C.y yields the value stored at C.X.y
	"""


	def __init__(self, internal_obj_name: str, attrname: str):
		"""
		An instance of the Proxy Descriptor, holding the name of the internal
		storage object holding the data, and the attribute that this PD instance
		is associated with

		:param internal_obj_name: The name of the object holding the data
									associated with this attribute
		:param attrname: The name of the attribute to access
		"""

		self.internal_obj_name = internal_obj_name
		self.attrname = attrname


	def __get__(self, obj: object, objtype = type[object]) -> Any:
		"""
		When code tries to access this descriptor, retrieve the object from
		the internal storage object

		:param obj: The object that this PD instance is a property of
		:param objtype: The class type of the object containing this PD
		:returns: The requested element from within the internal storage object
		:raises AttributeError: If the PD's attrname isn't in the internal storage
								object, then this raises an Exception
		"""

		internal_obj = getattr(obj, self.internal_obj_name)

		if not hasattr(internal_obj, self.attrname):
			raise AttributeError(f"ProxyDescriptor storage object doesn't have attribute '{self.attrname}'")

		return getattr(internal_obj, self.attrname)