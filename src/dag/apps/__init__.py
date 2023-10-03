import sys
from os.path import dirname, basename, isfile
import glob

#from dag.util import dagdebug
#sys.breakpointhook = dagdebug.set_trace

modules = glob.glob(dirname(__file__)+"/*.py")
__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]



def __getattr__(attr):
	import dag

	try:
		return dag.defaultapp.get_dagcmd(attr)
	# EXCEPT ValueError: No such dagcmd found. Pass so that importer will search for filename of {attr}.py
	except ValueError as e:
		raise AttributeError() from e