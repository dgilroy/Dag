import inspect

import dag
from dag.lib import comparison, dot
from dag.lib.proxy_descriptor import ProxyDescriptor
from dag.util import mixins, attribute_processors

from dag.responses import clean_name




class Resource(mixins.DagLaunchable, mixins.CacheFileNamer, mixins.DagStyleFormattable, mixins.DagDrillable, dot.DotAccess):
	def __init__(self, response, dagcollection = None, insertion_idx = -1):
		if not isinstance(response, dag.Response):
			response = dag.Response(response)

		if response.is_dict():
			for name in response._data.keys():
				setattr(self.__class__, name, ProxyDescriptor("_response", name))

		self._response = response or dag.Response({})


		if isinstance(response, Resource):
			dagcollection = self.response._dag.dagcollection
			self.response = response._response	
			
		self._dag = ResourceInfo(self)
		self._dag.dagcollection = dagcollection
		self._dag.settings = self._dag.dagcollection.settings._resource_settings
		self._dag.insertion_idx = insertion_idx


	def __contains__(self, attr):
		try:
			return attr in self._response
		except:
			return False



	# Mixin ABC methods
	def _dag_launch_item(self):
		return self._dag.launch_url

	def _dag_formatter_fn(self):
		return self._dag.settings.display

	def _dag_cachefile_name(self):
		if identifier := self._dag.identifier_setting:
			return getattr(self, identifier) # Done like this to not rush the formatting that happens inside the @properties

		return self



		
	def __add__(self, other):
		if isinstance(other, Resource):
			if self._dag.dagcollection.name != other._dag.dagcollection.name:
				raise TypeError("Resources must belong to the same collection")
		
			return self._dag.dagcollection.create_subcollection([self, other])
			
		elif isinstance(other, type(self._dag.dagcollection)):
			if self._dag.dagcollection.name != other.name:
				raise TypeError("Resource must belong to the collection it's being added to")
				
			other.append(self)
			return other
		
		raise TypeError("Must add Resource to other Resource")
		#return self.

		
	def __radd__(self, other): return self if other == 0 else self + other

			

	def __repr__(self): 
		try:
			try:
				keys = comparison.sortlist(list(self._response._keys()))
			except AttributeError:
				keys = ""

			return dag.format(f"""\n<c black b bg-orangered1>**Resource** </c>
<{object.__repr__(self)} -> {self._response=}>

<c b u>KEYS:</c> {keys}
<c b u>LABEL:</c> {self._dag.label}\n\n
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

















class ResourceInfo:
	def __init__(self, resource):
		self.resource = resource

	@property
	def launch_url(self):
		with dag.ctx(active_resource = self.resource):
			resource_format_dict = {}

			if self.resource._response and self.resource._response.is_dict():
				resource_format_dict = self.resource._response

			return launch.format(**{**self.dagcollection.parsed, **resource_format_dict}) if (launch := self.settings.launch) else None

		
	@property
	def label(self):
		with dag.ctx(active_resource = self.resource):
			try:
				label = self.settings.get('label')

				if label:
					if isinstance(label, dag.Nabber):
						label = self.settings.label
					else:
						if "{" in label:
							label = self.settings.label.format(**self.resource)
						else:
							label = dag.drill(self.resource, label)
						
					return clean_name(label, ignore_chars = self.settings.label_ignore_chars)

				return ""

			except AttributeError:
				return ""


	@property
	def id(self):
		with dag.ctx(active_resource = self.resource):
			try:
				if idd := self.settings.id:
					if "{" in idd:
						idd = self.settings.id.format(**self.resource)
					else:
						idd = getattr(self.resource, idd)
					
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
			return self.settings.label or self.settings.id


class ResourcesAttributeProcessor(attribute_processors.AttributeProcessor):
	def __init__(self, callerframe, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.callerframe = callerframe
		self.stop_storing_attrs = False


	def is_should_store_attribute(self):
		breakpoint()
		pass


	def __call__(self, *args, **kwargs):
		frame = inspect.stack()[1]
		breakpoint()
		pass

	def _dag_drill(self, drillee):
		breakpoint()
		pass