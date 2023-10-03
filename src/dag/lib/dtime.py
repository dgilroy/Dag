from __future__ import annotations

import datetime, time, re, operator, calendar
from datetime import timezone, timedelta
from typing import Optional, Union, NoReturn


# A function that returns the current time in milliseconds as an int (as opposed to milliseconds being a decimal)
current_milli_time = lambda: int(round(time.time() * 1000))
current_micro_time = lambda: int(round(time.time() * 1000000))


def humanize_milliseconds(milliseconds: int, ndigits: int = 3) -> str:
	"""
	Turns number of milliseconds into readable "ms" or "s" for seconds

	:param milliseconds: The number of milliseconds to humanize
	:param ndigits: The number of digits to round the milliseconds to
	:returns: The humanized string, (e.g. 1000 -> "1s")
	"""
	suffix = "ms"

	if milliseconds > 1000:
		suffix = "s"
		milliseconds /= 1000

	time = round(milliseconds, ndigits)

	return f"{time}{suffix}"


def humanize_microseconds(microseconds: int, ndigits: int = 3) -> str:
	"""
	Turns the number of microseconds into a readable amount of milliseconds or seconds

	:param microseconds: The number of microseconds to humanize
	:param ndigits: The number of digits to round the result to
	:returns: The humanized string (e.g. 1000 -. "1ms")
	"""
	return humanize_milliseconds(microseconds / 1000, ndigits = 3)



class DateTimeParser:
	"""
	A class holding various methods that help parse DateTime strings
	"""

	# Named values are words that mean different dates or times
	named_values = {}

	# Delta vals are letter markers that, if preceeded by an int n, indicate n timeunits,
	# Where the time unit is associated to a certain letter (e.g. Seconds to "s")
	deltavals = {}

	
	@classmethod
	def parse(cls, text: str, format: str | None = None) -> DTime:
		"""
		This can read various texts and interpret them as DTimes

		If a format is given, the DTime will have that as its format string

		In particular, it can translate:
			(1) Any named clas-provied named value (yesterday, noon, etc)
			(2) Any delta value (9y, 6s, etc)
			(3) Any value that DTime itself can interpret

		:param text: The text to parse (e.g. "today")
		:param format: (optional) The format string for the DTime instance (e.g. "%Y" for year)
		:return: The parsed text as a DTime, given that it can be parsed
		"""

		# If string is a named time: Return its associated value
		if text in cls.named_values:
			time = cls.named_values[text]()
			
			
		# If using delta string: Return the associated delta datetime
		elif cls.is_text_deltastr(text):
			delta_op = operator.neg

			if text[0] == "+":
				delta_op = lambda x: x

			deltavals = {k: delta_op(v) for k,v in cls.process_deltastr(text).items()}

			time = DTime().delta(**deltavals)
		# Else, no namedval or deltastr provided: Have DTime interpret input
		else:
			time = DTime(text)

		if format:
			time.formatstr = format

		return time


	@staticmethod
	def process_deltaval(matcher: str, text: str) -> int:
		"""
		Scans given text for an integer number preceding the given matcher string.

		This is used so that a shorthand 92m8d can be passed into the parser to mean 92 months and 8 days

		So, with "w" as a matcher: "92w" => 92

		If no match is found: return 0

		Note, any deltastr "$" will match the end of the string, making it a default.
		So, if "$" is a deltaval of "days": "9" => {"days": 9}


		:param matcher: The string used to delineate the end of a matched value
		:param text: The text to search
		:return: The integer-value of the deltaval
		"""

		try:
			return int(re.search(fr"(\d+){matcher}", text).group(1))
		except AttributeError:
			return 0


	@classmethod
	def get_deltamatchers(cls) -> str:
		"""
		Returns all of the class's deltamatchers as a comma-separated list. Used by regex

		So: {...: ["a", "b"], ...:["c", "x"]} => "a,b,c,x"

		Note: Order isn't guaranteed

		:returns: A comma-separated string list of all deltamatchers
		"""

		results = []

		for deltaname, deltamatchers in cls.deltavals.items():
			results += [dm for dm in deltamatchers if dm.isalpha()]

		return ",".join(results)



	@classmethod
	def process_deltastr(cls, text: str) -> dict[str, int]:
		"""
		Given a potential deltastring, process the string and return a dict of the processed values (useful for kwargs)

		So: "9w" => {"week": 9}

		If a deltaval has multiple deltastrs in the text, only the first one is used
		So: "9w6w" => {"week": 9}

		:param text: The text to analyze
		:returns: A dict of processed deltas
		"""

		results = {}

		for deltaname, deltavals in cls.deltavals.items():
			for deltaval in deltavals:
				result = cls.process_deltaval(deltaval, text)

				if result:
					results[deltaname] = result
					break

		return results


	@classmethod
	def is_text_deltastr(cls, text: str) -> bool:
		"""
		Checks whether a given text is a deltastr

		:param text: The text to analyze
		:returns: A flag indicating whether the text is a valid deltastr
		"""

		if deltastrs := cls.get_deltamatchers():
			return re.match(fr"^(\-|\+)(\d+[{deltastrs}]?)+$", text)

		return False




