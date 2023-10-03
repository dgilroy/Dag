import typing, inspect
from typing import Callable
from dataclasses import dataclass
import dag

def get_annotations(fn: Callable, argname: str = "", *, include_extras: bool = True) -> dict | typing.Annotated:
	if isinstance(fn, inspect.FullArgSpec):
		return fn.annotations
		
	if isinstance(fn, dag.lib.dummies.DummyNoArgCallable):
		return {}

	annotations = typing.get_type_hints(fn, include_extras = include_extras)

	return annotations.get(argname) if argname else annotations


def get_annotated_metadata(annotated):
	try:
		return annotated.__metadata__ # For typing.Annotated
	except AttributeError:
		return annotated.__args__ # For types.GenericAlias

def get_annotated_class(annotated):
	return annotated.__origin__

def parse_annotated(annotated):
	return get_annotated_class(annotated), get_annotated_metadata(annotated)




####>>>> Playing with a possible INT type that can cleanly hold min/max values
class INTMeta(type):
	def __gt__(cls, value):	return cls(min = value)
	def __lt__(cls, value):	return cls(max = value)


@dataclass
class INT(metaclass = INTMeta):
	min: int | None = None
	max: int | None = None

	def __gt__(self, value):
		self.min = value
		return self

	def __lt__(self, value):
		self.max = value
		return self


gg = 99 > INT > 3 # Doesn't work. It goes (99 > INT), gets True, and then checks (INT > 3)
gg2 = 99 > INT() > 3 # works bc INT is an object
