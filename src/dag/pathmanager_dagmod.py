import sys

import dag


infofile = dag.PATHINFO_PATH

pathmanager = dag.app("pathmanager")


@pathmanager.collection.DEFAULT(value = dag.nab.file.read(infofile), formatter = dag.CSV("path"), cache = False)
def paths():
	"""read added paths"""
	return



@pathmanager.arg.Directory("path", use_str = True)
@pathmanager.cmd(callback = pathmanager.nab.paths)
def add_path(path):
	"""Add a path to pathmanager"""
	sys.path.append(path) # May not work, am going to need a better way to handle __file__ stuff to get usable paths
	with dag.file.open(infofile, "a+") as file:
		file.write(f"{path}\n")

	return f"Path <c b>{path}</c> added to PathManager"



@paths.display
def _view_paths(paths, formatter):
	for path in formatter.idxitems(paths):
		formatter.add_row(path.path)



@paths.arg("path")
@pathmanager.cmd(callback = paths)
def remove_path(path):
	paths = paths()

	with dag.file.open(infofile, "w") as file:
		for p in paths:
			file.write(f"{path.path}\n")

	return f"path <c b>{path}</c> removed"
