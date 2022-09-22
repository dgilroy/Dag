import os, re, math, pathlib
from functools import cached_property

import dag
from dag.lib import strtools, platforms
from dag.lib.dtime import DateParser, TimeParser
from dag.util import nabbers

from dag.dagcli.alist import Alist
from dag.dagcli.arguments import CliArgument

from dag.exceptions import DagError, DagArgParserError, DagArgValidationException


class DagArg(CliArgument):
	handles_arrays = False

	def __init__(self, name, dagcmd = None, settings_dict = None):
		self._name = name
		self.dagcmd = dagcmd

		self.settings = nabbers.NabbableSettings(settings_dict or {})

		self.init_settings()


	def init_settings(self):
		self.settings.setdefault("nargs_join", " ")	
		self.settings.setdefault("prompt_prefill", "")
		self.settings.setdefault("stripquotes", True)
		self.settings.setdefault("cacheable", True)

		self.process_name()
		self._init_settings()


	def __repr__(self): return f"<\"{self.name}\": {object.__repr__(self)}>"


	def _init_settings(self):
		"""Used by subclasses"""
		pass


	def process_name(self):
		# If is --named-arg: Set appropriate properties
		if self.is_named_dagarg:
			if "flag" not in self.settings and "type" not in self.settings:
				self.settings.setdefault("nargs", float('inf'))
			elif self.settings.get("nargs") == -1:
				self.settings["nargs"] = float("inf")
			else:
				self.settings.setdefault("nargs", 1)
				
			self.settings.setdefault("required", False)

		# Else, is positional arg: Set appropriate properties	
		else:
			self.settings.setdefault("nargs", 1)
			self.settings.setdefault("required", True)

			if "flag" in self.settings: del self.settings["flag"]




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


	def complete(self, incmd):
		return []


	def process_string_value(self, value):
		if strtools.is_valid_quoted_string(value) and not self.settings.raw:
			value = value[1:-1]

		return value.replace("\\ ", " ")


	@property
	def is_named_dagarg(self): return self.name.startswith("-")

	@property
	def is_positional_dagarg(self):
		try:
			return not self.name.startswith("-")
		except AttributeError as e:
			breakpoint()
			pass

	@property
	def name(self):	return self._name
	
	@name.setter
	def name(self, value):
		pass

	@property
	def clean_name(self): return self.name.lstrip("-")


		
	
