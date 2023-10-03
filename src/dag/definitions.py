import os, pathlib

CODE_PATH = pathlib.Path(os.path.realpath(os.path.dirname(__file__)))
SRC_PATH = CODE_PATH.parent
ROOT_PATH = SRC_PATH.parent