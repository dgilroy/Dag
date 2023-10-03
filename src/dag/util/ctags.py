from __future__ import annotations

import re, abc, textwrap
from typing import Optional, Generator
from functools import reduce

import dag
from dag.lib import colors


TERMINAL = dag.get_terminal()


class CTag(str):
	def __init__(self, ctag: str):
		"""
		A helper class to process ctag strings

		CTags are tags styled like <c ...>BLAH</c>

		Closing CTags can contain styles allowing for selectively closing some styles and keeping others active

		:param ctag: The text of the ctag
		"""

		self.ctag = ctag


	def expand(self) -> list[CTag]:
		"""
		Takes a ctag with maybe multiple styles and returns a list of ctags with one style each

		(e.g. <c red blue> => <c red><c blue>)

		:returns: A list of single-style ctags
		"""

		closer = "/" if self.is_closing_tag else ""

		if len(self.styles) < 2:
			return [self]

		return [self.__class__(f"<{closer}c {style}>") for style in self.styles]



	@property
	def styles(self) -> list[str]:
		"""
		Return a list of styles attached to ctag

		(e.g. <c red bold> => ["red", "bold"])

		:returns: A list of the ctag's styles
		"""

		styles = re.search(r"\</?c (.*?)\>", self.ctag)

		stylelist = styles.groups()[0].lower().split(" ") if styles else []

		return [s for s in stylelist if s != ""] # Remove empty strings from styles


	@property
	def is_opening_tag(self) -> bool:
		"""
		Checks whether ctag is an opening tag

		:returns: Whether ctag is an opening tag
		"""
		return re.match(r"\<c ?(.*?)\>", self.ctag, re.IGNORECASE)


	@property
	def is_closing_tag(self) -> bool:
		"""
		Checks whether ctag is a closing tag

		:returns: Whether ctag is a closing tag
		"""

		return re.match(r"\</c ?(.*?)\>", self.ctag, re.IGNORECASE)


BACKGROUND_PREFIX = "bg-"

def strip_ctags(text):
	return re.sub(r"</?c\s?.*?>", "", text)




def iter_ctags_in_text(text: str) -> Generator[re.Match, None, None]:
	"""
	Scan text with regex searching for any ctags

	:param text: The text to parse
	:yields: the ctags from the text
	"""

	yield from re.finditer(r"\</?c\s?.*?\>", text, re.IGNORECASE)



def iter_open_ctags_in_text(text: str) -> Generator[re.Match, None, None]:
	"""
	Scan text with regex searching for any opening ctags

	Any closing tags (</c>, </c blue>) will not be matched

	:param text: The text to parse
	:yields: the ctags from the text
	"""

	yield from re.finditer(r"\<c .*?\>", text, re.IGNORECASE)


def kill_styles(active_styles, killed_styles):
	for ks in killed_styles:
		if ks.startswith("!"):
			ks = ks[1:]
			active_styles = [style for style in active_styles if style != ks]
		else:
			if ks in active_styles:
				active_styles.remove(ks)

	return active_styles


def expand_shortcut_ctags(text: str) -> str:
	"""
	Turns <c STYLE / text> into <c STYLE>text</c STYLE>
	"""
	otext = text
	text = re.sub(r"(\<c([^\>]+?)) */ *(.*?)\>", r"\1>\3</c\2>", text)

	if otext != text:
		text = expand_shortcut_ctags(text)

	return text


def process_closing_ctags(text: str) -> str:
	"""
	Closing Ctags are able to specify which styles are to be killed, leaving all other styles active
	If no style is provided, then all styles are killed

	So:
		<c red bold>text</c bold>text2</c> => <c red blue>text</c><c red>text2</c>
		<c red bold>text</c>text2</c> => <c red blue>text</c>text2</c>

	:param text: The text with closing ctags to be processed
	:returns: The text with processed ctags
	"""

	active_styles = []

	# Scans text and updates ctag styles to be compatible with any killed styles

	for colortag in iter_ctags_in_text(text):
		ctag = CTag(colortag.group(0))

		# if tag is an opening tag: Store active styles to activate
		if ctag.is_opening_tag:
			active_styles.extend(ctag.styles)
		# Else, tag is a close tag: Store closed styles to de-activate and update ctags to reflect non-killed styles
		elif ctag.is_closing_tag:
			killed_styles = ctag.styles

			# If no killed styles found, skip further processing
			if not killed_styles: # </c> kills all styles
				active_styles = []
				continue

			# Reverse active styles so the most recently-applied matching style gets removed
			active_styles.reverse()

			active_styles = kill_styles(active_styles, killed_styles)

			# Set active styles back to normal
			active_styles.reverse()

			active_ctags = ""

			for style in active_styles:
				active_ctags += f"<c {style}>"

			text = text[:text.index(ctag)] + f"</c>{active_ctags}" + text[text.index(ctag) + len(ctag):]

	return text


