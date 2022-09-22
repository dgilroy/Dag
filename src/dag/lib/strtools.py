import re

quotemarks = ['"', "'"]

def is_valid_quoted_string(text: str) -> bool:
	"""
	Checks the given text and sees whether the text is:
		(1) Correctly wrapped in quotation marks
		(2) Any quotation marks within the quotes are escaped
		(3) The final quotation mark isn't escaped

	:param text: The text to check whether its validly quoted
	:returns: Whether or not the text is validly quoted
	"""

	if not text or len(text) < 2 or text[0] not in quotemarks:
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

