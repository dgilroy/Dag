import abc, enum, functools
from dataclasses import dataclass, field

import dag
from dag.lib import browsers, dot
from dag.util import launcher, dagdebug


class DirectiveType(enum.Enum):
	DEFAULT = "directives"
	EXECUTION = "execution_directives"
	META = "meta_directives"
	RESPONSE = "response_directives"



class DirectiveList(dot.DotDict):
	def __init__(self, directives = None):
		super().__init__(directives)

		for dirtype in DirectiveType:
			setattr(self, f"get_{dirtype.name.lower()}_directives", functools.partial(self.get_directive_by_type, dirtype))


	def get_directive_by_type(self, type, default = None):
		return self._dict.get(type, default or [])



### MARKERS ###
registered_markers = {}



###### MARKER REGISTRATION ######
def is_valid_markerstr(markerstr):
	return len(set(markerstr)) == 1 and not markerstr.isalnum()


def build_markerobj(markerstr, parentcls, **kwargs):
	return type(markerstr, (parentcls,), {"marker": markerstr, "registered_directives": {}}, marker = markerstr, **kwargs)


def register_marker(markerstr, markercls = None):
	assert is_valid_markerstr(markerstr), "Marker must comprise of 1 or more identical non-alphanum characters"
	registered_markers.setdefault(markerstr, markercls or build_markerobj(markerstr, markercls or Marker))



def maybe_register_marker(marker = None, markercls = None):
	if marker is None:
		return

	register_marker(marker, markercls)



###### MARKER CLASSES ######
class Marker(abc.ABC):
	def __init_subclass__(cls, marker = None):
		maybe_register_marker(marker, cls)
		cls.marker = marker
		cls.registered_directives = {}


	@classmethod
	def register_directive(cls, name, directivecls):
		cls.registered_directives[name] = directivecls


	@classmethod
	def strip_marker(cls, token):
		return token.removeprefix(cls.marker)

	# Parser #
	@classmethod
	def parse(cls, token, ic_parser):
		token = cls.strip_marker(token)
		yield from cls._parse(token, ic_parser)

	@classmethod
	@abc.abstractmethod
	def _parse(cls, token, ic_parser):
		raise NotImplementedError


class RegistrationMarker(Marker):
	@classmethod
	def _parse(cls, token, ic_parser):
		directive = cls.registered_directives.get(token)
		yield directive() if directive else None


		## Accept any other following words as more directives (so "==raw debug" is same as "==raw ==debug")
		for token in ic_parser.tokens.dequeue_nondirective_tokens():
			yield cls.registered_directives.get(token)


class ShorthandMarker(RegistrationMarker):
	@classmethod
	def _parse(cls, token, ic_parser):
		charbuffer = ""
		for char in token:
			charbuffer += char
			if charbuffer == ".":
				continue

			if charbuffer in cls.registered_directives:
				directive =  cls.registered_directives.get(char)
				yield directive() if directive else None

			charbuffer = ""


## ==============================================
class Eq(ShorthandMarker, marker = "="):
	pass

class DoubleEq(RegistrationMarker, marker = "=="):
	pass


## @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
class At(ShorthandMarker, marker = "@"):
	pass


class DoubleAt(Marker, marker = "@@"):	
	@classmethod
	def _parse(cls, token, ic_parser):
		yield SettingsMeta(token)


## ############################################
class DoubleHash(Marker, marker = "##"):
	@classmethod
	def _parse(cls, token, ic_parser):
		filtname = token

		args = []
		for token in ic_parser.tokens.dequeue_nondirective_tokens():
			args.append(token)

		# Reversed so that "##filtname > value" gets inputted correctly
		yield FiltDirective(filtname, args)


## ::::::::::::::::::::::::::::::::::::::::::::
class DoubleColon(Marker, marker = "::"):
	@classmethod
	def _parse(cls, token, ic_parser):
		yield DrillerDirective(token)


## >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Great(Marker, marker = ">"):
	@classmethod
	def _parse(cls, token, ic_parser):
		filename = ""

		for token in ic_parser.tokens.dequeue_nondirective_tokens():
			filename = token
			break

		yield OutputRedirection(filename)




def get_markerstr(token):
	markerstr = ""
	while token and not token[0].isalnum():
		char = token[0]

		# Break once invalid marker (so that ::[0:3] doesn't think '::[' is the markerstr)
		if not is_valid_markerstr(markerstr + char):
			break

		markerstr += char
		token = token[1:]

	return markerstr


