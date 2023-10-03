import re, string

QUOTEMARKS = ['"', "'"]


def text_ends_with_punctuation(text: str, punctuation: str) -> bool:
	textnopunctuation = text.removesuffix(punctuation)

	if len(text) == len(textnopunctuation):
		return False

	textnoslash = textnopunctuation.rstrip("\\")

	if (len(textnopunctuation) - len(textnoslash)) % 2 == 0:
		return True

	return False


def isint(text: str, strip: str = "+-") -> bool:
	return text.lstrip(strip).isdigit()


def isfloat(text: str) -> bool:
	return text.replace('.', '', 1).isdigit() if text.count('.') <= 1 and text.lstrip('-').replace('.', '', 1).isdigit() else False



def strtoint(text: str) -> int:
	"""
	Like int(text), but handles multiple +/-'s at start of word
	"""
	is_negative = text.count("-") % 2 # If even number of -'s, this is a positive number, so #%0 == 0
	inttext = text.lstrip("+-")
	sign = -1 if is_negative else 1
	return int(inttext) * sign


def text_is_wrapped_with_unescaped(text: str, start: str, end: str = None) -> bool:
	if end is None:
		end = start

	if not text.startswith(start):
		return False

	if not text_ends_with_punctuation(text, end):
		return False

	return True


def is_valid_quoted_string(text: str) -> bool:
	"""
	Checks the given text and sees whether the text is:
		(1) Correctly wrapped in quotation marks
		(2) Any quotation marks within the quotes are escaped
		(3) The final quotation mark isn't escaped

	:param text: The text to check whether its validly quoted
	:returns: Whether or not the text is validly quoted
	"""

	if not text or len(text) < 2 or text[0] not in QUOTEMARKS:
		return False

	quotemark = text[0]
	text = text[1:]

	if not text.endswith(quotemark):
		return False

	is_escaped = False

	for i, ch in enumerate(text):
		if ch == "\\":
			is_escaped = not is_escaped
			continue

		if ch == quotemark and not is_escaped and i < len(text) - 1: # Can't have unescaped quotemark that's not at end of text
			return False
		elif ch == quotemark and is_escaped and i == len(text) - 1: # Can't end text with escaped quotemark
			return False

		is_escaped = False

	return True


def stripquotes(text: str) -> str:
	if is_valid_quoted_string(text):
		return text[1:-1]

	return text


def printable(text: str) -> str:
	return "".join(filter(lambda x: x in string.printable, text))


def strtoslice(text: str) -> slice:
	text = text.removeprefix("[").removesuffix("]")
	text = text.split(":")

	# Slices can either be of form slice(start), slice(start,end), slice(start,end,step). 
	# Make an array with the slice values, or None if no such value supplied
	def register_slice(idx):
		return int(text[idx]) if text[idx:idx+1] and text[idx] not in  ["None", ''] else None

	slice_text = [register_slice(0), register_slice(1), register_slice(2)]

	#slice_text = [int(text[0]) if text[0:1] else None, int(text[1]) if text[1:2] else None, int(text[2]) if text[2:3] else None]

	# Make the text a slice object from the inputted slice values
	return slice(*slice_text)


# TAKEN FROM PYTHOn CMD MODULE
def columnize(list: str, displaywidth: int = 80) -> str:
	"""Display a list of strings as a compact set of columns.
	Each column is only as wide as necessary.
	Columns are separated by two spaces (one was not legible enough).
	"""
	if not list:
		return ""

	nonstrings = [i for i in range(len(list))
					if not isinstance(list[i], str)]
	if nonstrings:
		raise TypeError("list[i] not a string for i in %s"
						% ", ".join(map(str, nonstrings)))
	size = len(list)
	if size == 1:
		return '%s\n'%str(list[0])
	# Try every row count from 1 upwards
	for nrows in range(1, len(list)):
		ncols = (size+nrows-1) // nrows
		colwidths = []
		totwidth = -2
		for col in range(ncols):
			colwidth = 0
			for row in range(nrows):
				i = row + nrows*col
				if i >= size:
					break
				x = list[i]
				colwidth = max(colwidth, len(x))
			colwidths.append(colwidth)
			totwidth += colwidth + 2
			if totwidth > displaywidth:
				break
		if totwidth <= displaywidth:
			break
	else:
		nrows = len(list)
		ncols = 1
		colwidths = [0]
	for row in range(nrows):
		texts = []
		for col in range(ncols):
			i = row + nrows*col
			if i >= size:
				x = ""
			else:
				x = list[i]
			texts.append(x)
		while texts and not texts[-1]:
			del texts[-1]
		for col in range(len(texts)):
			texts[col] = texts[col].ljust(colwidths[col])
		return "%s\n"%str("  ".join(texts))


def evaluate_name(name: str, default: object = True) -> tuple[str, bool]:
	"""
	Takes a string and determineis whether it should evaluate to true and false.
	A name evaluates to false it starts with "no-" or "no_"
	
	If a default is provided, starting the name with "!" will evlauate to not bool(default)

	:param name: The name to evaluate
	:param default: The value to flip (if provided) if the name starts with "!"
	:returns: A tuple of: (1) The name (lstripped of "no-", "no_", "!"), and (2) The bool value
	"""
	name = name.lower()
	value = default

	if name.startswith(("no-", "no_")):
		value = False
		name = name.removeprefix("no-").removeprefix("no_")
	elif name.startswith("!"):
		value = not bool(default)
		name = name.removeprefix("!")

	return name, value


def escape_unescaped_spaces(text: str, ignore_trailing_space = False) -> str:
	"""
	Take a string token and escape any non-escaped spaces (e.g.: "wow a dog" -> "wow\\ a\\ dog")
	Used for filepaths
	:param text: The text that will have escaped spaces
	:returns: The text so that any space will be preceeded by a backslash
	"""
	output = text.replace(" ", "\\ ").replace("\\\\ ", "\\ ")

	if ignore_trailing_space and output.endswith(" "):
		output = output.removesuffix("\\ ") + " "

	return output