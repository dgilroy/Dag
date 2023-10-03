import colorsys
from numbers import Real
from dataclasses import dataclass
from typing import Callable



htmlcolornames = { 'aliceblue': '#F0F8FF', 'antiquewhite': '#FAEBD7', 'aqua': '#00FFFF', 'aquamarine': '#7FFFD4', 'azure': '#F0FFFF', 'beige': '#F5F5DC', 'bisque': '#FFE4C4', 'black': '#000000', 'blanchedalmond': '#FFEBCD', 'blue': '#0000FF', 'blueviolet': '#8A2BE2', 'brown': '#A52A2A', 'burlywood': '#DEB887', 'cadetblue': '#5F9EA0', 'chartreuse': '#7FFF00', 'chocolate': '#D2691E', 'coral': '#FF7F50', 'cornflowerblue': '#6495ED', 'cornsilk': '#FFF8DC', 'crimson': '#DC143C', 'cyan': '#00FFFF', 'darkblue': '#00008B', 'darkcyan': '#008B8B', 'darkgoldenrod': '#B8860B', 'darkgray': '#A9A9A9', 'darkgreen': '#006400', 'darkkhaki': '#BDB76B', 'darkmagenta': '#8B008B', 'darkolivegreen': '#556B2F', 'darkorange': '#FF8C00', 'darkorchid': '#9932CC', 'darkred': '#8B0000', 'darksalmon': '#E9967A', 'darkseagreen': '#8FBC8F', 'darkslateblue': '#483D8B', 'darkslategray': '#2F4F4F', 'darkturquoise': '#00CED1', 'darkviolet': '#9400D3', 'deeppink': '#FF1493', 'deepskyblue': '#00BFFF', 'dimgray': '#696969', 'dodgerblue': '#1E90FF', 'firebrick': '#B22222', 'floralwhite': '#FFFAF0', 'forestgreen': '#228B22', 'fuchsia': '#FF00FF', 'gainsboro': '#DCDCDC', 'ghostwhite': '#F8F8FF', 'gold': '#FFD700', 'goldenrod': '#DAA520', 'gray': '#808080', 'green': '#008000', 'greenyellow': '#ADFF2F', 'honeydew': '#F0FFF0', 'hotpink': '#FF69B4', 'indianred': '#CD5C5C', 'indigo': '#4B0082', 'ivory': '#FFFFF0', 'khaki': '#F0E68C', 'lavender': '#E6E6FA', 'lavenderblush': '#FFF0F5', 'lawngreen': '#7CFC00', 'lemonchiffon': '#FFFACD', 'lightblue': '#ADD8E6', 'lightcoral': '#F08080', 'lightcyan': '#E0FFFF', 'lightgoldenrodyellow': '#FAFAD2', 'lightgray': '#D3D3D3', 'lightgreen': '#90EE90', 'lightpink': '#FFB6C1', 'lightsalmon': '#FFA07A', 'lightseagreen': '#20B2AA', 'lightskyblue': '#87CEFA', 'lightslategray': '#778899', 'lightsteelblue': '#B0C4DE', 'lightyellow': '#FFFFE0', 'lime': '#00FF00', 'limegreen': '#32CD32', 'linen': '#FAF0E6', 'magenta': '#FF00FF', 'maroon': '#800000', 'mediumaquamarine': '#66CDAA', 'mediumblue': '#0000CD', 'mediumorchid': '#BA55D3', 'mediumpurple': '#9370DB', 'mediumseagreen': '#3CB371', 'mediumslateblue': '#7B68EE', 'mediumspringgreen': '#00FA9A', 'mediumturquoise': '#48D1CC', 'mediumvioletred': '#C71585', 'midnightblue': '#191970', 'mintcream': '#F5FFFA', 'mistyrose': '#FFE4E1', 'moccasin': '#FFE4B5', 'navajowhite': '#FFDEAD', 'navy': '#000080', 'oldlace': '#FDF5E6', 'olive': '#808000', 'olivedrab': '#6B8E23', 'orange': '#FFA500', 'orangered': '#FF4500', 'orchid': '#DA70D6', 'palegoldenrod': '#EEE8AA', 'palegreen': '#98FB98', 'paleturquoise': '#AFEEEE', 'palevioletred': '#DB7093', 'papayawhip': '#FFEFD5', 'peachpuff': '#FFDAB9', 'peru': '#CD853F', 'pink': '#FFC0CB', 'plum': '#DDA0DD', 'powderblue': '#B0E0E6', 'purple': '#800080', 'rebeccapurple': '#663399', 'red': '#FF0000', 'rosybrown': '#BC8F8F', 'royalblue': '#4169E1', 'saddlebrown': '#8B4513', 'salmon': '#FA8072', 'sandybrown': '#F4A460', 'seagreen': '#2E8B57', 'seashell': '#FFF5EE', 'sienna': '#A0522D', 'silver': '#C0C0C0', 'skyblue': '#87CEEB', 'slateblue': '#6A5ACD', 'slategray': '#708090', 'snow': '#FFFAFA', 'springgreen': '#00FF7F', 'steelblue': '#4682B4', 'tan': '#D2B48C', 'teal': '#008080', 'thistle': '#D8BFD8', 'tomato': '#FF6347', 'turquoise': '#40E0D0', 'violet': '#EE82EE', 'wheat': '#F5DEB3', 'white': '#FFFFFF', 'whitesmoke': '#F5F5F5', 'yellow': '#FFFF00', 'yellowgreen': '#9ACD32'}


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
		return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

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
		return f"<c {self.hexstring}>{text}</c>"

	@property
	def bit8(self):
		def round8bit(num):
			return round((round(num*7/255)*255/7))

		r,g,b = round8bit(self.r), round8bit(self.g), round8bit(self.b)
		return type(self)(r,g,b)


	def closestchoice(self, choices):
		# Takes a list of hexstring chcoies, e.g. ["#FF0000", "#000000", ...]
		hexval = min(choices, key = lambda x: abs(int(x[1:3], 16) - self.r) + abs(int(x[3:5], 16) - self.g) + abs(int(x[5:7], 16) - self.b ))
		return type(self)(hexval)