def is_markered_directive(token):
	marker = get_markerstr(token)
	return bool(marker and marker in registered_markers)


def parse_directive(ic_parser):
	token = ic_parser.tokens.pop(0)
	marker = get_markerstr(token)

	for directive in registered_markers[marker].parse(token, ic_parser):
		yield directive






#EXECUTION DIRECTIVES
# (DO EVAL) modify execution ctx: update/raw/debug/timer/async/tempcache

# META DIRECTIVES
# (DONT EVAL) Directly Affect which response: @@settings/help/baseurl/documentation/editor/portalurl/launch
# (DONT EVAL) Get info about first preceding with appropriate info: documentation/editor/portalurl/launch
				# Maybe @@ by itself just returns whichever dagmod/dagcmd/dagarg precedes it

# RESPOSNE DIRECTIVES
# (MAYBE EVAL) Modify existing response: keys/choices/size/##filts/::drillers/Resource directive (replacing dagarg)

# have directives registered as incmd objects. @@ can operate on directives if applicable





# DIRECTIVE REGISTRATION #
def register_marker_directive(markerstr, name, directivecls):
	maybe_register_marker(markerstr)
	try:
		registered_markers[markerstr].register_directive(name, directivecls)
	except Exception as e:
		breakpoint()
		pass




### BASE DIRECTIVE CLASSES ###
class DagDirective:
	keyname = DirectiveType.DEFAULT


class ExecutionDirective(DagDirective, abc.ABC):
	keyname = DirectiveType.EXECUTION

	@abc.abstractmethod
	def process_incmd(self, incmd):
		raise NotImplementedError


class MetaDirective(DagDirective, abc.ABC):
	keyname = DirectiveType.META

	@abc.abstractmethod
	def process_incmd(self, incmd):
		raise NotImplementedError


class ResponseDirective(DagDirective, abc.ABC):
	keyname = DirectiveType.RESPONSE
	priority = 10

	@abc.abstractmethod
	def process_ic_response(self, ic_response):
		raise NotImplementedError


class ResponseRefinementDirective(ResponseDirective):
	priority = 0


class ResponseAnalysisDirective(ResponseDirective):
	priority = 20


class register_directive:
	def __init__(self, *directives):
		self.directives = directives

	def __call__(self, parentcls):
		for directive in self.directives:
			marker = get_markerstr(directive)	
			directivename = directive.removeprefix(marker)

			register_marker_directive(marker, directivename, parentcls)

		return parentcls


### EXECUTION DIRECTIVES ###
@register_directive("=u", "==update")##################
class UpdateCache(ExecutionDirective):
	def process_incmd(self, incmd):
		incmd.directives.update_cache = True

@register_directive("=r", "==raw")
class DontFormatResponse(ExecutionDirective):
	def process_incmd(self, incmd):
		incmd.directives.format_response = False

@register_directive("=d", "==debug")##########################
class DebugMode(ExecutionDirective, ResponseDirective):
	def process_incmd(sef, incmd):
		self.oldvalue = dagdebug.DEBUG_MODE
		dagdebug.DEBUG_MODE = True

	def process_ic_response(self, ic_response):
		dagdebug.DEBUG_MODE = self.oldvalue



@register_directive("=a", "==async")
class RunAsync(ExecutionDirective):
	def process_incmd(sef, incmd):
		incmd.directives.run_async = True


@register_directive("=t", "==tempcache")###################
class TempCache(ExecutionDirective, ResponseDirective):
	def process_incmd(sef, incmd):
		incmd.directives.tempcache = True		

	def process_ic_response(self, ic_response):
		ic_response.append_prepend("<c bold>READING FROM TEMPCACHE</c>\n-------------------------\n\n")


@dataclass
class OutputRedirection(ExecutionDirective):
	outfilename: str = ""

	def process_incmd(self, incmd):
		if self.outfilename:
			incmd.directives.outfile_name = outfilename
		else:
			incmd.directives.do_copy = True


@register_directive("=l", "==launch")
class LaunchDirective(ExecutionDirective):
	browser = browsers.DEFAULT
	priority = 50

	def process_incmd(self, incmd):
		incmd.directives.url = True
		launcher.launch(item, self.browser)



