from .shortcuts import *
from .colors import *
from .string_crumbler import crumble, StringCutter, WordIteratortex

from .rest import *
from .db import *



import logging
from core._logging import LoggingHandler
logging.setLoggerClass(LoggingHandler)