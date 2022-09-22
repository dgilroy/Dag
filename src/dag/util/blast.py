import shutil, re
from contextlib import contextmanager

import dag


def width():
	 return shutil.get_terminal_size().columns

def height():
	return shutil.get_terminal_size().lines


ANSI_START_PREV_LINE = "\033[F"



class Blast:
	def __init__(self):
		self.buffer = Buffer(self)
		self.buffers = [self.buffer]
		self.last_executed_buffer = None

		self.linedelta = 0

		self.reset()


	@property
	def buffer_no_ctags(self):
		return re.sub("</?c.*?>", "", self.buffer)


	def reset(self):
		self.buffer = Buffer(self)
		self.buffers.append(self.buffer)


	@staticmethod
	@contextmanager
	def session():
		sess = Blast()

		try:
			yield sess
		finally:
			sess.exit()


	def print(self, text, **kwargs):
		if style := kwargs.get("ctag"):
			text = f"<c {style}>{text}</c {style}>"

		self.buffer.add(text)
		return self


	def printline(self, text, **kwargs):
		return self.print(text.ljust(width())[0:width()], **kwargs)


	def fillline(self, text = " ", **kwargs):
		text = text or " " # Prevents a string of len 0
		filled_text = text*(width()//len(text))
		leftover = width() - len(filled_text)
		return self.printline(filled_text + text[:leftover], **kwargs)


	def newline(self, **kwargs):
		return self.fillline(" ", **kwargs)


	def exec(self):
		try:
			self.buffer.print()
			self.last_executed_buffer = self.buffer
		finally:
			self.reset()


	def exit(self):
		# Implement so that the cursor moves to the end of previously-printed text.
		linedelta = self.buffers[0].linecount

		for i in range(len(self.buffers[1:-1])):
			if self.buffers[i+1].linecount == 0:
				continue

			linedelta += self.buffers[i].linecount - self.buffers[i+1].linecount


		print("\n"*abs(linedelta))


	def __mul__(self, quantity = 1):
		return self.buffer.__mul__(quantity)



class Buffer:
	def __init__(self, session):
		self.session = session
		self.lines = [""]


	def add(self, line):
		self.lines.append(str(line))


	@property
	def lastline(self):
		return self.lines[-1]


	@property
	def text(self):
		return "".join(self.lines)


	@property
	def text_no_ctags(self):
		return re.sub("</?c.*?>", "", self.text)


	@property
	def linecount(self):
		return 1 + (len(self.text_no_ctags)-1)//width()


	def __iadd__(self, other):
		"""
		Allows buffer += "text" to add "text" to the buffer
		"""

		if not isinstance(other, str):
			raise NotImplementedError

		self.lines.add(other)
		return self


	def __mul__(self, quantity):
		quant = quantity-1 if quantity-1 >= 0 else 0

		for i in range(quant):
			self.lines.append(self.lastline)


	def print(self):
		textlength = len(self.text_no_ctags)
		print(dag.format(self.text), end = (ANSI_START_PREV_LINE * (self.linecount-1)) + "\r")