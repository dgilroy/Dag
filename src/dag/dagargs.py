import os, re, math, re, inspect, types, copy, string
from functools import cached_property
from collections import UserList
from collections.abc import Sequence

import dag
from dag.lib import strtools, dummies
from dag.lib.dtime import DateParser, TimeParser
from dag.util import nabbers, rslashes
from dag.util.argspectools import map_argspec_to_locals 

from dag.exceptions import DagError, DagArgParserError, DagArgValidationException
from dag.parser import inputobjects
from dag.parser.arguments import CliArgument, PrefixedCliArgument



SHORT_NAMED_PREFIX = "-"
LONG_NAMED_PREFIX = "--"


def clean_name(name: str) -> str:
	return name.lstrip(SHORT_NAMED_PREFIX).replace("*", "")


def is_named_arg(token: str) -> re.Match:
	return re.match(fr"^{SHORT_NAMED_PREFIX}[a-zA-Z]", token) or token.startswith(LONG_NAMED_PREFIX)


def is_short_named_arg(token: str) -> re.Match:
	return re.match(rf"^{SHORT_NAMED_PREFIX}[a-zA-Z]", token)


def maybe_add_dagargslist_to_fn(fn):
	if not hasattr(fn, "dagargs"):
		with dag.catch() as e:
			argspec = inspect.getfullargspec(fn)
			fn.dagargs = DagArgsList(argspec = argspec)
	return fn


class ExpansionList(UserList):
	pass




class ArgBuilder(): # Hopefully someday can make it so that dag.arg("name", **settings) will yield a simple dagarg
	def __init__(self):
		self.names = ()
		self.settings = {}


	def __getattr__(self, attr):
		if attr in registered_settings:
			self.settings |= registered_settings[attr]

		return self


	def __call__(self, *names, **settings):
		dagargclass = get_dagarg_class(self.settings)
		dagarg = dagargclass(*(self.names + names), **(self.settings | settings))
		return dagarg




def get_dagarg_class(settings = None, fn = None):
	settings = settings or {}
	if fn is None:
		return settings.get("_arg_type", DagArg)




def build_from_type(argtype, name, argspec):
	settings = {}
	metadata = ()

	if isinstance(argtype, types.GenericAlias):
		argtype, metadata = dag.parse_annotated(argtype)

		if argtype == dag.Resource and metadata:
			settings |= {"collectioncmd": metadata[0]}
	
	if (annosettings := registered_arg_annotations.get(argtype)):
		annotatedsettings = annosettings.settings

		if annosettings.defaultvaluesettings and clean_name(name) in dag.argspectools.get_default_values(argspec):
			annotatedsettings = annosettings.defaultvaluesettings[dag.argspectools.get_default_values(argspec)[clean_name(name)]]

		settings |= annotatedsettings

	argclass = get_dagarg_class(settings)
	#argclass = argclass.process_argclass(argtype, metadata)

	arg = argclass(*dag.listify(name), **settings)
	arg = arg.process_annotated_metadata(argtype, *metadata)
	return arg





