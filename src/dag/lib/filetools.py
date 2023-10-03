import os
from pathlib import Path

def listdir(directory: str | Path = ".", dirs: bool = True, files: bool = True, filetypes: list[str] | None = None) -> list[Path]:
	"""
	Get the files listed in for a given directory

	:param directory: The directory to search
	:param dir: Whether or not to include subdirectories
	:param file: Whether or not to include files
	:param filetypes: A list of filetypes to narrow search for (if given)
	:returns: A list of files in the given directory
	"""

	# Appends "." to the beginning of a filetype if it's not already there (e.g.: "jpg" -> ".jpg")
	filetypes = filetypes or []
	filetypes = ["." + f.removeprefix(".") for f in filetypes or []]

	try:
		# Retrieve the files in the directory
		basefiles = next(os.walk(directory))
	except Exception:
		return []

	# The items to be returned
	items = []
	
	# Get directories
	if dirs:
		items += [f"{f}/" for f in basefiles[1]]
		
	# Get files
	if files:
		fileitems = [f"{f}" for f in basefiles[2]] #fileitems so that filetypes can be filtered before adding to main items list

		# IF filetypes were provided: Limit the files to those of the given filetype
		if filetypes:
			fileitems = [f for f in fileitems if "." + f.split(".")[-1] in filetypes]

		items += fileitems

	# Turn the items in to pathlib Paths
	return [Path(i) for i in items]



	"""
	-> TOO SLOW FOR BIG DIRECTORIES

	
	# Turn the directory into a pathlib Path (Not dag.Path bc this is in lib)
	directory = Path(directory)

	# Make sure filetyeps start with "." (e.g.: ".jpg" instead of "jpg")
	filetypes = ["." + f.removeprefix(".") for f in filetypes or []]

	# IF given directory is in fact a file: Just return the given path
	if not directory.is_dir():
		return directory

	files = []

	# FOR items in directory: See if item should be included in response
	for item in directory.iterdir():
		# IF item is a directory and directories are requested: Include the directory
		if item.is_dir() and dir:
			files.append(item)
		# IF item is file, files are requested, and file is a desired filetype: Include the file
		elif item.is_file() and file and (not filetypes or item.suffix in filetypes):
			files.append(item)

	return files

	"""