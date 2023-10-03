import re, random, json, uuid

from collections.abc import Sequence, Mapping

import dag
from dag.lib import comparison, dot
from dag.util import prompter, mixins, daguuid

from dag.dagcollections.partitioned_collection import PartitionedCollection
from dag.dagcollections.resource import Resource
from dag.exceptions import DagContinueLoopException
from dag.dagcmd_exctx import DagCmdExecutionContext



ALIAS_FILENAME = "alias"

def setup_resource(item, dagcoll, resource_class):
	if isinstance(item, Resource):
		return item
		
	return resource_class(item, dagcoll)



class Collection(Sequence, dot.DotAccess, mixins.DagLaunchable, mixins.DagDrillable, mixins.Alistable, mixins.DagStyleFormattable):
	_resource_class = Resource

	def __init__(self, response, settings = None, parsed = None, name = ""):
		if not response:
			response = dag.Response([])

		self.settings = settings or dag.DotDict()

		while isinstance(response, Collection):
			response = response.response
			
		if not isinstance(response, dag.Response):
			response = dag.listify(response)
			response = dag.Response(response)

		elif dag.is_mapping(response) and settings.keyval:
			dresponse = []

			for key, val in response.items():
				dresponse.append({"key": key, "val": val})

			self.settings.setdefault("label", "key")

			response = dag.Response(dresponse) # Done since some collections are dicts with the IDs as keys
			#response = dag.Response(response._values()) # Done since some collections are dicts with the IDs as keys

		if response and dag.is_sequence(response) and isinstance(response[0], str):
			response = dag.Response([{"label": item} for item in response])
			self.settings._resource_settings.label = "label"

		self.response = response
		self.resources = []

		self.name = name
		self.parsed = parsed or {}
		
		self.settings.setdefault("label", "")												#RESOURCE
		self.settings.setdefault("label_ignore_chars", []) 									#RESOURCE
		self.settings.setdefault("id", "")													#RESOURCE
		self.settings.setdefault("idx", "")													#COLL
		self.settings.setdefault("launch", "")												#RESOURCE
		self.settings.setdefault("_resource_settings", dag.DotDict())						#RESOURCE

		self.launch_url = self.settings.launch.format(**self.parsed)					#COLL

		self.resource_settings = self.settings._resource_settings

		self.collectioncmd = None # Set by collection dagcmd when returning the collection

		self._setup(response)


	def remove_duplicates(self):
		self.resources = [*set(self.resources)]
		return self


	@property
	def schema(self):
		def extract_keys(mapping):
			result = {}
			for key, value in mapping.items():
				if isinstance(value, Mapping):
					result[key] = extract_keys(value)
				else:
					result[key] = type(value)

			return dag.DotDict(result)

		resource = self[0]
		response = resource._response
		return extract_keys(response)


	@property
	def flatschema(self) -> dag.DotDict:
		def flatten_dict(d: Mapping, parent_key: str = '', sep: str ='.') -> dict:
			items = []
			for k, v in d.items():
				new_key = parent_key + sep + k if parent_key else k
				if isinstance(v, Mapping):
					items.extend(flatten_dict(v, new_key, sep=sep).items())
				else:
					items.append((new_key, v))
			return dict(items)

		return dag.DotDict(flatten_dict(self.schema))


	@property	
	def nab(self, label):
		return dag.nabbers.SimpleNabber(self)


	@property
	def to_exctx(self): # since cachefiles use exctx's
		return DagCmdExecutionContext(self.collectioncmd, self.parsed)


	def __setstate__(self, d):
		d["collectioncmd"] = None # Make sure the collectioncmd doesn't get pickled bc it carries a lot of baggage
		super().__setstate__(d)
		# ALIAS loading will go here
		#breakpoint()
		#pass


	def has_alias(self, name):
		if not self.collectioncmd:
			return False

		return name in self.collectioncmd.load_aliases()


	def set_alias(self, item, name):
		if not self.collectioncmd:
			return

		if not item._dag.label:
			raise ValueError("Resource must be from a labelled collection")

		if name in self.choicesdict:
			dag.echo(f"Name \"<c b u>{name}</c b u>\" is already registered")
			return

		aliases = self.collectioncmd.load_aliases()

		aliases[name] = item._dag.label

		with self.collectioncmd.file.open(ALIAS_FILENAME, "w") as file:
			file.write(json.dumps(aliases))

		self.collectioncmd.write_cached_choices(self)

		dag.echo(f"alias <c bu>{name}</c bu> set for <c bu>{item._dag.identifier}</c bu>")


	def write_cached_choices(self):
		self.collectioncmd.write_cached_choices(self)


	def unset_alias(self, name):
		if not self.collectioncmd:
			return

		aliases = self.collectioncmd.load_aliases()

		if name in aliases:
			aliasedlabel = aliases.pop(name)

			with self.collectioncmd.file.open(ALIAS_FILENAME, "w") as file:
				file.write(json.dumps(aliases))

			if name in self.choicesdict and self.choicesdict[name]._dag.label == aliasedlabel:
				self.choicesdict.pop(name)

			#self.choicesdict.pop(name, None) -> Don't pop this in case the alias has been replaced with a new resource with the same label as the old alias
			self.collectioncmd.write_cached_choices(self)



	def all(self, resource_fn):
		return all([resource_fn(res) for res in self.resources])


	def any(self, resource_fn):
		return any([resource_fn(res) for res in self.resources])


	def __bool__(self):
		return bool(self.resources)


	def is_empty(self):
		return not bool(self.resources)


	def random(self):
		return random.choice(self)


	def update_collection(self, x):
		match x:
			case Collection():
				self.resources = x.resources
			case Resource():
				self.resources = [x]
			case _:
				raise AttributeError("updater must be Collection or Resource")

		self.process_resources()
		return self


	def reverse(self):
		self.resources = [item for item in reversed(self.resources)]
		return self


	def keys(self):
		if self.resources:
			return comparison.sortlist(self.resources[0]._keys())
			
		return []


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


	def create_empty_collection(self):
		return self._new_collection([])


	def _setup(self, response):
		if isinstance(response, dag.Response) and dag.is_mapping(response):
			response = [v for v in response._values()]

		self.resources = [setup_resource(r, self, self._resource_class) for r in response] # No clue why, but setup_resource seems much faster than having Resource(r,self) in the listcomp

		self.process_resources()



	def process_resources(self):
		self._choicesdict = {}
		self._ids = {}

		for resource in self.resources:
			if self.resource_settings.label:		
				if label := resource._dag.label:
					self._choicesdict[dag.slugify(label, ignore_chars = self.settings.label_ignore_chars)] = resource

			if id := resource._dag.id:
				self._ids[id] = resource

			if (datevalues := self.resource_settings.datevalues):
				for dateval in dag.listify(datevalues):
					try:
						dateentry = dag.drill(resource, dateval)
						dtime = dag.DTime(dateentry)
						dag.util.drill.set_idx_via_drill(dateval, dtime, resource._response)
					except ValueError:
						pass

			if (uuidvalues := self.resource_settings.uuidvalues):
				for uv in dag.listify(uuidvalues):
					try:
						uuidentry = dag.drill(resource, uv)
						uuidvalue = daguuid.DagUUID(uuidentry)
						dag.util.drill.set_idx_via_drill(uv, uuidvalue, resource._response)
					except ValueError:
						pass




	@property
	def choicesdict(self):
		dic = self._choicesdict

		if not self.collectioncmd:
			return dic
			
		for key, itemlabel in self.collectioncmd.load_aliases().items():
			if key in dic:
				continue

			try:
				dic[key] = dic[itemlabel]
			except:
				pass

		return dic


	def __len__(self): return len(self.resources)
	def total_resoures(self): return len(self) # Used for compatilibity with partitioned_collection
	def __str__(self): return self.__repr__()


	def drill(self, drillee):
		return [dag.drill(res, drillee) for res in self]


	def map(self, lamb):
		return [lamb(res) for res in self]


	def values_for_attr(self, attr):
		parts = set()
		for item in self.resources:
			parts.add(getattr(item, attr))
			
		return comparison.sortlist([*parts])


	def length(self):
		return len(self)


	def labeldict(self):
		if not self.settings._resource_settings.label:
			raise ValueError("Collection must have a set label to build a Label Dict")

		return {r._dag.label: r for r in self}


	def sortby(self, attr = None, reverse = False):
		if callable(attr):
			key = attr
		else:
			drillparts = dag.util.drill.get_drillparts(attr)
			if drillparts and drillparts[0] not in self.keys():
				raise AttributeError(f"Attribute \"{attr}\" not found in collection \"{self.name}\"")

			key = lambda x: dag.drill(x, attr) or ""

		return self.update_collection(self.create_subcollection(comparison.sortlist(self.resources, key = key, reverse = reverse)))


	sort = sortby
	order = sortby


	def compare(self, id, op = "==", *args):
		try:
			op = comparison.ops[op]
		except KeyError as e:
			raise AttributeError(f"Invalid comparison operator: {op}") from e

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


	def choices(self, sort = True):
		if sort:
			return comparison.sortlist([*self.choicesdict.keys()])

		return [*self.choicesdict.keys()]


	def ids(self):
		return comparison.sortlist([*self._ids.keys()])



	def find(self, *names, ignore_labels = False, ignore_ids = False):
		items = []

		for name in names:

			if not ignore_labels and (item := self.choicesdict.get(name)):
				items.append(item)

			if not ignore_ids and (item := self._ids.get(str(name))): # IDs are turned to strings for CLI purposes
				items.append(item)

		if len(names) == 1 and len(items) == 1:
			return items[0]

		return self.create_subcollection(list(set(items)))

	search = find


	def find_regex(self, *names, flags = ""):
		items = []

		re_flags = dag.rslashes.parse_flagchars(flags)

		for name in names:
			items.extend([v for k,v in self.choicesdict.items() if re.search(str(name), k, re_flags)])
			#items.extend([v for k,v in self._ids.items() if re.search(str(name), k)]) -> This is bad for regexes looking for negative matches

		return self.create_subcollection(list(set(items)))



	def filter_regex(self, **filters):
		if not filters:
			return self

		filtered_resources = []
		resources = self
	
		for key, value in filters.items():
			value = dag.listify(value)

			filtered_resources.extend([res for res in resources if [v for v in value if re.search(str(v), str(res.get(key)))]])
			resources = filtered_resources
			
		return self.create_subcollection(list(set(filtered_resources)))




	def filter(self, *lambs):
		if not lambs:
			return self

		filtered_resources = []
		resources = self

		for item in self:
			try:
				for lamb in lambs:
					response = lamb(item)
					if not response or response == NotImplemented:
						raise DagContinueLoopException()

				filtered_resources.append(item)
			except (Exception, BaseException):
				pass

		resources = filtered_resources.copy()
		return self.create_subcollection(resources)


	def lacks(self, *lambs):
		items = []
		
		for item in self:
			try:
				for lamb in lambs:
					response = lamb(item)
					if response in [None, NotImplemented]:
						items.append(item)
						break

			except (Exception, BaseException):
				pass

		return self.create_subcollection(items)


	def has(self, *lambs):
		items = []
		for item in self:
			try:
				for lamb in lambs:
					response = lamb(item)
					if response in [None, NotImplemented]:
						raise DagContinueLoopException()

				items.append(item)
			except (Exception, BaseException):
				pass

		return self.create_subcollection(items)



		
	def __sub__(self, other):
		assert isinstance(other, (Resource, Collection)), "Subtracted resource must be a Resource of Collection"
		if isinstance(other, Resource) and other in self.resources:
			return self.create_subcollection([r for r in self.resources if r is not other])
		
		return self.create_subcollection([r for r in self.resources if r not in other.resources])


	def prompt(self, message = "", display_choices = True, prefill = "", id = ""):
		while True:
			try:
				intext = dag.cli.prompt(message, complete_list = [*self.choicesdict.keys()], display_choices = display_choices, prefill = prefill, id = id)
			except KeyboardInterrupt as e:
				if prefill:
					prefill = ""
					continue

				raise e
			except EOFError as e:
				raise e from e
			except AttributeError as e:
				breakpoint()
				pass

			if intext is None:
				raise dag.exceptions.DagExitDagCmd()
			
			if self.choicesdict:
				if intext not in self.choicesdict:
					dag.echo("Choice not in choices")
					continue

				return self.find(intext)
					
			elif self.collectioncmd is not dag.instance.controller.alist.collection_dagcmd:
				if not intext.isdigit():
					dag.echo("Please enter valid index number")
					continue
					
				intext = int(intext)
				
				if intext < len(self):
					return self(int(intext))
				
				continue
				
			return intext


	def format_each_with(self, urlformat):
		items = []

		for resource in self:
			formatinfo = {"resource": resource}
			if self.settings.resource_argname:
				formatinfo[self.settings.resource_argname] = resource

			items.append(urlformat.format(**formatinfo))

		return items


	def partition(self, attr):
		return PartitionedCollection(attr, self)


	def get_values_of(self, attr):
		parts = set()

		for resource in self.resources:
			if callable(attr):
				part = attr(resource)
			else:
				part = dag.drill(resource, attr)

			parts.add(part)

		return [*parts]


	def add_shortcut(self, name, resource):
		self.choicesdict[dag.slugify(name)] = resource
		return self


	def get_labels(self):
		return [*self.choicesdict.keys()]
		

	def __getitem__(self, idx):
		if isinstance(idx, slice):
			return self.create_subcollection(self.resources[idx])
		
		elif isinstance(idx, int) or dag.strtools.isint(idx):
			return self.resources[int(idx)]

		if self.settings.label:
			return self.resources.choicesdict[idx]

		raise KeyError(f"Cannot get key <c b>\"idx\"</c b> from collection")
		

	def __repr__(self):
		total = len(self)
		maxdisplay = 200

		totaltext = ""
		if total > maxdisplay:
			totaltext = f"\n\n<c bu red>Only the last {maxdisplay} shown</c bu red>"

		return dag.format(f"""\n<{object.__repr__(self)} -> {self.resources[-maxdisplay:]=}>\n
<c black b bg-teal>**Collection** </c>
<c b>NAME:</c> {self.name}
<c b>LEN:</c> {len(self)}
<c b>ITEM LABELS (IF CLIST) (UP TO 50 shown):</c> {self.choices(sort = False)[0:50]}{'...' if len(self.resources) > 50 else ''}{totaltext}
""")


	def __radd__(self, other): return self if other == 0 else self + other


	def exclude(self, *lambs):
		return self - self.filter(*lambs)


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
			if self.name != other._dag.collection.name:
				raise TypeError("Resource must be part of Collection")
				
			return self.create_subcollection(self.resources + [other])
		if not isinstance(other, Collection):
			breakpoint()
			raise TypeError("Must add Collection to other Collection")
			
		if self.name != other.name:
			raise TypeError(f"Collections of same collection. Left belongs to {self.name} and right belongs to {other.name}")
			
		return self.create_subcollection(self.resources + other.resources)
		

		
	def _new_collection(self, response):
		collection = self.__class__(response, settings = self.settings, parsed = self.parsed, name = self.name)
		collection.collectioncmd = self.collectioncmd
		return collection

		
			

	def add_resource(self, resource):
		assert type(resource) == self._resource_class, f"When adding resource to Collection, it must be of type {self._resource_class.__name__}"
		assert resource._dag.collection == self, "Resource must come from same Collection"
		
		self.resources.append(resource)
		
		if self.settings.label:
			self.choicesdict[dag.slugify(resource._dag.label, ignore_chars = self.settings.label_ignore_chars, remove_chars = self.settings.label_remove_chars)] = resource

		if self.settings.id:
			self._ids[resource._dag.id] = resource