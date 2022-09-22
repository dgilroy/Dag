import dag

class TimeProfiler:
	def __init__(self):
		self.timestart = 0
		self.timeend = 0
		self.is_ended = False
		self.diff = 0

	def __enter__(self):
		self.timestart = dag.current_milli_time()
		return self


	def __exit__(self, type, value, traceback):
		self.timeend = dag.current_milli_time()
		self.diff = self.timeend - self.timestart
		self.is_ended = True

	def __repr__(self):
		return f"\n{object.__repr__(self)=}\n" + (f"DIFF: {self.diff}" if self.is_ended else "PROFILER IN PROGRESS") + "\n"