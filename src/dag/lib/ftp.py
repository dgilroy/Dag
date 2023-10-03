import subprocess

class FtpClient:
	name = None

	@staticmethod
	def passwordparam(password, *args, **kwargs):
		raise NotImplementedError

	@staticmethod
	def openurl(url, *args, **kwargs):
		raise NotImplementedError


class WinSCP(FtpClient):
	name: str = "winscp.exe"

	@staticmethod
	def generateparam(name: str, value: str) -> str:
		return f"/{name}={value}"


	@classmethod
	def passwordparam(cls, password: str) -> str:
		return cls.generateparam("password", password)


	@classmethod
	def openurl(cls, url: str, password: str = "", **kwargs) -> None:
		args = [cls.name, url]
		if password:
			args.append(cls.passwordparam(password))

		for name,value in kwargs.items():
			args.append(cls.generateparam(name, value))

		subprocess.run(args)