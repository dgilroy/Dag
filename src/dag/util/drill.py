import re
from typing import Union, Any, Optional

import dag

class DagDrillError(BaseException): pass


def get_drillbits(driller: str, splitter: str = ".") -> list[str]:
	"""
	Takes the drillstring and splits it into drillbits. This takes into account:
		(1) Words separated by the splitter ("drill1.drill2" => ["drill1", "drill2"])
		(2) Words inside square brackets ("drill1[drill2]" => ["drill1", "[drill2]"])
		(3) Words inside parenthases ("drill1(drill2)" => ["drill1", "(drill2)"]) 

	Currently doesn't work with nested lists or functions with params:
		(1) Nested lists seem ok, but would require something to process the opening/closing brackets
		(2) fn params would be hard to implement because all args would be assumed to be strings

	:param drillstring: The string to convert into drillbits
	:param splitter: The char that will split words into drillbits
	"""

	with dag.catch() as e:
		if driller.startswith(splitter):
			driller = driller.lstrip(splitter)

	# If there is an index query in drillbits: replace all "[...]" with ".[...]." for splitting
	if "[" in driller:

		# Wraps "[...]" with the splitter so that it is properly added as a drillbit (e.g.: attr1[item1].attr2 => ["attr1", "[item1]", "attr2"])
		# The brackets are kept so that future items know whether it's an attr query of an index query
		driller = re.sub(r"(?<!^)(\[.*?\])(\.?)", fr"{splitter}\1\2", driller)

	# If there is an index query in drillbits: replace all "(...)" with ".(...)." for splitting
	if "(" in driller:
		driller = re.sub(r"(?<!^)(\(.*?\))(\.?)", fr"{splitter}\1\2", driller)

	# Split the drillstring at the splitter
	return driller.split(splitter)

	
# For a name "itemName.attrName", returns tuple (drilleeName, drillBits)
def get_drillparts(drilltext: str, splitter: str = ".", combined_drillbits: bool = True) -> tuple[str, Union[str, list[str]]]:
	"""
	Given a piece of text, splits it into:
		(1) The name of the item to be drilled into
		(2) The piece(s) of text used to drill into the named object

	:param drilltext: The text to analyze and split
	:param splitter: The character used to distinguish between words
	:param combined_drillbits: Whether or not to return drillbits as a string or to split into a list of individual components
	:returns: A tuple (the name of the drillee, the drillbits)
	"""

	i, n = 0, len(drilltext)

	# If drilltext is a URL: return original data and don't drill further
	if re.match("^(https?|ftp)://", drilltext): return drilltext, ""

	# Iterate through drillname until [, (, or . 
	while i < n and drilltext[i] not in f"[({splitter}": i = i+1

	drillbits = drilltext[i:] if combined_drillbits else get_drillbits(drilltext[i:], splitter)

	return drilltext[:i], drillbits
	
	

	
# Take an item and search through it from a string query
def drill(drillee: object, driller: object, splitter: str = ".", drill_until: int = 0) -> Any:
	"""
	A utility built to allow a CLI to query an object for
		(1) list indices
		(2) dict keys
		(3) callable functions

	e.g. given a list of Resources, can parse and return Resources[1].dict()["key1"]

	:param drillee: The object to be drilled into
	:param driller: The string of bits to process and use to drill, or a DagDriller
	:param splitter: The character used to separate words
	:param drill_until: Indicates how many drillbits to process (-1 will drill all but last drillbit)
	:returns: The result after drilling into the object
	"""

	if isinstance(driller, dag.util.mixins.DagDriller):
		return driller._dag_drill(drillee)

	if isinstance(driller, dag.ResourcesLambdaBuilder):
		return driller(drillee)

	# Stores the original item being drilled into
	original_drillee = drillee
	original_driller = driller

	# Iterate through driller to separate attr queries and index queries (e.g.: "attr1[item1].attr2" => ["attr1", "item1", "attr2"]). Filters out Nones
	drillbits = [bit for bit in get_drillbits(driller, splitter) if bit is not None]

	if drill_until:
		drillbits = drillbits[:drill_until]
		#driller = splitter.join(drillbits)
		#driller = get_drillbits(driller, splitter)
	
	# Try to query through drillee
	try:
		# Iterate through each drillbit, searching for element
		for bit in drillbits:
			# If bit is empty: Skip bit
			if not bit:
				continue

			# If drillbit is dict index: Process index query
			if bit.startswith("["):

				# If index query is wrapped in quotes (aka is a dict entry): Extract the string text (e.g.: "'hi'" => "hi")
				is_bit_quoted = False

				# If text in brackets is wrapped in quotes: Mark as such and remove the brackets/quotes
				if (match := re.match(r"^\[['\"](.*)['\"]\]$", bit)):
					is_bit_quoted = True
					bit = match.groups()[0]
				# Else, index query isn't looking for a string (aka is a list idx): Remove the "[", "]" wrapping drillbit
				else:
					bit = bit[1:-1]
				

				# If letters exist in the query index; this is a dict index and not a list index. Skip to next step
				if is_bit_quoted or re.match("[a-zA-Z]", bit) or dag.strtools.is_valid_quoted_string(bit):
					pass
				# Elif index query query is a list index: Process potential slicing (even if only one number present)
				elif ":" in bit:
					# Split slice query at ":"'s'
					bit = dag.strtools.strtoslice(bit)
				# Elif, query is all numerical: Turn into an int
				elif not isinstance(bit, float):
					try:
						bit = int(bit)
					except ValueError:
						pass

				try:
					drillee = drillee.__getitem__(bit)
				except (TypeError, KeyError):
					drillee = drillee.__getitem__(str(bit))
					
			# Elif query is calling an object function and calling: query function and call
			# NOTE: Only supports functions with no args
			elif bit.startswith("("):
				if len(bit) > 2:
					raise DagDrillError(f"Drillbits can't include function args at this time")

				drillee = drillee.__call__()
				
			# Else, querying an object property: Get object property
			else:
				drillee = getattr(drillee, bit)
	except (AttributeError, IndexError) as e:
		raise DagDrillError(f"\fn Drill error: {e} {drillee=} {drillbits=} {original_drillee=}") from e

	return drillee