class ResourceArg(DagArg):
	def __init__(self, name, dagcmd = None, settings_dict = None):
		DagArg.__init__(self, name, dagcmd, settings_dict)
		
		self._args = [arg for arg in self.settings.get('args', [])]


	@cached_property
	def collection_cmds(self):
		if isinstance(self.settings.get('collection'), (nabbers.Nabber, nabbers.Nabbable, type(self.dagcmd))):
			_collection_cmds = self.settings.collection
			_collection_cmds = _collection_cmds if isinstance(_collection_cmds, (list, tuple)) else [_collection_cmds]
			#return [c() if isinstance(c, type(self.dagcmd)) else c for c in _collection_cmds] This was forcing non-cached collection_cmds to call just to get their settings
			return _collection_cmds
		else:
			collection_cmds = self.settings.get("collection")
			_collection_names = collection_cmds if isinstance(collection_cmds, (list, tuple)) else [collection_cmds]
			return [dag.drill(self.dagcmd.dagmod, c) for c in _collection_names if c is not None]


	def _get_args(self):
		breakpoint()
		pass
	

	def nabbed_args(self):
		return dag.nab_if_nabber(self._args)
		
		
	def process_raw_argval(self, value, incmd, do_prompt = True):
		if not value:
			return None
		try:
			dagmod = incmd.dagcmd.dagmod

			#ALIST CHECK HERE BEFORE GET COLLECTION
			for collection_cmd in self.collection_cmds:				
				if collection_cmd and collection_cmd == Alist.collection_dagcmd and (value.lstrip("-+").isdigit() or (value == "_" and Alist.current_id)):
					if value.lstrip("-+").isdigit():
						return Alist[int(value)]
					elif value == "_" and Alist.current_id:
						return Alist[Alist.current_id]
					else:
						if len(self.collection_cmds) == 1:
							raise ValueError("Alist Index must be an integer") #This is set up because if non-int is passed into alist-accepting cmd, gets stuck in infinite loop
						else:
							continue
					
				if collection_cmd.settings.idx  and value.isdigit():
					collection_cmd = getattr(dagmod, next((name for name in self.collection_cmds if getattr(dagmod, name).settings.idx)))

					dag.echo("<c #DF87FF underline>THIS ALIST HAD NOT BEEN GENERATED. PLEASE RUN COMMAND AGAIN</c>\n")
					raise DagError(f"This command's Alist had not been generated. Please run <c #DF87FF underline>{dagmod.name} {collection.fn_name}</c #DF87FF underline> first")

			resource = None

			while resource is None and do_prompt:
				if value == "": raise DagArgParserError("Empty value detected. Exiting prompt")

				resource, collection_cmd = self.get_resource_from_value(value)

				if resource is None and not incmd.complete_active:
					choices = [*filter(lambda x: re.search(f".*{value}.*", x), self.inputarg.get_complete(incmd) or [])]
					choice_prompt = f"Did you mean any of [<c red>{', '.join(choices[:50])}</c red>]{'...? (up to 50 shown)' if len(choices) > 50 else '?'}" if choices else ""
					value = self.inputarg.prompt_value(incmd,
						f"""value {value} not found in {dagmod.name}.{self.collection_cmds[0]}.
{choice_prompt}
Please enter <c red u>{self.collection_cmds[0]}</c red u> name</c>. Press <c white>*tab*</c> for completion options""",
						show_choices = False,
						prefill = choices[0] if (len(choices) == 1) else ""
					)
					
				if value != "" and resource is None:
					resource = collection_cmd(**incmd.parsed).find(value)

			if resource and self.settings.get("drill"):
				resource = dag.drill(resource, self.settings.drill)

			return resource

		except (AttributeError, TypeError, DagArgParserError):
			return value
			
			
	def get_resource_from_value(self, value):
		args = self.nabbed_args()
		
		for collection_cmd in self.collection_cmds:
			collection_cmd = collection_cmd(*args)
			
			if res := collection_cmd.find(value):
				return res, collection_cmd
				
		return None, None

			
	def complete(self, incmd):
		try:				
			args = self.nabbed_args()
			
			choices = []
			for collection_cmd in self.collection_cmds:				
				if collection_cmd.settings.idx: continue

				choices.extend(collection_cmd(*args).choices())
				
			return choices
		except (AttributeError, TypeError) as e:
			return []


	def item_is_regex(self, item):
		return item.startswith("r/") and item.endswith("/")
		

	def get_regex_content(self, item):
		return item[2:-1]

	
	
class CollectionResourceArg(ResourceArg):
	handles_arrays = True
	
	def _init_settings(self):
		self.settings.nargs = float("inf")
		self.settings.required = False
		self.settings.nargs = -1
		self.settings.cacheable = False

		
	def process_raw_argval(self, items, incmd):
		self.collection_cmds = self.dagcmd.resources_dagarg.collection_cmds

		# Remove duplicates
		items = [*set(items)]

		resources = []
		args = self.nabbed_args()
		collection = incmd.dagcmd(*args)
		
		has_regex = any(filter(lambda x: self.item_is_regex(x), items)) # If any item is a regex searcher, set this boolean so value won't be prompted for

		for i, item in enumerate(items):
			if self.item_is_regex(item) and (res := collection.find_regex(self.get_regex_content(item))):
				resources.append(res)
			else:
				resources.append(super().process_raw_argval(item, incmd, do_prompt = not has_regex))

		return sum(resources)


	def skip_if_unfilled(self):
		return True



class ColorArg(DagArg):
	def complete(self, incmd):
		return list(platforms.get_terminal().colormap.keys())



class DagCmdArg(DagArg):
	def __init__(self, name, dagcmd = None, settings_dict = None):
		super().__init__(name, dagcmd, settings_dict)


	def complete(self, incmd):
		return dag.default_dagcmd.subcmdtable.get_completion_names()



class MessageArg(DagArg):
	def validate_input_formatting(self, inputarg):
		value = inputarg.joined_value

		if not strtools.is_valid_quoted_string(value):
			raise DagArgValidationException(f"Message Arg \"<c u b>{self.name}</c u b>\" must be wrapped by two matching unescaped quotation marks")

		return True



