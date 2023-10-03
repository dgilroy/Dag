import random, shutil, tempfile, secrets, string, atexit
from tempfile import TemporaryDirectory
from pathlib import Path

import dag
from dag.cachefiles import DagCmdExCtxPersistenceFile


class TempDagCmdExCtxPersistenceFile(DagCmdExCtxPersistenceFile):
	def __init__(self):
		# Inititally set to "None" so that code is less likely to clutter /tmp with unneeded/forgotten tmp directories unless it is truly needed to be made
		self._tempdir = None
		self._root = None


	@property
	def tempdir(self):
		if self._tempdir is None:
			self._tempdir = tempfile.TemporaryDirectory(prefix = "dag-")

		return self._tempdir

	@property
	def root(self):
		if self._root is None:
			self._root = Path(self.tempdir.name)

		return self._root


	def get_folder_from_dagcmd_exctx(self, exctx):
		"""
		if self.tempdir is None:
			self.tempdir = tempfile.TemporaryDirectory(prefix = "dag-")
			self.root = Path(tempdir.name)
		"""

		return super().get_folder_from_dagcmd_exctx(exctx)



# The manager that writes/reads tempcache files
tempcachefiles = TempDagCmdExCtxPersistenceFile()


def clean() -> None:
	"""removes all tempcache files related to Dag instance"""
	if tempcachefiles.tempdir:
		tempcachefiles.tempdir.cleanup()



def generate_filepath(filename: str = ""):
	temprootpath = tempcachefiles.root
	filename = filename or dag.generate_password(spchars = "")

	return temprootpath / filename