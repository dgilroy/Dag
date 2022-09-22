import json, collections, re, copyreg, csv, io
from collections.abc import Mapping, Sequence

import xml.etree.ElementTree
from lxml import etree
from lxml import objectify
from lxml import html as lxmlhtml

import yaml

import dag
from dag.lib.proxy_descriptor import ProxyDescriptor
from dag.util.mixins import DagLaunchable





def clean_name(name, ignore_chars = [], remove_chars = []):
	for ch in set([" ", "'", "/", "&amp;", ")", "&", ";", "|", "[", "]"] + remove_chars) - set(ignore_chars): #&, ;, | added for command splitting purposes
		name = name.replace(ch, "")		

		
	for ch in set(["("]): # Since ( tends to demarcate words, replace with period. ) is currently erased to prevent double dots when at the end of file names
		name = name.replace(ch, ".")

	return name.lower()




def is_mapping(data):
	return isinstance(data, Mapping)

def is_sequence(data):
	return isinstance(data, Sequence) and not isinstance(data, str)

def is_none(data):
	return data is None




class UnfilledArg: pass



class DagResponse(dag.dot.DotAccess, DagLaunchable, collections.abc.MutableSequence, collections.abc.MutableMapping):
	_dag_response_str_formatter = str


	def __init__(self, data = None, parser = None):
		# Contains the internal data

		while isinstance(data, DagResponse):
			data = data._data

		self._dag_response_data = data
		self._data = self._dag_response_data
		self._parser = parser
		self._dag_return_class = type(self)

		# Add to dict to make it a property (useful for dagpdb completions)
		if self.is_dict():
			for name, value in self._data.items():
				setattr(self.__class__, name, ProxyDescriptor("_data", name))




	# Implements DagLaunchable mixin
	def _dag_launch_item(self):
		return self._data


	# Mapping/Sequence/None type checking
	def is_mapping(self, data = UnfilledArg):
		data = data if data != UnfilledArg else self._data
		return is_mapping(data)

	is_dict = is_mapping


	def is_sequence(self, data = UnfilledArg):
		data = data if data != UnfilledArg else self._data
		return is_sequence(data)

	is_list = is_sequence


	def is_none(self, data = UnfilledArg):
		data = data if data != UnfilledArg else self._data
		return is_none(data)


	# ABC Methods
	def __setitem__(self, idx, value): self._data[idx] = value
	def __delitem__(self, idx): del self._data[idx]
	def __len__(self): return len(self._data)
	def __iter__(self): return iter([self.maybe_make_dagresponse(i) for i in self._dag_response_data])
	def insert(self, idx, value): self._dag_response_data.insert(idx, value)

	# Other magic methods
	def __bool__(self): return bool(self._data)
	def __reversed__(self): return self.maybe_make_dagresponse([i for i in reversed(self._dag_response_data)])

	def __eq__(self, other):
		data = other

		if isinstance(other, type(self)):
			data = other._data

		return self._data == data


	# FILTER
	# Search for subitems via a search dictionary {value_name: needle, ...}
	def _dag_do_filter(self, _dag_filter_fn, **values):
		# If no values: return Nothing
		if values is None or self._dag_response_data is None:
			return_items = None

		# Else, there are values: find items matching the values
		else:
			# All response items
			return_items = self

			# If responseItem's type is a mapping: put mapping's values() into an array
			if self.is_mapping():
				return_items = [*return_items.values()]

			for attr_name, needle in values.items():
				return_items = [item for item in return_items if _dag_filter_fn(item, attr_name, needle)]
				
		# Return the item, making it a DagResponse if not a primitive (str/int/etc...)
		return self.maybe_make_dagresponse(return_items)



	# Search for subitems via a search dictionary {value_name: needle, ...}
	def filter(self, **values):
		filterfn = lambda item, attr_name, needle: dag.drill(item, attr_name) == needle
		return self._dag_do_filter(filterfn, **values)



	def regex(self, **values):
		filterfn = lambda item, attr_name, needle: dag.drill(item, attr_name) and re.match(str(needle), str(item.get(attr_name)))
		return self._dag_do_filter(filterfn, **values)



	# Convert to a collection	
	def to_collection(self):
		from dag.dagcollections.collection import Collection # Done to prevent circular import
		
		response = self

		if not self.is_sequence():
			response = [self]

		return Collection(self)


	#
	# DICT METHODS
	#
	def _get(self, attr, default = None): return self.maybe_make_dagresponse(self._dag_response_data.get(attr, default))
	def _keys(self): return self._dag_response_data.keys()
	def _values(self): return [self.maybe_make_dagresponse(v) for v in self._dag_response_data.values()]
	def _items(self): return self._dag_response_data.items()




	# Internal data state methods
	@staticmethod
	def is_can_be_dagresponse(data = None):
		# Currently, None will be allowable as a ResponseType
		return is_mapping(data) or is_sequence(data)# or is_none(data) -> This was initially so that None.None.None.etc... would still work, but it was outputting as "null"


	# Process data being returned
	def maybe_make_dagresponse(self, data):
		if self.is_can_be_dagresponse(data):
			return self._dag_return_class(data)

		return data


	# Adding DagResponses together
	def __add__(self, other):
		if not isinstance(other, DagResponse):
			raise TypeError("Cannot add non-DagResponse to DagResponse")
			
		if self.is_sequence() and other.is_sequence():
			return self.maybe_make_dagresponse(self._dag_response_data + other._dag_response_data)
		if self.is_mapping() and other.is_mapping():
			return self.maybe_make_dagresponse({**self._dag_response_data, **other._dag_response_data})
		if self.is_none() and other.is_none():
			return self.maybe_make_dagresponse(None)

		raise TypeError("Must add two DagResponse Lists or two DagResponse Dicts")


	#
	# UNIONING
	#
	def __or__(self, other):
		return self._combine_dag_response_mappings(self, other)


	def __ior__(self, other):
		self._dag_response_data = self._combine_dag_response_mappings(self, other)


	def __ror__(self, other):
		return self._combine_dag_response_mappings(other, self)


	def _combine_dag_response_mappings(self, d1, d2):
		if not isinstance(d1, DagResponse) or not isinstance(d2, DagResponse):
			return NotImplemented

		if not d1.is_mapping() or not d2.is_mapping():
			return NotImplemented

		return self.maybe_make_dagresponse({**d1._dag_response_data, **d2._dag_response_data})



	#
	# ATTR ACCESS
	#
	def __getattr__(self, attr, default = None):
		try:
			return self.maybe_make_dagresponse(self._dag_response_data[attr])
		except (AttributeError, KeyError, TypeError):
			if attr in ("keys", "values", "get", "items"):
				return object.__getattribute__(self, attr)
		except Exception as e:
			breakpoint()
			pass

		return self.maybe_make_dagresponse(default)


	def __getitem__(self, idx):
		if self.is_list() and isinstance(idx, str):
			idx = int(idx)
 
		try:
			return self.maybe_make_dagresponse(self._data[idx])
		except IndexError:
			raise dag.DagError(f"Index {idx} not in response (response has length {len(self)})")



	def __getattribute__(self, attr):
		if attr in ("keys", "values", "get", "items"):
			return self.__getattr__(attr)
			
		return object.__getattribute__(self, attr)

	#
	# REPR
	#
	#def __repr__(self): return dag.format(f"\n<c b bg-chartreuse1 black>Dag Response Item:</c>\n\t{self._dag_response_str_formatter(self._dag_response_data)}\n")
	def __repr__(self): return dag.format(self._dag_response_str_formatter(self._dag_response_data) + "\n")











