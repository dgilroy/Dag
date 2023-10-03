import io, math, shutil, pathlib
from collections import namedtuple

import dag

with dag.dtprofiler("import PIL Image"):
	from PIL import Image

ImgDimensions = namedtuple("ImgDimensions", "height width")
FILETYPES = [".jpg", ".png", ".jpeg", ".gif", ".bmp", ".tiff"]


class DagImg(dag.DotProxy):
	def __init__(self, img):
		if isinstance(img, bytes):
			from PIL import Image
			img = Image.open(io.BytesIO(img))

		self.img = img # Should be a Pillow Image
		super().__init__(self.img)


	def convert(self, *args, **kwargs):
		self.img = self.img.convert(*args, **kwargs)
		return self


	@staticmethod
	def new(*args, **kwargs):
		from PIL import Image
		return Image.new(*args, **kwargs)


	def to_cli(self, symbol = "█", maxwidth = 99999, maxheight = 99999, sharp = False, cropbbox = True):
		from PIL import Image
		img = self.img


		if cropbbox:
			bbox = img.getbbox()
			img = img.crop((bbox[0], bbox[1], bbox[2], bbox[3]))

		# Converts image so that transparent pixels turn black (looks better on black terminal)
		if not sharp:
			img = img.convert('RGBA')
		
			background = Image.new('RGBA', img.size, (0,0,0))
			img = Image.alpha_composite(background, img)


		maximgwidth = shutil.get_terminal_size().columns - 5
		maximgheight = min(maxheight, shutil.get_terminal_size().lines - 5)
		
		newwidth = min(maxwidth, math.floor(img.size[0] * (maximgheight / img.size[1]) *(20/9)), maximgwidth)
		#newheight = math.floor(maximgheight * (maxwidth / newwidth)) if newwidth > maximgwidth else maximgheight
		newheight = int(math.floor(newwidth * img.height/img.width) * 16/29)

		img2 = img.resize((newwidth, newheight), resample = Image.BILINEAR)
		rgb = img2.convert("RGB")

		
		hexes = {}
		for col in range(0, newheight):
			hexes[col] = []
			for pixel in range(0, newwidth):
				r = format(rgb.getpixel((pixel, col))[0], "x").rjust(2, "0")
				g = format(rgb.getpixel((pixel, col))[1], "x").rjust(2, "0")
				b = format(rgb.getpixel((pixel, col))[2], "x").rjust(2, "0")
				hex = f"#{r}{g}{b}"
				hexes[col].append(hex)
			
		output = ""
		for col in hexes.values():
			for hex in col:
				output += f"<c {hex}>{symbol}</c>"
			output += "\n"

		return output


	@classmethod
	def from_url(cls, url, cache = True, bytes = True):
		from PIL import Image
		get = dag.get

		if cache:
			get = get.CACHE

		if bytes:
			get = get.BYTES

		imgbytes = get(url)
		img = Image.open(io.BytesIO(imgbytes))
		return cls(img)


	@classmethod
	def open(cls, path):
		from PIL import Image

		img = Image.open(path)
		return cls(img)


	from_path = open


	@classmethod
	def from_pdf(cls, path):
		import pdf2image
		breakpoint()
		pass


	def to_formatter(self, formatter, **kwargs):
		cli_img = self.to_cli(**kwargs)

		for row in cli_img.split("\n"):
			formatter.add_row(row, id = "img")

		return formatter


	def to_ascii(self):
		from PIL import Image

		gscale2 = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
		gscale1 = '@%#*+=-:. '
		
		img = self.img
		
		maxwidth = shutil.get_terminal_size().columns - 5
		maxheight = shutil.get_terminal_size().lines - 5
		
		newwidth = min(math.floor(img.size[0] * (maxheight / img.size[1]) *(29/16)), maxwidth)
		newheight = math.floor(maxheight * (maxwidth / newwidth)) if newwidth > maxwidth else maxheight

		img2 = img.resize((newwidth, newheight), resample = Image.BILINEAR)
		grey = img2.convert("L")
		
		asciis = {}
		for col in range(0, newheight):
			asciis[col] = []
			for pixel in range(0, newwidth):
				val = grey.getpixel((pixel, col))
				idx = int(val/255 * len(gscale1)) - 1
				asciis[col].append(gscale1[idx])
			
		output = ""
		for col in asciis.values():
			for ascii in col:
				output += ascii
			output += "\n"
			
		return output


	def resize(self, height = 0, width = 0):
		assert height or width, "Must enter height or width"
		
		if height and width:
			self.img = self.img.resize((width, height))
		else:
			height = height or 10000
			width = width or 10000
			self.img.thumbnail((width, height))

		return self


	def save(self, filename, subsampling = 0, **kwargs):
		filename = dag.file.filename_avoid_overwrite(filename)
		dag.echo(f"Saving images <c b>{filename}</c> at size <c b>{self.img.width}x{self.img.height}</c>")
		self.img.save(filename, subsampling = subsampling, **kwargs)
		return self


	def dim(self) -> ImgDimensions:
		return ImgDimensions(self.height, self.width)


	def __repr__(self):
		return f"DagImg({self.filename})"