@register_directive("=x", "==lynx")
class LaunchInLynx(LaunchDirective):
	browser = browsers.LYNX


@register_directive("=o", "==chrome")
class LaunchInChrome(LaunchDirective):
	browser = browsers.CHROME


@register_directive("=p", "==portalurl")
class PortalUrl(LaunchDirective):
	def process_ic_response(self, ic_response):
		incmd.directives.url = True


### META DIRECTIVES ###




@dataclass
class SettingsMeta(MetaDirective):
	settingname: str = ""

	def process_inputobj(self, incmd):
		return inputobj.settings



@register_directive("=h", "==help")
class Help(MetaDirective):
	def process_incmd(self, incmd):
		pass

@register_directive("=b", "==baseurl")
class BaseUrl(MetaDirective):
	def process_incmd(self, incmd):
		return inputobj.settings.baseurl

@register_directive("=D", "==doc")
class Documentation(MetaDirective):
	def process_incmd(self, incmd):
		return inputobj.settings.doc

@register_directive("=e", "==editor")
class Editor(MetaDirective):
	def process_incmd(self, incmd):
		return inputobj.settings.editor




### RESPONSE DIRECTIVES ###
@register_directive("=k", "==keys")
class Keys(ResponseAnalysisDirective):
	priority = 20

	def process_ic_response(self, ic_response):
		try:
			ic_response.append_response(f"\n\n<c bold>Keys:</c>{[k for k in ic_response.raw_response.keys()]}")
		except AttributeError:
			ic_response.append_response(f"\n\n<c bold>Cannot get response's keys.</c>");


@register_directive("=c", "==choices")
class Directive_Choices(ResponseAnalysisDirective):
	def process_ic_response(self, ic_response):
		try:
			choices = ic_response.raw_response.choices() or "None"
			ic_response.append_response(f"\n\n<c bold>Choices/Labels:</c>{choices}")
		except (AttributeError, TypeError) as e:
			ic_response.append_response(f"\n\n<c bold>Cannot get labels for response: {e}</c>")


@register_directive("=s", "==size")
class Directive_Size(ResponseAnalysisDirective):
	def process_ic_response(self, ic_response):
		try:
			ic_response.append_response(f"\n\n<c bold>Size:</c>{len(ic_response.raw_response)}")
		except (AttributeError, TypeError) as e:
			ic_response.append_response(f"\n\n<c bold>Cannot get response's size: {e}</c>")


@dataclass
class FiltDirective(ResponseRefinementDirective):
	filtname: str
	args: list[str] = field(default_factory=list)

	def process_ic_response(self, ic_response):
		# If no value: Partition by filtname
		if not self.args:
			ic_response.raw_response = ic_response.raw_response.partition(self.filtname).sort_by_keys()

		# Else, has value: return items that whose filtname matches value criteria
		else:
			collection = ic_response.raw_response

			action = lambda **filters: ic_response.raw_response.filter(_dag_use_str = True, **filters)
			if self.args[0] in ["<",">","=","<=",">=", "!="]:
				op = self.args[0] # Preserves value for lambda
				action = lambda x: ic_response.raw_response.compare(id = x, op = op)
				self.args.pop(0)

			items = ic_response.raw_response.create_subcollection()

			for arg in self.args:
				arg = arg[1:] if arg[0] in ["'", '"'] else arg # Strip quotes
				arg = arg[:-1] if arg[-1] in ["'", '"'] else arg # Strip quotes

				if arg.startswith("r/") and arg.endswith("/"):
					arg = arg[2:-1]
					action = lambda **filters: ic_response.raw_response.filter_regex(**filters)

				items += action({self.filtname: arg})

			ic_response.raw_response = items


@dataclass
class DrillerDirective(ResponseRefinementDirective):
	drillname: str

	def process_ic_response(self, ic_response):
		ic_response.raw_response = dag.drill(ic_response.raw_response, self.drillname)


@dataclass
class ResourceDirective(ResponseRefinementDirective):
	resourcename: str
	priority = -1

	def process_ic_response(self, ic_response):
		ic_response.raw_response = ic_response.raw_response.search(ic_response)


@register_directive("=i", "==timer")
class TimeResponse(ResponseAnalysisDirective):
	def process_ic_response(self, ic_response):
		ic_response.append_response(f"{ic_response.execution_time}")
