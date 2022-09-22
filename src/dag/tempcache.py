import random, shutil, tempfile
from typing import NoReturn

import dag
from dag.persistence import DagCmdExCtxPersistenceFile


def get_tempcache_path(idno: int) -> str:		
	"""Returns the directory that stores Dag instance's tempcache files"""
	return dag.config.TEMPCACHE_DIR + f"/{idno}"


# Randomly generated temp ID that will store temp results
_tempcacheID = random.randint(0, 1e32-1)


# The manager that writes/reads tempcache files
TempCacheFile = DagCmdExCtxPersistenceFile(get_tempcache_path(_tempcacheID))


def clean() -> NoReturn:
	"""removes all tempcache files related to Dag instance"""

	assert _tempcacheID, "_tempcacheID must be specified for directory deletion to occur"
	shutil.rmtree(dag.ROOT_PATH / f"{dag.config.TEMPCACHE_DIR}/{_tempcacheID}", ignore_errors = True)