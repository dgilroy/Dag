import gzip, os, pathlib

import dag

ext = dag.settings.CACHEFILE_EXT + ".gz"

	
class PersistenceFile:
	def __init__(self, root):
		self.root = pathlib.Path(root)


	def format_filename_chars(self, name):
		return name.replace("://", ".").replace("?", ".").replace("/", "-").replace(" ", "%20").replace("&", ".").replace("\\", "")


	def process_filepath(self, folder, filename):
		filename = self.format_filename_chars(filename.strip("/")).removesuffix(ext) + ext
		return self.root / folder / filename


	def exists(self, folder, filename):
		filepath = self.process_filepath(folder, filename) 
		return dag.file.exists(filepath)


	def read(self, folder, filename):
		import dill
		filepath = self.process_filepath(folder, filename) 

		with dag.file.open(filepath, "rb", opener = gzip.open) as f:
			return dill.load(f)


	def write(self, text, folder, filename):
		import dill

		filepath = self.process_filepath(folder, filename) 
		
		try:
			with dag.file.open(filepath, "wb+", opener = gzip.open) as f:
				dill.dump(text, f)

		except TypeError as e:
			dag.echo(f"\n\nCacheFile Write Error: {e}\nSkipping Writing CacheFile\n\n")
			os.remove(filepath)

		return filepath