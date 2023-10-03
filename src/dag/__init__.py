import inspect, typing, logging, sys, time, contextlib
from dotenv import load_dotenv
from dataclasses import dataclass
from collections.abc import Sequence


dtresults = {}

@contextlib.contextmanager
def dtprofiler(name, *args, **kwargs):
	from dag.lib.profilers import TimeProfiler
	with TimeProfiler(name, *args, **kwargs) as tp:
		yield tp
	dtresults.setdefault(name, tp.diff)



with dtprofiler("Total Dag import"):
	def exit(code = 0):
		return sys.exit(code)


	is_init = False
	oninit_fns = []
	def oninit(fn):
		if is_init:
			fn()
		else:
			oninit_fns.append(fn)



	instance = None
	is_instance_running = False # Initialized when Instance intialized

	argspec = inspect.getfullargspec


	@dataclass
	class Error:
		message: str


	# Used to indicate whether a value (possibly None) has been passed into an optional argument
	class UnfilledArg: pass


	with dtprofiler("Total Dag import (definitions)"):
		from .definitions import CODE_PATH as CODE_PATH
		from .definitions import SRC_PATH as SRC_PATH
		from .definitions import ROOT_PATH as ROOT_PATH

	# Loads dotenv info into environ
	with dtprofiler("Total Dag import (load dotenv)"):
		load_dotenv(dotenv_path = ROOT_PATH / ".env")

	with dtprofiler("Total Dag import (load config)"):
		from . import config as config

	with dtprofiler("Total Dag import (lib)"):
		from .lib.profilers import TimeProfiler as tprofiler
		from .lib.listtools import is_nonstring_sequence, listify, unlistify, nonefilter, flattenlist
		from .lib import ostools as os
		from .lib import filetools
		from .lib import strtools
		from .lib.strtools import evaluate_name
		from .lib import ftp
		from .lib import dot
		from .lib.ostools import EnvGetter
		env = EnvGetter()
		from .lib.ostools import OptionalEnvGetter
		getenv = OptionalEnvGetter()
		from .lib.dot import DotDict
		from .lib.dot import DotAccess
		from .lib.dot import DotProxy
		from .lib import dtime
		from .lib import colors
		Color = colors.Color
		from .lib.dtime import DTime
		from .lib.dtime import DTime as date
		from .lib.dtime import current_milli_time
		from .lib.dtime import current_micro_time
		now = DTime.now
		from .lib.encoding import B64 as b64
		from .lib.enumbuilder import build_enum
		from .lib.enumbuilder import EnumBuilder
		enum = EnumBuilder()
		from .lib.frameinfo import callframeinfo
		from .lib.platforms import get_platform
		from .lib.platforms import get_terminal
		from .lib import words as words
		from .lib.registereditems import RegisteredItems as ItemRegistry
		from .lib import browsers as browsers
		from .lib.passwords import generate_password
		from .lib.profilers import callcounter
		from .lib import dummies
		from .lib import ctxmanagers
		from .lib import asttools
		from .lib import tracetools
		from .lib.dagpath import DagPath as Path

	with dtprofiler("Total Dag import (ctx)"):
		ctx = ctxmanagers.Context()
		ctx.directives = dot.DotDict()

	with dtprofiler("Total Dag import (directories)"):
		from . import directories as directories
		STATEDIR = directories.STATE
		DATADIR = directories.DATA
		CACHEDIR = directories.CACHE
		CONFIGDIR = directories.CONFIG
		PATHINFO_PATH = DATADIR / "pathinfo"

	with dtprofiler("Total Dag import (exceptions)"):
		from . import settings as settings
		from .exceptions import catch
		from .exceptions import passexc
		from .exceptions import DagError
		from .exceptions import DagContinueLoopException as ContinueLoopException
		from .exceptions import DagBreakLoopException as BreakLoopException
		from .exceptions import DagReloadException
		from .exceptions import print_traceback
		from .exceptions import postmortem

	with dtprofiler("Total Dag import (utils)"):
		from .util.ctags import format as format
		from .logger import logger as log

		from .util import ctags
		from .util.ctags import echo
		from .util.nabbers import Nabber
		from .util import dagdebug as debug
		bbtrigger = debug.set_trigger
		bb = debug.DebugTriggerer()
		from .util import dagauth as auth
		from .util import launcher
		from .util.ctags import rawformat
		from .util.drill import drill
		from .util.hooks import HooksAPI
		hooks = HooksAPI()
		hook = hooks.hookbuilder
		from .util import nabbers
		from .util.nabbers import nab
		from .util.nabbers import response
		from .util.nabbers import args
		from .util.nabbers import nab_if_nabber
		from .util.nabbers import resources
		from .util.dagbrowser import DagBrowser as Browser
		from .util.launcher import Launcher
		launch = Launcher()
		from .util.launcher import get_browser
		from .util.textcopy import copy_text
		from .util import editors
		from .util.editors import get_editor
		from .util.typingtools import get_annotations
		from .util.typingtools import get_annotated_metadata
		from .util.typingtools import get_annotated_class
		from .util.typingtools import parse_annotated
		from .util.styleformatter import DagStyleFormatter as formatter
		from .util import mixins
		from .util import argspectools
		from .util.lambdabuilders import LambdaBuilder
		from .util import rslashes
		from .util.searchers import Searcher
		from .util.daguuid import DagUUID
		from .util.daguuid import uuid4

	with dtprofiler("import_dag (after utils)"):
		with dtprofiler("import_dag1"):
			from .responses import is_mapping
			from .responses import is_sequence
			from .responses import is_none
			from .responses import DagResponse as Response
			from .responses import clean_name as slugify

		with dtprofiler("import_dag2"):
			from .io import dagio as dagio
			from .io.dagio import iomethod as iomethod
			from .io import files as _files
			FileManager = _files.FileManager
			file = FileManager()

		with dtprofiler("import_dag (http)"):
			from .io import daghttp as http
			get = http.get
			post = http.post
			put = http.put
			delete = http.delete
			head = http.head
			Pager = http.Pager
			postencode = http.postencode
			urlencode = http.urlencode
			inputfill_param = http.inputfill_param


		with dtprofiler("import_dag (io.cli)"):
			from .io import cli as cli
			prompt = cli.prompt

		with dtprofiler("import_dag (io.images)"):
			from .io import images as images
			from .io.images import DagImg as img
			Img = img

		with dtprofiler("import_dag (response parsers)"):
			from .responses import CsvParser
			from .responses import HtmlParser
			from .responses import JsonParser
			from .responses import XmlParser
			from .responses import YamlParser

			from .responses import registered_parsers as _registered_parsers

			# Sets CSV, HTML, JSON, XML, YAML, and any other registered parsers
			for parsername, parser in _registered_parsers.items():
				globals()[parsername] = parser # globals() only affects the module

		with dtprofiler("import_dag (collections/resources)"):
			from .dagcollections.collection import Collection as Collection
			from .dagcollections.resource import Resource as Resource
			from .dagcollections.resource import ResourcesLambdaBuilder as ResourcesLambdaBuilder
			r_ = ResourcesLambdaBuilder()

		with dtprofiler("import_dag6b"):
			from .decorators import arg as arg
		with dtprofiler("import_dag6c"):
			from .dagargs import ArgBuilder as ArgBuilder
		with dtprofiler("import_dag6d"):
			from .dagargs import DagArg as DagArg

			"""
			# Imports all base-directory-level files into module
			from os.path import dirname as _dirname
			from os.path import basename as _basename
			from os.path import isfile as _isfile
			from os.path import join as _join
			import glob as _glob
			__all__ = [ _basename(f)[:-3] for f in _glob.glob(_join(_dirname(__file__), "*.py")) if _isfile(f) and not f.endswith('__init__.py')]
			"""

		with dtprofiler("import_dag7"):
			def __getattr__(attr):
				match attr:
					case "cmd":
						cfi = callframeinfo(inspect.currentframe())
						cmdbuilder = defaultapp.cmd
						cmdbuilder.callframeinfo = cfi
						return cmdbuilder
					case "collection":
						cfi = callframeinfo(inspect.currentframe())
						collectionbuilder =  defaultapp.collection
						collectionbuilder.callframeinfo = cfi
						return collectionbuilder
					case "arg2":
						return ArgBuilder()

				raise AttributeError(f"Attribute {attr} not found in dag.__init__")

		with dtprofiler("import_dag8"):
			from .applications import AppBuilder as AppBuilder
			from .applications import DagApp

			from .dagcmds import DagCmd

			from .defaultdagcmd import defaultapp
			from .defaultdagcmd import get_dagcmd

			app = AppBuilder(defaultapp)

		with dtprofiler("import_dag9"):
			from .identifiers import Identifier
			from . import appmanager

			cmdtemplate = defaultapp.cmdtemplate
			ctx.active_dagcmd = defaultapp





		def getsettings(item):
			if isinstance(item, mixins.DagSettings):
				return item._dag_get_settings()

			return getattr(item, "settings", nabbers.NabbableSettings())



	def dirmerge(*items):
		return list(set(items))

	with dtprofiler("Total dag import (Context Setter)"):
		class ContextSetter:
			def __getattr__(self, attr):
				return ctxmanagers.CtxSetter(ctx, attr)

		setctx = ContextSetter()


	with dtprofiler("Total dag import (oninit fns)"):
		for fn in oninit_fns:
			fn()
		is_init = True




	# Sort the dictionary by keys
	def sort_by_keys(dic):
		return dict(sorted(dic.items()))


	# Sort the dictionary by values
	def sort_by_values(dic):
		return dict(sorted(dic.items(), key=lambda item: item[1]))



"""
@iomethod(name = "launch", group = "launcher")
def do_launch(item, browser, return_url = False, **kwargs):
	return launch(item, browser, return_url)
"""
