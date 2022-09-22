import gzip, dill, bz2, os

import dag

ext = dag.config.CACHEFILE_EXT + ".gz"

	
class PersistenceFile:
	def __init__(self, file_root_dir):
		self.file_root_dir = file_root_dir.strip("/")


	def format_filename_chars(self, name):
		return name.replace("://", ".").replace("?", ".").replace("/", "-").replace(" ", "%20").replace("&", ".").replace("\\", "")


	def process_filepath(self, folder, filename):
		folder = folder.lstrip("/").removeprefix(self.file_root_dir).strip("/")
		filename = self.format_filename_chars(filename.strip("/")).removesuffix(ext) + ext
		return f"{self.file_root_dir}/{folder}/{filename}"


	def exists(self, folder, filename):
		filepath = self.process_filepath(folder, filename) 

		return dag.file.file_exists(filepath, inside_dag = True)


	def read(self, folder, filename):
		filepath = self.process_filepath(folder, filename) 

		with dag.file.open_in_dag(filepath, "rb", opener = gzip.open) as f:
			return dill.load(f)


	def write(self, text, folder, filename):
		filepath = self.process_filepath(folder, filename) 
		filepath = dag.file.force_inside_dag(filepath)
		
		try:
			with dag.file.open_in_dag(filepath, "wb", opener = gzip.open) as f:
				dill.dump(text, f)

		except TypeError as e:
			print(f"\n\nCacheFile Write Error: {e}\nSkipping Writing CacheFile\n\n")
			os.remove(filepath)