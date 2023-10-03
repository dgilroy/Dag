import json, collections, re, copyreg, csv, io, itertools, string, copy, pprint
from collections.abc import Mapping, Sequence

import dag
from dag.lib import comparison, strtools
from dag.lib.proxy_descriptor import ProxyDescriptor
from dag.util.mixins import DagLaunchable, DagJsonEncodable


from dag.attrsettings import AttrSettable




def clean_name(name, ignore_chars = [], remove_chars = []):
	name = name.replace("'", "") # so larry's -> larrys
	#name = name.replace("'", "").replace(" ", "") # so larry's -> larrys

	def clean(name):
		ignoredchars = "\\" + "\\".join(ignore_chars) if ignore_chars else ""
		newname = re.sub(rf"[^\w\-{ignoredchars}]", "-", name).lower().strip("-")
		return re.sub(r"\-{2,}", "-", newname) #Replaces sequences of 2 or more periods (-) with one period.

	return clean(name)


	"""
	chars_to_remove = [" ", "'", "/", "&amp;", "&", ";", "|", "[", "]", ",", "•"]
	chars_to_keep = string.ascii_letters + string.digits + ["-", "_", "."]

	for ch in chars_to_remove + [ch for ch in remove_chars if ch not in chars_to_remove]:
		if ch in ignore_chars:
			pass
		name = name.replace(ch, "")

	for ch in set(["(", ")"]): # Since ( and ) tends to demarcate words, replace with period.
		name = name.replace(ch, ".")


	name = re.sub(r"\.{2,}", ".", name) #Replaces sequences of 2 or more periods (.) with one period. This is so ranges (../...) work with resource labels

	replacers = {"á": "a", }

	return name.lower()
	"""




def is_mapping(data: object) -> bool:
	"""Checks whether given data is a mapping/dict"""
	while isinstance(data, DagResponse):
		data = data._data

	return isinstance(data, Mapping)


def is_sequence(data: object) -> bool:
	"""Checks whether given data is a sequence/list/tuple (AND NOT A STRING)"""
	while isinstance(data, DagResponse):
		data = data._data

	return isinstance(data, Sequence) and not isinstance(data, str)


def is_none(data: object) -> bool:
	"""Checks whether given data is None"""
	while isinstance(data, DagResponse):
		data = data._data

	return data is None


def filter(response, *lambs):
		if not lambs:
			return response

		filtered_items = []

		data = response._data

		if is_mapping(response):
			data = response._data.values()

		data = response._maybe_make_dagresponse(data)

		for item in data:
			item = response._maybe_make_dagresponse(item)

			try:
				for lamb in lambs:
					response = lamb(item)
					if not response or response == NotImplemented:
						raise DagContinueLoopException()

				filtered_items.append(item)
			except (Exception, BaseException):
				pass
				
		return filtered_items


def sortby(response, key, reverse = False):
	return comparison.sortlist(response._data, key = key, reverse = reverse)




# Convert to a collection	
def to_collection(response, label = None, id = None):
	from dag.dagcollections.collection import Collection # Done to prevent circular import

	if not is_sequence(response):
		response = [response]

	settings = dag.nabbers.NabbableSettings()

	if label:
		settings.setdefault('_resource_settings', dag.nabbers.NabbableSettings())['label'] = label

	if id:
		settings.setdefault('_resource_settings', dag.nabbers.NabbableSettings())['id'] = id

	coll = Collection(response, settings)

	if label:
		breakpoint()

	return coll


class DagResponseJsonEncoder(json.JSONEncoder):
	def default(self, obj):
		return obj._data




