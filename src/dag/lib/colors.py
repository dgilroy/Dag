import colorsys
from dataclasses import dataclass



@dataclass
class Color:
	r: int = 0
	g: int = 0
	b: int = 0

	@property
	def r1(self):
		return self.r/255

	@property
	def g1(self):
		return self.g/255

	@property
	def b1(self):
		return self.b/255


	@property
	def hexstring(self):
		return f"#{self.r:x}{self.g:x}{self.b:x}"

	@property
	def rgb(self):
		return self.r, self.g, self.b

	def _colorsys_rgb_to(self, fn):
		return fn(self.r1, self.g1, self.b1)

	@property
	def yiq(self):
		return self._colorsys_rgb_to(colorsys.rgb_to_yiq)

	@property
	def hls(self):
		return self._colorsys_rgb_to(colorsys.rgb_to_yiq)

	@property
	def hsv(self):
		return self._colorsys_rgb_to(colorsys.rgb_to_yiq)


	def gradient(self, other, steps = 3):
		def step(color, delta, step):
			return color + int(delta*step/(steps-1))

		dr = other.r - self.r
		dg = other.g - self.g
		db = other.b - self.b

		return [Color(step(self.r, dr, i), step(self.g, dg, i), step(self.b, db, i)) for i in range(steps)]


	def __str__(self):
		return self.hexstring

	def __iter__(self): # Allows for unpacking color
		return iter((self.r, self.g, self.b))

	def ctag(self, text = ""):
		return f"<c {self.hexstr}>{text}</c>"


def to255(number):
	return int(number*255)


def rgb(r,g,b):
	return Color(r,g,b)


def rgb1(r,g,b):
	return rgb(to255(r),to255(g),to255(b))


def colorsys_from(fn, *args):
	return rgb1(*fn(*args))


def hls(h,s,l): return (colorsys.hls_to_rgb, h, s, l)
def yiq(y,i,q): return (colorsys.yiq_to_rgb, y, i, q)
def hsv(h,s,v): return (colorsys.hsv_to_rgb, h, s, v)


def expand_hexstr(hexstr: str) -> str:
	"""
	An interpreter that takes in hex-like strings and converts them into a properly-formatted 6-character hex string

	eg:
		(1) F => FFFFFF
		(2) FF => FFFFFF
		(3) F0F => FF00FF
		(4) F00 => FF0000

	:param color: The hex string to interpret
	:returns: The hex value converted to 6-characters
	:raises AttributeError: If the string cannot be interpreted as a hex string
	"""

	# Strip the prefix hashmark and background prefix
	orig_hexstr = hexstr
	hexstr = hexstr.upper().replace("#", "")

	# If hexstr is one character: sextuple it into a grey hexstr				eg) #F -> #FFFFFF
	if len(hexstr) == 1:
		return hexstr*6
	# If hexstr is two characters: triple it into a grey hexstr					eg) #F0 -> #F0F0F0
	if len(hexstr) == 2:
		return hexstr*3
	# Elif hexstr is three characters: double each character to get hexstr		eg) #F00 -> #FF0000
	elif len(hexstr) == 3:
		return hexstr[0]*2 + hexstr[1]*2 + hexstr[2]*2
	# Elif hexstr is 6 characters: return the orig_hexstr	
	elif len(hexstr) == 6:
		return hexstr


	# Else, hexstr isnt 2,3, or 6 chars long: Raise exception
	raise AttributeError(f"Invalid HEX string specified: {orig_hexstr}")


def hexstr(hexstr):
	hexstr = hexstr.strip("#")
	hexstr = expand_hexstr(hexstr)

	r = int(hexstr[0:2], 16)
	g = int(hexstr[2:4], 16)
	b = int(hexstr[4:6], 16)
	return Color(r,g,b)