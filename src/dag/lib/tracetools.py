import sys
from contextlib import contextmanager
from typing import Generator, Callable, Any
from dataclasses import dataclass


@contextmanager
def set_systrace(fn: Callable[..., Any]) -> Generator[None, None, None]:
	"""
	Sets the given fn as the current tracer. Reverts to the old tracer when finished

	A Tracer is a cpython debugging tool that executes on line-change, function call/return, etc.

	:param fn: The fn to set as the current code tracer
	"""

	try:
		old_settrace = sys.gettrace()
		sys.settrace(fn)
		yield
	finally:
		sys.settrace(old_settrace)


@dataclass
class FunctionCallBreakpointSetter:
	filepath: str
	lineno: int

	def __call__(self, frame, event, arg = None):
		"""
		Set a breakpoint if we have entered the right file and lineno
		"""

		# IF event is "call": Check to see if it's time to trigger the breakpoint
		#	NOTE: "call" has to be used so that code stepping works normally. Otherwise, it might get caught inside of a list/dict comprehension
		if event == "call":
			filepath = frame.f_code.co_filename
			lineno = frame.f_lineno # This is done bc something is updating the callframe with different linenumbers as it works down the module

			# <= lineno because sometimes self.lineno is where "def" was defined and lineno is where where the uppermost @decorator is defined (could be @dag.arg)
			if self.filepath == filepath and lineno <= self.lineno:
				sys.settrace(None)
				breakpoint()
				return None

		return self