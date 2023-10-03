import dag

class DagAuthError(dag.DagError): pass

class AuthBase:
	header_name = "Authorization"
	prefix = ""
	base64 = False

	token = None

	def __init__(self, token = None, expires_in = 0):
		self.raw_token = token
		self.expires_in = expires_in
		self.timeset = None 	# Keeps track of whenever a token is set to check whether it eventually times out


	def initialize_token(self):
		self.token = dag.nab_if_nabber(self.raw_token)

		if callable(self.token):
			self.token = self.token()

		self.timeset = dag.now()


	def process_token(self):
		pass


	def set_token(self):
		with dag.ctx(setting_token = True):
			dag.hooks.do("pre_set_token")
			self.initialize_token()
			self.process_token()
			dag.hooks.do("post_set_token", self.token)


	def is_token_being_set(self):
		return dag.ctx.setting_token


	def is_token_timed_out(self):
		return self.expires_in and self.timeset and self.timeset.secsago > self.expires_in


	def is_token_set(self):
		return self.token is not None


	def is_should_set_token(self):
		return not self.is_token_set() or self.is_token_timed_out()


	def process_request(self, request):
		if self.is_should_set_token():
			self.set_token()

		try:		
			request.headers[self.header_name] = self.prefix + self.token
		except TypeError as e:
			raise dag.DagError("Error creating token:") from e


	def __call__(self, request):
		if self.is_token_being_set():
			return request

		self.process_request(request)

		return request




class Basic(AuthBase):
	prefix = "Basic "
	base64 = True

	def __init__(self, username, password = "", **kwargs):
		super().__init__(**kwargs)
		self.raw_username = username
		self.raw_password = password

	def initialize_token(self):
		username = dag.nab_if_nabber(self.raw_username)
		password = dag.nab_if_nabber(self.raw_password)
		self.token = f"{username}:{password}" if password else username

	def process_token(self):
		if self.base64:
			try:
				self.token = dag.b64.encode(self.token)
			except TypeError as e:
				tokenname = self.raw_token._stored_attrs[-1].attr_name if isinstance(self.raw_token, dag.Nabber) else self.raw_token
				raise DagAuthError(f"Token {tokenname} is not defined") from e




class OAuth(AuthBase):
	prefix = "Bearer "

	def process_token(self):
		match self.token:
			case str():
				self.expires_in = 0
			case _:
				try:
					self.prefix = self.token.token_type + " "
					self.expires_in = self.token.expires_in
					self.token = self.token.access_token
				except AttributeError as e:
					tokenname = self.raw_token._stored_attrs[-1].attr_name if isinstance(self.raw_token, dag.Nabber) else self.raw_token
					raise DagAuthError(f"Token {tokenname} is not defined") from e



class Header(AuthBase):
	def __init__(self, header_name = None, token = "", prefix = "", **kwargs):
		super().__init__(token, **kwargs)
		self.header_name = header_name or self.header_name
		self.prefix = prefix or self.prefix


class UrlParam(AuthBase):
	def __init__(self, paramval, token):
		self.paramval = paramval
		self.token = token

	def process_request(self, request):
		prefix = "&" if "?" in request.url else "?"
		paramval = dag.nab_if_nabber(self.paramval)
		token = dag.nab_if_nabber(self.token)

		request.url += f"{prefix}{paramval}={token}" 



BASIC = Basic
OAUTH = OAuth
HEADER = Header
PARAM = UrlParam