class JsonResponse(DagResponse):
	_dag_response_str_formatter = lambda self, x: json.dumps(x, indent=4, sort_keys=True)


class YamlResponse(DagResponse):
	_dag_response_str_formatter = lambda self, x: yaml.dump(x)




class XmlResponse(DagResponse):
	_dag_response_str_formatter = lambda self, x: str(etree.tostring(x, pretty_print=True), 'utf-8')

	def __getattr__(self, attr, default = None):
		# for getting text. In future maybe need _text to get attrs or tags
		if attr == "text":
			return self._data.text

		# If starts with _, favor attributes before tags
		breakpoint()
		if attr.startswith('_') and attr[1:] in self._data.attrib:
			return self._data.attrib.get(attr[1:], default)

		item = self._data.findall(attr)
		
		# If no tag found, see whether attribute exists
		if len(item) == 0:
			item = self._data.attrib.get(attr, default)
		# If only one element, return XMLResponse
		elif len(item) == 1:
			item = self.__class__(item[0])
		# If multiple elements, return list of XMLResponses
		else:
			item = [self.__class__(item) for item in item]

		return self.maybe_make_dagresponse(item)
		
		
	def select(self, selector):
		items = [self._parser.parse(etree.tostring(item, encoding = "unicode")) for item in self._data.cssselect(selector)]

		#if len(items) == 1 && selector.split()[-1].startswith("#"):
		#	return items[0]
		# Could make this work with ID stuff, but then things get confousing if something is poorly made and has multiple ID's.
		# Could implement so that if a single item is iterated over, it just yields itself, similar to how FirefoxElement is currently done

		return items
		return self.maybe_make_dagresponse(items)
		
		
	def css(self, selector):
		return self.select(selector)

		
	def __repr__(self):
		return str(etree.tostring(self._data, pretty_print=True), 'utf-8')


	def __bool__(self):
		return str(self) not in ["[]", ""]


	def __getitem__(self, item):
		if isinstance(item, (int, slice)):
			return self[item]
		else:
			return self.select(item)



