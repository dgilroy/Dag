import re

from collections.abc import Sequence

import dag
from dag.lib import comparison, dot
from dag.util import prompter, mixins

from dag.responses import clean_name
from dag.dagcollections.partitioned_collection import PartitionedCollection
from dag.dagcollections.resource import Resource



def setup_resource(item, idx, dagcoll, resource_class):
	if isinstance(item, Resource):
		return item
		
	return resource_class(item, dagcoll, insertion_idx = idx)

	


class Collection(Sequence, dot.DotAccess, mixins.DagLaunchable, mixins.DagFiltable, mixins.DagDrillable, mixins.Alistable, mixins.DagStyleFormattable):
	_resource_class = Resource

	def __init__(self, response, settings = None, parsed = None, name = ""):
		if not response:
			response = dag.Response([])

		if isinstance(response, Collection):
			response = response.response
			
		elif not isinstance(response, dag.Response):
			if not isinstance(response, (list, tuple)): # So dict respons
				response = [response]

			response = dag.Response(response)

		elif response.is_dict():
			response = dag.Response(response._values()) # Done since some collections are dicts with the IDs as keys
			#response = [response]
			#response = dag.Response(response)


		self.response = response
		self.resources = []

		self.name = name
		self.parsed = parsed or {}
		self.settings = settings or dag.DotDict()
		
		self.settings.setdefault("label", "")												#RESOURCE
		self.settings.setdefault("label_ignore_chars", []) 									#RESOURCE
		self.settings.setdefault("id", "")													#RESOURCE
		self.settings.setdefault("idx", "")													#COLL
		self.settings.setdefault("launch", "")												#RESOURCE
		self.settings.setdefault("parent", None)											#COLL

		self.launch_url = self.settings.launch.format(**{**self.parsed})					#COLL

		self.resource_settings = self.settings._resource_settings or dag.DotDict()			#RESOURCE

		self._setup(response)

	def all(self, resource_fn):
		return all([resource_fn(res) for res in self.resources])


	def any(self, resource_fn):
		return any([resource_fn(res) for res in self.resources])


	def __bool__(self):
		return bool(self.resources)


	def is_empty(self):
		return not bool(self.resources)


	def update_collection(self, x):
		if isinstance(x, Collection):
			self.resources = x.resources

		elif isinstance(x, Resource):
			self.resources = [x]

		else:
			raise AttributeError("updater must be Collection or Resource")

		self._init()
		return self


	def reverse(self):
		self.resources = [item for item in reversed(self.resources)]
		return self


	def keys(self):
		if self.resources:
			return comparison.sortlist(self.resources[0]._keys())
			
		return []


	def _init(self):
		self._choices = {}
		self._ids = {}
		pass


	def format_via_resources(self, text):
		return [text.format(**resource) for resource in self]


	def create_subcollection(self, response = []):
		if isinstance(response, self.__class__):
			return response
		elif isinstance(response, Resource):
			response = dag.Response([response])
		else:
			response = dag.Response(response)
			
		return self._new_collection(response)


	def _setup(self, response):
		self._init()

		if isinstance(response, dag.Response) and response.is_dict():
			response = [v for v in response._values()]

		self.resources = [setup_resource(r, i, self, self._resource_class) for i,r in enumerate(response)] # No clue why, but setup_resource seems much faster than having Resource(r,self) in the listcomp

		if self.resource_settings.label:		
			for resource in self.resources:
				if label := resource._dag.label:
					self._choices[clean_name(label, ignore_chars = self.settings.label_ignore_chars)] = resource

		if self.resource_settings.id:
			for resource in self.resources:
				if id := resource._dag.id:
					self._ids[id] = resource



	def __len__(self): return len(self.resources)
	def total_resoures(self): return len(self) # Used for compatilibity with partitioned_collection
	def __str__(self): return self.__repr__()

	def drill(self, drillee):
		return [dag.drill(res, drillee) for res in self]


	def values_for_attr(self, attr):
		parts = set()
		for item in self.resources:
			parts.add(getattr(item, attr))
			
		return comparison.sortlist([*parts])
		

	def sort_by(self, attr = None, reverse = False):
		if callable(attr):
			key = attr
		else:
			if attr not in self.keys():
				raise AttributeError(f"Attribute \"{attr}\" not found in collection \"{self.name}\"")

			key = lambda x: dag.drill(x, attr)

		return self.update_collection(self.create_subcollection(comparison.sortlist(self.resources, key = key, reverse = reverse)))


	def sort(self, *args, **kwargs): return self.sort_by(*args, **kwargs)
	def order(self, *args, **kwargs): return self.sort_by(*args, **kwargs)


	def compare(self, id, op = "==", *args):
		try:
			op = comparison.ops[op]
		except KeyError:
			raise AttributeError(f"Invalid comparison operator: {op}")

		items = []
		
		for item in self:
			for key, val in id.items():
				try:
					if op(item[key], type(item[key])(val)):
						items.append(item)
				except KeyError:
					continue

		return self.create_subcollection(items)

		
	def __reversed__(self): return self.create_subcollection([*reversed(self.resources)])


	def choices(self):
		return comparison.sortlist([*self._choices.keys()])


	def ids(self):
		return comparison.sortlist([*self._ids.keys()])



	def find(self, *names, ignore_labels = False, ignore_ids = False):
		items = []

		for name in names:
			if not ignore_labels and (item := self._choices.get(name)):
				items.append(item)

			if not ignore_ids and (item := self._ids.get(str(name))): # IDs are turned to strings for CLI purposes
				items.append(item)

		if len(names) == 1 and len(items) == 1:
			return items[0]

		return self.create_subcollection(list(set(items)))


	def find_regex(self, *names):
		items = []

		for name in names:
			items.extend([v for k,v in self._choices.items() if re.search(str(name), k)])
			items.extend([v for k,v in self._ids.items() if re.search(str(name), k)])

		return self.create_subcollection(list(set(items)))



	def filter_regex(self, **filters):
		if not filters:
			return self

		filtered_resources = []
		resources = self
	
		for key, value in filters.items():
			if not isinstance(value, (tuple, list)):
				value = [value]

			filtered_resources.extend([res for res in resources if [v for v in value if re.search(str(v), str(res.get(key)))]])
			resources = filtered_resources
			
		return self.create_subcollection(list(set(filtered_resources)))


	def filter(self, _dag_use_str = False, **filters):
		if not filters:
			return self

		filtered_resources = []
		resources = self

		for key, value in filters.items():
			# This whole rigmarole is so that (nba teams ##isNBAFranchise true) matches for True boolean, or int filts match ints
			for resource in resources:
				val = value
				item = dag.drill(resource, key)
				
				if _dag_use_str and not isinstance(item, str):
					item = str(item).lower()
					val = [str(v).lower() for v in value]

				if item == val:
					filtered_resources.append(resource)
	
			resources = filtered_resources
				
		return self.create_subcollection(list(set(filtered_resources)))


	def lacks(self, *attrs):
		items = self

		for attr in attrs:
			items = items.create_subcollection([res for res in items if not dag.drill(res, attr)])

		return items


	def has(self, *attrs):
		items = self

		for attr in attrs:
			items = items - items.lacks(attr)

		return items


		
	def __sub__(self, other):
		assert isinstance(other, (Resource, Collection)), "Subtracted resource must be a Resource of Collection"
		if isinstance(other, Resource) and other in self.resources:
			return self.create_subcollection([r for r in self.resources if r is not other])
		
		return self.create_subcollection([r for r in self.resources if r not in other.resources])


	def prompt(self, message = "", display_choices = True, prefill = ""):
		while True:
			input = prompter.prompt(message, [*self._choices.keys()], display_choices, prefill).strip()
			
			if self._choices:
				if input not in self._choices:
					print("Choice not in choices")
					continue

				return self.find(input)
					
			elif self.settings.idx:
				if not input.isdigit():
					print("Please enter valid index number")
					continue
					
				input = int(input)
				
				if input < len(self):
					return self(int(input))
				
				continue
				
			return input


	def partition(self, attr):
		return PartitionedCollection(attr, self)


	def add_shortcut(self, name, resource):
		self._choices[clean_name(name)] = resource
		return self


	def get_labels(self):
		return [*self._choices.keys()]
		

	def __getitem__(self, idx):
		if isinstance(idx, slice):
			return self.create_subcollection(self.resources[idx])
		
		elif isinstance(idx, int) or idx.isdigit():
			return self.resources[int(idx)]

		if self.settings.label:
			return self.resources._choices[idx]

		raise KeyError(f"Cannot get key <c b>\"idx\"</c b> from collection")
		

	def __repr__(self): return dag.format(f"""\n<{object.__repr__(self)} -> {self.resources=}>\n
<c black b bg-teal>**Collection** </c>
<c b>LEN:</c> {len(self)}
<c b>ITEM LABELS (IF CLIST) (UP TO 50):</c> {self.choices()[0:50]}{'...' if len(self.resources) > 50 else ''}""")


	def __radd__(self, other): return self if other == 0 else self + other


	def exclude(self, _dag_use_str = False, **filters):
		return self - self.filter(_dag_use_str = _dag_use_str, **filters)


	def exclude_regex(self, **filters):		
		return self - self.filter_regex(**filters)


	def _dag_formatter_fn(self):
		return self.settings.display


	def _dag_launch_item(self):
		return self.launch_url



	
	def __or__(self, other):
		return self.create_subcollection(list(set(self + other)))

	
	def __add__(self, other):
		if isinstance(other, Resource):
			if self.name != other._dag.dagcollection.name:
				raise TypeError("Resource must be part of Collection")
				
			return self.create_subcollection(self.resources + [other])
		if not isinstance(other, Collection):
			breakpoint()
			raise TypeError("Must add Collection to other Collection")
			
		if self.name != other.name:
			raise TypeError(f"Collections of same collection. Left belongs to {self.name} and right belongs to {other.name}")
			
		return self.create_subcollection(self.resources + other.resources)
		

		
	def _new_collection(self, response):
		return self.__class__(response, settings = self.settings, parsed = self.parsed, name = self.name)

		
			

	def add_resource(self, resource):
		assert type(resource) == self._resource_class, f"When adding resource to Collection, it must be of type {self._resource_class.__name__}"
		assert resource._dag.dagcollection == self, "Resource must come from same Collection"
		
		self.resources.append(resource)
		
		if self.settings.label:
			self._choices[clean_name(resource._dag.label, ignore_chars = self.settings.label_ignore_chars, remove_chars = self.settings.label_remove_chars)] = resource

		if self.settings.id:
			self._ids[resource._dag.id] = resource