#>>>> DagArg
class DagArg(CliArgument):
	handles_arrays = False

	def __init__(self, *names, **settings):
		self.names = names
		self.name = None
		self.shortname = None

		self.settings = nabbers.NabbableSettings(settings)
		self.initialize()
		self.process_names()

		self.target = self.settings.target or self.clean_name


	def get_default(self, incmd):
		return self.settings.default


	def process_incmd(self, incmd, value): # NOTE, TAKES 2ND ARGUMENT
		return incmd


	def process_annotated_metadata(self, argtype, *metadata):
		return self


	def process_raw_parser(self, rawparser):
		if self.is_named_dagarg and not self.clean_name:
			rawparser.is_positional_only = True
			return False

		return True


	def expand_parsed(self, parsed, inputarg):
		return


	def process_icresponse(self, ic_response):
		pass


	def generate_input_argument(self, parser):
		from dag.parser.inputdagargs import InputDagArg
		breakpoint() # Not sure if I need this function call anymore. If I do, figure out how to handle passing value into InputDagArg (pop(0) or [0])
		return InputDagArg(dagarg = self, incmd = parser.incmd, value = parser.proctokens[0])


	def initialize(self):
		self.settings.setdefault("prompt_prefill", "")
		self.settings.setdefault("prompt_if", True)
		self.settings.setdefault("cacheable", True)
		self.settings.setdefault("nargs", 1)

		if self.settings.get("nargs") == -1:
			self.settings["nargs"] = float("inf")

		self._init_settings()


	def __call__(self, fn = None):
		return self.process_fn(fn)


	def process_fn(self, fn = None):
		from dag.dagcmds import extract_fn

		if fn:
			fn, origfn = extract_fn(fn)
			maybe_add_dagargslist_to_fn(fn)

			with dag.catch() as e:
				fn.dagargs.add(self)

			if (annotations := dag.get_annotations(fn)):
				if annotations:
					names = [name.lstrip('-') for name in self.names]
					target = [self.settings.get('target')]

					annotationname = set(annotations).intersection(set(names + target))

					if annotationname:
						annotationname = [*annotationname][0]
						annotationtype = annotations[annotationname]

						dagarg_template_name = registered_arg_annotations.get(annotationtype)

						if dagarg_template_name:
							self.settings |= registered_settings.get(dagarg_template_name, {})

			return origfn # This is done for chaining of dagarg decorators

		return fn


	def filter_icresponse(self, icresponse):
		items = icresponse.raw_response

		if "filter" in self.settings:
			items = []

			for i in icresponse.raw_response:
				if self.settings.filter(i):
					items.append(i)

			if isinstance(response, dag.Collection):
				items = response.create_subcollection(items)

			icresponse.raw_response = items


	def __repr__(self):
		return f"<\"{self.name}\": {object.__repr__(self)}>"


	def _init_settings(self):
		"""Used by subclasses"""
		pass


	def process_names(self):
		global LONG_NAMED_PREFIX

		if not self.names:
			raise ValueError("DagArg requires at least one name")

		if self.settings.nargs and len(self.names) > self.settings.nargs:
			raise ValueError(f"Too many arg names for arg {self.names[0]}. {len(self.names)} detected, but only this arg only takes {dag.words.quantize('argument', self.settings.nargs)} ")

		self.name = self.names[0]
		self.shortname = ""

		self.validate_names()

		names = self.name.split()

		if len(names) == 2 and self.is_named_dagarg:
			longidx = 0 if names[0].startswith(LONG_NAMED_PREFIX) else 1
			shortidx = 0 if longidx else 1
			self.name = names[longidx]
			self.shortname = names[shortidx]
		
		self.settings.setdefault("required", self.is_positional_dagarg)


	def validate_names(self):
		global SHORT_NAMED_PREFIX

		with dag.catch() as e:
			if  len(self.names) > max(self.settings.nargs, 1) and self.is_positional_dagarg: # max(.,.) is here because flags have nargs of 0
				raise AttributeError(f"Positional Dagarg only takes {dag.words.quantize('name', self.settings.nargs)}")

		if  len(self.names) == 2 and self.is_named_dagarg:
			n1, n2 = self.names[0], self.names[1]
			smatch = r"^-\w"
			lmatch = r"^--\w"
			nmatch = r"^\w"

			if re.match(smatch, n1) and re.match(smatch, n2):
				raise AttributeError(f"Two short names (starting with '-') detected: {n1}, {n2}")

			if re.match(lmatch, n1) and re.match(lmatch, n2):
				raise AttributeError(f"Two long names (starting with '--') detected: {n1}, {n2}")

			if re.match(nmatch, n2):
				raise AttributeError(f"Both arguments of a named dagarg must start with a {SHORT_NAMED_PREFIX}. Detected: {n2}")




		if  len(self.names) > 2:
			raise AttributeError("Named DagArg takes at most 2 names (long & short)")


	def apply_value_to_parsed(self, val, parsed):
		parsed[self.target] = val
		return parsed



	def process_parsed_arg(self, argval):
		return argval


	def process_raw_argval(self, value, incmd):
		return value


	@property
	def __name__(self):
		return self.__class__.__name__


	def skip_if_unfilled(self):
		return False


	def modify_completion_text(self, text):
		return text


	def validate_input_formatting(self, inputarg):
		return True


	def complete(self, incmd, parsed, inputarg):
		return []



	@property
	def is_named_dagarg(self):
		return is_named_arg(self.name)


	@property
	def is_positional_dagarg(self):
		global SHORT_NAMED_PREFIX
		try:
			return not self.name.startswith(SHORT_NAMED_PREFIX)
		except AttributeError as e:
			breakpoint()
			pass
	

	@property
	def clean_name(self) -> str:
		return clean_name(self.name)


	@property
	def clean_shortname(self) -> str:
		return clean_name(self.shortname or "")
#<<<< DagArg
	

