import abc
import dill
from dag.lib.dtime import DTime


class DagLaunchable(abc.ABC):
	@abc.abstractmethod
	def _dag_launch_item():
		raise NotImplementedError


class CacheFileNamer(abc.ABC):
	@abc.abstractmethod
	def _dag_cachefile_name():
		raise NotImplementedError
		
CacheFileNamer.register(DTime)


class DagStyleFormattable(abc.ABC):
	@abc.abstractmethod
	def _dag_formatter_fn():
		raise NotImplementedError


class DagFiltable: pass


class DagDrillable:	pass


class DagDriller:
	@abc.abstractmethod
	def _dag_drill(self, drillee):
		raise NotImplementedError


class Alistable: pass



# Used by NabbableSettings to know to populate with active dagmod
class DagDecortorDagmodUtility:
	dagmod = None


class DagCompletable(abc.ABC):
	@abc.abstractmethod
	def complete(self, incmd):
		pass

	def _dag_modify_completion_text(self, text):
		return text



@dill.register(abc.ABCMeta)
def save_abc(pickler, obj):
	from pickle import _Pickler as StockPickler
	StockPickler.save_type(pickler, obj)