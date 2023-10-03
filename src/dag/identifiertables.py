from __future__ import annotations

from typing import Mapping

import dag
from dag.util import rslashes

class IdentifierTable(Mapping, dag.dot.DotAccess):
	"""
	Note, this is made to be case-insensitive
	"""

	def __init__(self, owner: Identifier, root = None, parent = None, name = "", **settings):
		self.dagcmds = {}

		self.owner = owner
		self.root = root if root is not None else self
		self.parent = parent
		self.name = name

		self.settings = dag.DotDict(settings or {})
		self.settings.setdefault("complete", True)
		self.settings.setdefault("ignore_duplicates", False)

		self.children = dag.DotDict()

		self.table_containing = {}

		self.regexcmds = {}


	def __getitem__(self, idx):
		return self.dagcmds[idx.lower()]


	def __contains__(self, idx):
		with dag.catch() as e:
			return idx in self.dagcmds

	def __iter__(self): return iter(self.dagcmds)
	def __len__(self): return len(self.dagcmds)


	def __getattr__(self, attr):
		try:
			return self.children[attr]
		except KeyError as e:
			raise AttributeError(f"Identifier Table doesn't have child named \"<c b u>{attr}</c b u>\"") from e


	def __dir__(self):
		return [*set(object.__dir__(self) + [*self.children.keys()])]


	# For when need to check settings
	def _iter(self, return_names = False):
		breakpoint()
		for idname, idval in self.items():
			if isinstance(idval, Mapping):
				yield from self._iter(idval, return_names)
			else:
				if return_names:
					yield idname
				else:
					yield idval


	def iter_dagcmds(self):
		yield from self.dagcmds.values()


	def names(self):
		names = []

		for name in self.keys():
			dagcmd = self[name]

			# IF dagcmd is a resource_method and we aren't currently looking for those: skip
			if dagcmd.settings.is_resource_method and not dag.ctx.is_getting_resource_methods:
				continue

			names.append(name)

		return names
		#return [k for k in self.keys()]


	def get_completion_names(self):
		return [n for n in self.names() if self.table_containing[n].settings.complete and not rslashes.item_is_rslash(n)]


	def add(self, dagcmd: Identifier, name = None):
		if dagcmd.is_regexcmd:
			priority = dagcmd.settings.regex_priority or 10
			self.regexcmds.setdefault(priority, []).append(dagcmd)
			return self

		table = self

		# Can't add dagcmd directly to root table
		if table is table.root: # "is" because comparing table items, so any empty tables are == eachother
			table = table.maybe_register_child("dagcmds")
			#raise TypeError("Cannot add dagcmd directly to root dagcmds. Please add to a child, registering the child first if necessary")

		# Can't have same dagcmd in table
		name = str(name if name is not None else dagcmd.name).lower().replace("_", "-")

		# Add dagcmd to list of identifiers
		table.dagcmds[name] = dagcmd
		table.table_containing[name] = table

		# Add dagcmd info to all parent tables
		# Note: Since can't add() to root, this table always has a parent 
		parent = table.parent

		while parent is not None:
			parent.dagcmds[name] = dagcmd
			parent.table_containing[name] = table
			parent = parent.parent

		return table


	def remove(self, name):
		if name not in self:
			return

		table = self.table_containing.get(name)

		while table is not None:
			table.dagcmds.pop(name, None)
			table.table_containing.pop(name, None)
			table = table.parent

		return self


	def maybe_register_child(self, name, **settings):
		# If already registered, ignore
		if name in self.children:
			return self.children[name]

		return self.register_child(name, **settings)


	def register_child(self, name, **settings):
		self.children[name] = IdentifierTable(self.owner, root = self.root, parent = self, name = name, **(self.settings | settings))
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
		for idname in dict(self.dagcmds).keys():
			self.remove(idname)

		return self


	def __repr__(self):
		return f"<names = {self.names()}, {object.__repr__(self)}>"