#>>>> ResourceDagArg
class ResourceDagArg(DagArg):
	def _init_settings(self):
		if "collectioncmd" in self.settings:
			self.settings.type = dag.Resource[self.settings['collectioncmd']]
		else:
			self.settings.type = dag.Resource


	def process_annotated_metadata(self, argtype, *metadata):
		if metadata:
			if len(metadata) > 1:
				newarg = ResourcesDagArg(*self.names, **self.settings)
				newarg.settings["collectioncmd"] = metadata;
				return newarg

			self.settings["collectioncmd"] = metadata[0];

		return self


	@classmethod
	def process_argclass(cls, argtype, metadata):
		#breakpoint()
		return argtype


	@property
	def collectioncmds(self):
		# Kept in ResourceDagArg (rather than ResourcesDagArg) because alist uses it to get resource cmds
		return dag.listify(self.settings.collectioncmd)

	@property
	def collectioncmd(self):
		return self.settings.collectioncmd

	@property
	def collection(self):
		return self.get_collection_from_collectioncmd(self.collectioncmd)


	def expand_parsed(self, parsed, inputarg):
		if isinstance(inputarg.value, ExpansionList):
			parseds = []

			for i in inputarg.value:
				newparsed = parsed.copy()
				newparsed[inputarg.target] = i
				parseds.append(newparsed)

			return parseds


	def is_alist_resourcedagarg(self, collectioncmd = None):
		alist = dag.instance.controller.alist

		if not alist:
			return False

		collectioncmds = collectioncmd or self.collectioncmds
		collectioncmds = dag.listify(collectioncmd)

		for collection_dagcmd in self.collectioncmds:
			if collection_dagcmd == alist.collection_dagcmd:
				return True

		return False


	def check_alist_for_collectioncmd(self, value, collectioncmd):
		from dag.dagcli import alists

		alist = dag.instance.controller.alist
		resource = None

		if collectioncmd == alist.collection_dagcmd:
			if match := re.fullmatch(fr"({alists.ALIST_REGEX})(:{{1,2}})({alists.ALIST_REGEX})", value):
				resources = ExpansionList()

				idx1, ranger, idx2 = match.groups()

				idx1 = alist.current_id if idx1 == "_" else dag.strtools.strtoint(idx1)
				idx2 = alist.current_id if idx2 == "_" else dag.strtools.strtoint(idx2)

				match ranger:
					case "::": #:: translates to [items)
						idx2 += 1
					case ":": #: translates to [items]
						pass

				try:
					for i in range(idx1, idx2):
						resources.append(alist[i])
				except Exception:
					pass

				return resources

			if dag.strtools.isint(value, "+-") or (value == "_" and alist.current_id):
				if dag.strtools.isint(value, "+-"):
					return alist[dag.strtools.strtoint(value)]
				elif value == "_" and alist.current_id:
					return alist[alist.current_id]
				else:
					raise ValueError("alist Index must be an integer") #This is set up because if non-int is passed into alist-accepting cmd, gets stuck in infinite loop

				if not collectioncmd.is_labelled and dag.dagcli.alists.isidx(value):
					dag.echo("<c #DF87FF underline>THIS ALIST HAD NOT BEEN GENERATED. PLEASE RUN COMMAND AGAIN</c>\n")
					raise DagError(f"This command's Alist had not been generated. Please run \"<c #DF87FF underline / {self.collectioncmd.cmdpath(' ')}>\" first")

		return resource

	
	def process_raw_argval(self, value, incmd):
		if not value:
			return None

		#ALIST CHECK
		if resource := self.check_alist_for_collectioncmd(value, self.collectioncmd):
			return resource

		if self.collectioncmd.is_labelled:
			collection = self.get_collection_from_collectioncmd(self.collectioncmd)
			resource = self.collection.find(value)

		if resource is None:
			raise DagArgParserError(f"\"{value}\" not found in <c u>{self.collectioncmd.name}</c u>")

		if resource and self.settings.get("drill"):
			resource = dag.drill(resource, self.settings.drill)

		return resource


	def get_collection_from_collectioncmd(self, collectioncmd):
		if isinstance(collectioncmd, dag.Collection): # Sometimes, might have "collectioncmd = this.COLLECTION().filter(blah...)"
			return collectioncmd
		else:
			argspec_args = map_argspec_to_locals(collectioncmd.argspec, {"args": (), "kwargs": dag.ctx.parsed})
			return collectioncmd(**argspec_args)


	def get_collectioncmd_from_collection(self, collectioncmd):
		if not isinstance(collectioncmd, dag.Collection): # Sometimes, might have "collectioncmd = this.COLLECTION().filter(blah...)"
			return collectioncmd
		else:
			return collectioncmd.collectioncmd


	def get_collection_resources_from_rslash(self, item, collection):
		resources = []

		pattern, flags = rslashes.get_regex_content(item)
		if res := collection.find_regex(pattern, flags = flags):
			resources.append(res)

		return resources


	def get_resource_from_collection(self, value, collection, incmd):
		return collection.find(value) or None


	def complete_from_collectioncmd(self, incmd, parsed, collectioncmd):
		try:
			collection = None

			compitems = []
			alist = dag.instance.controller.alist

			if alist and self.is_alist_resourcedagarg(collectioncmd):
				compitems += [str(i) for i in range(len(alist))]

			if isinstance(collectioncmd, dag.Collection):
				compitems += collectioncmd.choices()
			else:
				if not collectioncmd.is_labelled:
					return compitems

				# If collection is already cached and there's an arg filtering the colleciton: get the filtered collection
				if incmd.is_cached_collection and len(incmd.inputargs) >= 2 and isinstance(incmd.inputargs[-2], PrefixedCliArgument):
					icresponse = incmd.execute_all_but_last_inputarg()
					collection = icresponse.raw_response

				if collection:
					compitems += collection.choices()
				else:
					if collectioncmd.settings.cache:
						compitems += collectioncmd.get_cached_choices(incmd, parsed)
					else:
						compitems += collectioncmd().choices()

			return compitems
		except (AttributeError, TypeError) as e:
			breakpoint()
			return []


	def complete(self, incmd, parsed, inputarg):
		return self.complete_from_collectioncmd(incmd, parsed, self.collectioncmd)