def to255(number: Real) -> int:
	"""
	Used to convert between a number 0<= X <=1 and integer 0 <= X <= 255

	:param number: The decimal number being input
	:returns: That number as a value between 0 and 255
	"""
	return int(number*255)


def rgb(r: int, g: int, b: int) -> Color:
	return Color(r,g,b)


def rgbfromdecimal(r: Real, g: Real, b: Real) -> Color:
	return rgb(to255(r),to255(g),to255(b))


def colorsys_from(fn: Callable[[Real, Real, Real], tuple[float, float, float]], *args) -> Color:
	return rgbfromdecimal(*fn(*args))


def hls(h: Real, s: Real , l: Real) -> Color:
	return colorsys_from(colorsys.hls_to_rgb, h, s, l)


def yiq(y: Real, i: Real, q: Real) -> Color:
	return colorsys_from(colorsys.yiq_to_rgb, y, i, q)


def hsv(h: Real, s: Real, v: Real) -> Color:
	return colorsys_from(colorsys.hsv_to_rgb, h, s, v)


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


def fromhexstr(hexstr: str) -> Color:
	hexstr = hexstr.strip("#")
	hexstr = expand_hexstr(hexstr)

	r = int(hexstr[0:2], 16)
	g = int(hexstr[2:4], 16)
	b = int(hexstr[4:6], 16)
	return Color(r,g,b)


def fromstr(name) -> Color:
	import dag

	# If name in colormap (e.g.: "red"), then convert to proper hex value
	if name in dag.get_terminal().colormap:
		mapval = dag.get_terminal().colormap.get(name)
		name = dag.get_terminal().termtorgb.get(mapval)
	elif name in htmlcolornames:
		name = htmlcolornames[name]

	return fromhexstr(name)