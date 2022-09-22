import random
from pathlib import Path

from dag.lib import dtime, comparison

import dag
from dag import this



@dag.mod("test", test_setting = "TEST SETTING")
class Test(dag.DagMod):
	'''TEST DOCSTRING'''
	
	_property = 499


	@dag.cmd()
	def printmsg(self, msg):
		print(str(msg) + "MSG PRINTED")

	@dag.cmd()
	def dagenum(self):
		denum = dag.build_enum("cow", "cat", bird = "SQUA")

		breakpoint()


	@dag.cmd()
	def thisarg(arg = this.dagenum()):
		breakpoint()
		pass
		

	#@dag.cmd(value = "wo" + dag.nab("WOW").lower() == "wowow")
	#@dag.cmd(value = dag.nab(0) or dag.nab(3))
	@dag.cmd(value = dag.nab(1) if dag.nab(0) else dag.nab(3))
	def nabattr(self):
		pass


	@dag.arg("inint", type = int)
	@dag.cmd(value = dag.nab(1) if dag.arg("inint") else dag.nab(3))
	def nablinearg(self, inint):
		pass



	@dag.arg("arg")
	@dag.cmd(value = dag.arg(-1))
	def nabintlinearg(self, arg):
		return



	@dag.cmd()
	def debugmode(self):
		breakpoint(0)


	@dag.cmd()
	def getdescriptor(self):
		return self.descriptor


	@dag.cmd()
	def property(self):
		return self._property


	@dag.arg.Path("file_exists", verify = True)
	@dag.cmd(value = dag.arg("file_exists"))
	def fileexists(self, file_exists):
		return

		
	@dag.cmd(callback = dag.nab.bell)
	def bellafter(self): return


	@dag.cmd(value = this.nargsjoin("test message"))
	def test_mod_nabber(self):
		return
		
		
	@dag.arg.Path("file", force = True)
	@dag.cmd(value = dag.arg("file"))
	def filemake(self, file):
		return

		
	@dag.cmd()
	def closetag(self):
		return "<c bold underline red>hi</c red bold> how are you?</c>"


	@dag.cmd()
	def fnprompt(self):
		return dag.cli.prompt("testprompt", ["aaaa", "bob", "cable", "daddyo", "elephant", "eggplant"])


	@dag.cmd(subcmds = {"subcmd1": this._subcmd1, "2sub": this._subcmd2	})
	def subcmds(self, dummyarg = None):
		return


	@dag.arg("message", nargs = -1, prompt = "Message to output", nargs_join ="+")
	@dag.cmd()
	def nargsjoin(self, message):
		return message


	@dag.arg("message", nargs = -1)
	@dag.cmd()
	def _subcmd1(self, message):
		return f"subcmd1: {message}"


	@dag.arg("message", choices = ["AAA", "BBB", "CCC", "doggy", "elephant", "fightman"])
	@dag.cmd()
	def _subcmd2(self, message):
		return f"subcmd2: {message}"


	@dag.cmd()
	def compare(self):
		coll = self.test_collection()
		lt = coll.compare({"key2" : "123"}, op = "<")
		le = coll.compare({"key2" : "123"}, op = "<=")
		gt = coll.compare({"key2" : "123"}, op = ">")
		ge = coll.compare({"key2" : "123"}, op = ">=")

		breakpoint()
		pass

		
	@dag.arg("arg1", complete = ["aaaaa", "bbbbb", "ccccc"])
	@dag.cmd()
	def complete(self, arg1):
		return

		
	@dag.arg("--arg2", prompt = "The value of arg 2", required = True)
	@dag.arg("arg1", prompt = "The value of arg1")
	@dag.cmd()
	def promptarg(self, arg1, arg2):
		return

		
	@dag.cmd(value = [1,2,3])
	def list_value(self):
		return

		
	@dag.arg("arg2", choices = ["bernie", "meow"])
	@dag.arg("arg1", choices = ["ban", "cat"])
	@dag.cmd()
	def choices(self, arg1, arg2):
		return


	@dag.arg("strtolower", type = str.lower)
	@dag.cmd()
	def lowercase(self, strtolower):
		return strtolower


	@dag.arg("--arg4")
	@dag.arg("--arg3")
	@dag.arg("arg2")
	@dag.arg("arg1")
	@dag.cmd()
	def argslist(self, arg2, arg1, arg5 = "woof", *arg_vargs, arg3 = 3, arg4 = 4, **arg_kwargs):
		return_str = f"arg1: {arg1}, arg2: {arg2}, varargs: {arg_vargs}, arg3: {arg3}, arg4: {arg4}, kwargs: {arg_kwargs}"
		return return_str
		
		
	@dag.arg("arg")
	@dag.cmd()
	def testarg(self, arg):
		print(arg)
		
	@dag.cmd()
	def calltest(self):
		print(self.argslist("fxf", 222, "wyohowhy", "mememe", arg4 = True, arg99 = "BOAT"))
		print(self.lowercase("FFF"))
		print(self.no_vargs())


	def _testlist(self):
		return [1,2,3]

		
	@dag.cmd(value = "no_varargs")
	def no_vargs(self, arg1, arg2, arg3 = 3, arg4 = 4):
		return


	@dag.cmd()
	def getch(self):
		print("Press 'c' to end")
		from Getch import Getch
		getch = Getch()
		getch()


	@dag.cmd(value = dag.nab.os.env("wow"))
	def envval(self):
		return
		
	
	@dag.arg("message", prefix = ".PREFIX.", suffix = ".SUFFIX.", wrap = ".WRAP.")
	@dag.cmd()
	def wrap(self, message = "MESSAGE"):
		return message


	@dag.arg("arg1", password = "Enter password")
	@dag.cmd()
	def password(self, arg1):
		print("PASSWORD ENTERED", arg1)


	@dag.cmd()
	def windowSize(self):
		import shutil
		size = shutil.get_terminal_size()
		print(f"Rows: {size.lines}, Columns: {size.columns}")


	@dag.cmd()
	def fxftest(self):
		self._test("foof", "woof", "fee", dog = "three")
		

	@dag.cmd()
	def _test(self, test = None, *more_args, dog = None):
		breakpoint()
		pass


	@dag.arg("arg1", type = int)
	@dag.cmd()
	def inttest(self, arg1 = 5):
		return f"Arg1 is {arg1}, Arg1+1 is {arg1 + 1}"
	
	
	def animal_sounds_dict(self):
		return {"moo": "cow", "woof": "dog", "oink": "pig", "squeak": "guineapig"}

		
	@dag.arg("animal", complete = this.animal_sounds(dag.arg("sound")))
	@dag.arg("sound", choices = this.animal_sounds_dict().keys())
	@dag.cmd()
	def nabberarg(self, sound, animal):
		return sound, animal

		
	def animal_sounds(self, sound):
		return self.animal_sounds_dict()[sound]

		
	@dag.arg ("--message")
	@dag.arg ("--flag2", flag = "Y")
	@dag.arg("--flag", flag = True)
	@dag.cmd()
	def flag(self, flag = False, flag2 = "z", message = ""):
		print(f"flag value: {flag=} {flag2=}: MESSAGE: {message=}")

		
	@dag.arg("not_dest", prompt = "Say something", dest = "dest")
	@dag.cmd()
	def dest(self, dest):
		print(dest)
		

	@dag.cmd()	
	def responsetest(self):
		from dag.responses import DagResponse
		dd3 = DagResponse({"a":[1,2,{"c":"three"}], "b": 2, "c": "dog"})
		dd4 = DagResponse({"g":[1,2,{"c":"three"}], "bb": 2, "cc": "dog"})
		breakpoint()


	@dag.cmd()
	def responseitem(self):
		from dag.responses import DagResponse
		dd3 = DagResponse({"a":[1,2,{"c":"three"}], "b": 2, "c": "dog"})
		dd4 = DagResponse({"g":[1,2,{"c":"three"}], "bb": 2, "cc": "dog"})
		dd4.g[2].c
		dd5 = DagResponse(None)
		print(dd3 | dd4)
		breakpoint()

		
		
	@dag.cmd()
	def pokemon(self):
		pokemon = dag.get_dagcmd("pokemon")
		return pokemon.pokemon("vulpix")
		
		
	@dag.arg("args", nargs_join = None)
	@dag.cmd()
	def varargs(self, *args):
		breakpoint()
		return
		
		
	@dag.resources(label = "key")
	@dag.collection(cache = False)
	def test_collection(self):
		return [
			{"key": "val1", "key2": "123", "key3": "WOO"},
			{"key": "val2", "key2": "123", "key3": "EAT"},
			{"key": "XXX", "key2": "123", "key3": "GOO"},
			{"key": "True", "key2": "234", "key3": "CAT"},
			{"key": "False", "key2": "2345", "key3": [{1:2}, {3:4}, {5:6}]},
		]


	@test_collection("coll")
	@dag.cmd()
	def nabcollection(self, coll = "val1"):
		breakpoint()
		
	
	@dag.cmd()
	def testcollection(self):
		coll = self.test_collection()
		breakpoint()
		return coll
	
	@test_collection("resource", nargs = -1)
	@dag.cmd()
	def collectionnargs(self, resource):
		return resource
		
	#@dag.arg.Resource("resource", nargs = -1, collection = "test_collection", drill = "key2")
	@dag.arg.Resource("resource", collection = dag.collection(this.test_collection).key2)
	@dag.cmd()
	def collectionattr(self, resource):
		return resource
		
		
	@dag.arg.Resource("resource", nargs = -1, nargs_join = ",", collection = "test_collection", drill = "key3")
	@dag.cmd()
	def collectionnargsjoin(self, resource = None):
		return resource
		
	def _get_collection_for_drill(self):
		return self.test_collection
	
	@dag.arg.Resource("resource", collection = "_get_collection_for_drill()")
	@dag.cmd()	
	def collectiondrill(self, resource):
		return resource
		
		
	@dag.cmd()
	def excludecollection(self):
		coll = self.test_collection()
		print("Removing key: val1")
		breakpoint()
		return coll.exclude(key = "val1")


	@dag.arg("pause")
	@dag.cmd()
	def partition(self, pause = False):
		collection = self.test_collection()
		partition = collection.partition("key2")
		partition.partition("key")
		p = partition.partition("key3")
		
		if pause:
			breakpoint()
			pass
			
		return p
		
		
	@dag.cmd()
	def partitionyield_collections(self):
		p = self.partition()
		for i in p.yield_collections():
			breakpoint()
			pass
	
	@dag.cmd()	
	def partitionyield_subpartitions(self):
		p = self.partition()
		for i in p.yield_subpartitions():
			breakpoint()
			pass
			
		return p
		
	
	@dag.cmd()
	def partitioncollect(self):
		p = self.partition()
		return p.collect()
		
		
	@dag.cmd()
	def partitionfilter(self):
		p = self.partition()
		pfilt = p.filter({"key" : "234"})
		breakpoint()
		return pfilt

	
	@dag.arg("regex")
	@dag.cmd()
	def collectionregex(self, regex = ""):
		return self.test_collection().find_regex(regex)
		
				
	@dag.cmd()
	def collectionprompt(self):
		return self.test_collection().prompt("<c bold>what is thy bidding</c>")
		
		
	@dag.arg("--linekwarg")
	@dag.arg("linearg")
	@dag.cmd(callback = this.after_test.partial(dag.arg("linearg"), linekwarg = "linekwarg intentionally not passed"))
	def after(self, linearg = "DEFAULT_LINEARG", linekwarg = "DEFAULT_KWARG"):
		return f"COMMAND {linearg=} {linekwarg=}"
		
		
	@dag.cmd(display = this._display_after_test)
	def after_test(self, linearg = "", linekwarg = ""):
		return f"AFTER: {linearg=} {linekwarg=}"
		
		
	def _display_after_test(self, response):
		return response + " <c red bold>AFTER FORMATTER</c bold red>"

	
	@dag.arg("no_pipe")	
	@dag.arg("times", type = int)
	@dag.cmd()
	def multiget(self, times = 4, no_pipe = False):
		if no_pipe:
			return dag.get("http://www.dylangilroy.com")

		with dag.tprofiler() as timer:
			response = dag.get(["http://www.dylangilroy.com"]*times)

		breakpoint()

		return response


	@dag.arg("arg1")
	@dag.cmd()
	def multipipe(self, arg1 = ""):
		if arg1:
			return dag.cli.pipe("ls")

		response = dag.cli.pipe(["ls", "pwd"]*4)
		breakpoint()
		return response


	@dag.arg("arg1")
	@dag.cmd()
	def multirun(self, arg1 = ""):
		if arg1:
			return dag.cli.run("ls")

		response = dag.cli.run(["ls", "pwd"]*4)
		breakpoint()
		return response
		
		
	@dag.arg("message", prompt = "Message: ", prompt_prefill = dag.arg("prefill"))
	@dag.arg("prefill", nargs = -1)
	@dag.cmd()
	def promptprefill(self, prefill, message):
		return f"{prefill=} {message=}"


	@dag.hook.test_hook_decorator
	def _test_hook_decorator_fn(self):
		print("TEST HOOK DECORATOR FN")


	@dag.cmd()
	def decoratorhook(self):
		dag.hooks.do("test_hook_decorator")

		
	@dag.cmd()
	def cmdhook(self):
		def _cmdhook_test(response):
			print(f"CALLED BY HOOK: {response=}")

		with dag.hook(testhook = _cmdhook_test):
			dag.hooks.do("testhook", "wow")
			
		return self.nocmdhook()

	def nocmdhook(self):
		dag.hooks.do("testhook", "not wow")
		return "no testhook action"
		
	@dag.cmd()
	def collectionsortlist(self):
		return comparison.sortlist([None, "hi", "bye", 3, -3, 0, True, False, True])
		
	
	@dag.cmd()
	def add_collections(self):
		coll = self.test_collection()
		return coll("true") + coll("xxx")
		
		
	@dag.cmd()
	def sub_collections(self):
		coll = self.test_collection()
		return coll - coll("xxx")
		
		
		
	@dag.cmd()
	def add_resource_to_collection(self):
		coll = self.test_collection()
		return coll("true") + coll("xxx") + coll("val2")
		
		
	@dag.cmd()
	def browser(self):
		with dag.Browser() as browser:
			browser.get("http://www.dylangilroy.com")
			breakpoint()
			pass
		

	@dag.arg("--js", flag = True)
	@dag.cmd()
	def browserheadless(self, js = False):
		with dag.Browser(headless = True, javascript = js) as browser:
			browser.get("http://www.dylangilroy.com")
			breakpoint()
			return browser.page_source
			
			
	def rackspace_partition(self):
		rs = dag.get_dagcmd("rackspace")
		rs.services().partition("endpoints.region")
		
		
	@dag.cmd()
	def futurethreadrequests(self):
		urls = ["http://www.dylangilroy.com"]*40
		import concurrent.futures
		
		def load_url(url, numb):
			print(numb)
			resp = dag.get(url)
			print(f"got {url}")
			return url

		# We can use a with statement to ensure threads are cleaned up promptly
		with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
			# map
			l = list(executor.map(load_url, urls, [i for i in range(1,41)]))

		breakpoint()
		print('Done.')


	@dag.arg("completion", complete = ["hi there"])
	@dag.cmd()
	def spacecomplete(self, completion):
		return


	@dag.arg.File("file", native_path = True)
	@dag.cmd()
	def nativepath(self, file):
		return file


	@dag.arg.File("file")
	@dag.cmd()
	def filename_avoid_overwrite(self, file = None):
		if file is None:
			contents = [Path(".").glob("*")]
			file = contents[0] if contents else Path("TESTFILE.test.file")
			
		return dag.file.filename_avoid_overwrite(file)

	
	@dag.cmd()
	def dagfileopen(self):
		with dag.file.open("test/testfile", inside_dag = True) as file:
			breakpoint()
			pass


	@dag.collection(cache = True)
	def nestedcollection(self):
		coll = self.test_collection()
		coll[0]._data['nested'] = coll[1]
		return coll


	@dag.cmd()
	def reqsession(self):
		with dag.http.session() as sess:
			lp = sess.get("http://www.dylangilroy.com")
			breakpoint()
			pass

	@dag.cmd("alias", "@@@")
	def __aliasX(self):
		return "alias"


	@dag.cmd(tempcache = True)
	def tempcache(self):
		return random.random()


	@dag.arg("--portalurl", flag = True)
	@dag.arg("url")
	@dag.cmd()
	def testlaunch(self, url = "http://www.dylangilroy.com", portalurl = False):
		return dag.launch(url, return_url = portalurl)


	@dag.cmd()
	def cliconfirmer(self):
		return "True" if dag.cli.confirm("Test confirmer") else "False"


	@dag.cmd(confirm = "are you suuuuuure?")
	def confirm(self):
		return "yeah, you're sure"


	@dag.cmd()
	def multiarg(self, arg1, arg2, arg3, arg4, *args):
		return (arg1, arg2, arg3, arg4, args)


	@dag.arg.Msg("textnonraw", raw = False)
	@dag.arg.Msg("textraw", raw = True)
	@dag.cmd()
	def msg(self, textraw, textnonraw = "", *args):
		return f"{textraw} {textnonraw}"


	@dag.cmd()
	def csvresponse(self):
		from dag import responses
		csvtext = "pig,oink\ncow,moo\ncat,meow\nguinea pig,squeak"
		csvtype = responses.Csv("animal", "sound")
		csvdata = csvtype(csvtext)

		animal1 = csvdata[0]

		breakpoint()


	@dag.cmd()
	def csv2(self):
		from dag.responses import CSV
		header_csvtext = "animal,noise\npig,oink\ncow,moo\ncat,meow\nguinea pig,squeak"
		noheader_csvtext = "pig,oink\ncow,moo\ncat,meow\nguinea pig,squeak"

		headers = ["animal", "noise"]

		csv_noargs = CSV()
		csv_args = CSV("animal", "noise")
		csv_dataonly = CSV(header_csvtext)
		csv_oneheader = CSV("header1")
		breakpoint()
		pass


	@dag.arg("text", nargs = 2, complete = ["hee", "haa", "fee", "faa"])
	@dag.cmd()
	def twonargs(self, text):
		print(text)

	@dag.arg("text", nargs = -1, complete = ["hee", "haa", "fee", "faa"])
	@dag.cmd()
	def infnargs(self, text):
		print(text)


	@dag.cmd()
	def multibrowser(self):
		with dag.Browser() as browser:
			browser.get("http://www.dylangilroy.com")
			breakpoint()		

		breakpoint()
		pass


	@dag.cmd()
	def comparisonrecorder(self):
		from dag.lib.comparison import ComparisonRecorder
		cr = ComparisonRecorder()
		b1 = (cr == 2).do_comparison(2)
		b2 = (cr == 2).do_comparison(3)
		breakpoint()
		pass


	@dag.arg("--do_int", flag = True)
	@dag.arg("text")
	@dag.cmd(testbool = 1 <= dag.response < 3)
	def nabcomparison(self, text, do_int = False):
		return int(text) if do_int else text


	@dag.arg("--int", target = "do_int", flag = True)
	@dag.cmd()
	def target(self, do_int = False):
		print(do_int)



	class Wow:
		class Inwow:
			@staticmethod
			def func(*args, **kwargs):
				return args, kwargs
		cow = [Inwow]



	@dag.cmd()
	def this2(self):
		from dag.modules import importing

		with importing():
			nabbed = this.Wow.cow[0].func("arg1", kwarg1 = "val1")

		result = nabbed.nab(self)
		breakpoint()
		pass


	@dag.arg("arg")
	@dag.cmd(value = dag.arg("arg").upper())
	def argnabber(self, arg = "defaultval"):
		breakpoint()
		pass


	@dag.cmd()
	def newdrill(self):
		coll = self.test_collection()
		pcoll = coll.partition(dag.resources.key3[0])
		pass


	@dag.cmd()
	def _testnabkwarg(self, start = dag.nab.now(), end = dag.nab.arg("start") + 1):
		return start, end


	@dag.cmd()
	def nabkwarg(self):
		return self._testnabkwarg()



@dag.mod("testchild")
class ChildTest(Test):

	@dag.cmd()
	def childcmd(self):
		return "WOW"