class DagResponse(dag.dot.DotAccess, DagLaunchable, DagJsonEncodable, collections.abc.MutableSequence, collections.abc.MutableMapping):
	_parser = None
	_dag_response_str_formatter = str


	def __init__(self, data = None):
		# Contains the internal data
		while isinstance(data, DagResponse):
			data = data._data

		self._data = data


	@property
	def _dag_return_class(self):
		return type(self)


	def _dag_json_encoder(self):
		return DagResponseJsonEncoder
		

	# Implements DagLaunchable mixin
	def _dag_launch_item(self):
		return self._data


	# ABC Methods
	def __setitem__(self, idx, value): self._data[idx] = value
	def __delitem__(self, idx): del self._data[idx]
	def __len__(self): return len(self._data)
	def __iter__(self):
		return iter([self._maybe_make_dagresponse(i) for i in self._data])
	def insert(self, idx, value): self._data.insert(idx, value)


	# Other magic methods
	def __bool__(self): return bool(self._data)
	def __reversed__(self): return self._maybe_make_dagresponse([i for i in reversed(self._data)])


	def __eq__(self, other):
		data = other

		if isinstance(other, type(self)):
			data = other._data

		return self._data == data


	def __dir__(self):
		try:
			return [*set(object.__dir__(self) + [*self._data.keys()])]
		except:
			return [*set(object.__dir__(self))]


	# FILTER
	# Search for subitems via a search dictionary {value_name: needle, ...}
	def _dag_do_filter(self, _dag_filter_fn, **values):
		# If no values: return Nothing
		if values is None or self._data is None:
			return_items = None

		# Else, there are values: find items matching the values
		else:
			# All response items
			return_items = self

			# If responseItem's type is a mapping: put mapping's values() into an array
			if is_mapping(self):
				return_items = [*return_items.values()]

			for attr_name, needle in values.items():
				return_items = [item for item in return_items if _dag_filter_fn(item, attr_name, needle)]
				
		# Return the item, making it a DagResponse if not a primitive (str/int/etc...)
		return self._maybe_make_dagresponse(return_items)


	#
	# DICT METHODS
	#
	def _get(self, attr, default = None): return self._maybe_make_dagresponse(self._data.get(attr, default))
	def _keys(self): return self._data.keys()
	def _values(self): return [self._maybe_make_dagresponse(v) for v in self._data.values()]
	def _items(self): return self._data.items()




	# Internal data state methods
	@staticmethod
	def _is_can_be_dagresponse(data = None):
		# Currently, None will be allowable as a ResponseType
		return is_mapping(data) or is_sequence(data)# or is_none(data) -> This was initially so that None.None.None.etc... would still work, but it was outputting as "null"


	# Process data being returned
	def _maybe_make_dagresponse(self, data):
		with dag.catch() as e:
			if isinstance(data, DagResponse):
				return data

			if self._is_can_be_dagresponse(data):
				return self._dag_return_class(data)

			return data


	# Adding DagResponses together
	def __add__(self, other):
		if not isinstance(other, DagResponse):
			raise TypeError("Cannot add non-DagResponse to DagResponse")
			
		if is_sequence(self) and is_sequence(other):
			return self._maybe_make_dagresponse(self._data + other._data)
		if is_mapping(self) and is_mapping(other):
			return self._maybe_make_dagresponse({**self._data, **other._data})
		if is_none(self) and is_none(other):
			return self._maybe_make_dagresponse(None)

		raise TypeError("Must add two DagResponse Lists or two DagResponse Dicts")


	#
	# UNIONING
	#
	def __or__(self, other):
		return self._combine_dag_response_mappings(self, other)


	def __ior__(self, other):
		self._data = self._combine_dag_response_mappings(self, other)


	def __ror__(self, other):
		return self._combine_dag_response_mappings(other, self)


	def _combine_dag_response_mappings(self, d1, d2):
		if not isinstance(d1, DagResponse) or not isinstance(d2, DagResponse):
			return NotImplemented

		if not is_mapping(d1) or not is_mapping(d2):
			return NotImplemented

		return self._maybe_make_dagresponse({**d1._data, **d2._data})



	#
	# ATTR ACCESS
	#
	def __getattr__(self, attr, default = None):
		try:
			return self._maybe_make_dagresponse(self._data[attr])
		except (AttributeError, KeyError, TypeError):
			if attr in ("keys", "values", "get", "items"):
				return object.__getattribute__(self, attr)
		except Exception as e:
			breakpoint()
			pass

		return self._maybe_make_dagresponse(default)


	def __getitem__(self, idx):
		if is_sequence(self) and isinstance(idx, str) and idx.lstrip('-').isdigit():
			idx = int(idx)
 
		try:
			return self._maybe_make_dagresponse(self._data[idx])
		except IndexError as e:
			raise dag.DagError(f"DagResponse error: Index {idx} not in response (response has length {len(self)})") from e
		except TypeError:
			return self._data[idx]



	def __getattribute__(self, attr):
		if attr in ("keys", "values", "get", "items"):
			return self.__getattr__(attr)
			
		return object.__getattribute__(self, attr)

	#
	# REPR
	#
	#def __repr__(self): return dag.format(f"\n<c b bg-chartreuse1 black>Dag Response Item:</c>\n\t{self._dag_response_str_formatter(self._data)}\n")
	def __repr__(self): return dag.format(self._dag_response_str_formatter(self._data) + "\n")



