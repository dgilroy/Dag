from typing import Self
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

from dag.lib import dot

class _Server(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.end_headers()

		breakpoint()
		self.server.requests.append(self)


class Server(dot.DotAccess):
	def __init__(self, hostname, port, requestHandler = _Server, **kwargs):
		self.settings = kwargs
		self.requestHandler = requestHandler
		self.hostname = hostname
		self.port = port
		self.server = None

		self.requests = []
		

	def __enter__(self) -> Self:
		self.server = HTTPServer((self.hostname, self.port), self.requestHandler)
		dag.echo(f"DagServer started http://{self.hostname}:{self.port}")
		return self


	def __exit__(self, type, value, traceback):
		self.server.server_close()
		self.server = None
		dag.echo("DagServer closed")


	def __getattr__(self, value, default = None):
		return getattr(self.server, value, default)


	def serve_once(self) -> None:
		self.server.serve_forever()
		return

	def listen_once(self, retry_time: float = 1) -> None:
		while True:
			if self.requests:
				return self.requests.pop(0)

			time.sleep(retry_time)


with Server("localhost", 8080) as server:
	#request = server.listen_once()
	server.serve_forever()
	breakpoint()
	pass