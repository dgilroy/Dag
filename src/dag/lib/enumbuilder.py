import enum
from typing import Self


class EnumBuilder:
	activeattr = ""

	def __getattr__(self, attr) -> Self:
	 	self.activeattr = attr
	 	return self


	def __call__(self, *args, **kwargs) -> enum.Enum:
		name = kwargs.get("_name", self.activeattr)

		# If name being used: set it here, while allowing for the fact that kwargs doesn't need to have "_name" set
		if name:
			kwargs["_name"] = name

		return build_enum(*args, **kwargs)




def build_enum(*args, _name: str = "DagEnum", **kwargs) -> enum.Enum:
	"""
	A simple method that allows for the quick generation of Enums.

	Any string positional args will (1) have their text CAPIALIZED for the name, and (2) have their value match their list index value

	Any kwargs will (1) have their kwarg key CAPITALIZED for the name, and (2) Their kwarg value set as the enum value

	:param args: Any positional args to be put into the enum
	:param _name: The name for the enum (Defaults to 'DagEnum')
	:param kwargs: Any positional args to be put into the enum
	"""

	data = {item.upper(): idx for idx,item in enumerate(args) if isinstance(item, str)} | {k.upper(): v for k,v in kwargs.items()}

	return enum.Enum(_name, data)


'''
class DagEnum:
	"""
	A simple class that allows for the quick generation of Enums.

	Any string positional args will (1) have their text CAPIALIZED for the name, and (2) have their value match their list index value

	Any kwargs will (1) have their kwarg key CAPITALIZED for the name, and (2) Their kwarg value set as the enum value
	"""

	def __new__(self, *args, **kwargs):
		data = {item.upper(): idx for idx,item in enumerate(args) if isinstance(item, str)} | {k.upper(): v for k,v in kwargs.items()}

		return enum.Enum
'''