def drill_for_properties(obj: object, drilltext: str = "", drillbits = "", approved_initial_properties: list[str] | None = None, lstrip: str = "") -> list[str]:
	"""
	Drill into an object and return any of the returned-object's properties that start with the same letters as the final drillbit

	This is used for auto-completion in dagpdb

	(e.g.) response[1].property1.property2.pr returns any elements of property2 that start with "pr"

	:param obj: The starting object to be investigated
	:param drilltext: The text to process and use to drill the starting obj
	:param approved_properties: Provides a list of properties that can be used. If none, will use dir(item)
	:returns: A list of properties that match the drilltext
	"""

	drilled_args = []

	if drilltext:
		drillee, drillbits = get_drillparts(drilltext)
	else:
		drillee, drillbits = "", drillbits

	_, drillbits_list = get_drillparts(drillbits, combined_drillbits = False)

	if drillbits:
		try:
			# Set up like this because dagpdb can only send a dict of locals
			#if not isinstance(obj, dict):
			#	obj = vars(obj) | vars(obj.__class__)

			# [{drillee}] because dagpdb can only send a dict of locals
			#item = drill(obj, f"[{drillee}]" + drillbits, drill_until = -1)
			item = drill(obj, f"{drillee}" + drillbits, drill_until = -1)
			drilled_args = approved_initial_properties if approved_initial_properties and len(drillbits_list) < 2 else dir(item)
			driller = ".".join(drillbits.split(".")[:-1]) + "."
			combined_drillparts = drillee  + driller

			# IF final drillbit starts with "_": Go ahead and show attributes starting with "_"
			if drillbits.split(".")[-1].startswith("_"):
				return[(combined_drillparts + arg).lstrip(lstrip) for arg in drilled_args if (combined_drillparts + arg).startswith(drilltext)]
			# ELSE, final drillbit does not start with "_": Ignore attributes starting with "_" (There are usually a lot so it clutters the screen)
			else:
				return [(combined_drillparts + arg).lstrip(lstrip) for arg in drilled_args if (combined_drillparts + arg).startswith(drilltext) and not arg.startswith("_")]
		except DagDrillError:
			pass
	elif not (drillee or drillbits):
		drilled_args = [d for d in dir(obj) if not d.startswith("_")]

	return drilled_args



if __name__ == "__main__":
	import dag
	with dag.ctx(testval = 2):
		items = drill_for_properties(dag, ".ctx.")
		breakpoint()
		pass





def set_idx_via_drill(drillstr, newvalue, response):
	if isinstance(drillstr, dag.LambdaBuilder):
		drillstr = dag.util.lambdabuilders.convert_lb_to_string(drillstr)

	drillbits = get_drillbits(drillstr)

	# If no drillstr provided, replace the response with the new value
	if not drillbits:
		response._data = newvalue
		return response
	
	key = drillbits.pop()

	parentdict = dag.drill(response, ".".join(drillbits))
	parentdict[key] = newvalue
	return response


@dag.oninit
def _():
	@dag.cmd
	def drill(drillee, drillstring: str):
		return dag.drill(drillee, drillstring)