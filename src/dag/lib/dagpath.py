from pathlib import Path


pathtype = type(Path())

class DagPath(pathtype):
	def __contains__(self, otherpath: Path) -> bool:
		"""
		Checks whether a given path is contained within this path

		This lets 'DagPath("/wow") in DagPath("/")' return True

		:param otherpath: The path to check whether its inside this path
		:returns: Whether the given path is inside this path
		"""

		return self in otherpath.absolute().parents


	def unresolve(self):
		cwd = self.cwd()

		if self in cwd:
			pathstr = str(self).replace(str(cwd), ".")
			return type(self)(pathrstr)

		return self