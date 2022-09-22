from __future__ import annotations

import copy
from collections import namedtuple
from collections.abc import Mapping, MutableMapping
from typing import Any

import dag




class DagCmdTable(Mapping, dag.dot.DotAccess):
	"""
	Note, this is made to be case-insensitive
	"""

	def __init__(self, owner: DagCmdBase, root = None, parent = None, name = "", **settings):
		self._subcmds = {}
		self.subcmdtable = self # For easier parsing

		self.owner = owner
		self.root = root if root is not None else self
		self.parent = parent
		self.name = name

		self.settings = dag.DotDict(settings or {})
		self.settings.setdefault("complete", True)
		self.settings.setdefault("ignore_duplicates", False)

		self.children = dag.DotDict()

		self.table_containing = {}

		if self.root is self:
			self.register_child("innercmds")
			self.register_child("subcmds")
			self.register_child("parentcmds", ignore_duplicates = True)


	def __getitem__(self, idx):
		idx = idx.lower()
		value = self._subcmds[idx]
		return self.owner._get_subcmd(idx, value)


	def getraw(self, idx):
		return self._subcmds[idx]


	def rawvalues(self):
		for key in self.keys():
			yield self.getraw(key)


	def rawitems(self):
		return [(k, self.getraw(k)) for k in self.keys()]


	def __contains__(self, idx):
		return idx in self._subcmds

	def __iter__(self): return iter(self._subcmds)
	def __len__(self): return len(self._subcmds)


	def __getattr__(self, attr):
		try:
			return self.children[attr]
		except KeyError:
			raise AttributeError(f"DagCmdBase Table doesn't have child named \"<c b u>{attr}</c b u>\"")


	def __dir__(self):
		return [*set(object.__dir__(self) + [*self.children.keys()])]


	# For when need to check settings
	def _iter(self, return_names = False):
		for idname, idval in self.items():
			if isinstance(idval, Mapping):
				yield from self._iter(idval, return_names)
			else:
				if return_names:
					yield idname
				else:
					yield idval


	def names(self):
		return [*self.keys()]

	def get_completion_names(self):
		return [n for n in self.names() if self.table_containing[n].settings.complete]

	def identifiers(self):
		return [*self.values()]


	def add(self, dagcmd: DagCmdBase, name = None):
		# Can't add dagcmd directly to root table
		if self is self.root: # "is" because comparing table items, so any empty tables are == eachother
			raise TypeError("Cannot add dagcmd directly to root subcmdtable. Please add to a child, registering the child first it if necessary")

		# Can't have same dagcmd in table
		name = str(name if name is not None else dagcmd.name).lower()
		if name in self.root:
			if self.settings.ignore_duplicates:
				return
			else:
				if not dag.ctx.is_reloading_dagmod:
					raise ValueError(f"Item \"{name}\" already registered in IDTable in child {self.table_containing[name].name}")

		# Add dagcmd to list of identifiers
		self._subcmds[name] = dagcmd
		self.table_containing[name] = self

		# Add dagcmd info to all parent tables
		# Note: Since can't add() to root, this table always has a parent 
		table = self
		parent = self.parent

		while parent is not None:
			parent._subcmds[name] = dagcmd
			parent.table_containing[name] = table
			parent = parent.parent

		return self




	def remove(self, name):
		if name not in self:
			return

		table = self.table_containing.get(name)

		while table is not None:
			table._subcmds.pop(name, None)
			table.table_containing.pop(name, None)
			table = table.parent

		return self


	def maybe_register_child(self, name, **settings):
		# If already registered, ignore
		if name in self.children:
			return self.children[name]

		return self.register_child(name, **settings)


	def register_child(self, name, **settings):
		self.children[name] = DagCmdTable(self.owner, root = self.root, parent = self, name = name, **(self.settings | settings))
		return self.children[name]


	def drop(self):
		self.clear()

		if self.parent:
			self.parent.children.pop(self.name, None)

		return self


	def populate(self, infodict):
		for dagcmd_name, dagcmd in infodict.items():
			self.add(dagcmd, dagcmd_name)



	def clear(self):
		for idname in dict(self._subcmds).keys():
			self.remove(idname)

		return self


	def __repr__(self):
		return f"<names = {self.names()}, {object.__repr__(self)}>"




class DagCmdBase:
	"""
	Anything identifiable will contain a table allowing for further searches
	"""

	subcmdtable: DagCmdTable
	name: str = ""
	settings: Mapping
	dagmod: DagMod


	def __init__(self, ):
		self.subcmdtable = DagCmdTable(self)
		self.completion_cmdtable = self.subcmdtable
		#self._parent_dagcmd = dag.ctx.active_dagcmd -> Causing issues with pickling
		self._parent_dagcmd = None


	def _get_subcmd(self, subcmdname, subcmdtable_val):
		return getattr(self, subcmdname)


	def parents(self):
		parents = [self._parent_dagcmd]

		while hasattr(parents[-1], "_parent_dagcmd") and parents[-1]._parent_dagcmd:
			parent = parents[-1]._parent_dagcmd

			if parent == dag.default_dagcmd:
				break

			parents.append(parent)

		return [*filter(None, parents)]


	def cmdpath(self, separator = ".", until = 0):
		parents = [self] + self.parents()

		path = ""

		if until:
			parents = parents[abs(until):]

		for parent in parents:
			if parent == dag.default_dagcmd:
				break

			breakpoint(parent.name == "default_fn")
			path = parent.name + separator + path

		return path.rstrip(separator)
































if __name__ == "__main__":
	try:
		id1 = DagCmdBase()
		id1.name = "banana"

		id2 = DagCmdBase()
		id2.name = "apple"

		id3 = DagCmdBase()
		id3.name = "h"

		idt = DagCmdTable()
		idt.register_child("testitems", complete = False).add(id1).add(id2)

		names = idt.names()
		identifiers = idt.subcmds()
		idt.children.testitems.clear().add(id3)

		idt.register_child("testitems2", complete = True).add(id1).add(id2)
		complete_names = idt.children.testitems2.get_completion_names()
		breakpoint()
		pass
	except Exception as e:
		print(e)
		breakpoint()
		pass