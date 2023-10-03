import re, os

import dag



img = dag.app("img")


@img.cmd
def imgpath(imgpath: dag.Img):
	return imgpath



@dag.cmd
def dim(path: dag.Path):
	if path.is_dir():
		files = [*path.iterdir()]
	else:
		files = [path]

	imgs = []
	for file in files:
		with dag.passexc():
			img = dag.img.from_path(file)
			img.name = file.name
			imgs.append(img)

	return imgs


@dim.display
def display_dim(response, formatter):
	for img in response:
		formatter.add_row(img.name)
		formatter.add_row(f"<c red b / {img.height}px h x {img.width}px w>\n")

	return formatter


@img.arg.Path("path")
@img.cmd
def crop(path, *, bgcolor = "#FFF", height: int = -1, width: int = -1, quality: int = 100):
	if height < 0 and width < 0:
		return "Must enter a height or a width in pixels"

	if path.is_dir():
			files = [*path.iterdir()]
	else:
		files = [path]

	for file in files:
		if file.suffix not in [".jpg", ".png", ".jpeg"]:
			continue

		img = dag.img.from_path(file)

		cwidth  = img.width if width < 0 else width
		cheight = img.height if height < 0 else height

		canvas_size = (cwidth, cheight)  # Change these values to your desired canvas size
		canvas_image = dag.img.new('RGB', canvas_size, dag.colors.fromhexstr(bgcolor).rgb)

		paste_x = (canvas_size[0] - img.width) // 2
		paste_y = (canvas_size[1] - img.height) // 2

		canvas_image.paste(img, (paste_x, paste_y))

		filename = file.stem
		ext = file.suffix[1:]
		full_filename = filename + f"-{cwidth}x{cheight}." + ext
		canvas_image.save(full_filename, quality = quality)

		dag.echo(f"saved file <c b red / {full_filename}>")



@img.arg.Flag("--sharp", help = "Whether to darken alpha pixels")
@img.arg.Int("--maxheight -h", help = "The maximum height of the image")
@img.arg.Int("--maxwidth -w", help = "The maximum width of the image") #Apparently naming arg "width" annoys Image.open
@img.arg("--symbol", help = "The text symbol used to display the image")
@img.arg("url", help = "The URL of the image to display")
@img.DEFAULT.cmd
def from_url(url = "http://www.dylangilroy.com/favicon.ico", symbol = "█", maxwidth: int = 99999, maxheight = 99999, sharp = False):
	"""View an image for a given URL"""
	return dag.img.from_url(url).to_cli(symbol = symbol, maxwidth = maxwidth, maxheight = maxheight, sharp = sharp)




@img.arg("--name")
@img.arg.Int("--quality")
@img.arg.Int("--width", min = 0)
@img.arg.Int("--height", min = 0)
@img.arg.Path('file')
@img.cmd
def resize(file, *, height: int = 0, width = 0, quality: int = 100, name = None):
	if not (height or width):
		return "Please enter --height or --width"

	if file.is_dir():
		files = [*file.iterdir()]
	else:
		files = [file]

	for file in files:
		filename = name or file.stem
		ext = file.suffix[1:]
		img = dag.img.from_path(file)

		img.resize(height = height, width = width)

		full_filename = filename + f"-{img.width}x{img.height}." + ext
		img.save(full_filename, quality = quality)

	return full_filename


@img.arg.File("file")
@img.cmd
def jpg(file, quality: int = 100):
	if re.match("jp.?g", file.suffix):
		return

	img = dag.img.from_path(file)
	img = img.convert("RGB")
	img.save(file.with_suffix(".jpg"), quality = quality)




@img.arg("url", help = "The URL of the image to display")
@img.cmd
def ascii(url = "http://www.dylangilroy.com/favicon.ico"):
	return dag.img.from_url(url).to_ascii()




@dag.arg.Flag("--all", target = "allpages")
@dag.arg("--name")
@dag.arg("--quality")
@dag.arg.Int("--width", min = 0)
@dag.arg.Int("--height", min = 0)
@dag.arg.File('file', filetype = "pdf")
@dag.cmd
def pdf2img(file, page: int = None, height = 0, width = 900, quality: int = 80, name = None, allpages = False):
	import pdf2image

	pdfinfo = pdf2image.pdfinfo_from_path(file)

	startpage = None
	endpage = None

	if allpages or pdfinfo["Pages"] == 1:
		page = -1
	else:
		page = page if page is not None else int(dag.cli.prompt("Enter page number (-1 for all)"))

	if page != -1:
		startpage = page
		endpage = page+1

	images = pdf2image.convert_from_path(file, first_page = startpage, last_page = endpage)

	firstfilename = None

	for i, image in enumerate(images):
		filename = name or file.stem
		firstfilename = firstfilename or filename
		filename = f"{filename}-{i+1}" if len(images) > 1 else filename
		dag.img(image).resize(height = height, width = width).save(f"{filename}.jpg", quality = quality)

	return dag.Path(firstfilename)