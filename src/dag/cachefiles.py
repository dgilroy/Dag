import dag, pathlib

from dag.util import mixins, persistencefile

class DagCmdExCtxPersistenceFile(persistencefile.PersistenceFile):

	def generate_filename_from_dagcmd_parsed(self, dagcmd, parsed):
		filename = ""

		if parsed:
			argnames = sorted(parsed.keys())

			for argname in argnames:
				dagarg = dagcmd.dagargs.get(argname)
				if not dagarg or dagarg.settings and not dagarg.settings.cacheable:
					continue

				parsedvalue = parsed[argname]

				if not parsedvalue:
					continue 

				try: # Done this way because DTimes can't be made into CacheFileNamer's
					parsedvalue = parsedvalue._dag_cachefile_name()
				except AttributeError:
					pass

				filename += f"--{argname}-{parsedvalue}"

		return self.format_filename_chars(f"{filename}.{persistencefile.ext}")


	def generate_filename_from_dagcmd_exctx(self, exctx):
		return self.generate_filename_from_dagcmd_parsed(exctx.dagcmd, exctx.parsed) 


	def get_base_folder_from_dagcmd_exctx(self, exctx):
		return "/".join(exctx.dagcmd.parentnames)

	def get_folder_from_dagcmd(self, dagcmd):
		return dagcmd.cmdpath("/").lower()


	def get_folder_from_dagcmd_exctx(self, exctx):
		return self.get_folder_from_dagcmd(exctx.dagcmd)


	def get_filename_from_dagcmd_exctx(self, exctx):
		return self.generate_filename_from_dagcmd_exctx(exctx).strip("/")


	def get_folder_filename_from_dagcmd_exctx(self, exctx):
		folder = self.get_folder_from_dagcmd_exctx(exctx)
		filename = self.get_filename_from_dagcmd_exctx(exctx)

		return folder, filename


	def exists_from_dagcmd_exctx(self, exctx):
		folder, filename = self.get_folder_filename_from_dagcmd_exctx(exctx)
		return super().exists(folder, filename)


	def read_from_dagcmd_exctx(self, exctx):
		folder, filename = self.get_folder_filename_from_dagcmd_exctx(exctx)
		return super().read(folder, filename)


	def write_from_dagcmd_exctx(self, response, exctx):
		folder, filename = self.get_folder_filename_from_dagcmd_exctx(exctx)
		return super().write(response, folder, filename)


cachefiles = DagCmdExCtxPersistenceFile(dag.directories.CACHE)




class DBCache:
	def __init__(self, rootdir = dag.directories.CACHE):
		self.rootdir = pathlib.Path(rootdir)

	def get_db_and_query_from_exctx(self, exctx):
		pass

	def entry_exists_from_exctx(self, exctx):
		pass

	def read_response_from_exctx(self, exctx):
		pass

	def write_response_from_exctx(self, response, exctx):
		pass


dbcache = DBCache()



'''
import sqlite3
import json

def create_table(cursor, data, table_name=''):
    if isinstance(data, dict):
        # If the data is a dictionary, create a table with columns for each key
        columns = ', '.join([f'{key} TEXT' for key in data.keys()])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({columns})')

        # Recursively process the dictionary values
        for key, value in data.items():
            create_table(cursor, value, f'{table_name}_{key}')

    elif isinstance(data, list):
        # If the data is a list, create a separate table for each element
        for i, item in enumerate(data):
            create_table(cursor, item, f'{table_name}_{i}')

    else:
        # If the data is a simple value, insert it into the current table
        cursor.execute(f'INSERT INTO {table_name} VALUES (?)', (str(data),))

# Read the JSON data from a file or an API response
json_data = """
{
  "person": {
    "name": "John Doe",
    "age": 30,
    "address": {
      "street": "123 Main St",
      "city": "New York"
    },
    "pets": [
      "dog",
      "cat"
    ]
  },
  "company": {
    "name": "ABC Inc",
    "employees": [
      {
        "name": "Alice",
        "age": 25
      },
      {
        "name": "Bob",
        "age": 35
      }
    ]
  }
}
"""

# Convert JSON to Python object
data = json.loads(json_data)

# Connect to the SQLite database
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Create tables and insert data recursively
create_table(cursor, data)

# Commit the changes and close the connection
conn.commit()
conn.close()
'''