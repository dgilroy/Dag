import sys

is_instance_running = False # Initialized when Instance intialized

from .definitions import ROOT_DIR as ROOT_DIR
from .definitions import ROOT_PATH as ROOT_PATH

from . import config as config

from .lib import ostools as os
from .lib import dot as dot
from .lib.dot import DotDict as DotDict
from .lib.dot import DotAccess as DotAccess
from .lib.ostools import EnvGetter as env
from .lib import  dtime as dtime
from .lib.dtime import DTime as DTime
from .lib.dtime import DTime as date
from .lib.dtime import current_milli_time as current_milli_time
now = DTime.now
from .lib.encoding import B64 as b64
from .lib.enumbuilder import build_enum as build_enum
from .lib.platforms import get_platform as get_platform
from .lib.platforms import get_terminal as get_terminal
from .lib import words as words

from .util import dagauth as auth
from .util import launcher as launcher
from .util.ctags import format as format
from .util.ctags import echo as echo
from .util.drill import drill as drill
from .util.hooks import instance_hooks as hooks
hook = hooks.hookbuilder
from .util.nabbers import Nabber as Nabber
from .util.nabbers import nab as nab
from .util.nabbers import response as response
from .util.nabbers import this as this
from .util.nabbers import nab_if_nabber as nab_if_nabber
from .util.dagbrowser import DagBrowser as Browser
from .util.launcher import launch as launch
from .util.textcopy import copy_text as copy_text

from .responses import DagResponse as Response

from .io.dagio import iomethod as iomethod
from .io import files as file

from .io import daghttp as http
get = http.get
post = http.post
put = http.put
delete = http.delete
head = http.head

from .io import cli as cli
from .io.images import DagImg as img


from .ctx import instance_ctx as ctx
from .profilers import TimeProfiler as tprofiler

from .decorators import arg as arg
from .decorators import cmd as cmd
from .decorators import collection as collection
from .decorators import collection as coll
from .decorators import dagmod as dagmod
from .decorators import dagmod as mod
from .decorators import resources as resources

from .responses import CsvParser as CsvParser
from .responses import HtmlParser as HtmlParser
from .responses import JsonParser as JsonParser
from .responses import XmlParser as XmlParser
from .responses import YamlParser as YamlParser

from .responses import registered_parsers as _registered_parsers

# Sets CSV, HTML, JSON, XML, YAML, and any other registered parsers
for parsername, parser in _registered_parsers.items():
	globals()[parsername] = parser # globals() only affects the module




from .dagcollections.collection import Collection as Collection
from .dagcollections.resource import Resource as Resource

from .exceptions import catch as catch
from .exceptions import DagError as DagError

# Imports all base-directory-level files into module
from os.path import dirname as _dirname
from os.path import basename as _basename
from os.path import isfile as _isfile
from os.path import join as _join
import glob as _glob
__all__ = [ _basename(f)[:-3] for f in _glob.glob(_join(_dirname(__file__), "*.py")) if _isfile(f) and not f.endswith('__init__.py')]


dag_module = sys.modules[__name__]

class DagClass:
	def __getattr__(self, attr):
		def is_decorator(attr):
			return attr in ["cmd", "arg", "dagmod", "mod", "collection", "coll", "resources"]

		if is_decorator(attr):
			ctx.DAG_DECORATOR_ACTIVE = True # Will be reset to False when decorator has __set_name__() called

		#return getattr(process_module(dag_module), attr)
		return getattr(dag_module, attr)


	def __dir__(self):
		return list(set(object.__dir__(self) + dir(dag_module)))



sys.modules[__name__] = DagClass()


from .dagmods import DagMod as DagMod
from .defaultdagcmd import default_dagcmd_instance as default_dagcmd
from .defaultdagcmd import get_dagcmd as get_dagcmd
from .defaultdagcmd import load_dagcmd as load_dagcmd

ctx.active_dagcmd = default_dagcmd