class DictResponse(DagResponse):
	def __init__(self, data):
		self._data = data

	def __str__(self):
		return pprint.pformat(self._data, indent=4, sort_dicts = True)
		#return json.dumps(self._data, indent=4, sort_keys=True)




class XmlResponse(DagResponse):
	def __init__(self, data):
		from lxml import etree

		self._parser = XmlParser()
		self._dag_response_str_formatter = lambda x: str(etree.tostring(x, pretty_print=True), 'utf-8')
		super().__init__(data)


	def __getattr__(self, attr, default = None):
		# for getting text. In future maybe need _text to get attrs or tags
		if attr == "text":
			return self._data.text

		# If starts with _, favor attributes before tags
		if attr.startswith('_') and attr[1:] in self._data.attrib:
			return self._data.attrib.get(attr[1:], default)

		item = self.select(attr)
		
		# If no tag found, see whether attribute exists
		if len(item) == 0:
			item = self._data.attrib.get(attr, default)
		# If only one element, return XMLResponse
		elif len(item) == 1:
			return item[0]

		return self._maybe_make_dagresponse(item)


	def __getitem__(self, idx):
		breakpoint()
		pass

		
		
	def select(self, selector):
		from lxml import etree
		data = dag.listify(self._data)

		items = []

		for d in data:
			if isinstance(d, type(self)):
				d = d._data
			items += [self._parser.parse(etree.tostring(item, encoding = "unicode").strip()) for item in d.cssselect(selector)]

		return self.__class__(items)


		#if len(items) == 1 && selector.split()[-1].startswith("#"):
		#	return items[0]
		# Could make this work with ID stuff, but then things get confousing if something is poorly made and has multiple ID's.
		# Could implement so that if a single item is iterated over, it just yields itself, similar to how FirefoxElement is currently done

		#return items
		return self._maybe_make_dagresponse(items)
		
		
	def css(self, selector):
		return self.select(selector)

		
	def __repr__(self):
		from lxml import etree
		try:
			text = str(etree.tostring(self._data, pretty_print=True), 'utf-8').strip()
			return "\n".join([s for s in text.split("\n") if s.strip()])
		except Exception as e:
			return str(self._data)



	def __bool__(self):
		return str(self) not in ["[]", ""]


	def __getitem__(self, item: object) -> object:
		if isinstance(item, (int, slice)):
			return self._data[item]
		else:
			return self.select(item)

	@property
	def printable(self) -> str:
		"""Strips odd artifacts from the string"""
		return strtools.printable(self.text or "")




