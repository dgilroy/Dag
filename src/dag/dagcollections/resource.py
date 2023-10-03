import inspect, copy, json
from functools import partial
from typing import Annotated
from types import GenericAlias

import dag
from dag.lib import comparison, dot
from dag.lib.proxy_descriptor import ProxyDescriptor
from dag.util import mixins, lambdabuilders




class Resource(mixins.DagLaunchable, mixins.CacheFileNamer, mixins.DagStyleFormattable, mixins.DagDrillable, dot.DotAccess, mixins.DagSettings):
	def __init__(self, response, collection = None):
		breakpoint(collection)
		if not isinstance(response, dag.Response):
			response = dag.Response(response)

		if dag.is_mapping(response):
			for name in response._data.keys():
				setattr(self.__class__, name, ProxyDescriptor("_response", name))

		self._response = response or dag.Response({})

		if isinstance(response, Resource):
			collection = self.response._dag.collection
			self.response = response._response	

		self._dag = ResourceInfo(self, collection)


	def __call__(self):
		return self._dag


	def __class_getitem__(cls, item):
		# Get item via Annotated.__metadata__. Get cls by Annotated.__origin__
		return GenericAlias(cls, item)


	def __contains__(self, attr):
		try:
			return attr in self._response
		except:
			return False



	# Mixin ABC methods
	def _dag_get_settings(self):
		return self().settings

	def _dag_launch_item(self):
		return self().launch_url

	def _dag_formatter_fn(self):
		return self().settings.display

	def _dag_cachefile_name(self):
		return self._dag_identifier_value() or self


	def __format__(self, formatstr):
		return dag.drill(self(), formatstr)


	def _dag_identifier_value(self):
		identifier = (self().settings.id or self().settings.label) or ""

		try:
			identifier = identifier.format(**self)
		except Exception:
			pass

		try:
			identifier = dag.drill(self, identifier)
		except:
			pass


		return identifier


	def __add__(self, other):
		if isinstance(other, Resource):
			if self._dag.collection.name != other._dag.collection.name:
				raise TypeError("Resources must belong to the same collection")
		
			return self._dag.collection.create_subcollection([self, other])
			
		elif isinstance(other, type(self._dag.collection)):
			if self._dag.collection.name != other.name:
				raise TypeError("Resource must belong to the collection it's being added to")
				
			other.append(self)
			return other
		
		raise TypeError("Must add Resource to other Resource")
		#return self.

		
	def __radd__(self, other): return self if other == 0 else self + other


	def __repr__(self): 
		response = self._response

		try:
			
			with dag.catch() as e:
				if dag.is_mapping(self._response):
					response = {}

					for k, v in self._response._data.items():
						if isinstance(v, dict):
							pass
						elif not isinstance(v, (str, int, bool)):
							try:
								v = v._dag_resource_repr()
							except (AttributeError, TypeError):
								v = v.__repr__()

						response[k] = v
				else:
					pass

			response = json.dumps(response, indent=4, sort_keys=True, cls = self._response._dag_json_encoder())
		except Exception as e:
			breakpoint()
			pass

		try:
			try:
				keys = comparison.sortlist(list(response._keys()))
			except AttributeError:
				keys = ""

			return dag.format(f"""\n
<c black b bg-#A00>>>>> Dag Resource </c>
<{object.__repr__(self)} -> self._response={response}>

<c b u>KEYS:</c> {keys}
<c b u>LABEL:</c> {self._dag.label}\n\n
<c black b bg-#A00><<<<< Dag Resource </c>\n
""")
		except Exception as e:
			breakpoint()
			pass


	def set(self, attr,value):
		self._response._data[attr] = value
		return self


	def __len__(self):
		return 1


	def __getattr__(self, attr):
		return getattr(self._response, attr)


	def __dir__(self):
		return [*set(object.__dir__(self) + dir(object.__getattribute__(self, "_response")))]

		
	def __getitem__(self, attr):
		return self._response[attr]


	def __iter__(self):
		yield self


	def keys(self):
		return self._response.keys()
#<<<< Resource



#>>>> ResourceInfo
class ResourceInfo:
	def __init__(self, resource, collection):
		self.resource = resource
		self.collection = collection


	def __getattr__(self, attr):
		item = self.settings.get(attr)

		if isinstance(item, ResourcesLambdaBuilder):
			return item(self.resource)

		return item


	@property
	def settings(self):
		return self.collection.settings | self.collection.settings._resource_settings


	@property
	def launch_url(self):
		with dag.ctx(active_resource = self.resource):
			resource_format_dict = {}

			if self.resource._response and dag.is_mapping(self.resource._response):
				resource_format_dict = self.resource._response

			launch = self.settings.launch

			if callable(launch):
				launch = launch(self.resource)

			launch = launch or ""

			return launch.format(**{**self.collection.parsed, **resource_format_dict})

		
	@property
	def label(self):
		with dag.ctx(active_resource = self.resource):
			try:
				label = self.settings.get('label')

				if label:
					if callable(label):
						label = label(self.resource)
					elif isinstance(label, dag.Nabber):
						label = self.settings.label
					else:
						if "{" in label:
							label = self.settings.label.format(**self.resource)
						else:
							label = dag.drill(self.resource, label)
						
					return dag.slugify(label, ignore_chars = self.settings.label_ignore_chars)

				return ""

			except AttributeError:
				return ""


	@property
	def id(self):
		with dag.ctx(active_resource = self.resource):
			try:
				if idd := self.settings.id:
					if isinstance(idd, str) and "{" in idd:
						idd = self.settings.id.format(**self.resource)
					else:
						idd = dag.drill(self.resource, idd)
					
					return str(idd)
					
				return ""
			except AttributeError:
				return ""


	@property
	def identifier(self):
		with dag.ctx(active_resource = self.resource):
			return self.label or self.id


	@property
	def identifier_setting(self):
		with dag.ctx(active_resource = self.resource):
			identifier = self.settings.label or self.settings.id

			if callable(identifier):
				identifier = identifier()
				
			return identifier
#<<<< ResourceInfo


class ResourcesLambdaBuilder(lambdabuilders.LambdaBuilder):
	def _do_call(self, *args, **kwargs):
		if dag.ctx.active_resource:
			return super()._do_call(dag.ctx.active_resource)

		return super()._do_call(*args, **kwargs)