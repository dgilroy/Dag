from collections import OrderedDict 
from collections.abc import MutableMapping

import dag
from dag.lib import comparison


class PartitionedCollection(MutableMapping):
	def __init__(self, attr, collection):
		self.collection = collection
		self.resources = self.collection.resources
		self.attr = attr
		self._partition = self._build_partition(attr)


	def create_subpartition(self, collection):
		return PartitionedCollection(self.attr, collection)
		
		
	def collection_keys(self):
		return self.collection.keys()
		
		
	def _build_partition(self, attr):
		parts = OrderedDict()

		for item in self.resources:
			part = dag.drill(item, attr)
			parts.setdefault(part, []).append(item)
			
		for part in parts:
			parts[part] = self.collection.create_subcollection(parts[part])

		return parts


	def yield_resources(self):
		for collection in self.yield_collections():
			yield from iter(collection.resources)

	
	def yield_collections(self, partition = None):
		partition = partition if partition is not None else self._partition
		
		for k, v in partition.items():
			if isinstance(v, PartitionedCollection):
				yield from self.yield_collections(v)
			else:
				yield v
				
				
	def yield_subpartitions(self, partition = None):
		partition = partition if partition is not None else self
		
		for k, v in partition.items():
			if isinstance(v, PartitionedCollection):
				yield from self.yield_subpartitions(v)

		yield partition
	

	def partition(self, attr, partition = None):
		partition = partition if partition is not None else self

		for k, v in partition.items():
			if isinstance(v, MutableMapping):
				partition[k] = self.partition(attr, v)
			else:
				partition[k] = v.partition(attr)

		return partition


	def filter_regex(self, text, **kwargs):
		return self.filter(regex = text, **kwargs)
		
	
	def filter(self, id = None, regex = None, item = None):
		from dag.dagcollections.collection import Collection
		
		item = item if item is not None else self
		
		if isinstance(item, PartitionedCollection):
			for sp in item.yield_subpartitions():
				try:
					for k, v in sp.items():
						self.filter(id = id, regex = regex, item = v)
						if sp[k].is_empty():
							del sp[k]
				except RuntimeError as e:
					pass
				
		elif isinstance(item, Collection):
			filtered_collection = item.filter(id, regex = regex)
			item.update_collection(filtered_collection)
			return item
			
		if item == self and item.is_empty():
			self._partition = {}
			self.collection = Collection([], self.collection.collection_dagcmd)
			
		return self


	def choices(self):
		return [resource._dag.label for resource in self.yield_resources()]
		

	def is_empty(self):
		return all(map(lambda x: x.is_empty(), self.yield_collections()))
		

	# Trim each subcollection in partition to have at most {total} entries
	def cull_partitions(self, total = 2):
		self._partition = {k: v[0:int(total)] for k, v in self._partition.items()}
		return self

	# Take resources from partition and turn into a Collection in order
	def collect(self, *items):
		if not items:
			return sum(list(self.yield_collections()))

		collected = []
		for key in items:
			try:
				collected = collected + self[key] if collected else self[key]
			except KeyError:
				continue

		return collected
		
		
	# Flip the order of entries in each subcollection
	def flip_collections(self):
		self._partition = {k: reversed(v) for k, v in self._partition.items()}
		return self

	# Sort partition by partitioned attribute names
	def sort_by_keys(self, reverse = False):
		self._partition =  OrderedDict(sorted(self._partition.items(), reverse = reverse))
		return self


	# Sort partitioned subcollections by given attribute
	def sort_by(self, attr = None, reverse = False):
		for collection in self.yield_collections():
			collection.sort_by(attr, reverse)

		return self

		
		
	def values_for_attr(self, attr):
		return self.collection.values_for_attr(attr)

	
	# Reverse the order of keys in the partition
	def __reversed__(self): self._partition = OrderedDict(reversed(list(self._partition.items()))); return self

	def __getitem__(self, key):
		if isinstance(key, slice):
			keys = [*self.keys()][key]
			new_dagcoll = sum([self[key] for key in keys])
			return self.create_subpartition(new_dagcoll)

		return self._partition[key]

	def __setitem__(self, key, value): self._partition[key] = value
	def __delitem__(self, key): del self._partition[key]
	def __iter__(self):	return iter(self._partition)
	def __len__(self): return len(self._partition)
	def total_resoures(self): return sum([len(c) for c in self.yield_collections()])

	def __repr__(self):		
		response = ""
		for key, collection in self._partition.items():
			response += f"\n\n<c u b>{key}</c>: {collection}<c u b>\nKEY:</c> {key}\n"

		response += "\n\n<c black b bg-yellow black bold>**PartitionedCollection** </c>"
		response += f"\n<c bold>TOTAL RESOURCES:</c> {self.total_resoures()}"
		response += f"\n<c bold>TOTAL PARTITIONS:</c> {len(self)}"
		response += f"\n<c bold>COLLECTION:</c> {self.collection.name}"
		response += f"\n<c bold>COLLECTION KEYS:</c> {self.collection_keys()}"
		response += f"\n<c bold>PARTITIONED ATTR:</c> {self.attr}\n"
		response += f"\n<c bold>PARTITION KEYS (sorted by key):</c> {comparison.sortlist([*self._partition.keys()])}\n"
		p = self._partition
		sorted_keys = sorted(p, key=lambda k: len(p[k]), reverse=True)
		if sorted_keys and len(p[sorted_keys[0]]) != len(p[sorted_keys[-1]]):
			formatted_sorted_keys = [f"{k}: ({len(p[k])})" for k in sorted_keys]
			response += f"\n<c bold>PARTITION KEYS (sorted by size):</c> {formatted_sorted_keys}\n"

		return dag.format(response)