class HtmlResponse(XmlResponse):
	def __init__(self, data, run_parser = False):
		self._parser = HtmlParser()

		# IF the data is a string and parser should be run: Parse the string
		# (This exists because pickle can't store lxml.html.HtmlElement objects)
		if isinstance(data, str) and run_parser:
			data = self._parser().parse(data)._data


		super().__init__(data)
		from lxml import etree
		self._dag_response_str_formatter = lambda x: str(etree.tostring(x, pretty_print=True), 'utf-8')



	@property
	def text(self):
		return self._data.text_content()


	def __getattr__(self, item):
		return self.select(item)

	@property
	def attrib(self):
		return dag.DotDict({k: v.strip() for k,v in self._data.attrib.items()})

	@property
	def attr(self):
		return self.attrib

	@property
	def cls(self):
		return self.attrib['class'].strip()
		



# Used to pickle HTML Responses
def pickle_response(response):
	# This is necessary because HtmlElement cannot be pickled
	#htmldata = str(etree.tostring(htmlresponse._data, pretty_print=False), 'utf-8').strip()
	#_dag_response_str_formatter = lambda self, x: str(etree.tostring(x, pretty_print=True), 'utf-8')

	data = response._dag_response_str_formatter(response._data)
	return HtmlResponse, (data, True)
copyreg.pickle(HtmlResponse, pickle_response)


		








############ DagResponse Parsers ######################

# Take a string data, parse it, and return a DagResponse
class DagResponseParser:
	response_class = DagResponse
	preparser_method = lambda self, x, *args, **kwargs: x
	parser_method = lambda self, x, *args, **kwargs: x
	postparser_method = lambda self, x, *args, **kwargs: x
	parser_error = SyntaxError
	_encoding = "utf-8"


	def __init__(self, **settings):
		self.settings = settings

	def parse(self, data, **kwargs):
		preparsed_data = self.preparser_method(data)
		parsed_data = self.parser_method(preparsed_data, **(self.settings | kwargs))
		postparsed_data = self.postparser_method(parsed_data)
		return self.response_class(postparsed_data)

	def __call__(self, *args, **settings):
		return type(self)(*args, **settings)



class DictParser(DagResponseParser):
	response_class = DictResponse

	def parse(self, data, **kwargs):
		preparsed_data = self.preparser_method(data)
		parsed_data = self.parser_method(preparsed_data, **(self.settings | kwargs))
		postparsed_data = self.postparser_method(parsed_data)
		return self.response_class(postparsed_data)



class JsonParser(DictParser):
	def __init__(self, *args, **settings):
		super().__init__(*args, **settings)
		self.parser_method = lambda *args, **kwargs: json.loads(*args, **kwargs)
		self.parser_error = json.decoder.JSONDecodeError


class YamlParser(DictParser):
	def __init__(self, *args, **settings):
		super().__init__(*args, **settings)
		import yaml
		self.parser_method = lambda *args, **kwargs: yaml.load(*args, Loader = yaml.FullLoader, **kwargs)
		self.parser_error = yaml.YAMLError


class TomlParser(DictParser):
	def __init__(self, *args, **settings):
		super().__init__(*args, **settings)
		import tomllib
		self.parser_method = lambda *args, **kwargs: tomllib.loads(*args, *kwargs)
		self.parser_error = tomllib.TOMLDecodeError



class XmlParser(DagResponseParser):
	def __init__(self, *args, **settings):
		super().__init__(*args, **settings)
		import xml.etree.ElementTree
		from lxml import objectify

		self.response_class = XmlResponse
		self.parser_method = lambda *args, **kwargs: objectify.fromstring(*args, **kwargs)
		self.parser_error = xml.etree.ElementTree.ParseError


	def preparser_method(self, data):
		# utf-8 bc lxml is annoying
		if data.find('ï»¿<') == 0:
			data = data[3:]

		return data.encode(self._encoding)



