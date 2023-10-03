import inspect, copy

def dummyfn(*args, **kwargs) -> None:
	pass


class DummyClass:
	pass


class DummyCallable:
	def __call__(self, *args, **kwargs) -> None:
		pass


class DummyNoArgCallable:
	def __call__(self) -> None:
		pass


def emptyfn() -> None:
	pass



def __getattr__(attr):
	if attr == "emptyargspec":
		# This is being used so each call for an emptyargspec gets a fresh copy
		return copy.copy(inspect.getfullargspec(emptyfn))
