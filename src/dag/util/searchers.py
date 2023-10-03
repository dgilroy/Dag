import re, fnmatch

from dag.lib import dot
from dag.util import rslashes

class Searcher(str, dot.DotProxy):
	def __new__(cls, text: str, *args, **kwargs):
		regexflags = 0

		# Will be set to True if this is an rslash (e.g.: r/text.*/)
		is_regex = False

		# IF the text is an rslash: prep regex info
		if rslashes.item_is_rslash(text):
			is_regex = True
			text, flagchars = rslashes.get_regex_content(text)
			regexflags = rslashes.parse_flagchars(flagchars)


		searcher =  super().__new__(cls, text)
		searcher.is_regex = is_regex
		searcher.regexflags = regexflags

		# TRY: re will complain if string starts with "*" (aka a GLOB string). Listen for complaint and respond if it happens
		try:
			searcher.compiled = re.compile(searcher, searcher.regexflags)
		# EXCEPT re.error: If string starts with "*", append a "." in front so it behaves as desired
		except re.error as e:
			# IF searcher starts with "*": This is what caused the complaint, so attempt a fix
			if searcher.startswith("*"):
				searcher.compiled = re.compile("." + searcher, searcher.regexflags)
			# ELSE, text doesn't start with "*": Something else caused the error. Raise the exception
			else:
				raise e

		searcher._add_proxy(searcher.compiled)

		return searcher


	def split(self, value):
		return self.compiled.split(value)


	def fnmatch(self, key):
		return fnmatch.fnmatch(key, self)


	def search(self, key):
		if self.is_regex:
			return re.search(self, key)

		return self.fnmatch(key)