def expand_ctags(text: str) -> str:
	text = expand_shortcut_ctags(text)
	text = process_closing_ctags(text)
	return text


class CTagFormatter(abc.ABC):
	"""
	A class that converts c-tags (e.g. <c red>TEXT</c>) into termial coloring
	"""


	@classmethod
	def get_xterm_color_code(cls, style: str) -> str:
		"""
		xterm stores various stylings as control sequences. Retreive the sequence (if given style applies)

		:param style: The c-tag style being applied 
		:returns: the xterm control sequence
		"""

		style = style.lower()

		# If requested color is 1-3 digit number: treat it as ansi color digit
		if re.search(r"^\d{1,3}$", style):
			return style
		# Elif we are passing a HEX value: process it
		elif re.search(r"#[0-9a-fA-F]{2,6}$", style):
			style = style.replace(BACKGROUND_PREFIX.upper(), "")
			return cls.get_rgb_style_code_number(style)
		# Elif style is an xterm named color
		elif style in TERMINAL.colormap:
			return TERMINAL.colormap[style]
		elif style in dag.colors.htmlcolornames:
			stylehex = dag.colors.htmlcolornames[style]
			with dag.bbtrigger("htmlcolor"):
				return cls.get_rgb_style_code_number(stylehex)

		# If color didn't match any of the above patterns: return an empty string, ignoring the style
		return ""


	@classmethod
	def get_style_sequence(cls, style: str) -> str:
		"""
		process style and return proper TERMINAL styling

		Options:
			(1) A number that represents xterm color's index number
			(2) A named style
			(3) A hex vale

		:param style: The param to translate into TERMINAL styling
		:returns: The TERMINAL-compatible styling
		"""

		style = style.lower()
		
		# IF named terminal style: Return the entry's control sequence
		if style in TERMINAL.stylemap:
			return TERMINAL.stylemap[style]

		base = TERMINAL.COLOR_TEXT_BASE
		is_bg = False

		# IF style is a background: Indicate its background-ness and strip bg- prefix
		if style.startswith(BACKGROUND_PREFIX.lower()):
			is_bg = True
			base = TERMINAL.COLOR_BG_TEXT_BASE
			style = style.lstrip(BACKGROUND_PREFIX.lower())

		xterm_color = cls.get_xterm_color_code(style)

		# IF ";" in xterm sequence: This is probably RGB - set the appropriate base
		if ";" in xterm_color:
			base = cls.hex_bg_base if is_bg else cls.hex_text_base

		return base.format(xterm_value = xterm_color) if xterm_color else ""



	@classmethod
	def replace_ctags(cls, text: str) -> str:
		"""
		Ctags apply styles to TERMINAL outputs. This translates those ctags to the appropriate style codes

		:param text: The text with ctags to transform
		:returns: The text with transformed ctags
		"""

		replacements = {}

		# Replace ctags with appropriate TERMINAL styling
		for colortag in iter_open_ctags_in_text(text):
			ctag = CTag(colortag.group(0))

			if ctag in replacements:
				continue

			try:
				styles_str = ""
				
				for style in ctag.styles:
					styles_str += cls.get_style_sequence(style)
					
				replacements[ctag] = styles_str
			except AttributeError:
				continue	
			
		for tag in replacements.keys():
			text = text.replace(tag, replacements[tag])

		# Throw away any remaining empty opening ctags
		text = re.sub(r"<c\s*>", "", text, re.IGNORECASE)

		# Replace all closing tags with terminating style and return
		return text.replace("</c>", "\x1b[0m")



	@classmethod
	def format(cls, text: str) -> str:
		"""
		Takes an input text and converts its ctags into TERMINAL style sequences

		:param text: The text whose ctags must be processed
		:returns: The text with ctags turned into TERMINAL style sequences
		"""

		# Pass through texts that aren't strings
		if type(text) is not str:
			return text

		if dag.settings.NO_COLOR or dag.getenv.NO_COLOR or dag.getenv.TERM == "dumb":
			return strip_ctags(text)
		
		# Set up so that '<c red bold>hi</c red> bye' has bold bye
		text = process_closing_ctags(text)

		if dag.settings.noctags:
			return text

		return cls.replace_ctags(text)
		
			
	@classmethod
	def echo(cls, *args: tuple[str], **kwargs) -> str:
		"""
		Formats ctags and prints the output

		:param text: The text whose ctags will be processed
		:returns: The text with ctags replaced with style codes
		"""

		formatted_text = (cls.format(text) for text in args)

		try:
			dag.instance.view.echo(*formatted_text, **kwargs)
		except AttributeError:
			if not (dag.settings.silent or dag.settings.silent):
				print(*formatted_text, *args, **kwargs)
		return formatted_text


	@abc.abstractmethod
	def get_rgb_style_code_number(style: str) -> str:
		"""
		An abstract method for a method that turns RGB to control codes

		:param style: The hex to translate to style code
		:returns: The control code for the hex
		"""

		raise NotImplementedError("Must use a subclass of CTagFormatter to process hex strings")