class TimeParser(DateTimeParser):
	"""
	A utility class used to parse text into a time-oriented DTime
	"""

	named_values = {
					'now': lambda: DTime(),
					'noon': lambda: DTime().noon,
					'midnight': lambda: DTime().midnight,
				}


	deltavals = {
				'hours': ['h', '$'],
				'minutes': ['m'],
				'seconds': ['s'],
	}


	

class DateParser(DateTimeParser):
	"""
	A utility class used to parse text into a date-oriented DTime
	"""

	named_values = {
				'today': lambda: DTime.today(),
				'yesterday': lambda: DTime.today() - 1,
				'tomorrow': lambda: DTime.today() + 1,
				'halloween': lambda: DTime(month = 10, day = 31),
				'christmas': lambda: DTime(month = 12, day = 25),
				'newyears': lambda: DTime(month = 1, day = 1),
	}


	deltavals = {
				'years': ['y'],
				'months': ['m'],
				'weeks': ['w'],
				'days': ['d', '$'],
	}




class Parser:
	"""
	A method class that points to date/time parsers
	"""

	@staticmethod
	def date(text: str) -> DTime:
		"""
		Parse the given date text into a DTime
		"""

		return DateParser.parse(text)


	@staticmethod
	def time(text: str) -> DTime:
		"""
		Parse the given time text into a DTime
		"""

		return TimeParser.parse(text)





# Two lists maintaining which py datetime params are for dates vs time
dateparams = ["year", "month", "day"]
timeparams = ["hour", "minute", "second", "microsecond"]


Dateable = Union[str, int, datetime.date]


monthstrs = [*filter(None, [m.lower() for m in calendar._localized_month('%B')])] + [*filter(None, [m.lower() for m in calendar._localized_month('%b')])]


