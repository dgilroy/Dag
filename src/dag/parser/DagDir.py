import abc
from dataclasses import dataclass, field



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
class Marker:
	def __init_subclass__(cls, marker = None):
		maybe_register_marker(marker, cls)
		cls.marker = marker
		cls.registered_directives = {}


	def strip_marker(self, token):
		return token.removeprefix(self.marker)

	# Parser #
	def parse(self, tokens, incmd):
		# SINGLE PARSER
		pass


class DoubleEq(Marker, marker = "=="):
	def parse(self, tokens, incmd):
		pass


class DoubleAt(Marker, marker = "@@"):
	def parse(self, tokens, incmd):
		pass


class DoubleHash(Marker, marker = "##"):
	def parse(self, tokens, incmd):
		pass

class DoubleColon(Marker, marker = "::"):
	def parse(self, tokens, incmd):
		pass





def get_markerstr(token):
	markerstr = ""
	while token and not token[0].isalnum():
		marker += token[0]
		token = token[1:]
	return markerstr


def is_markered(token):
	marker = get_markerstr(token)
	return bool(is_valid_markerstr(marker) and marker in registered_markers)






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
		registered_markers[markerstr].registered_directives[name] = directivecls
	except Exception as e:
		breakpoint()
		pass




### BASE DIRECTIVE CLASSES ###
class DagDirective:
	pass


class ExecutionDirective(DagDirective, abc.ABC):
	@abc.abstractmethod
	def process_incmd(self, incmd):
		raise NotImplementedError


class MetaDirective(DagDirective, abc.ABC):
	@abc.abstractmethod
	def process_inputobj(self, inputobj):
		raise NotImplementedError


class ResponseDirective(DagDirective, abc.ABC):
	priority = 10

	@abc.abstractmethod
	def process_ic_response(self, ic_response):
		raise NotImplementedError


@dataclass
class register_directive:
	marker: str
	default_name: str
	long_name: str = ""

	def __call__(self, parentcls):
		# Register marker
		register_marker_directive(self.marker, self.default_name, parentcls)

		# Regsiter longname, if valid
		if self.long_name and len(self.marker) == 1:
			register_marker_directive(self.marker*2, self.long_name, parentcls)

		return parentcls



### EXECUTION DIRECTIVES ###
@register_directive("=", "u", "update")
class UpdateCache(ExecutionDirective):
	def process_incmd(self, incmd):
		incmd.directives.update_cache = True

@register_directive("=", "r", "raw")
class DontFormatResponse(ExecutionDirective):
	def process_incmd(self, incmd):
		incmd.directives.format_response = False

@register_directive("=", "d", "debug")
class DebugMode(ExecutionDirective):
	def process_incmd(sef, incmd):
		incmd.directives.debug_mode = True

@register_directive("=", "i", "timer")
class TimeResponse(ExecutionDirective):
	def process_incmd(sef, incmd):
		incmd.directives.timer = True


@register_directive("=", "a", "async")
class RunAsync(ExecutionDirective):
	def process_incmd(sef, incmd):
		incmd.directives.run_async = True


@register_directive("=", "t", "tempcache")
class TempCache(ExecutionDirective):
	def process_incmd(sef, incmd):
		incmd.directives.tempcache = True		


### META DIRECTIVES ###
class SettingsMeta(MetaDirective):
	def process_inputobj(self, inputobj):
		return inputobj.settings

def parse(self, tokens, incmd):
	pass



@register_directive("@", "h")
class Help(MetaDirective):
	def process_inputobj(self, inputobj):
		pass

@register_directive("@", "b")
class BaseUrl(MetaDirective):
	def process_inputobj(self, inputobj):
		return inputobj.settings.baseurl

@register_directive("@", "d")
class Documentation(MetaDirective):
	def process_inputobj(self, inputobj):
		pass

@register_directive("@", "e")
class Editor(MetaDirective):
	def process_inputobj(self, inputobj):
		pass

@register_directive("@", "p")
class PortalUrl(MetaDirective):
	def process_inputobj(self, inputobj):
		pass


### RESPONSE DIRECTIVES ###
@register_directive("=", "k", "keys")
class Keys(ResponseDirective):
	priority = 20

	def process_ic_response(self, ic_response):
		try:
			ic_response.append_response(f"\n\n<c bold>Keys:</c>{[k for k in ic_response.raw_response.keys()]}")
		except AttributeError:
			ic_response.append_response(f"\n\n<c bold>Cannot get response's keys.</c>");


@register_directive("=", "c", "choices")
class Directive_Choices(ResponseDirective):
	priority = 20

	def process_ic_response(self, ic_response):
		try:
			choices = ic_response.raw_response.choices() or "None"
			ic_response.append_response(f"\n\n<c bold>Choices/Labels:</c>{choices}")
		except (AttributeError, TypeError) as e:
			ic_response.append_response(f"\n\n<c bold>Cannot get labels for response: {e}</c>")


@register_directive("=", "s", "size")
class Directive_Size(ResponseDirective):
	priority = 20

	def process_ic_response(self, ic_response):
		try:
			ic_response.append_response(f"\n\n<c bold>Size:</c>{len(ic_response.raw_response)}")
		except (AttributeError, TypeError) as e:
			ic_response.append_response(f"\n\n<c bold>Cannot get response's size: {e}</c>")


@register_directive("=", "l", "launch")
class Launch(ResponseDirective):
	def process_inputobj(self, inputobj):
		pass


@register_directive("=", "x", "lynx")
class LaunchInLynx(ResponseDirective):
	def process_inputobj(self, inputobj):
		pass

@register_directive("=", "o", "chrome")
class LaunchInChrome(ResponseDirective):
	def process_inputobj(self, inputobj):
		pass





class FiltDirective(ResponseDirective):
	def process_ic_response(self, ic_response):
		pass



class DrillerDirective(ResponseDirective):
	def process_ic_response(self, ic_response):
		pass



class ResourceDirective(ResponseDirective):
	priority = -1

	def process_ic_response(self, ic_response):
		pass


breakpoint()
pass