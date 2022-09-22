import pytest

from dag.util import drill

 


def test__get_drillbits():
	drillstr = drill._get_drillbits("wow.now[1]")
	assert drillstr == ['wow', 'now', '[1]']

	drillstr = drill._get_drillbits("wow.now['1']")
	assert drillstr == ['wow', 'now', "['1']"]

	drillstr = drill._get_drillbits('wow.now["1"]')
	assert drillstr == ['wow', 'now', '["1"]']

	drillstr = drill._get_drillbits("wow.outside[inside(1)]")
	assert drillstr == ['wow', 'outside', '[inside', '(1)]']

	drillstr = drill._get_drillbits("bing.bang(arg1, arg2, arg3)")
	assert drillstr == ['bing', 'bang', '(arg1, arg2, arg3)']

	drillstr = drill._get_drillbits("oof,goof,mcgee", splitter = ",")
	assert drillstr == ['oof', 'goof', 'mcgee']

	drillstr = drill._get_drillbits("wow")
	assert drillstr == ['wow']

	drillstr = drill._get_drillbits("")
	assert drillstr == ['']

	drillstr = drill._get_drillbits("oof\ngoof", splitter = "\n")
	assert drillstr == ['oof', 'goof']

	drillstr = drill._get_drillbits("wow.now[1].browncow()")
	assert drillstr == ['wow', 'now', '[1]', "browncow", "()"]


def test_get_drillparts():
	drillee, bits = drill.get_drillparts("wow.now[1]")
	assert drillee == "wow" and bits == ".now[1]"

	drillee, bits = drill.get_drillparts("wow.now[1]", combined_drillbits = False)
	assert drillee == "wow" and bits == ["now", "[1]"]

	drillee, bits = drill.get_drillparts("wow.now['1']")
	assert drillee == "wow" and bits == ".now['1']"

	drillee, bits = drill.get_drillparts("wow.outside[inside(1)]")
	assert drillee == 'wow' and bits == ".outside[inside(1)]"

	drillee, bits = drill.get_drillparts("meow[32]")
	assert drillee == 'meow' and bits == "[32]"

	drillee, bits = drill.get_drillparts("testfunc().keys()")
	assert drillee == 'testfunc' and bits == "().keys()"

	drillee, bits = drill.get_drillparts("testfunc().keys()", combined_drillbits = False)
	assert drillee == 'testfunc' and bits == ["()", "keys", "()"]

	drillee, bits = drill.get_drillparts("testfunc(),keys()", splitter = ",")
	assert drillee == 'testfunc' and bits == "(),keys()"

	drillee, bits = drill.get_drillparts("http://www.test.com")
	assert drillee == 'http://www.test.com' and bits == ""

	drillee, bits = drill.get_drillparts("https://www.test.com")
	assert drillee == 'https://www.test.com' and bits == ""


class TestClass:
	testdict = {"wow": "now", "brown": {"beef": "cow", "brown": "color"}}
	testdict2 = {"2": "TWO"}
	testlist = ["a", "B", "cCc", {"keey": "vaal"}]
	teststr = "bAllOoN"

class TestClass2:
	tc = TestClass()

tc = TestClass()
tc2 = TestClass2()



def test_drill():
	assert drill.drill(tc, "testdict[wow]") == tc.testdict["wow"]
	assert drill.drill(tc, ".testdict[wow]") == tc.testdict["wow"]
	assert drill.drill(tc, "testdict['wow']") == tc.testdict["wow"]
	assert drill.drill(tc, 'testdict["wow"]') == tc.testdict["wow"]
	assert drill.drill(tc.testdict, "[brown]") == tc.testdict["brown"]
	assert drill.drill(tc.testdict, "[brown][beef]") == tc.testdict["brown"]["beef"]
	assert drill.drill(tc.testdict, "[brown]['beef']") == tc.testdict["brown"]['beef']

	assert drill.drill(tc, "testdict2['2']") == tc.testdict2["2"]
	assert drill.drill(tc, 'testdict2["2"]') == tc.testdict2["2"]
	assert drill.drill(tc, "testdict2[2]") == tc.testdict2["2"]

	assert drill.drill(tc, "testlist[0]") == tc.testlist[0]
	assert drill.drill(tc, "testlist[1]") == tc.testlist[1]
	assert drill.drill(tc.testlist, "[2]") == tc.testlist[2]
	assert drill.drill(tc.testlist, "[2].upper()") == tc.testlist[2].upper()

	with pytest.raises(drill.DagDrillError):
		# At this time, function calls cant have args
		drill.drill(tc.testlist, "[2].__getitem__(1)")

	assert drill.drill(tc.testlist, "[3]") == tc.testlist[3]

	assert drill.drill(tc, "teststr") == tc.teststr
	assert drill.drill(tc, ".teststr") == tc.teststr
	assert drill.drill(tc.teststr, "") == tc.teststr

	assert drill.drill(tc, "testdict['brown']['beef']", drill_until = -1) == tc.testdict['brown']
	assert drill.drill(tc, "testlist[0]", drill_until = -1) == tc.testlist
	assert drill.drill(tc, "testlist[0]", drill_until = -2) == tc
	assert drill.drill(tc, "testlist[0]", drill_until = 0) == tc.testlist[0]

	assert drill.drill(tc2, "tc.teststr") == tc2.tc.teststr
	assert drill.drill(tc2, ".tc.teststr") == tc2.tc.teststr
	assert drill.drill(tc2.tc, ".teststr") == tc2.tc.teststr
	assert drill.drill(tc2.tc, "teststr") == tc2.tc.teststr



def test_drill_for_properties():
	assert drill.drill_for_properties(tc2, "") == []
	assert set(drill.drill_for_properties(tc2, "tc.te")) == set([f"tc.{k}" for k in (vars(tc) | vars(tc.__class__)).keys() if not k.startswith("_")])
	assert set(drill.drill_for_properties(tc2, "tc.testlist.")) == set([f"tc.testlist.{k}" for k in vars(tc.testlist.__class__).keys()  if not k.startswith("_")])