import sys, importlib, platform, inspect, ast, traceback, time, toml, os
from typing import Iterator

import dag
from dag.util import dagdebug
from dag.dagcli import alists, completers
from dag.parser import arguments, inputobjects

@dag.cmd(value = dag.nab.generate_password(dag.args.length))
def password_generate(length: int = 24):
	pass


@dag.arg.GreedyWords("text")
@dag.cmd(aka = ">")
def copy(text = "", *, echo: bool = False) -> str | None:
	text = text or dag.instance.controller.last_ic_response.response_no_multicol
	response = dag.copy_text(dag.format(text), echo)
	
	if echo:
		return response


@dag.cmd
def memuse():
	with dag.tprofiler("tm") as tp:
		import tracemalloc
	snapshot = tracemalloc.take_snapshot()
	top_stats = snapshot.statistics('lineno')
	per_stats = snapshot.statistics('lineno').copy()
	per_stats.sort(key = lambda x: x.size / x.count, reverse = True)
	breakpoint()
	pass



@dag.cmd("debugmode")
def debugmode():
	newval = not dagdebug.DEBUG_MODE
	dagdebug.DEBUG_MODE = newval
	return f"Debug Mode: <c b>{newval}</c>"


@dag.cmd
def slice():
	return dag.instance.controller.run_line("test testcollection :::3")


@dag.arg.InCmd("incmd")
@dag.cmd
def which(incmd):
	if callframeinfo := incmd.dagcmd._callframeinfo:
		filepath = callframeinfo.filepath
		lineno = callframeinfo.lineno
	else:
		filepath = inspect.getfile(incmd.dagcmd.fn)
		lineno = inspect.findsource(incmd.dagcmd.fn)[1]

	return f"{filepath}:{lineno}"


@dag.cmd(aka = "len")
def size(input):
	return len(input)


@dag.arg.InCmd("incmd")
@dag.cmd
def clearcache(incmd):
	from dag.cachefiles import cachefiles
	folder, filename = cachefiles.get_folder_filename_from_dagcmd_exctx(incmd)
	
	cachedir = dag.directories.CACHE

	if incmd.is_default_cmd and not incmd.args:
		cachedir /= cachefiles.get_base_folder_from_dagcmd_exctx(incmd)
	else:
		cachedir /= cachefiles.get_folder_from_dagcmd_exctx(incmd)

	if incmd.args:
		cachedir /= cachefiles.get_filename_from_dagcmd_exctx(incmd)

	if not cachedir.exists():
		return f"File not found: <c #F00 bu>{cachedir}</c #F00 bu>"

	status = dag.file.delete(cachedir)

	if status:
		return f"File deleted: <c #F00 bu>{cachedir}</c #F00 bu>"



@dag.arg.Cmd("line", stripquotes = True)
@dag.cmd
def completeline(line = ""):
	with dag.bbtrigger("completetest"):
		comp = line or ""

		with dag.tprofiler() as profiler:
			with dag.ctx("completeline_active"):
				completion = completers.complete_line(comp)

		dag.echo(f"\"{comp}\"\n")
		dag.echo(completion)
		dag.echo(f"COMPLETION TIME: {profiler.diff}ms")



@dag.arg.InCmd("incmd")
@dag.cmd
def baseurl(incmd):
	return incmd.settings.baseurl



@dag.cmd(aka = "l")
def launch(*items):
	# IF no items, get current alist item
	if not items:
		items = ["_"]

	for item in items:
		incmd = dag.ctx.active_incmd

		if item and isinstance(item, str):
			alist = dag.instance.controller.alist

			if item.isdigit():
				item = alist[int(item)]
			elif item == "_":
				item = alist[item]

		dag.launch(item, incmd.directives.browser)


@dag.cmd(store_ic_response = False, aka = "re", store_inputscript = False)
def last():
	if dag.instance.controller.last_inputscript:
		dag.instance.controller.run_inputscript(dag.instance.controller.last_inputscript)
		return

	return "No last incmd"


@dag.arg.Identifier("identifier")
@dag.cmd
def documentation(identifier, launch: bool = False):
	doc = dag.getsettings(identifier).get("doc", f"No documentation found for dagapp: <c bu / {identifier.cmdpath()}>")

	if launch:
		return dag.launch(doc)

	return doc
	


