from collections import UserList
import dag



class InputObjects(UserList):
	def execute(self, hookname, *args, _inputobj_execution_breaker = None, **kwargs):
		_breaker = _inputobj_execution_breaker or (lambda x: False)
		prioritylist = {}

		for obj in self.data:
			#breakpoint(hookname == "filter_icresponse")
			if hookname in dir(obj):
				hookfn = getattr(obj, hookname)
				priority = getattr(hookfn, "priority", 10)

				prioritylist.setdefault(float(priority), []).append(hookfn)

		prioritylist = {k: prioritylist[k] for k in sorted(prioritylist, reverse = True)}

		for prioritylevel, hookfns in prioritylist.items():
			for hookfn in hookfns:
				response = hookfn(*args, **kwargs)
				if _breaker(response):
					return response



class InputObject(dag.dot.DotProxy):
	name = ""
	
	def __init__(self, obj = dag.UnfilledArg):
		self.obj = self

		if obj is not dag.UnfilledArg:
			super().__init__(obj)
			self.obj = obj



class InputIdentifier(InputObject):
	def __init__(self, identifier):
		super().__init__(identifier)
		self.identifier = identifier


	def __repr__(self):
		return dag.format(f"<c bg-#620 black / InputIdentifier:>\n\t{self.identifier}\n<c bg-#620 black / /InputIdentifier>")