import time, os
from collections.abc import Sequence

import dag


class BrowserDriver(dag.dot.DotAccess):
	def __init__(self, driver):
		pass
		#super().__init__(driver)


class FirefoxDriver(BrowserDriver):
	def __init__(self, *args, **kwargs):
		from selenium import webdriver
		
		log_path = dag.directories.STATE / "firefox-logs"
		
		if not os.path.exists(log_path):
			os.makedirs(log_path)
		
		self.driver = webdriver.Firefox(log_path = str(log_path / 'geckodriver.log'), **kwargs)

		super().__init__(self.driver)


	def __call__(self, *args, **kwargs):
		return self.select(*args, **kwargs)

		
	def select(self, attr, tries = 1, retry_time = 1):
		elements = []
		
		for i in range(tries):
			#elements = FirefoxElementsCollection([FirefoxElement(e) for e in self.driver.find_elements_by_css_selector(attr)])
			elements = [FirefoxElement(e) for e in self.driver.find_elements_by_css_selector(attr)]

			if elements:
				break
			
			if i < tries - 1:
				dag.echo(f"element <c b>\"{attr}\"</c> not found. <c b>{tries - i - 1}</c> attempts remaining. Retrying in {retry_time} seconds.")
				time.sleep(retry_time)
		
		if attr.startswith("#") and " " not in attr and len(elements) == 1:
			return elements[0]
			
		return elements
		
		
	def type(self, text, element, speed = 0):
		[element.send_keys(c) for c in text if time.sleep(speed) is None]
		
		
	def js(self, script):
		from selenium.common.exceptions import JavascriptException
		try:
			return self.driver.execute_script(f"return {script.lstrip('return ')}")
		except JavascriptException as e:
			time.sleep(1)
			return self.driver.execute_script(f"return {script.lstrip('return ')}")
			
			
	def sleep(self, sec = 1, message = ""):
		if message: print(message)
		print(f"sleeping for {sec} second{'s' if sec != 1 else ''}")
		time.sleep(sec)
				

	def close(self, sleep_after = 0):
		if sleep_after:
			dag.echo(f"<c b>Sleeping for {sleep_after} seconds</c>")
			time.sleep(sleep_after)
				
		dag.echo("Closing browser...")
		try:
			self.driver.close()
		except Exception as e:
			breakpoint()
			pass

	def get(self, url, *args, **kwargs):
		print(f"Getting {url}")
		return self.driver.get(url, *args, **kwargs)


class FirefoxElementsCollection(Sequence):
	def __init__(self, elements):
		self.elements = elements

	def __getitem__(self, idx): return self.elements[idx]

	def __len__(self): return len(self.elements)

	def filter(self, map):
		items = [*filter(map, self)]
		return self.__class__(items)



class FirefoxElement:
	def __init__(self, element, *args, **kwargs):
		self.element = element
		self.iterated = False
		
		
	def type(self, text, speed = 0):
		[self.element.send_keys(c) for c in text if time.sleep(speed) is None]
		
		
	def submit(self):
		from selenium.webdriver.common.keys import Keys
		self.element.send_keys(Keys.RETURN)


	@property
	def html(self):
		return self.element.get_attribute("innerHTML")


	def __call__(self, attr, tries = 1, retry_time = 1):
		return self.select(attr, tries, retry_time)


	def select(self, attr, tries = 1, retry_time = 1):
		elements = []
		
		for i in range(tries):
			elements = [FirefoxElement(e) for e in self.element.find_elements_by_css_selector(attr)]

			if elements:
				break
			
			if i < tries - 1:
				dag.echo(f"element <c b>\"{attr}\"</c> not found. <c b>{tries - i - 1}</c> attempts remaining. Retrying in {retry_time} seconds.")
				time.sleep(retry_time)
		

		if attr.startswith("#") and " " not in attr and len(elements) == 1:
			return elements[0]
			
		return elements
		

	def __getattr__(self, attr, default = None):
		return getattr(self.element, attr, default)


	def __iter__(self): # Added so that if a single element is returned, can still use in a for loop
		self.iterated = False
		return self
		

	def __next__(self):
		if not self.iterated:
			self.iterated = True
			return self

		raise StopIteration

		
class DagBrowser:
	def __init__(self, *args, headless = False, javascript = False, sleep_after = 0, profile = None, download_location = None, login = None, **kwargs):
		self.headless = headless
		self.javascript = javascript
		self.sleep_after = sleep_after
		self.args = args
		self.kwargs = kwargs
		self.profile = profile or {}
		self.download_location = download_location or os.getcwd()
		self.login = login

		self.driver = None
	
	def __enter__(self):	
		browser = self.browse()

		if self.login is not None:
			print("logging in")
			self.login(browser)
			print("logged in")

		return browser


	def browse(self):
		try:
			from selenium import webdriver
			firefox_options = webdriver.FirefoxOptions()
			firefox_profile = webdriver.FirefoxProfile()
			
			firefox_profile.set_preference("browser.download.dir", self.download_location) # Location to download files to (defaults ot os.getcwd)
			firefox_profile.set_preference("browser.download.folderList",2)					# Necessary to make sure file isn't download to Downloads folder
			firefox_profile.set_preference("browser.download.manager.showWhenStarting",False)	# Prefents firefox from doing any download animationsxzx
			
			for setting, option in self.profile.items():
				firefox_profile.set_preference(setting, option)
			
			if self.headless:
				firefox_options.add_argument("--headless")
				#firefox_options.set_headless()
				
			if self.javascript is False:
				firefox_options.set_preference("javascript.enabled", False)
				
			headless_str = " headless" if self.headless else ""
			js_str = "without javascript enabled" if not self.javascript else "with javascript enabled"
			dag.echo(f"Starting{headless_str} browser {js_str}...")
			
			#self.driver = webdriver.Firefox(firefox_options=firefox_options)
			self.driver = FirefoxDriver(options=firefox_options, firefox_profile = firefox_profile)
			
			return self.driver
			
		except ImportError as e:
			dag.echo("is selenium installed? If not: Install and (for firefox), get geckodriver.exe (FOR WINDOWS), add to PATH, and chmod +x")
			breakpoint()
			raise e
			
		except Exception as e:
			dag.echo("If using Firefox/Cygwin, make sure geckodriver.exe (FOR WINDOWS) is installed, in PATH, and chmodded to +x.\nmake sure it's up to date: https://github.com/mozilla/geckodriver/releases")
			breakpoint()
			raise e


	def __exit__(self, type, value, traceback):
		if self.driver is not None:
			return self.driver.close(sleep_after = self.sleep_after)