@dag.cmd
def todo():
	dag.get_editor().open_file(dag.ROOT_PATH / "todo.txt")


@dag.cmd
def history():
	dag.get_editor().open_file(dag.directories.STATE / dag.settings.HISTORY_FILE_NAME)


@dag.cmd
def cache():
	path = dag.directories.CACHE
	dag.echo(f"opening <c bu>{path}</c bu> in file explorer")
	dag.get_platform().file_manager(path)


@dag.cmd
def pyversion():
	return platform.python_version()


@dag.cmd
def dpdb():
	dp = dagdebug.DagPdb()
	dp.debug()


@dag.cmd
def last_incmd():
	return dag.instance.controller.last_incmd


@dag.cmd
def inlineparser(text = "test test_collection ##key val1 ##key2 =d"):
	from dag.parser import InputCommandParser, inputscripts
	incmd = inputscripts.generate_from_text(text).get_last_incmd()
	ilp = InputCommandParser.InputCommandParser(incmd)
	ilp.parse_incmd_tokens()


@dag.arg.File("file")	
@dag.cmd
def open(file):
	dag.get_platform().open(f"'{file}'")


@dag.cmd
def keys(dic):
	return [*dic.keys()]


@dag.cmd
def values(dic):
	return [*dic.values()]

_max = dag.cmd("max", fn = max)
_min = dag.cmd("min", fn = min)
_sum = dag.cmd("sum", fn = sum)
_list = dag.cmd("list", fn = list)
reverse = dag.cmd("reverse", fn = lambda x: [*reversed(x)])
pop = dag.cmd("pop", fn = lambda x, idx = -1: x.pop(idx))


@dag.cmd
def sort(item, reverse: bool = False):
	return sorted(item, reverse = reverse)

literal = dag.cmd("literal", fn = lambda x: ast.literal_eval(str(x)))



@dag.cmd
def lynx(item): return dag.launch.LYNX(item)

@dag.cmd
def chrome(item): return dag.launch.CHROME(item)

@dag.cmd
def firefox(item): return dag.launch.FIREFOX(item)


url = dag.cmd("url", fn = dag.launcher.get_item_url)


@dag.arg.Cmd("item")
@dag.cmd(aka = "e")
def editor(item = None):
	filename = item
	lineno = 0

	# If no item is passed in, open editor to source of latest exception
	if item is None:
		tbinfo = traceback.extract_tb(dag.instance.controller.last_exception.__traceback__)[-1]
		lineno = tbinfo.lineno
		filename = tbinfo.filename

	elif isinstance(item, str) and ":" in item:
		filename, lineno = item.split(":")
	elif isinstance(item, dag.Identifier):
		filename, lineno, *_ = item._callframeinfo
	elif isinstance(item, inputobjects.InputIdentifier):
		filename, lineno, *_ = item.identifier._callframeinfo

	editr = dag.get_editor()
	editr.open_file(filename, lineno)

	return f"Opening <c bu/{filename}:{lineno}> in <c bu/{editr.cli_name}>"


@dag.cmd
def callcounts():
	return dag.callcounter.calls


@dag.cmd("type")
def _type(item):
	return type(item)



@dag.cmd
def tinydb():
	with dag.dtprofiler() as tp1:
		import tinydb

	with dag.dtprofiler() as tp2:
		db = tinydb.TinyDB("tinydbTEST.json")
		new_item = {"name": "Book", "quantity": 5}
		db.insert(new_item) 

		items = [
			{"name": "Cake", "quantity": 1},
			{"name": "Candles", "quantity": 10},
			{"name": "Balloons", "quantity": 50}
		]*100
		db.insert_multiple(items)   

	with dag.dtprofiler() as tp3:
		Todo = tinydb.Query()
		balloons = db.search(Todo.name == 'Balloons')

	breakpoint()
	pass
	

