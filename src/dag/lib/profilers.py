import time
from typing import Self


current_milli_time = lambda: int(round(time.time() * 1000))
current_micro_time = lambda: int(round(time.time() * 1000000))


class TimeProfiler:
	def __init__(self, name: str = "", lamb = None, times: int = 1, debug: bool = False):
		if not lamb:
			self.timestart = 0
			self.timeend = 0
			self.is_ended = False
			self.diff = 0

		self.debug = debug


	def __enter__(self):
		self.timestart = current_micro_time()
		return self


	def __exit__(self, type = None, value = None, traceback = None) -> None:
		self.timeend = current_micro_time()
		self.diff = (self.timeend - self.timestart)/1000
		self.is_ended = True

		if self.debug:
			breakpoint()
			pass


	def __repr__(self) -> str:
		return f"\n{object.__repr__(self)=}\n" + (f"DIFF: {self.diff/1000:.3}ms" if self.is_ended else "PROFILER IN PROGRESS") + "\n"


	def __call__(self, lamb, times: int = 1) -> Self:
		### NOTE THIS IS WAY SLOWER THAN CONTEXT MANAGER BC LAMBDA IS SLOWER THAN A PLAIN EXPRESSION ###
		self.__enter__()
		for i in range(times):
			lamb()
		self.__exit__()
		return self	



class CallCountProfiler:
	def __init__(self):
		self.calls = {}

	def __call__(self, callname: str) -> None:
		callcount = self.calls.get(callname, 0)
		self.calls[callname] = callcount + 1

callcounter = CallCountProfiler()