#<<<< ResourceDagArg


#>>>> OpResourceDagArg
class OpResourceDagArg(ResourceDagArg):
	def get_default(self, incmd):
		return incmd.settings.default
#<<<< OpResourceDagArg


#>>>>  ResourcesDagArg
class ResourcesDagArg(ResourceDagArg):
	def _init_settings(self):
		super()._init_settings()

		if "collectioncmd" in self.settings:
			self.settings.collectioncmd = dag.listify(self.settings.collectioncmd)


	def yield_collections_from_collectioncmd(self, incmd):
		for collectioncmd in self.collectioncmds:
			yield self.get_collection_from_collectioncmd(collectioncmd)


	def get_resource_from_value(self, value, incmd):
		for collection in self.yield_collections_from_collectioncmd(incmd):
			if res := self.get_resource_from_collection(value, collection, incmd):
				return res, collection
				
		return None, None


	def complete(self, incmd, parsed, inputarg):
		choices = []

		for collectioncmd in self.collectioncmds:
			choices.extend(self.complete_from_collectioncmd(incmd, parsed, collectioncmd))
			
		return choices


	def get_resources_from_rslash(self, item, incmd):
		resources = []

		for collection in self.yield_collections_from_collectioncmd(incmd):
			resources.extend(self.get_collection_resources_from_rslash(item, collection))

		return resources


	def process_raw_argval(self, value, incmd):
		alist = dag.instance.controller.alist

		if not value:
			return None

		try:
			#ALIST CHECK HERE BEFORE GET COLLECTION
			for collectioncmd in self.collectioncmds:
				if resource := self.check_alist_for_collectioncmd(value, collectioncmd):
					return resource

			resource, collection = self.get_resource_from_value(value, incmd)

			if resource is None:
				try:
					collectionnames = ", ".join(map(lambda x: x.cmdpath(), self.collectioncmds))
				except AttributeError:
					collectionnames = ""
					
				collection = dag.words.pluralize_by_quantity("collectioncmd", len(self.collectioncmds))
				breakpoint()
				raise DagArgParserError(f"\"{value}\" not found in {collection} <c u>{collectionnames}</c u>")

			if resource and self.settings.get("drill"):
				resource = dag.drill(resource, self.settings.drill)

			return resource

		except (AttributeError, TypeError) as e:
			breakpoint()
			return value
#<<<< ResourcesDagArg
	

#>>>> CollectionResourceDagArg
class CollectionResourceDagArg(ResourceDagArg):	
	def _init_settings(self):
		self.settings.required = False
		self.settings.cacheable = False


	def filter_icresponse(self, icresponse):
		inputarg = icresponse.incmd.dagargsmap[self]
		icresponse.raw_response = inputarg.value


	def process_raw_argval(self, value, incmd):
		resources = []

		if rslashes.item_is_rslash(value):
			resources = self.get_collection_resources_from_rslash(value, self.collection)
		elif "*" in value:
			itemregex = f"^{value}$".replace("*", ".*")
			resources = self.collection.find_regex(itemregex)
		else:
			resources = super().process_raw_argval(value, incmd)

		return sum(resources) or []


	def skip_if_unfilled(self):
		return True
#<<<< CollectionResourceDagArg


#>>>> CollectionResourceMethodDagArg
class CollectionResourceMethodDagArg(DagArg):
	def _init_settings(self):
		self.settings.required = False
		self.settings.cacheable = False


	def complete(self, incmd, parsed, inputarg):
		cmds = self.settings.collectioncmd.get_resource_dagcmds()
		return [c.name.replace("_", "-") for c in cmds]


	def process_incmd(self, incmd, value):
		cmds = self.settings.collectioncmd.get_resource_dagcmds()

		for cmd in cmds:
			if value[0] in cmd.names() + [n.replace("_", "-") for n in cmd.names()]:
				# Save old values
				oldparsed = incmd.raw_parsed
				olddagargs = incmd.dagargs
				oldval = oldparsed[self.settings.collectioncmd.resource_name]

				# Set incmd for new dagcmd
				incmd.set_dagcmd(cmd)
				incmd.rawparser.parsed = {}
				incmd.rawparser.positionalargs = incmd.dagargs.positionalargs

				# Inject resource as first positional arg
				arg = incmd.dagargs.positionalargs[0]
				target = arg.target
				argname = arg.clean_name
				incmd.rawparser.parsed[target] = oldval
				incmd.rawparser.positionalidx = 1
				incmd.inputdagargs = {}
				incmd.inputargs = inputobjects.InputObjects()
				incmd.args = oldval + incmd.rawparser.tokens


				# IF first arg is not a ResourceDagArg: convert it to a ResourceDagArg (this is used by @dag.cmd.ResourceMethod)
				if not isinstance(incmd.dagargs.positionalargs[0], ResourceDagArg):	
					oldarg = incmd.dagargs.positionalargs[0]
					resarg = ResourceDagArg(argname, **oldarg.settings, collectioncmd = self.settings.collectioncmd)
					incmd.dagargs.dagargs_dict[argname] = resarg
					incmd.dagargs.positionalargs[0] = resarg

				return incmd
