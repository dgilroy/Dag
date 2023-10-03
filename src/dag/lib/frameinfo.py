import inspect, linecache, sys
from collections import namedtuple
from types import FrameType

CallFrameInfo = namedtuple("CallFrameInfo", "filepath lineno line coll_offset module")


def callframeinfo(frame: FrameType, fback: int = 1) -> tuple[str, int, str, int, object]:
	"""
	Since frame objects themselves are mutable, they can't be saved to a variable (Due to the fact that the variable stores a memory reference and the frame at that reference is prone to changing).
	Therefore, this function grabs the frameinfo that I want and stores it to a tuple

	:param frame: The frame to be inspected
	:param fback: The number of frames back to go from the given frame
	:returns: The frameinfo (filename, linenumber, codetext, column posiiton, module)
	"""

	for f in range(fback):
		frame = frame.f_back

	import dag
	#with dag.dtprofiler("frameinfo"):
	#	frameinfo = inspect.getframeinfo(frame) #<- This is too slow

	filepath = frame.f_code.co_filename
	lineno = frame.f_lineno # This is done bc something is updating the callframe with different linenumbers as it works down the module
	line = linecache.getline(filepath, lineno).strip()
	module = inspect.getmodule(frame.f_code)

	with dag.dtprofiler("codeposition"):
		lineno, endlineno, col_offset, end_col_offset = inspect._get_code_position(frame.f_code, frame.f_lasti)

	return CallFrameInfo(filepath, lineno, line, col_offset, module)