class CTagFormatter8Bit(CTagFormatter):
	hex_text_base = TERMINAL.COLOR_TEXT_BASE
	hex_bg_base = TERMINAL.COLOR_BG_TEXT_BASE


	@classmethod
	def get_closest_hex_value(cls, color: colors.Color) -> str:
		"""
		Given a hex color string, finds the closest TERMINAL hex color key and returns that key

		:param hexstr: The hex string to find closest TERMINAL hex color to
		:returns: The closest TERMINAL hex color
		"""
				
		# Find the hex value with the smallest difference to the given hexstr and return the associated TERMINAL value
		return color.closestchoice(TERMINAL.rgb)


	@classmethod
	def get_rgb_style_code_number(cls, hexstr: str) -> str:
		"""
		Takes a given hexstr and finds its closest style code among the TERMINAL's colors

		:param hexstr: The hex color to translate into a style code
		:returns: The style code number of the color
		"""

		color = colors.fromhexstr(hexstr)
			
		try:
			return TERMINAL.rgb[str(color)]
		except AttributeError as e:
			raise AttributeError(f"Invalid Hex Value: {color}") from e
		except KeyError:
			return TERMINAL.rgb[cls.get_closest_hex_value(color)]




class CTagFormatter24Bit(CTagFormatter):
	hex_text_base = TERMINAL.COLOR_TEXT_BASE_24B
	hex_bg_base = TERMINAL.COLOR_BG_TEXT_BASE_24B

	@classmethod
	def get_rgb_style_code_number(cls, hexstr: str) -> str:
		"""
		Takes a given hexstr and translates it to the appropriate control code for full-color TERMINALs

		e.g. "#FF0000" => "255;0;0"

		:param hexstr: The hex color to translate into a style code
		:returns: The style code number of the color
		"""

		color = colors.fromhexstr(hexstr)
		return f"{color.r};{color.g};{color.b}"





def format(text: str, use_24b: Optional[bool] = None, close: bool = True) -> str:
	"""
	(1) Takes a given text, (2) Determines whether to use 8-bit or 24-bit color depth, (3) Returns text with ctag turned into style codes

	:param text: The text whose ctags will be processed
	:param use_24b: A param that, if set, will activate or deactivate 24bit mode
	:returns: The text whose ctags are processed
	"""

	if use_24b is None:
		use_24b = dag.get_platform().is_24b_color()

	# Turn <c STYLE / text> into <c STYLE>text</c STYLE>
	text = str(text)
	text = expand_shortcut_ctags(text)
	text = text + ("</c>" if close else "")

	ctagformatter = CTagFormatter24Bit if use_24b else CTagFormatter8Bit

	if dag.settings.noctags:
		return text

	return ctagformatter.format(text)


def rawformat(*args, **kwargs) -> str:
	return format(*args, **kwargs).replace("\\", "\\\\")