#<<<< CollectionResourceMethodDagArg



class ColorDagArg(DagArg):
	def process_raw_argval(self, val, incmd):
		return dag.colors.fromstr(val)

	def complete(self, incmd, parsed, inputarg):
		return list(dag.get_terminal().colormap.keys()) + list(dag.get_terminal().stylemap.keys()) + list(dag.colors.htmlcolornames.keys())



class DagCmdDagArg(DagArg):
	def complete(self, incmd, parsed, inputarg):
		return dag.defaultapp.dagcmds.get_completion_names()



class MessageDagArg(DagArg):
	def validate_input_formatting(self, inputarg):
		value = inputarg.joined_value

		if not strtools.is_valid_quoted_string(value):
			breakpoint()
			raise DagArgValidationException(f"Message Arg \"<c u b>{self.name}</c u b>\" must be wrapped by two matching unescaped quotation marks")

		return True


	def provide_autofill(self, incmd, indagarg):
		if indagarg.joined_value == "":
			return '""'

		return ""


	def autofill_move_cursor(self, incmd, indagarg) -> int:
		return -1



class IntDagArg(DagArg):
	def _init_settings(self):
		self.settings.setdefault("min", -math.inf)
		self.settings.setdefault("max", math.inf)

	def process_raw_argval(self, number, incmd):
		number = int(dag.lib.mathtools.eval_math(number))

		if self.settings.range is not None:
			return sorted((self.settings.range[0], number, self.settings.range[1]))[1]

		return sorted((self.settings.min, number, self.settings.max))[1]
		

#>>>> DTimeDagArg
class DTimeDagArg(DagArg):
	parser = None

	def process_raw_argval(self, date_str, incmd):
		dtime = self.parse_dtime(date_str)
		return self.process_dtime(dtime)


	def process_parsed_arg(self, dtime):
		if self.settings.dateformat is None:
			dtime.formatstr = dag.ctx.active_dagcmd.settings.dateformat or dag.lib.dtime.default_formatstr

		return dtime


	def parse_dtime(self, dtstr):
		return self.parser.parse(dtstr, self.settings.dateformat)


	def process_dtime(self, dtime):
		return dtime


	def complete(self, incmd, parsed, inputarg):
		return list(self.parser.named_values.keys())		
#<<<< DTimeDagArg



class DateDagArg(DTimeDagArg):
	parser = DateParser


class TimeDagArg(DTimeDagArg):
	parser = TimeParser



#>>>> MonthDagArg
class MonthDagArg(DTimeDagArg):
	def _init_settings(self):
		self.settings.setdefault("complete", dag.dtime.monthstrs)


	def parse_dtime(self, dtstr):
		if dtstr.isdigit():
			month = int(dtstr)
			if month >= 13:
				raise ValueError("Month must be <= 12")

			return dag.DTime(year = dag.now().year, month = month).firstofmonth

		return dag.DTime(dtstr).firstofmonth


	def complete(self, incmd, parsed, inputarg):
		return self.settings.complete
#<<<< MonthDagArg



		
		
