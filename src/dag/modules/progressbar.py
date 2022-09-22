import time, shutil, signal

import dag
from dag import this
from dag.util import blast



def stop_iteration(signum, frame):
	raise StopIteration()


@dag.mod("progressbar", default_cmd = this.progressbar)
class ProgressBar(dag.DagMod):
	def _init(self):
		self.icons = r"||//_"
		self.iconsflipped = r"||//_\\"
		self.colors = ["#2BA4B8", "#1C7071", "#259C58", "#C49B3F", "#E87136"]
		self.colorsflipped = self.colors + [*reversed(self.colors)][1:-2]

		self.original_sigint_handler = signal.getsignal(signal.SIGINT)


	@dag.hook.before_evaulate_dagcmd
	def set_sigint(self):
		self.original_sigint_handler = signal.getsignal(signal.SIGINT)
		signal.signal(signal.SIGINT, stop_iteration)


	@dag.hook.after_evaulate_dagcmd
	def unset_sigint(self):
		signal.signal(signal.SIGINT, self.original_sigint_handler)


	@dag.arg("sleep", type = float)
	@dag.arg("total", type = int)
	@dag.cmd()
	def progressbar(self, total = 50, sleep = .12):
		# A List of Items
		items = list(range(0, total))
		l = len(items)

		with blast.Blast.session() as sess:
			# Initial call to print 0% progress
			try:
				for i, item in enumerate(items):
					# Do stuff...
					time.sleep(sleep)

					icon = self.iconsflipped[i%len(self.iconsflipped)] 
					color = self.colorsflipped[i%len(self.colorsflipped)]
					sess.printline(" "*i + f"<c {color}>{icon}</c>" + " "*(total-i)).exec()

				sess.newline().exec()
			except StopIteration:
				pass
			finally:
				sess.print("</c>").exec()

			sess.newline().exec()


	@dag.arg("sleep", type = float)
	@dag.arg("total", type = int)
	@dag.cmd()
	def pb2(self, total = 50, sleep = .12):
		# A List of Items
		items = list(range(0, total))
		l = len(items)

		def coloridx(i):
			return self.colorsflipped[i%len(self.colorsflipped)]

		# Initial call to print 0% progress
		with blast.Blast.session() as sess:
			try:
				for i, item in enumerate(items):
					# Do stuff...
					time.sleep(sleep)

					color = self.colorsflipped[i%len(self.colorsflipped)]
					color2 = self.colorsflipped[(i+1)%len(self.colorsflipped)]
					
					sess.fillline(f"{self.iconsflipped}", ctag = coloridx(i))
					sess.fillline(f"{self.iconsflipped}", ctag = coloridx(i-1))
					sess.fillline(f"{self.iconsflipped}", ctag = coloridx(i-2))
					sess.fillline(f"{self.iconsflipped}", ctag = coloridx(i-3))
					sess.fillline(f"{self.iconsflipped}", ctag = coloridx(i-4))

					sess.exec()
			except StopIteration:
				pass
			finally:
				sess.print("</c>").exec()