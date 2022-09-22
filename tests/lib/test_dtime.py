import datetime, time
from datetime import timezone, timedelta

import pytest
from freezegun import freeze_time

from dag.lib import dtime


TESTYEAR = 2000
TESTMONTH = 1
TESTDAY = 14
TESTHOUR = 12
TESTMINUTE = 0
TESTSECOND = 0
TESTMICROSECOND = 0

TEST_TZOFFSET = -5

TESTDATESTR = f"{TESTMONTH}/{TESTDAY}/{TESTYEAR} {TESTHOUR}:{str(TESTMINUTE).zfill(2)}:{str(TESTSECOND).zfill(2)}.{TESTMICROSECOND}" # "1/14/2000 12:00"
TESTDATE = dtime.DTime(TESTDATESTR, tzinfo = timezone(timedelta(seconds=60*60*TEST_TZOFFSET)))

TESTSTAMP = int(TESTDATE.timestamp)


@pytest.fixture
def dt():
	return dtime


@pytest.fixture
def dtp():
	return dtime.DateTimeParser


@pytest.fixture
def tp():
	return dtime.TimeParser


@pytest.fixture
def dp():
	return dtime.DateParser


@pytest.fixture
def do():
	return dtime.DTime

@pytest.fixture
def day(do):
	return do(TESTDATESTR)



def test_current_milli_time(dt, mocker):
	secvalue = 10

	with mocker.patch("time.time", return_value = secvalue):
		assert dt.current_milli_time() == secvalue * 1000


def test_process_deltaval(dtp):
	assert dtp.process_deltaval("w", "3w") == 3
	assert dtp.process_deltaval("w", "32w") == 32
	assert dtp.process_deltaval("$", "987") == 987

	assert dtp.process_deltaval("ab", "6ab") == 6

	assert dtp.process_deltaval("3", "93") == 9

	assert dtp.process_deltaval("Q", "93") == 0


def test_parse_datetime(dtp, do):
	with pytest.raises(ValueError):
		assert dtp.parse("yesterday")

	assert dtp.parse("2000") == do(2000,1,1)
	assert dtp.parse("4pm") == do(hour = 16)

	assert dtp.parse("2000", "%Y").formatted == "2000"
	assert dtp.parse("2000", "%m").formatted == "01"


test_deltavals = {"week": ["a", "b"], "cats": ["c", "x", "mm", "$", "μ"], "months": ["999"], "val1": ["v"], "val2": ["v"]}



def test_get_deltamatchers_datetime(dtp, monkeypatch):
	assert dtp.get_deltamatchers() == ""

	monkeypatch.setattr(dtp, "deltavals", test_deltavals)
	assert dtp.get_deltamatchers() == "a,b,c,x,mm,μ,v,v"


def test_process_deltastr_datetime(dtp, monkeypatch):
	assert dtp.process_deltastr("") == {}
	assert dtp.process_deltastr("9w") == {}
	assert dtp.process_deltastr("jaowiejf") == {}

	monkeypatch.setattr(dtp, "deltavals", test_deltavals)
	assert dtp.process_deltastr("") == {}
	assert dtp.process_deltastr("TEST") == {}

	assert dtp.process_deltastr("9a") == {"week": 9}
	assert dtp.process_deltastr("-6b") == {"week": 6}

	assert dtp.process_deltastr("-19") == {"cats": 19}
	assert dtp.process_deltastr("-23mm") == {"cats": 23}
	assert dtp.process_deltastr("-1μ") == {"cats": 1}

	assert dtp.process_deltastr("-1v") == {"val1": 1, "val2": 1}

	assert dtp.process_deltastr("9a6c") == {"week": 9, "cats": 6}
	assert dtp.process_deltastr("9a6c8b") == {"week": 9, "cats": 6}



def test_is_text_deltastr_datetime(dtp, monkeypatch):
	assert not dtp.is_text_deltastr("")
	assert not dtp.is_text_deltastr("92")
	assert not dtp.is_text_deltastr("11w")

	monkeypatch.setattr(dtp, "deltavals", test_deltavals)

	assert not dtp.is_text_deltastr("11w")
	assert dtp.is_text_deltastr("11b")
	assert dtp.is_text_deltastr("78μ")