# >>>> PathDagArg		
class PathDagArg(DagArg):
	def _init_settings(self):
		self.settings.setdefault("file", True)
		self.settings.setdefault("dir", True)
		self.settings.setdefault("expanduser", True)
		self.settings.setdefault("resolve", True)
		self.settings.setdefault("no_space", True)


	def process_raw_argval(self, value: str, incmd) -> dag.Path | str | bool:
		#value = strtools.escape_unescaped_spaces(value) <- commented out bc it was messing up for filenames with unescaped spaces
		path = dag.Path(value.replace('"', "").replace("'", ""))

		if self.settings.expanduser:
			path = path.expanduser()

		if self.settings.resolve: # <- Turn "." into path of current directory, "../" to path of parent, etc
			path = path.resolve()

		if self.settings.force and not os.path.exists(value):
			os.mknod(path)
			
		if self.settings.verify:
			return os.path.exists(path)

		if self.settings.output_full_path or self.settings.native_path:
			path = f"{os.getcwd()}/{path}"

			if self.settings.native_path:
				return dag.get_platform().path_to_native(path)

			return path
			
		return path if not self.settings.use_str else str(path)


	def get_completion_path_from_inputarg(self, inputarg) -> dag.Path:
		"""
		Determines which directory to scan based on input text (Defaults to ./ (current directory))

		:param inputarg: The inputarg to derive information from
		:returns: The path to scan for files
		"""

		# Get the inputted path
		origpath = inputarg.rawvalue[0] if inputarg.rawvalue else "./"

		# Turn the inputted path into a pathlib path
		path = dag.Path(origpath)

		# Get the parent unless the value ends with "/" (e.g.: "/ok/" -> "/ok/", while "/ok" -> "/")
		return path if origpath.endswith("/") else path.parent



	def complete(self, incmd, parsed, inputarg) -> list[str]:
		path = self.get_completion_path_from_inputarg(inputarg)

		# Get the files
		files = dag.filetools.listdir(path, dirs = self.settings.dir, files = self.settings.file, filetypes = dag.listify(self.settings.filetype or []))
		return self.format_completion_files(files, path)


	def format_completion_files(self, files, path) -> list[str]:
		"""
		Takes a list of files and a path and modifies the output text to be formatted for CLI usage
		Also replaces spaces with "\\ " and removes "./" if necessary

		:param files: The list of files to process
		:param path: The path to prepend the files with
		:returns: The files prepended with the path
		"""

		return [f"{path}/{f}".replace(" ", r"\ ").removeprefix("./") for f in files]

		
	def modify_completion_text(self, text):
		return text
		return text.replace(" ", r"\ ")
		#return text
		return text.split("/")[-1].replace(" ", r"\ ")
		#return "" if text.endswith(" ") else text.split("/")[-1].replace(" ", "\ ")
#<<<< PathDagArg			
		


#>>>> FileDagArg
class FileDagArg(PathDagArg):
	def _init_settings(self):
		super()._init_settings()
		self.settings.file = True
		self.settings.dir = False
#<<<< FileDagArg



#>>>> DirectoryDagArg
class DirectoryDagArg(PathDagArg):
	def _init_settings(self):
		super()._init_settings()
		self.settings.file = False
		self.settings.dir = True
#<<<< DirectoryDagArg


class ImageDagArg(PathDagArg):
	def process_raw_argval(self, value: str, incmd) -> dag.Img:
		return dag.img.from_path(value)

	def complete(self, incmd, parsed, inputarg) -> list[str]:
		# Get the path to check
		path = self.get_completion_path_from_inputarg(inputarg)

		# Get the files
		files = dag.filetools.listdir(path, filetypes = dag.images.FILETYPES)

		# Format the files for CLI
		return self.format_completion_files(files, path)





class WordDagArg(DagArg):
	def complete(self, incmd, parsed, inputarg):
		return [word.strip() for word in dag.file.iterlines(dag.CODE_PATH / ".etc/english_words2")]
		words = []

		with dag.file.open(dag.CODE_PATH / ".etc/english_words2") as f:
			words.extend([word.strip() for word in f])

		return words




class FilterDagArg(DagArg):
	def __init__(self, name, condition, **kwargs):
		super().__init__(name, **kwargs)
		self.condition = condition


	def _init_settings(self):
		self.settings.filter = self.settings.filter or self.settings.regex or {}
		self.settings.required = False
		self.settings.cacheable = False


	def filter_icresponse(self, ic_response):
		items = []

		for item in ic_response.raw_response:
			if self.condition(item):
				items.append(item)

		ic_response.raw_response = items




class InputCmdDagArg(DagArg):
	def _init_settings(self):
		self.settings.nargs = float("inf")
		self.settings.nargs_join = " "


	def process_raw_argval(self, value, incmd):
		if self.settings.usestr:
			return value
			
		from dag.parser import inputscripts
		with dag.ctx(parse_while_valid = True):
			return [*inputscripts.yield_incmds_from_text(value)][-1]


	def complete(self, incmd, parsed, inputarg):	
		from dag.parser import inputscripts

		inscript = inputscripts.generate_from_text(" ".join(incmd.args))
		newincmd = inscript.get_last_incmd()

		return newincmd.complete(newincmd.tokens[0], parsed)


	def modify_completion_text(self, text):
		return text.split(" ")[-1]




class IdentifierDagArg(InputCmdDagArg):
	def _init_settings(self):
		self.settings.nargs = float("inf")
		self.settings.nargs_join = " "


	def process_raw_argval(self, value, incmd):
		incmd = super().process_raw_argval(value, incmd)
		return incmd.dagcmd




class InputObjectDagArg(InputCmdDagArg):
	def _init_settings(self):
		self.settings.nargs = float("inf")
		self.settings.nargs_join = " "


	def process_raw_argval(self, value, incmd):
		incmd = super().process_raw_argval(value, incmd)
		return incmd.inputobjects[-1] if incmd.inputobjects else ""