class IntArg(DagArg):
	def _init_settings(self):
		self.settings.setdefault("min", -math.inf)
		self.settings.setdefault("max", math.inf)

	def process_raw_argval(self, number, incmd):
		number = int(number)

		if self.settings.range is not None:
			return sorted((self.settings.range[0], number, self.settings.range[1]))[1]

		return sorted((self.settings.min, number, self.settings.max))[1]
		


class DTimeArg(DagArg):
	parser = None

	def process_raw_argval(self, date_str, incmd):
		dtime = self.parse_dtime(date_str)

		return self.process_dtime(dtime)


	def parse_dtime(self, dtstr):
		return self.parser.parse(dtstr, self.settings.dateformat)


	def process_dtime(self, dtime):
		return dtime


	def complete(self, incmd):
		return list(self.parser.named_values.keys())		



class DateArg(DTimeArg):
	parser = DateParser


class TimeArg(DTimeArg):
	parser = TimeParser



class MonthArg(DTimeArg):
	def _init_settings(self):
		self.settings.setdefault("choices", dag.dtime.monthstrs)


	def parse_dtime(self, dtstr):
		return dag.DTime(dtstr).firstofmonth
		
		
		
class PathArg(DagArg):
	def _init_settings(self):
		self.settings.file = True
		self.settings.dir = True

	def process_raw_argval(self, value, incmd):
		path = pathlib.Path(value.replace("\\", "").replace('"', "").replace("'", ""))

		if self.settings.force and not os.path.exists(value):
			os.mknod(path)
			
		if self.settings.verify:
			return os.path.exists(path)

		if self.settings.output_full_path or self.settings.native_path:
			path = f"{os.getcwd()}/{path}"

			if self.settings.native_path:
				return platforms.get_platform().path_to_native(path)

			return path
			
		return path if not self.settings.use_str else str(path)

		
	def get_files(self, basepath = "."):
		basefiles = next(os.walk(basepath))
		files = []
		
		# Get directories
		if self.settings.dir:
			files += [f"{f}/" for f in basefiles[1]]
			
		# Get files
		if self.settings.file:
			files += [f"{f}" for f in basefiles[2]]

			if self.settings.filetype:
				files = [f for f in files if f.endswith(self.settings.filetype)]

		return files


	def complete(self, incmd):
		path = incmd.args[-1]

		if path.startswith("/") and path.count("/") == 1:
			basepath = "/"
		else:
			basepath = path[:path.rfind("/")] if "/" in path else "."

		files = self.get_files(basepath)

		return [f.replace(" ", r"\ ") for f in files]

		
	def modify_completion_text(self, text):
		#return text
		return text.split("/")[-1].replace(" ", r"\ ")
		#return "" if text.endswith(" ") else text.split("/")[-1].replace(" ", "\ ")
		
		

class FileArg(PathArg):
	def _init_settings(self):
		self.settings.file = True
		self.settings.dir = False



class DirectoryArg(PathArg):
	def _init_settings(self):
		self.settings.file = False
		self.settings.dir = True



class WordArg(DagArg):
	def complete(self, incmd):
		return [word.strip() for word in dag.file.iterlines(dag.ROOT_PATH / ".etc/english_words")]
		words = []

		with dag.file.open(dag.ROOT_PATH / ".etc/english_words") as f:
			words.extend([word.strip() for word in f])

		return words


class FilterArg(DagArg):
	def _init_settings(self):
		self.settings.filter = self.settings.filter or self.settings.regex or {}
		self.settings.required = False
		self.settings.cacheable = False




registered_settings = {}


def register_arg(name, **settings):
	registered_settings[name] = settings


register_arg("Word", _arg_type = WordArg)
register_arg("Directory", _arg_type = DirectoryArg)
register_arg("File", _arg_type = FileArg)
register_arg("Path", _arg_type = PathArg)
register_arg("Time", _arg_type = TimeArg)
register_arg("Date", _arg_type = DateArg)
register_arg("Month", _arg_type = MonthArg)
register_arg("Int", _arg_type = IntArg)
register_arg("Msg", _arg_type = MessageArg)
register_arg("DagCmd", _arg_type = DagCmdArg)
register_arg("Color", _arg_type = ColorArg)
register_arg("Resource", _arg_type = ResourceArg)
register_arg("Filter", _arg_type = FilterArg)
register_arg("Cmd", nargs = -1)
#register_arg("ResourceArg", _arg_type = CollectionResourceArg)