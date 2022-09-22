import re

vowels = "aeiou"
consonants = "bcdfghjklmnpqrstvwxyz"


def pluralize(text: str) -> str:
	"""
	A naieve function for pluralizing english words
	Doesn't account for irregular plurals

	:param text: The word to pluralize
	:returns: The pluralized word
	"""

	suffix = "s"

	if text.endswith("s") or text.endswith("sh"):
		suffix = "es"
	elif re.search(fr"[{consonants}]y$", text):
		text = text[:-1] + "ie"

	return text + suffix



def pluralize_by_quantity(quantity: float, text: str, plural: str = "") -> str:
	"""
	Pluralized the given text if the quantity doesn't equal 1

	:param quantity: The quantity of the word being pluralized
	:param text: The word to pluralize
	:param plural: The desired pluralized word if it's an irregular plural
	:returns: The pluralized word
	"""

	if quantity != 1:
		return plural or pluralize(text)

	return text


def quantize(quantity: float, text: str, plural: str = "") -> str:
	"""
	Returns a string with the quantity and the text, pluralized if necessary

	:param quantity: The quantity of the word being pluralized
	:param text: The word to pluralize
	:param plural: The desired pluralized word if it's an irregular plural
	:returns: A string with the quantity and the (possibly pluralized) word
	"""

	return f"{quantity} " + pluralize_by_quantity(quantity, text, plural)


def quantize_or_ignore(quantity: float, text: str, plural: str = "") -> str:
	"""
	Returns a string with the quantity and the text, pluralized if necessary
	If quantity is 0: return an empty string

	:param quantity: The quantity of the word being pluralized
	:param text: The word to pluralize
	:param plural: The desired pluralized word if it's an irregular plural
	:returns: A string with the quantity and the (possibly pluralized) word
	"""

	return quantize(quantity, text, plural) if quantity else ""


def gerund(word):
	if not word:
		return ""

	suffix = "ing"

	if len(word) <= 2:
		return word + suffix

	if word.endswith("ee"):
		pass
	elif word[-2] in vowels and word[-1] in consonants:
		word = word + word[-1] # dat => datt
	elif word[-1] == "e":
		word = word[:-1]	# date => dat

	return word + suffix