class TestDTimeInitialization:
	@freeze_time(TESTDATESTR)
	class TestOneArg:
		def test_noargs(self, do):
			assert do() == TESTDATE

		@pytest.mark.parametrize("year", [1, 1111, 9999, "1", "1111", "9999"])
		def test_under_10000_yields_newyear(self, do, year):
			assert do(year) == do(int(year), 1, 1)

		def test_over_10000_reads_timestamp(self, do):
			assert do(TESTSTAMP) == TESTDATE
			assert do(TESTSTAMP+1) == TESTDATE.delta(seconds = 1)

		def test_negative_is_timestamp(self, do):
			assert do(-1).timestamp == -1

		def test_float_to_int(self, do):
			assert do(1.0) == do(1)

		def test_str_to_int(self, do):
			assert do("1") == do(1)

		def test_str_dateutil_parse(self, do):
			assert do("1/1/2000") == do(2000, 1, 1)

		def test_datetime(self, do):
			assert do(datetime.datetime(2000,1,1)) == do(2000, 1, 1)

		def test_datetobj(self, do):
			assert do(do(2000,1,1)) == do(2000, 1, 1)

		def test_datetime_fail(self, do):
			with pytest.raises(ValueError):
				assert do({1:2})



	@freeze_time(TESTDATESTR)
	class TestNoArgsYesKwargs:
		def test_datetime_kwargs(self, do):
			assert do(year = 2000) == do(2000,1,1)
			assert do(year = 2000, month = 1) == do(2000,1,1)

			assert do(year = TESTYEAR, month = TESTMONTH, day = TESTDAY) == TESTDATE.midnight()
			assert do(year = TESTYEAR, month = TESTMONTH, day = TESTDAY, hour = TESTHOUR) == TESTDATE
			assert do(year = TESTYEAR, month = TESTMONTH, day = TESTDAY, hour = TESTHOUR, minute = 15) == TESTDATE.replace(minute = 15)
			assert do(year = TESTYEAR, month = TESTMONTH, day = TESTDAY, hour = TESTHOUR, minute = 15, second = 15) == TESTDATE.replace(minute = 15, second = 15)
			assert do(year = TESTYEAR, month = TESTMONTH, day = TESTDAY, hour = TESTHOUR, minute = 15, second = 15, microsecond = 15) == TESTDATE.replace(minute = 15, second = 15, microsecond = 15)

		def test_no_args_one_kwarg(self, do):
			assert do(year = 3) == do(3, 1, 1, 0, 0, 0, 0)
			assert do(month = 3) == do(TESTYEAR, 3, 1, 0, 0, 0, 0)
			assert do(day = 3) == do(TESTYEAR, TESTMONTH, 3, 0, 0, 0, 0)
			assert do(hour = 3) == do(TESTYEAR, TESTMONTH, TESTDAY, 3, 0, 0, 0)
			assert do(minute = 3) == do(TESTYEAR, TESTMONTH, TESTDAY, TESTHOUR, 3, 0, 0)
			assert do(second = 3) == do(TESTYEAR, TESTMONTH, TESTDAY, TESTHOUR, TESTMINUTE, 3, 0)
			assert do(microsecond = 3) == do(TESTYEAR, TESTMONTH, TESTDAY, TESTHOUR, TESTMINUTE, TESTSECOND, 3)

		def test_no_args_multi_kwarg(self, do):
			assert do(year = 3, month = 3) == do(3,3,1,0,0,0,0)
			assert do(year = 3, month = 3, day = 3) == do(3,3,3,0,0,0,0)
			assert do(year = 3, month = 3, day = 3, hour = 3) == do(3,3,3,3,0,0,0)
			assert do(year = 3, month = 3, day = 3, hour = 3, minute = 3) == do(3,3,3,3,3,0,0)
			assert do(year = 3, month = 3, day = 3, hour = 3, minute = 3, second = 3) == do(3,3,3,3,3,3,0)
			assert do(year = 3, month = 3, day = 3, hour = 3, minute = 3, second = 3, microsecond = 3) == do(3,3,3,3,3,3,3)

		def test_args_and_kwargs(self, do):
			assert do(1111, minute = 3) == do(1111, 1, 1, 0, 3, 0, 0)
			assert do("2/3/4444", minute = 3) == do(4444, 2, 3, 0, 3, 0, 0)



	@freeze_time(TESTDATESTR)
	class TestMultiArgs:
		def test_multi_datetime_params(self,do):
			assert do(1111).year == 1111

			assert do(1111,9).year == 1111
			assert do(1111,9).month == 9

			assert do(1111,9,8).day == 8
			assert do(1111,9,8,12).hour == 12
			assert do(1111,9,8,12,30).minute == 30
			assert do(1111,9,8,12,30,15).second == 15
			assert do(1111,9,8,12,30,15,10).microsecond == 10

		def test_default_params(self,do):
			assert do(1111) == do(1111, 1) == do(1111, 1, 1) == do(1111, 1, 1, 0) == do(1111, 1, 1, 0, 0) == do(1111, 1, 1, 0, 0, 0) == do(1111, 1, 1, 0, 0, 0, 0)