def echo(*args: tuple[str], use_24b: Optional[bool] = None, close = True, **kwargs) -> str:
	"""
	Formats the provided text's ctags and prints the output

	:param text: The text whose ctags will be processed and printed
	:param use_24b: A param that, if set, will activate or deactivate 24bit mode
	:returns: The text whose ctags are processed
	"""

	formatted_text = [format(text, use_24b = use_24b, close = close) for text in args]

	try:
		dag.instance.view.echo(*formatted_text, **kwargs)
	except AttributeError:
		if not (dag.ctx.silent or dag.settings.silent):
			print(*formatted_text, **kwargs)
	#return formatted_text If you want the text, format it






class CTagWordWrapper:
	def __init__(self, width: int):
		self.width = width
		self.reset()

	def reset(self):
		self.lines = []
		self.curline = ""
		self.curword = ""
		self.active_styles = []


	def create_textwrapper(self, len):
		return textwrap.TextWrapper(len)

	def process_text(self, text):
		return text.replace("\t", "    ")

	def itertext(self, text):
		if text:
			return text[0], text[1:]

		return '', ''


	def end_active_line(self):
		if self.active_styles:
			stylestr = " ".join(self.active_styles)
			self.curline += f"</c {stylestr}>"

		self.lines.append(self.curline)
		self.curline = ""

		if self.active_styles:
			self.curline += f"<c {stylestr}>"

		self.curline += self.curword.lstrip(" ")
		self.curword = ""


	def maybe_process_curword(self):
		# IF there is a current active word: Add to current line OR append to new line
		if self.curword:
			newlen = len(strip_ctags(self.curline + self.curword))

			# IF current line + current word is NOT too wide: Append current word to current line
			if newlen <= self.width:
				self.curline += self.curword
				self.curword = ""
			# ELIF current line + current word is not too wide if we ignore the trailing space: Remove space and append
			# current word to current line
			elif newlen == self.width + 1 and self.curword.endswith(" "):
				self.curword = self.curword[:-1]
				self.maybe_process_curword()
				return
			# Else, current line + current word is too wide: Close current line and append current word to new line
			else:
				if len(self.curword) > self.width:

					chunks = [self.curword[i:i+self.width] for i in range(0, len(self.curword), max(self.width, 1))]
					"""
					This hyphenates overly-long words
					chunks = [self.curword[i:i+self.width-1] + "-" for i in range(0, len(self.curword), max(self.width-1, 1))]
					if chunks:
						chunks.reverse()

						for i, chunk in enumerate(chunks):
							# IF first chunk is nothing but spaces and a dashe: make it empty
							if chunk.strip().removeprefix("-") == "":
								chunks[i] = ""
								continue
							# ELSE, chunk has letters: Remove the ending dash and then break the loop
							# (Only want to remove dash from last letter of the chunked word)
							else:
								chunks[i] = chunks[i].removesuffix("-") 	
								break

						chunks.reverse()
					"""
					for chunk in chunks:
						self.curword = chunk
						self.maybe_process_curword()
				self.end_active_line()


	def wrap(self, intext):
		self.reset()

		origtext = intext
		tw = self.create_textwrapper(len)

		intext = self.process_text(intext)

		textlines = intext.splitlines()

		ctag = ""

		for text in textlines:
			t = text

			while text:
				ch, text = self.itertext(text)

				match ch:
					case "<":
						self.maybe_process_curword()
						self.curword += ch

						ch, text = self.itertext(text)
						self.curword += ch

						if ch == "/":
							ch, text = self.itertext(text)
							self.curword += ch

						if ch == "c":
							ctag = self.curword
							self.curword = ""

							while text:
								ch, text = self.itertext(text)
								ctag += ch

								match ch:
									case ">":
										ctag = CTag(ctag)

										if ctag.is_opening_tag:
											self.active_styles += ctag.styles
										elif ctag.is_closing_tag:
											if not ctag.styles:
												self.active_styles = []
											else:
												self.active_styles = kill_styles(self.active_styles, ctag.styles)
												#need to process styled closing tags
										else:
											self.active_styles += ctag.styles
											
										self.curline += ctag
										ctag = ""
										break
					case " " | "-":
						if ch == " " and not strip_ctags(self.curline + self.curword):
							continue
						self.curword += ch
						self.maybe_process_curword()
					case _:
						self.curword += ch

			self.maybe_process_curword()
			self.end_active_line()

		return self.lines

