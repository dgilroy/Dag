import sys

import dag
from dag import this


@dag.mod("pathmanager", default_cmd = this.paths)
class PathManager(dag.DagMod):
	def __init__(self):
		super().__init__()
		self.infofile = dag.config.PATHINFO_FILE or dag.config.CONFIG_PATH / "pathinfo"


	@dag.arg.Directory("path", use_str = True)
	@dag.cmd(callback = this.paths)
	def add_path(self, path):
		"""Add a path to pathmanager"""
		sys.path.append(path) # May not work, am going to need a better way to handle __file__ stuff to get usable paths
		with dag.file.open(self.infofile, "a+", inside_dag = True) as file:
			file.write(f"{path}\n")

		return f"Path <c b>{path}</c> added to PathManager"


	@dag.collection(value = dag.nab.file.read_in_dag(this.infofile), type = dag.CSV("path"), idx = True, cache = False, display = this._view_paths)
	def paths(self):
		"""read added paths"""
		return


	def _view_paths(self, paths, formatter):
		for path in paths:
			formatter.add_row(path.path)


	@paths("path")
	@dag.cmd(callback = this.paths)
	def remove_path(self, path):
		paths = self.paths()

		with dag.file.open_in_dag(self.infofile, "w") as file:
			for p in paths:
				if p._dag.insertion_idx != path._dag.insertion_idx:
					file.write(f"{path.path}\n")

		return f"path <c b>{path}</c> removed"
