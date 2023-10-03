import inspect, sys

import dag
from dag.util.attribute_processors import get_stored_attrs

from dag.dagcmd_exctx import DagCmdExecutionContext
from dag.cachefiles import cachefiles
from dag.tempcache import tempcachefiles
from dag.exceptions import StopDagCmdExecutionException



class DagCmdExecutor(DagCmdExecutionContext):
	def __init__(self, dagcmd, parsed, update_cache = False):
		super().__init__(dagcmd, parsed)

		self.update_cache = update_cache
		self.response = None
		self.has_updated_cache = False


	## THE dagcmd runner
	def run(self):
		dagcmd = self.dagcmd

		with dag.bbtrigger(self.dagcmd.cmdpath("_")):
			with dag.ctx(parsed = self.parsed, active_dagcmd = dagcmd, dagcmd_execution_ctx = self):
				try:
					self.response = self.run_dagcmd()

					with dag.ctx(active_response = self.response):
						self.cache_response()

					self.process_response()

					return self.response

				except dagcmd.settings.catch as e:
					dag.echo("<c red>>>>>DagCmd: Caught anticipated error:>>>></c red>")
					tb = dag.print_traceback()
					dag.echo("<c red><<<<DagCmd: Caught anticipated error:<<<<</c red>")
					return tb
				except StopDagCmdExecutionException:
					pass

	def process_response(self):
		return self.response


	@property
	def is_use_cache(self) -> bool:
		return self.dagcmd.settings.cache


	@property
	def is_should_write_cache(self) -> bool:
		return self.is_use_cache and (dag.settings.update_all_caches or self.update_cache or not self.is_cached())


	def cache_response(self):
		if self.is_should_write_cache:
			self.has_updated_cache = True
			self.write_cachefile()
		if self.dagcmd.settings.tempcache and not tempcachefiles.exists_from_dagcmd_exctx(self):
			self.write_tempfile()


	def write_cachefile(self):
		try:
			return cachefiles.write_from_dagcmd_exctx(self.response, self)
		except Exception as e:
			breakpoint()
			dag.echo(f"<c red>Writing CacheFile failed: ({e})</c red>")


	def write_tempfile(self):
		return tempcachefiles.write_from_dagcmd_exctx(self.response, self)


	def is_cached(self):
		return cachefiles.exists_from_dagcmd_exctx(self)


	# Used by CollectionDagCmd for further processing
	def run_dagcmd(self):
		with dag.ctx(parsed = self.parsed):
			return self.get_response()



	def get_response(self):
		with dag.ctx(parsed = self.parsed):
			response = None
			dagcmd = self.dagcmd

			if not dag.settings.update_all_caches and not self.update_cache and not dag.ctx.dontcache:
				# Check tempcache first
				if dagcmd.settings.tempcache and tempcachefiles.exists_from_dagcmd_exctx(self):
					response = tempcachefiles.read_from_dagcmd_exctx(self)

				elif self.is_use_cache and self.is_cached():
					response = self.read_from_cachefile()

				if response is not None:
					return response

			try:
				dag.hooks.do("before_evaulate_dagcmd", self.parsed)

				if dagcmd.settings.get("confirm"):
					confirmval = dagcmd.settings.confirmval

					if dag.cli.confirm(message = dagcmd.settings.confirm.format(**self.parsed), confirmval = confirmval):
						pass
					else:
						dag.echo("NO ACTION TAKEN")
						raise StopDagCmdExecutionException()

				# If "value" setting is set, grab that as response
				if "value" in dagcmd.settings:
					response = self.get_dagcmd_value()
				else:
					# If fn is Nabber: run the nabber
					if response is None and isinstance(dagcmd.fn, dag.Nabber):
						response = dag.nab_if_nabber(dagcmd.fn)
					
					# Runs the function if no cache or value setting found
					if response is None:
						response = self.run_fn()

			finally:
				dag.hooks.do("after_evaulate_dagcmd", self.dagcmd)

			return self.process_response_type(response)


	def process_response_type(self, response):
		dagcmd = self.dagcmd

		if dagcmd.settings.get("type") and isinstance(response, str):
			return dagcmd.settings.type(response)

		return response


	def read_from_cachefile(self):
		with dag.ctx(cachefile_reading = True):
			dag.hooks.do("dagcmd_before_cachefile_read")
			response = cachefiles.read_from_dagcmd_exctx(self)
			dag.hooks.do("dagcmd_after_cachefile_read", response)
			return response


	def get_dagcmd_value(self):
		dagcmd = self.dagcmd
		response = None

		try:
			dag.hooks.do("dagcmd_before_value")
			response = dagcmd.settings.value

			return response
		except:
			raise
		finally:
			if response is not None:
				dag.hooks.do("dagcmd_after_value", response)

			

	def run_fn(self):
		args, kwargs = self.translate_parsed_to_fn_args()
		dagcmd = self.dagcmd
		dagcmdcallframe = dagcmd._callframeinfo
		
		dag.hooks.do("dagcmd_before_fn")

		if dagcmd.argspec.args and dagcmd.argspec.args[0] == "self" and not inspect.ismethod(dagcmd.fn): # Inject the app anywhere where "self" is an arg
			args = [dagcmd.dagapp, *args]

		dagcmdfn = dagcmd.fn # Done this way to simplify stepping if ==breakpoint directive is being used

		#breakpoint(dag.settings.do_dagcmd_breakpoint)
		trace = dag.tracetools.FunctionCallBreakpointSetter(dagcmdcallframe.filepath, dagcmdcallframe.lineno) if dagcmdcallframe and dag.settings.do_dagcmd_breakpoint else None
		with dag.tracetools.set_systrace(trace):
			response = dagcmdfn(*args, **kwargs)

		dag.hooks.do("dagcmd_after_fn", response)
		return response
			

	# Used to make sure parsed dagargs.kwargs conform to internal callable argspec
	def translate_parsed_to_fn_args(self):
		parsed = self.parsed
		dagcmd = self.dagcmd
		argspec = dagcmd.argspec

		args = []
		nonself_args = [arg for arg in argspec.args if arg != "self"]

		for arg in nonself_args:
			if arg in parsed:
				args.append(parsed.get(arg))
					
		if argspec.varargs:
			argval = parsed.get(argspec.varargs, [])
			if isinstance(argval, (list, tuple)):
				args.extend(argval)
			else:
				args.append(argval)
				
		kwargs = {name:val for name,val in parsed.items() if name in argspec.kwonlyargs}
			
		if argspec.varkw:
			argnames = [*filter(None, (nonself_args + argspec.kwonlyargs) + [argspec.varargs])]
			kwargs.update({name:val for name,val in parsed.items() if name not in argnames})

		return (args, kwargs)





class CollectionDagCmdExecutor(DagCmdExecutor):
	def process_response(self):
		if not isinstance(self.response, (dag.Response, dag.Collection)):
			self.response = dag.Response(self.response)

		if dag.ctx.skip_make_collection:
			return self.response

		if not isinstance(self.response, dag.Collection):
			if self.dagcmd.resource_argname:
			 	self.dagcmd._settings['resource_argname'] = self.dagcmd.resource_argname

			self.response = dag.Collection(self.response, settings = self.dagcmd.settings, parsed = self.parsed, name = self.dagcmd.cmdpath())

		self.response.settings = self.dagcmd.settings # Updates the collection's settings to whatever is currently the collection dagcmd's settings

		self.response.collectioncmd = self.dagcmd

		if self.has_updated_cache:
			self.write_choices()
			
		return self.response


	@property
	def is_use_cache(self):
		return super().is_use_cache or (self.dagcmd.settings._resource_settings.label and self.dagcmd.settings.cache is not False);


	def write_choices(self):
		if choices := self.response.choices():
			self.dagcmd.write_cached_choices(self.response)