@dag.arg.GreedyWords("args")
@dag.cmd("r/==.+/", raw = True)
def set_session_settings(setting, args = ""):
	setting = setting.lstrip("=")
	settingsdagcmd = dag.get_dagcmd("settings").dagcmds['set']

	if not args:
		default = True

		# Strip the "!" so ==!wow correctly reads as "wow"
		session_setting_name = setting.lstrip("!")

		# IF the setting is already a session setting: get its value
		if session_setting_name in dag.settings.session_settings and setting.startswith("!"):
			default = getattr(dag.settings.session_settings, session_setting_name)

		name, value = arguments.DirectiveArg.get_name_and_value(setting, default)
		response = settingsdagcmd(name, value)
	else:
		response = settingsdagcmd(setting, args)

		dag.echo(response)



@dag.cmd("@", "r/@.*/")
def get_py_obj(*args):
	args = list(args)

	if args and args[0].startswith("@"):
		args[0] = args[0][1:]

	from dag.parser import inputscripts
	inscript = inputscripts.generate_from_text(" ".join(args))
	with dag.ctx(completer_active = True, skip_validate_inputarg = True, skip_type_parser = True):
		with dag.ctx(parse_while_valid = True):
			incmd = inscript.get_last_incmd()

	if incmd.dagcmd == dag.defaultapp.default_dagcmd and len(incmd.tokens) == 1:
		return dag.defaultapp.default_dagcmd

	try:
		return incmd.inputobjects[-1].identifier
	except AttributeError:
		return incmd.inputobjects[-1]




#@dag.cmd.Prefixed("@@", regex_priority = 20, raw = True, store_ic_response = False, complete = dag.nab.instance.controller.last_incmd.identifier.settings)
@dag.cmd("r/@@.*/", regex_priority = 20, raw = True, store_ic_response = False)
def get_settings(setting):
	if setting.startswith("@@"):
		setting = setting[2:]

	settings = dag.getsettings(dag.instance.controller.last_incmd)

	if not setting:
		return settings

	return settings.get(setting)


@dag.cmd(r"r/\$.*/")
def get_variable(*args):
	var = args[0].lstrip("$")
	dagvars = dag.instance.controller.vars

	if args[1:]:
		item = args[1]
		dagvars[var] = item
	else:
		item = dagvars.get(var, os.environ.get(var))

	return item


@dag.cmd(r"r/\$\$.*/", regex_priority = 20, raw = True, store_ic_response = False)
def unset_variable(*args):
	var = args[0].lstrip("$")
	dagvars = dag.instance.controller.vars

	if var in dagvars:
		dagvars.pop(var)



@dag.cmd("r/\".*\"/")
def returnstring(text):
	return text


@dag.cmd("str")
def _str(item):
	return str(item)


@dag.cmd("ss")
def open_sublime():
	dag.editors.get_editor("SUBL").open_file()


@dag.cmd
#def tokensplit(text = "a.b(c.d).e[f].\"g.h\".", punct = "."):
def tokensplit(text = "self.teams().", punct = "."):
	from dag.parser.lexer import token_split
	return token_split(text, punct)


@dag.cmd
def lb_tostring():
	from dag.util.attribute_processors import convert_lb_to_string

	lb = dag.r_.wow(1,2,3, "w").get[3] >= dag.r_.mee[3:5]
	strrep = convert_lb_to_string(lb)
	return strrep

@dag.cmd
def schemacoll():
	nhl = dag.get_dagcmd("nhl")
	teams = nhl.teams()
	return teams.schema


@dag.arg("level", choices = ["critical", "debug", "error", "fatal", "info", "notset", "warning"])
@dag.cmd
def log(level = None):
	if not level:
		return dag.log

	dag.log.setLevel(getattr(dag.logging, level.upper()))
	return f"set {dag.log} to {level}"


@dag.cmd(r"r/dag\..*/")
@dag.cmd("dag")
def _dag_cmd(cmdtext = "", arg = dag.UnfilledArg):
	if not cmdtext:
		return dag

	_, *args = cmdtext.split(".")

	try:
		item = dag.drill(dag, ".".join(args)) 

		if arg is not dag.UnfilledArg:
			return item(arg)
	except:
		return f"<c bu /\"{'.'.join(args)}\"> not found in <c bu / \"dag\">"

	return item


@dag.cmd
def sleep(*msec: list[int]):
	msec = msec or [100]
	
	for ms in msec:
		dag.echo(f"sleeping <c b u/{ms}> milliseconds")
		time.sleep(ms/1000)