class CsvParser(DictParser):
	def __init__(self, *fieldnames, delimiter = ",", **settings):
		super().__init__(fieldnames = fieldnames or None, delimiter = delimiter, **settings)
		self.preparser_method = lambda *args, **kwargs: io.StringIO(*args, **kwargs)
		self.parser_method = lambda *args, **kwargs: csv.DictReader(*args, **kwargs)
		self.postparser_method = lambda x: [*x]
		self.parser_error = csv.Error



class HtmlParser(XmlParser):
	def __init__(self, *args, **settings):
		super().__init__(*args, **settings)
		from lxml import html as lxmlhtml
		from lxml import etree

		self.response_class = HtmlResponse
		self.parser_method = lambda *args, **kwargs: lxmlhtml.fromstring(*args, **kwargs)
		self.parser_error = etree.ParserError



# >>>>>>>>>>>>> ParserBuilder
class ParserBuilder:
	def __init__(self, parsercls, *args, **settings):
		self.parsercls = parsercls
		self.settings = dag.DotDict(settings)

	def buildparser(self, **settings):
		return self.parsercls(**(self.settings | settings))

	def parse(self, data):
		return self.buildparser().parse(data)

	def __call__(self, *args, **settings):
		return type(self)(self.parsercls, *args, **settings)
# <<<<<<<<<<<<< ParserBuilder





registered_parsers = dag.ItemRegistry()


registered_parsers.register("DAGRESPONSE", ParserBuilder(DagResponseParser))
registered_parsers.register("JSON", ParserBuilder(JsonParser))
registered_parsers.register("XML", ParserBuilder(XmlParser))
registered_parsers.register("HTML", ParserBuilder(HtmlParser))
registered_parsers.register("CSV", ParserBuilder(CsvParser))
registered_parsers.register("YAML", ParserBuilder(YamlParser))
registered_parsers.register("TOML", ParserBuilder(TomlParser))























def parse_response_item(response, response_parser = None):
	parser = response_parser or (dag.ctx.active_dagcmd.settings.response_parser)

	if not parser:
		return response

	# TRY: If paraser is actually a parserbuilder, build the parser
	try:
		parser = parser.buildparser()
	# EXCEPT AttrributError: Parser is not a parserbuilder. Assume it is already a parser 
	except AttributeError:
		pass

	try:
		if isinstance(response, str):
			return parser.parse(response)

		return [parser.parse(r) for r in response] 
	except parser.parser_error as e:
		dag.hooks.do("response_read_error", response, e)
		#print(f"DagResponse read error: \"{response}\" as {parser}\n\nERROR TEXT: {e}")
	except Exception as e:
		pass

	return str(response)





class ResponseParserAttrSettings(AttrSettable):
	def __init__(self, **settings):
		super().__init__(**settings)
		for parsername, parser in registered_parsers.items():
			self.set_settings_attr(parsername, "response_parser", parser, default = dag.Response)




def persist_response(response, dbfile):
	if not response:
		return

	import sqlite3

	response = dag.listify(response)

	con = sqlite3.connect(dbfile)

	with con:
		cur = con.cursor()

		for item in response:
			if not is_mapping(item):
				breakpoint()

			for key, value in item.items():
				breakpoint(show = (con, key, value))
				pass



@dag.oninit
def _():

	@dag.cmd
	def nested_response_db():
		data = [{
			"key1": "APPLE",
			"key2": "BANANA",
			"subdata": {
				"subdata1": 11,
				"subdata2": 100,
				"subdata3": {
					"subsub1": "AWOOGA",
					"subsub2": "WOOWOOWOO"
				},
			}
		},
		{
			"key1": "GRAPE",
			"key2": "TOMATO",
			"subdata": {
				"subdata1": 9.4,
				"subdata2": 903,
				"subdata3": {
					"subsub1": "STACK",
					"subsub2": "ATTACK"
				},
			}
		}

		]

		response = DictResponse(data)
		persist_response(response, dag.tempcache.generate_filepath("test-nested-db.db"))