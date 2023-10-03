import re

def item_is_rslash(text: str) -> bool:
	if not isinstance(text, str):
		return False

	if len(text) <= 2:
		return False

	return text.startswith("r/") and "/" in text[3:]


def get_regex_content(text: str) -> tuple[str, str]:
	rslashidx = text.find("r/")
	endslashidx = text.rfind("/")

	pattern = text[rslashidx+2:endslashidx]
	flags = text[endslashidx+1:]

	return pattern, flags


def parse_flagchars(flags: str) -> int:
	re_flags = 0

	if flags:
		for f in flags:
			re_flags |= getattr(re, f.upper()) # python regex flags re stored as re.I, re.X, etc...

	return re_flags


def run_regex_op(regexop, text, rslash):
	pattern, flags = get_regex_content(rslash)
	re_flags = parse_flagchars(flags)

	return regexop(pattern, text, re_flags)



def match_rslash(text, rslash):	return run_regex_op(re.match, text, rslash)
def search_rslash(text, rslash): return run_regex_op(re.search, text, rslash)
def fullmatch_rslash(text, rslash): return run_regex_op(re.fullmatch, text, rslash)
def findall_rslash(text, rslash): return run_regex_op(re.findall, text, rslash)
def finditer_rslash(text, rslash): return run_regex_op(re.finditer, text, rslash)