@dag.cmd.TOML
def pyproject():
	return dag.file.read(dag.definitions.ROOT_PATH / "pyproject.toml")


pyproject2 = dag.cmd("pyproject2").TOML.READ(dag.definitions.ROOT_PATH / "pyproject.toml")


@dag.cmd
def uuidcheck(input):
	import uuid

	try:
		return uuid.UUID(input)
	except ValueError:
		return False



format_test = dag.app("formattest")

@format_test.cmd
def yaml():
	yamldata = """\
name: John Smith
age: 30
gender: male
address:
  street: 123 Main Street
  city: Anytown
  state: California
  zip: 12345
email: john.smith@example.com
phone: 
  - type: home
    number: 555-1234
  - type: work
    number: 555-5678
"""

	yamlresponse = dag.YAML.parse(yamldata)

	return yamlresponse


@format_test.cmd
def toml():
	data = """\
# This is a TOML document

title = "TOML Example"

[owner]
name = "Tom Preston-Werner"
dob = 1979-05-27T07:32:00-08:00

[database]
enabled = true
ports = [ 8000, 8001, 8002 ]
data = [ ["delta", "phi"], [3.14] ]
temp_targets = { cpu = 79.5, case = 72.0 }

[servers]

[servers.alpha]
ip = "10.0.0.1"
role = "frontend"

[servers.beta]
ip = "10.0.0.2"
role = "backend"
"""

	response = dag.TOML.parse(data)

	return response


@format_test.cmd
def csv():
	data = """\
Name,Age,City
John Doe,25,New York
Jane Smith,30,San Francisco
Mark Johnson,35,Chicago
"""
	return dag.CSV.parse(data)


@dag.cmd
def raw(item):
	return item


@dag.cmd("dir")
def _dir(item):
	return dir(item)


@dag.cmd(r"r/\-.*/", raw = True)
def displayargs(*args):
	argstring = " ".join(args)
	lastincmd = dag.instance.controller.last_incmd

	from dag.parser.raw_arg_parser import RawArgParser
	rawparser = RawArgParser(lastincmd)
	rawparser.proctokens = list(args)

	with dag.bbtrigger("displayargs"):
		parsed = rawparser.parse_args()

	breakpoint()
	pass



#incmd = dag.cmd("incmd").ARGS(incmd = dag.arg[dag.parser.InputCommand]).RETURNS(dag.args.incmd)
#incmd = dag.cmd("incmd") | ARGS(incmd = dag.arg[dag.parser.InputCommand]) | RETURNS(dag.args.incmd)


@dag.arg.InCmd("incmd")
@dag.cmd
def incmd(incmd):
	return incmd



@dag.arg.Path("files")
@dag.cmd("<")
def _print_file(*files):
	response = []

	for file in files:
		response.append(dag.file.read(file) + "\n")

	return dag.unlistify(response)



@dag.arg.Path("files")
@dag.cmd("<<")
def _iter_file_lines(*files):
	response = []

	for file in files:
		response += dag.file.readlines(file)

	return response



@dag.cmd("iter")
def _iter(seq) -> Iterator:
	yield from dag.listify(seq)


@dag.cmd("next")
def _next(generator: Iterator) -> Iterator:
	return next(generator)


@dag.cmd("get")
def _get(url):
	return dag.get(url)

@dag.cmd
def html(content):return dag.HTML.parse(content)

@dag.cmd
def xml(content):return dag.XML.parse(content)

@dag.cmd
def json(content):return dag.JSON.parse(content)

@dag.cmd
def yaml(content):return dag.YAML.parse(content)


@dag.arg.Directory("directory")
@dag.cmd
def imgs(directory = ".", *exts):
		return dag.filetools.listdir(directory, dirs = False, filetypes = dag.images.FILETYPES + list(exts))


@dag.cmd
def sort_values(dic):
	breakpoint()
	return dag.sort_by_values(dic)


@dag.cmd
def dirlist(directory: dag.Path = dag.nab.Path.cwd()):
	return dag.filetools.listdir(directory)


@dag.cmd
def path(pathstr):
	return dag.Path(pathstr)