class BooleanDagArg(DagArg):
	def process_raw_argval(self, value, incmd):
		if str(value).lower() in ["yes", "on", "true", "1"]:
			return True

		if str(value).lower() in ["no", "off", "false", "0"]:
			return False

		raise DagArgParserError(f"{value} is not a valid Boolean type (Choose from yes/no, on/off, true/false, 1/0)")



class DateRangeDagArg(DateDagArg):
	def process_raw_argval(self, value, incmd):
		breakpoint()
		pass



class OptionDagArg(DagArg):
	def __init__(self, *names, **settings):
		names = [*names]
		if len(names) == 1 and not is_named_arg(names[0]):
			names[0] = "--" + names[0]

		super().__init__(*names, **settings)


class SearcherDagArg(DagArg):
	def process_raw_argval(self, value, incmd):
		return dag.Searcher(value)

		
#<<<<<<<<<<<<<<<< DagArg subclasses




#>>>>>>>>>>>> DagArgsList
class DagArgsList(Sequence):
	def __init__(self, dagargs_list = None, fn = None, argspec = None):
		self.dagargs_list = dagargs_list[:] if dagargs_list else []
		self.fn = fn
		self.argspec = copy.copy(argspec or (dag.argspec(fn) if fn else dummies.emptyargspec)) # copied so that the argspec won't update if dagcmd's is updated

		self.dagargs_dict = {}

		self.shortnames = {}

		self.positionalargs = []
		self.namedargs = {}

		# Process any passed-in arg settings
		for dagarg in self.dagargs_list:
			self.add(dagarg)


	@classmethod
	def build_from_argspec(cls, argspec, arglist = None):
		annotations = argspec.annotations
		arglist = arglist or cls(argspec = argspec)

		for argname in argspec.args:
			if argname == "self":
				continue

			if arglist.targetdict.get(argname) is None:
				dagarg = None
				if argname in annotations:
					argtype = annotations.get(argname)
					dagarg = build_from_type(argtype, argname, argspec)

				arglist.add(dagarg or get_dagarg_class()(argname))

		if varargname := argspec.varargs:
			if arglist.targetdict.get(varargname) is None:
				arglist.add(DagArg(varargname, **{"nargs": -1, "required": False}))

		# For any dagargs in the cmd fn that weren't specified in an @dag.arg, build them here
		for argname in argspec.kwonlyargs:
			if arglist.targetdict.get(argname) is None:
				prefixedargname = LONG_NAMED_PREFIX + argname.removeprefix(LONG_NAMED_PREFIX)
				dagarg = None

				if argname in annotations:
					argtype = annotations.get(argname)
					dagarg = build_from_type(argtype, prefixedargname, argspec)

				arglist.add(dagarg or get_dagarg_class()(prefixedargname))

		return arglist



	def copy(self):
		return type(self)(dagargs_list = self.dagargs_list, fn = self.fn, argspec = self.argspec)
			
		
	def __getitem__(self, idx): return self.dagargs[idx]
	def __setitem__(self, idx, value):
		self.dagargs_list[idx] = value
		self.positionalargs[idx] = value
	def __len__(self): return len(self.dagargs)


	@property
	def dagargs(self):
		return self.positionalargs + [*self.namedargs.values()]


	def add(self, dagarg, overwrite = True):
		if dagarg.clean_name in self.dagargs_dict and not overwrite:
			return

		self.dagargs_dict[dagarg.clean_name] = dagarg

		if dagarg not in self.dagargs_list:
			self.dagargs_list.append(dagarg)

		if dagarg.is_positional_dagarg:
			self.positionalargs.append(dagarg)			

			if self.argspec:
				argspecargs = [parg for arg_name in self.argspec.args if (parg := self.get(arg_name)) is not None and parg.is_positional_dagarg]
				nonargspecargs = [parg for parg in self.positionalargs if parg.name not in self.argspec.args]
				self.positionalargs = argspecargs + nonargspecargs
		else:
			self.namedargs[dagarg.clean_name] = dagarg

		self.process_shortnames() # Done here so that any added arg automatically gets added to shortnames. But need to process all args to make sure to prioritize those that specify a shortname


	def process_shortnames(self):
		self.shortnames = {}

		def maybe_add_shortname(shortname, dagarg):
			if shortname not in self.shortnames:
				self.shortnames[shortname] = dagarg
				return True

			return False

		for dagarg in [na for na in self.dagargs if na.shortname]:
			sn = dagarg.clean_shortname

			# IF duplicate shortname registered: complain
			if sn in self.shortnames:
				raise DagError(f"shortname \"{dagarg.shortname}\" used by two dagargs ({dagarg.name}, {self.shortnames[sn].name})")

			self.shortnames[sn] = dagarg


		for dagarg in [na for na in self.dagargs if not na.shortname]:
			for ch in dagarg.clean_name:
				if maybe_add_shortname(ch, dagarg):
					break

			if dagarg not in self.shortnames.values():
				for ch in string.ascii_lowercase + string.ascii_uppercase:
					if maybe_add_shortname(ch, dagarg):
						break


	def __contains__(self, dagarg):
		return dagarg in self.positionalargs or dagarg in self.namedargs.values()


		
	def get(self, name, default = None):
		return self.dagargs_dict.get(clean_name(name)) or self.targetdict.get(name) or default

	@property
	def targetdict(self):
		return {arg.target: arg for arg in self}
			

	def __str__(self):
		response =  f"<c bu>Positional DagArgs</c bu>: {self.positionalargs}\n"
		response +=  f"<c bu>Named DagArgs</c bu>: {self.namedargs}"
		return dag.format(response)


	def __repr__(self):
		return str(self)	