class DTimeParamParser:
	def __init__(self, *args, **kwargs):
		"""
		A parser that takes args/kwargs and returns the info necessary to create a new datetime.datetime instance

		arg/kwarg params work as follows:

		(1) If no args/kwargs supplied (DTime()): return the current datetime
		(2) Elif only one arg passed:
			Convert arg to int (is possible)
			(a) If arg is a string:
					Parse by dateutil.parser
			(b)	elif arg is int and 0 < arg < 10000:
					Treat as a unix timestamp
			(c) If not intable and not str:
					Raise ValueError
		(3) If no date could be gotten from steps (1)-(2):
			(a) If args:
				Treat each arg as a datetime.datetime arg (starting wtih year), and set unset args to their date/time defaults (1 or 0)
			(b) If no args and kwargs:
				Take the current time and for each kwarg: swap now's value with kwarg's value
			(c) If args and kwargs:
				Create the date generated by args, then replace the params as given in kwargs

		"""

		self.args = args
		self.dtargs = list(args)
		self.kwargs = kwargs
		self.date = None
		self.is_pickle_processing = False


	def apply_current_timezone_to_date(self, date: datetime.datetime) -> datetime.datetime:
		current_timezone = DTime.current_timezone()
		return date.replace(tzinfo = current_timezone)


	def _dag_filt_value(self, other, operator):
		breakpoint()
		pass


	def parse_datestr(self, arg: str) -> datetime.datetime:
		from dateutil import parser as dateutilparser
		date = dateutilparser.parse(arg)

		if not date.tzinfo:
			date = self.apply_current_timezone_to_date(date)

		# Turn "August/Aug" so that it is the start of the month
		if arg.lower() in monthstrs:
			date = date.replace(day = 1)

		return date


	def parse_timestamp(self, timestamp: int) -> datetime.datetime:
		return DTime.from_timestamp(timestamp).from_utc


	def parse_datetime_object(self, arg: datetime.datetime) -> datetime.datetime:
		date = arg

		if not date.tzinfo:
			date = self.apply_current_timezone_to_date(date)

		return date


	def process_solo_arg(self) -> NoReturn:
		arg = self.args[0]

		try:
			arg = int(arg)
		except:
			pass

		# If arg is a non-int string: Parse by dateutil.parser
		if isinstance(arg, str):
			if arg == "":
				self.date = datetime.datetime.now()
			else:
				try:
					self.date = self.parse_datestr(arg)
				except ValueError as e:
						raise ValueError(f"{arg} could not be parsed as a DTime") from e

			self.dtargs.pop(0)

		# elif arg is an int: Treat arg as a year or a timestring
		elif isinstance(arg, int):
			# if 0 < arg < 10000: datetime can only handle years up to 9999, so treat as year
			if not (0 < arg < 10000):
				self.date = self.parse_timestamp(arg)
				self.dtargs.pop(0)

		# elif arg is a datetime.date: Return DTime based on that datetime object
		elif isinstance(arg, datetime.datetime):
			self.date = self.parse_datetime_object(arg)
			self.dtargs.pop(0)

		# Else, type isn't compatible: Raise ValueError
		else:
			raise ValueError(f"{arg} of type {type(arg)} could not be parsed as a DTime")


	def get_date_from_params(self) -> NoReturn:
		# Pickle support. Taken from datetime.datetime
		if self.args and (isinstance(self.args[0], (bytes, str)) and len(self.args[0]) == 10 and 1 <= ord(self.args[0][2:3])&0x7F <= 12):
			self.date = datetime.datetime(*self.args)
			self.is_pickle_processing = True

		# If only one arg passed: Process based on its type
		elif len(self.args) == 1:
			self.process_solo_arg()

		# If the above code didn't parse a date: Use now 
		if not self.date:
			self.date = datetime.datetime.now()


	def get_datetime_info_from_params(self) -> dict[str, Union[str, int]]:
		# Info for parsing
		dtp = dateparams + timeparams
		dtparamsi = sorted([i for i, p in enumerate(dtp) if p in self.kwargs or i < len(self.dtargs)])

		dtinfo = {}

		for i, param in enumerate(dtp):
			default = 1 if param in dateparams else 0


			# If pickle processing, used given date
			if self.is_pickle_processing:
				dtinfo[param] = getattr(self.date, param)
			# If no datetime args/kwargs or datetime arg/kwarg wasn't supplied: Use parsed date from above to populate param
			elif not dtparamsi or i < dtparamsi[0]:
				dtinfo[param] = getattr(self.date, param)
			# If datetime arg/kwarg was supplied: Use given arg/kwarg
			elif i in dtparamsi:
				if i < len(self.dtargs):
					dtinfo[param] = self.dtargs[i]
				else:
					dtinfo[param] = self.kwargs.get(param, getattr(self.date, param))
			# Else, datetime arg/kwargs were given but not for this param: Use default param value
			else:
				dtinfo[param] = default

			# Make sure the param is an int
			try:
				dtinfo[param] = int(dtinfo[param])
			# When unpickling, int(...) raises error. Let datetime.datetime handle this
			except (TypeError, ValueError):
				pass


		dtinfo['tzinfo'] = self.kwargs.get("tzinfo", self.date.tzinfo or DTime.current_timezone())
		dtinfo['fold'] = self.kwargs.get("fold", getattr(self.date, "fold"))

		return dtinfo


	def get_datetime_info(self) -> dict[str, Union[int, str]]:
		self.get_date_from_params()
		return self.get_datetime_info_from_params()



