import logging
from logging.handlers import RotatingFileHandler

from dag import STATEDIR, format

# Get logger
logger = logging.getLogger(str(STATEDIR / "log"))
# Set logging level to the logger
logger.setLevel(logging.DEBUG) # <-- THIS!


# Create CLI handler
formatter = logging.Formatter(format('<c #088 bg-#11 bu / %(levelname)s:> %(message)s\n'))
c_handler = logging.StreamHandler()
c_handler.setFormatter(formatter)
logger.addHandler(c_handler)


# File handler
file_handler = RotatingFileHandler(str(STATEDIR / "log"), maxBytes=1000000, backupCount=5)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)