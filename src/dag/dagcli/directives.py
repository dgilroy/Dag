from functools import partial
from dag.lib import browsers


directives = {}
directive_prefix = "=="

short_directives = {}
short_directive_prefix = "="


class directive:
	def __init__(self, short_name, long_name):
		self.short_name = short_name
		self.long_name = long_name

	def __call__(self, parent):
		directives[directive_prefix + self.long_name] = parent
		short_directives[self.short_name] = parent
		return parent



# DAGCMD: =u, =h, =r, =k, =s, =p, =o, =b, =c, =e, =l, =m, =t, =x
# DAGMOD: =d documentation, =b baseurl, =h help, =e editor, =U update_collections
# BOTH?: =e editor, =h help
		

## DIRECTIVES:
@directive("u", "update_cache")
def update_cache(incmd):
	incmd.directives.update_dagcmd_cache = True
	

@directive("r", "raw")
def raw(incmd):
	incmd.directives.noformat = True
	
	
@directive("h", "help")
def man(incmd):
	incmd.directives.help_active = True
	
	
#@directive("b", "baseurl")
def baseurl(incmd):
	incmd.directives.baseurl = True


#@directive("k", "keys")
def keys(incmd):
	incmd.directives.keys_active = True
	

#@directive("s", "size")
def size(incmd):
	incmd.directives.size_active = True
	
	
#@directive("d", "documentation")
def documentation(incmd):
	incmd.directives.api_documentation_active = True


@directive("p", "portalurl")	
def portalurl(incmd):
	incmd.directives.portalurl = True


@directive("l", "launch")
def launch(incmd):
	incmd.directives.do_launch = True
	incmd.directives.browser = browsers.DEFAULT


@directive("t", "tempcache")
def tempcache(incmd):
	incmd.directives.tempcache = True


#@directive("c", "choices")
def choices(incmd):
	incmd.directives.choices_active = True
	

@directive("U", "update_all_caches")
def update_all_caches(incmd):
	incmd.directives.update_dagcmd_cache = True
	incmd.directives.update_all_caches = True


@directive("o", "chrome")
def open_with_chrome(incmd):
	incmd.directives.do_launch = True
	incmd.directives.browser = browsers.DEFAULT
	incmd.directives.chrome = True
	incmd.directives.browser = browsers.CHROME


@directive("x", "lynx")
def open_with_lynx(incmd):
	incmd.directives.do_launch = True
	incmd.directives.browser = browsers.DEFAULT
	incmd.directives.lynx = True
	incmd.directives.browser = browsers.LYNX


@directive("a", "async")
def run_async(incmd):
	incmd.directives.runasync = True

@directive("i", "time")
def time_execution(incmd):
	incmd.directives.time_execution = True

@directive("g", "executor")
def time_execution(incmd):
	incmd.directives.executor = True


	

#add_directive("async", "a", run_async)
#add_directive("baseurl", "b", baseurl)
#add_directive("choices", "c", choices)
#add_directive("documentation", "d", documentation)
#add_directive("debug", "D", debug)
#add_directive("editor", "e", documentation)
#add_directive("force", "f", force)??????????
#add_directive("help", "h", man)
#add_directive("json", "j", json)??????????
#add_directive("keys", "k", keys)
#add_directive("launch", "l", launch)
#add_directive("man", "m", man)
#add_directive("chrome", "o", open_with_chrome)
#add_directive("portalurl", "p", portalurl)
#add_directive("quiet", "q", quiet)
#add_directive("raw", "r", raw)
#add_directive("size", "s", size)
#add_directive("tempcache", "t", tempcache)
#add_directive("update_cache", "u", update_cache)
#add_directive("update_all_caches", "U", update_all_caches)
#add_directive("lynx", "x", open_with_lynx)
#add_directive("yes", "y", yes)????????????