class HtmlResponse(XmlResponse):
	_dag_response_str_formatter = lambda self, x: str(etree.tostring(x, pretty_print=True), 'utf-8')

	@property
	def text(self):
		return self._data.text_content()


	def __getattr__(self, item):
		return self.select(item)
		



# Used to pickle HTML Responses
def pickle_HtmlResponse(htmlresponse):
	return HtmlResponse, (htmlresponse._data, htmlresponse._parser)
copyreg.pickle(HtmlResponse, pickle_HtmlResponse)



class CsvResponse(DagResponse):
	pass

		








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
		return self.response_class(postparsed_data, self)

	def __call__(self, *args, **settings):
		return type(self)(*args, **settings)



class JsonParser(DagResponseParser):
	response_class = JsonResponse
	parser_method = lambda self, *args, **kwargs: json.loads(*args, **kwargs)
	parser_error = json.decoder.JSONDecodeError


class YamlParser(DagResponseParser):
	response_class = YamlResponse
	parser_method = lambda self, *args, **kwargs: yaml.load(*args, Loader = yaml.FullLoader, **kwargs)
	parser_error = yaml.YAMLError


class XmlParser(DagResponseParser):
	response_class = XmlResponse
	parser_method = lambda self, *args, **kwargs: objectify.fromstring(*args, **kwargs)
	parser_error = xml.etree.ElementTree.ParseError


	def preparser_method(self, data):
		# utf-8 bc lxml is annoying
		if data.find('ï»¿<') == 0:
			data = data[3:]

		return data.encode(self._encoding)



class HtmlParser(XmlParser):
	response_class = HtmlResponse
	parser_method = lambda self, *args, **kwargs: lxmlhtml.fromstring(*args, **kwargs)
	parser_error = etree.ParserError


class CsvParser(DagResponseParser):
	response_class = CsvResponse
	preparser_method = lambda self, *args, **kwargs: io.StringIO(*args, **kwargs)
	parser_method = lambda self, *args, **kwargs: csv.DictReader(*args, **kwargs)
	postparser_method = lambda self, x: [*x]
	parser_error = csv.Error

	def __init__(self, *fieldnames, delimiter = ",", separator = ",", **settings):
		super().__init__(fieldnames = fieldnames, delimiter = delimiter, **settings)




registered_parsers = {}

def register_parser(name, parser):
	registered_parsers[name] = parser

register_parser("JSON", JsonParser())
register_parser("XML", XmlParser())
register_parser("HTML", HtmlParser())
register_parser("CSV", CsvParser())
register_parser("YAML", YamlParser())



























def parse_response_item(response, response_parser = None):
	parser = response_parser or (dag.ctx.active_dagcmd.settings.response_parser) or DagResponseParser()

	try:
		if isinstance(response, str):
			return parser.parse(response)

		return [parser.parse(r) for r in response] 
	except parser.parser_error as e:
		dag.hooks.do("response_read_error", response, e)
		print(f"DagResponse read error: \"{response}\" as {parser}\n\nERROR TEXT: {e}")
	except Exception as e:
		breakpoint()
		pass

	return DagResponse(response)