#<<<<<<<<<<<< DagArgsList


#>>>> TempListDagArg
class TempListDagArg(DagArg):
	def process_raw_argval(self, value, incmd):
		templist = dag.instance.controller.templist

		if not templist:
			raise DagError("No Templist is currently active")

		thisapp = self.settings.templistapp
		thisname = self.settings.templistname

		templistapp = templist.manager.app
		templistname = templist.name

		if thisapp == templistapp and thisname == templistname:
			return templist[value]

		raise DagError(f"Templist \"<c bu / {thisapp.cmdpath()} {thisname}>\" is not the current active list.")
#<<<< TempListDagArg





registered_settings = dag.ItemRegistry()
registered_arg_annotations = dag.ItemRegistry()


class RegisteredArgAnnotation:
	def __init__(self, settings = None):
		self.settings = settings or {}
		self.defaultvaluesettings = {}

	def __repr__(self):
		return f"<{object.__repr__(self)}, {self.settings=} {self.defaultvaluesettings=}>"



def register_arg(name, _registered_arg_annotation = dag.UnfilledArg, _registered_arg_annotation_default = dag.UnfilledArg, **settings):
	registered_settings.register(name, settings)

	# If a registered arg annotation has been given: Process and record it
	if _registered_arg_annotation is not dag.UnfilledArg:
		# If annotation has not been registered already, set it up: 
		if _registered_arg_annotation not in registered_arg_annotations:
			regarganno = RegisteredArgAnnotation()
			registered_arg_annotations[_registered_arg_annotation] = regarganno

		# If a registered default has been given: Store it as a default value setting
		if _registered_arg_annotation_default is not dag.UnfilledArg:
			registered_arg_annotations[_registered_arg_annotation].defaultvaluesettings[_registered_arg_annotation_default] = settings
		# Else, no default value was given: Treat these settings as the main settings for the annotation type
		else:
			registered_arg_annotations[_registered_arg_annotation].settings = settings





register_arg("GreedyWords", nargs = -1, nargs_join = " ")
register_arg("Opt", _arg_type = OptionDagArg)
register_arg("Option", _arg_type = OptionDagArg)
register_arg("Word", _arg_type = WordDagArg)
register_arg("Directory", _arg_type = DirectoryDagArg)
register_arg("File", _arg_type = FileDagArg)
register_arg("Path", _arg_type = PathDagArg, _registered_arg_annotation = dag.Path)
register_arg("Time", _arg_type = TimeDagArg)
register_arg("Date", _arg_type = DateDagArg, _registered_arg_annotation = dag.DTime)
register_arg("Month", _arg_type = MonthDagArg)
register_arg("DateRange", _arg_type = DateRangeDagArg, nargs = 2)
register_arg("Int", _arg_type = IntDagArg, _registered_arg_annotation = int)
register_arg("Msg", _arg_type = MessageDagArg)
register_arg("Message", _arg_type = MessageDagArg)
register_arg("DagCmd", _arg_type = DagCmdDagArg)
register_arg("Color", _arg_type = ColorDagArg, _registered_arg_annotation = dag.Color)
register_arg("Resource", _arg_type = ResourceDagArg, _registered_arg_annotation = dag.Resource)
register_arg("Resources", _arg_type = ResourcesDagArg)
register_arg("Filter", _arg_type = FilterDagArg)
register_arg("Bool", _arg_type = BooleanDagArg)
register_arg("InCmd", _arg_type = InputCmdDagArg)
register_arg("Cmd", _arg_type = InputCmdDagArg, usestr = True)
register_arg("Flag", flag = True, nargs = 0, negatable = True, _registered_arg_annotation = bool, _registered_arg_annotation_default = False)
register_arg("FalseFlag", _registered_arg_annotation = bool, _registered_arg_annotation_default = True, **(registered_settings["Flag"] | {"flag": False}))
register_arg("Identifier", _arg_type = IdentifierDagArg)
register_arg("InputObject", _arg_type = InputObjectDagArg)
register_arg("Searcher", _arg_type = SearcherDagArg, _registered_arg_annotation = dag.Searcher)
register_arg("Img", _arg_type = ImageDagArg, _registered_arg_annotation = dag.Img)
register_arg("Image", _arg_type = ImageDagArg)