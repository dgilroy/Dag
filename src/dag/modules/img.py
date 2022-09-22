import dag
from dag import this



@dag.mod("img", default_cmd = this.from_url)
class ImgMod(dag.DagMod):

	@dag.arg.File('path')
	@dag.cmd()
	def dim(self, path):
		img = dag.img.from_path(path)
		return f"{img.height}px h x {img.width}px w"

	

	@dag.arg("--sharp", help = "Whether to darken alpha pixels", flag = True)
	@dag.arg("--maxheight", help = "The maximum width of the image", type = int)
	@dag.arg("--maxwidth", help = "The maximum width of the image", type = int) #Apparently naming arg "width" annoys Image.open
	@dag.arg("--symbol", help = "The text symbol used to display the image")
	@dag.arg("url", help = "The URL of the image to display")
	@dag.cmd()
	def from_url(self, url = "https://www.dylangilroy.com/logo.png", symbol = "█", maxwidth = 99999, maxheight = 99999, sharp = False):
		"""View an image for a given URL"""
		return dag.img.from_url(url).to_cli(symbol = symbol, maxwidth = maxwidth, maxheight = maxheight, sharp = sharp)




	@dag.arg("--name")
	@dag.arg("--quality")
	@dag.arg.Int("--width", min = 0)
	@dag.arg.Int("--height", min = 0)
	@dag.arg.File('file')
	@dag.cmd()
	def resize(self, file, height = 0, width = 0, quality = 100, name = None):
		if not (height or width):
			return "Please enter --height or --width"

		filename = name or file.stem
		ext = file.suffix[1:]
		img = dag.img.from_path(file)
		
		img.resize(height, width)

		full_filename = filename + f"-{img.width}x{img.height}." + ext
		img.save(full_filename, quality = quality)



	@dag.arg("--name")
	@dag.arg("--quality")
	@dag.arg.Int("--width", min = 0)
	@dag.arg.Int("--height", min = 0)
	@dag.arg.File('file', filetype = "pdf")
	@dag.cmd()
	def pdf(self, file, height = 0, width = 600, quality = 80, name = None):
		import pdf2image
		images = pdf2image.convert_from_path(file)
 
		for i, image in enumerate(images):
			# Save pages as images in the pdf
			filename = name or file.stem
			filename = f"{filename}-{i+1}" if len(images) > 1 else filename
			dag.img(image).resize(height = height, width = width).save(f"{filename}.jpg", quality = quality)



	@dag.arg("url", help = "The URL of the image to display")
	@dag.cmd()
	def ascii(self, url = "https://www.dylangilroy.com/logo.png"):
		return dag.img.from_url(url).to_ascii()