@freeze_time(TESTDATESTR)
class TestTimeSensitive:
	def test_now_class(self, do):
		assert isinstance(do.now, dtime.Now)

		assert do.now() == do(datetime.datetime.now())
		assert do.now.utc() == do(datetime.datetime.utcnow().timestamp())
		assert do.now.timestamp() == do().now.utc().timestamp


	def test_dtime_delta(self, do):
		day = do(TESTYEAR)

		assert day.delta(years = -1).year == TESTYEAR - 1
		assert day.delta(years = 1).year == TESTYEAR + 1

		assert day.delta(months = -1).year == 1999
		assert day.delta(months = -1).month == 12
		assert day.delta(months = 1).year == 2000
		assert day.delta(months = 1).month == 2

		assert day.delta(seconds = -1).year == 1999
		assert day.delta(seconds = -1).month == 12
		assert day.delta(seconds = -1).day == 31
		assert day.delta(seconds = -1).hour == 23
		assert day.delta(seconds = -1).minute == 59
		assert day.delta(seconds = -1).second == 59

	def test_dtime_delta_pluralize(self, do):
		day_plural = do().delta(years = -1, months = -1, days = -1, hours = -1, minutes = -1, seconds = -1, microseconds = -1)
		day_singul = do().delta(year = -1, month = -1, day = -1, hour = -1, minute = -1, second = -1, microsecond = -1)

		assert day_plural == day_singul


	def test_dtime_timestamp(self, do):
		assert do.utc(1970).timestamp == 0
		assert do.utc(1970, second = 1).from_utc().timestamp == 1
		assert do.utc(1971).timestamp == 60*60*24*365


	def test_dtime_format(self, do, day):
		assert day.format("%Y") == "2000"
		assert day.format() == day.format(day.formatstr)


	def test_dtime_formated(self, do, day):
		assert day.formatted == day.format(day.formatstr)

	def test_dtime_str(self, do, day):
		assert str(day) == day.format(day.formatstr)

	def test_dtime__dag_cachefile_name(self, day):
		assert day._dag_cachefile_name() == f"{TESTYEAR:0>4}{TESTMONTH:0>2}{TESTDAY:0>2}"

	def test_dtime_daysago(self, do,day):
		assert day.yesterday().daysago == 1
		assert day.delta(days = -1).daysago == 1
		assert day.delta(days = -1, hours=-1).daysago == 1
		assert day.delta(hours=-25).daysago == 1
		assert day.delta(days = -1,  hours=-1).daysago == 1
		assert day.delta(days = -1,  hours=-23).daysago == 2

		assert day.tomorrow().daysago == -1
		assert day.delta(days = 1).daysago == -1

		assert day.delta(seconds = -1).daysago == 0
		assert day.delta(seconds = 1).daysago == 0

		assert do().daysago == 0

	def test_dtime_yearsago(self, do,day):
		assert day.delta(years = 1).yearsago ==  -1
		assert day.delta(years = -1).yearsago ==  1

	def test_dtime_computer_utc_offset(self, do,day):
		assert day.computer_utc_offset() == 60*60*5

	def test_dtime_utc_now(self, do):
		assert do.utcnow().tzinfo == timezone.utc