default_formatstr = "%Y-%m-%d %I:%M:%S%p %Z"

class DTime(datetime.datetime):
	"""
	A subclass of datetime.datetime with modifcations to make it easier to use
	Features include:
		(1) Broader-ranging handling of input args
			(i)		Timestamps
			(ii)	Fewer args yield valid DTime compared to DTime
			(iii)	dateutil.parser
			(iv)	Other datetime.datet objects
		(2) Easy conversion to/from UTC
		(3) Easy time deltas
		(4) Easy application time from one DTime to date of another DTime
		(5) Adding by int N increases DTime by N days
		(6) noon/midnight/newyear methods to turn to those times
	"""

	# Makes it easier to retrieve the dateutil relativedelta class
	parse = Parser
	
	def __new__(cls, *args: tuple[Dateable], format: Optional[str] = None, utc = False, **kwargs: dict[str, Dateable]):
		"""
		An instance of the DTime

		args/kwargs are parsed by the DTime parser

		Contains a formatting string

		:param format: The format string used to print the date
		"""

		dtinfo = DTimeParamParser(*args, **kwargs).get_datetime_info()

		self = datetime.datetime.__new__(cls, **dtinfo)
		self.formatstr = format or default_formatstr

		if utc:
			self = self.replace(tzinfo = timezone.utc)

		return self


	def __call__(self, formatstr = "") -> str | DTime:
		"""
		Formats the date if a formatstr is provided, else just returns self (unless a better idea comes later)		
		
		:returns: datetime's now, wrapped in the given dobjclass
		"""

		if formatstr:
			return self.format(formatstr)

		return self



	@property
	def utc(self, *args, **kwargs):
		return self.to_utc()



	@staticmethod
	def generate_tzoffset(sec_offset: int) -> timezone:
		return timezone(timedelta(seconds=sec_offset))


	@classmethod
	def now(cls, formatstr: str = "") -> str | DTime:
		"""
		A way to access an instance of the Now method-class

		:returns: An instance of the now method class
		"""

		nowdtime = cls()

		if formatstr:
			return nowdtime.format(formatstr)

		return nowdtime


	@classmethod
	def utcnow(cls) -> DTime:
		"""
		Gets the current UTC time with timezone set

		:returns: The current UTC time with timezone set
		"""

		return cls(datetime.datetime.utcnow(), tzinfo = timezone.utc)


	def delta(self, **kwargs) -> DTime:
		"""
		Passes the given kwargs and yields a dtime whose dt params are deltad by the kwarg values

		Kwargs get pluralized before being passed into datedelta, since datedelta assumes pluralized kwargs

		:returns: A DTime object whose dt params are deltad by the given values
		"""

		# Since deltadate expects plural arguments, add "s" to end of parameters if not already there
		kwargs = {(k+"s" if not k.endswith("s") else k): v for k,v in kwargs.items()}

		from dateutil.relativedelta import relativedelta

		# If this object has a TZ other than the computer's (e.g: UTC) and then relativedelta is applied,
		# relativedelta will re-apply the computer's current TZ. Hence, this code replaces the tzinfo with the current object's tzinfo
		return (self + relativedelta(**kwargs)).replace(tzinfo = self.tzinfo)


	@property
	def timestamp(self) -> int:
		"""
		Returns the timestamp of the given datetime.
		Used as a property since dtimes are immutable

		:returns: The timestamp of the dtime object
		"""

		return int(super().timestamp())


	@property
	def millitimestamp(self) -> int:
		"""
		Returns the millisecond timestamp of the given datetime.
		Used as a property since dtimes are immutable

		:returns: The timestamp of the dtime object in milliseconds
		"""

		return int(super().timestamp()*1000)
		

	def format(self, formatstr: Optional[str] = None) -> str:
		"""
		Translates the dtime object into a string

		:param formatstr: Dictates how to format the dtime, if provided. Otherwise, uses the dtime object's formatstr
		:returns: A string representation of the date/time
		"""

		formatstr = formatstr or self.formatstr
		return self.strftime(formatstr)


	@property
	def formatted(self) -> str:
		"""
		A property that returns the dtime object formatted by the object's formatstr

		:returns: A string representation of the date/time
		"""

		return self.format()

				
	def __str__(self) -> str:
		"""
		When this object is turned into a string, format via the object's given formatstr

		:returns: A string representation of the date/time
		"""

		return self.format()


	def __repr__(self) -> str:
		"""
		Shows some object information along with the formatted datetime.
		Used for CLI debugging

		:returns: Some object information along with the formatted datetime
		"""

		return f"<{object.__repr__(self)} {self.__str__()}>"


	def _dag_resource_repr(self):
		return self.format('%s <c #70 / (%a., %b %d, %Y @ %I:%M:%S %p (%Z))>')
		

	# DTime is registered as DagCacheNamer elsewhere
	def _dag_cachefile_name(self) -> str:
		"""
		Returns the dtime formatted consistently for stored cached files

		:returns: The dtime's date/time as YYYYMMDD
		"""

		return self.format("%Y%m%d")


	@property
	def secondsago(self) -> int:
		return self.parse_timedelta(self.now() - self).seconds

	secsago = secondsago



	@property
	def daysago(self) -> int:
		"""
		This is set up so that anything from yesterday is 1 day ago, anything from today is 0 days ago, anything from tomorrow is -1 days ago

		This was done instead of "anything 24-48 hours ago is 1 day ago, anything from 48-72 hours ago is 2 days ago", etc

		:returns: how many days ago this dtime object is from now. Postitive if in the past, Negative if in the future
		"""

		return self.parse_timedelta(self.today().midnight - self.midnight).days


	@property
	def Ymd(self) -> str:
		"""
		Returns a string of the date as "yyyymmdd" 
		e.g.: March 5, 2048 -> 20480305

		:returns: A string representation of the DTime object as yyyymmdd
		"""

		return self.format("%Y%m%d")

	@property
	def ymd(self) -> str:
		"""
		Returns a string of the date as "yymmdd" 
		e.g.: March 5, 2048 -> 480305

		:returns: A string representation of the DTime object as yymmdd
		"""

		return self.format("%y%m%d")

	@property
	def yearsago(self) -> int:
		"""
		This is set up so that anything from last year is 1 year ago, anything from this year is 0 years ago, anything from next year is -1 years ago

		This means that 1/1/2000 is one year ago from 12/31/2001
		Or that 1/1/2000 is one year ago from 12/31/1999
		BUT: 3/3/2000 isn't two year ago from 4/4/2001

		This matches how I typically use this code

		This was done instead of "anything 24-48 hours ago is -1 day ago, anything from 48-72 hours ago is -2 days ago", etc

		:returns: how many days ago this dtime object is from now
		"""

		return self.parse_timedelta(self.today().newyear - self.newyear).years

		try:
			return (self.today() - self).days//365
		except AttributeError:
			return 0


	@staticmethod
	def compute_utc_offset() -> int:
		is_dst = time.daylight and time.localtime().tm_isdst > 0
		return time.altzone if is_dst else time.timezone


	@property
	def utc_delta(self):
		return self.tzinfo.utcoffset(self)


	@property
	def utc_offset(self):
		return self.utc_delta.seconds


	@classmethod
	def current_timezone(cls):
		return cls.generate_tzoffset(-cls.compute_utc_offset())


	@property
	def from_utc(self, force = False):
		if self.utc_offset == 0:
			return self.delta(seconds = -self.compute_utc_offset())

		return self

	@property
	def force_from_utc(self):
		return self.delta(seconds = -self.compute_utc_offset())


	@property
	def to_utc(self):
		if self.utc_offset == 0:
			return self

		return (self - self.utc_delta).replace(tzinfo = timezone.utc)

								
	@classmethod
	def from_timestamp(cls, timestamp):
		return cls(datetime.datetime.utcfromtimestamp(int(timestamp))).replace(tzinfo = timezone.utc)


	@staticmethod
	def parse_timedelta(timedelta):
		def __t(t, n):
			if t < n: return (t, 0)
			v = t//n
			return (t -  (v * n), v)

		(s, h) = __t(timedelta.seconds, 3600)
		(s, m) = __t(s, 60)	
		(micS, milS) = __t(timedelta.microseconds, 1000)

		delta_info = type('', (), {})() # Simple arbitrary object
		delta_info.years = int(timedelta.days / 365)
		delta_info.days = timedelta.days
		delta_info.hours = h
		delta_info.minutes = m 
		delta_info.seconds = s
		delta_info.milliseconds = milS
		delta_info.microseconds = micS
		delta_info.__class__.__repr__ = lambda x: "Date Delta Info: " + str({k: getattr(delta_info, k) for k in dir(delta_info) if not k.startswith("_")})

		return delta_info


	def time_ago(self):
		return self.parse_timedelta(self.now() - self)


	def units_ago(self):
		# Ultimately: Have decimal rep of time ago in years, months, days etc...
		# So, yesterday will be (1/365) years ago, (1/30) months ago, 1 day ago, 24 hours ago, etc...
		pass

	def __sub__(self, other):
		if isinstance(other, int):
			return self + datetime.timedelta(-other)

		return super().__sub__(other)


	def __add__(self, other):
		if isinstance(other, int):
			return self + datetime.timedelta(other)

		return super().__add__(other)


	def replace(self, **kwargs):
		date = super().replace(**kwargs)
		date.formatstr = self.formatstr
		return date


	@property
	def noon(self):
		return self.replace(hour = 12, minute = 0, second = 0, microsecond = 0)

	@property
	def midnight(self):
		return self.replace(hour = 0, minute = 0, second = 0, microsecond = 0)

	@property
	def newyear(self):
		return self.replace(month = 1, day = 1).midnight

	@property
	def yesterday(self):
		return self.delta(days = -1)


	@property
	def make_today(self):
		return self.now() | self

	@property
	def tomorrow(self):
		return self.delta(days = 1)


	@property
	def firstofmonth(self):
		return self.replace(day = 1).midnight


	@property
	def lastmonth(self):
		return self.delta(months = -1)

	@property
	def ispast(self):
		return self < self.now()

	@property
	def isfuture(self):
		return self > self.now()

	@property
	def iso(self):
		return self.isoformat()


	def __hash__(self):
		return hash(self.timestamp)


	def __or__(self, other):
		if isinstance(other, DTime):
			return self.replace(hour = other.hour, minute = other.minute, second = other.second, microsecond = other.microsecond)

		return super().__or__(other)


	def _dag_filt_value(self, operator, other):
		if isinstance(other, str):
			try:
				other = type(self)(other)
			except ValueError:
				pass

		return operator(self, other)




def dateslice(response, lamb, total, defaultidx = -1):
	total_items = len(response)
	nearest_item = next((item for item in response if lamb(item)), response[defaultidx])

	nearest_item_idx = response.index(nearest_item)
	slice_amt = int(total/2)

	startidx = max(0, nearest_item_idx - slice_amt)
	endidx = min(total_items, nearest_item_idx + slice_amt)

	if startidx == 0:
		endidx = min(total_items, total)
	elif endidx == total_items:
		startidx = max(0, total_items - total)

	return response[startidx:endidx], nearest_item
