import enum


def build_enum(*args, **kwargs):
	"""
	A simple method that allows for the quick generation of Enums.

	Any string positional args will (1) have their text CAPIALIZED for the name, and (2) have their value match their list index value

	Any kwargs will (1) have their kwarg key CAPITALIZED for the name, and (2) Their kwarg value set as the enum value

	:param args: Any positional args to be put into the enum
	:param kwargs: Any positional args to be put into the enum
	"""

	data = {item.upper(): idx for idx,item in enumerate(args) if isinstance(item, str)} | {k.upper(): v for k,v in kwargs.items()}

	return enum.Enum("DagEnum", data)


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