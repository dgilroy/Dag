import dag
from dag import r_, args



bstack = dag.app.JSON("browserstack", baseurl = "https://api.browserstack.com/automate/", launch = "https://www.browserstack.com/", doc = "https://www.browserstack.com/docs/automate/api-reference/selenium/introduction", auth = dag.auth.BASIC(dag.nab.env.BROWSERSTACK_NAME, dag.nab.env.BROWSERSTACK_KEY))

plan = bstack.cmd.CACHE.GET("plan.json")

browsers = bstack.collection(label_ignore_chars = ".").GET("browsers.json")
browsers.resources("browser")


@browsers.resources.LABEL
def _browsers_label(browser):
	b = browser
	return f"{b.os}-{b.browser}" if browser.browser_version not in [None, "none", "None"] else f"{b.os}-{b.browser}-{b.browser_version}"



@bstack.arg("--os", choices = browsers.nab().filter(r_.browser == dag.args.browsername).get_values_of("os"))
@bstack.arg("--version", choices = browsers.nab().filter(r_.browser == dag.args.browsername).get_values_of("browser_version"))
@bstack.arg("browsername", choices = browsers.nab().get_values_of("browser"))
@bstack.DEFAULT.cmd
def launchurl(browsername, url, *, version = None, os = None):
	return url