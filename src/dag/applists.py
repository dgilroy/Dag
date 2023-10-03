from collections import UserList
from contextlib import contextmanager

import dag
from dag import dagargs, idxlists


#>>>> AppListManager
class AppListManager:
	def __init__(self, app):
		self.app = app
		self.applists = {}

	def __getattr__(self, attr):
		return self.applists.get(attr.lower(), AppList(attr, self))
# <<<< AppListManager


#>>>> AppList
class AppList(idxlists.IdxList):
	def __init__(self, name, manager):
		super().__init__()
		self.name = name.lower()
		self.manager = manager


	@contextmanager
	def item(self, item, formatter):
		self.manager.applists.setdefault(self.name.lower(), self).append(item) # Only once you call "item" will the templist get added to the manager
		with formatter.templistitem(item, self) as item:
			yield item
#<<<< AppList


#>>>> TempListManager
class TempListManager:
	def __init__(self, applistmanager: AppListManager):
		self.applistmanager = applistmanager
		self.app = self.applistmanager.app
		self.templist = []

	def __getattr__(self, attr: str) -> "TempList":
		applist = getattr(self.applistmanager, attr.lower())
		return TempList(applist, self)
#<<<< TempListManager


#>>> TempList
class TempList(dag.DotProxy):
	def __init__(self, applist: AppList, templistmanager: TempListManager):
		super().__init__(applist)
		self.applist = applist
		self.templistmanager = templistmanager


	def arg(self, *names, **settings):
		return dagargs.TempListDagArg(*names, templistname = self.applist.name, templistapp = self.templistmanager.app, **settings)


	@contextmanager
	def item(self, *args, **kwargs):
		self.templistmanager.templist = self # Sets this to the current 

		with self.applist.item(*args, **kwargs):
			yield
#<<<< TempList