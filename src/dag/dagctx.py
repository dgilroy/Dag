from dag.lib import dot

class _DagCtx(dot.DotNone):
	_instance = None
	

	@staticmethod
	def get_instance():
		""" Static access method. """
		if _DagCtx._instance == None:
			_DagCtx()
		return _DagCtx._instance 

		
	def __init__(self):
		if _DagCtx._instance is None:
			_DagCtx._instance = self

		self.dag = None
			
		
	def get(self, attr, default = None):
		return getattr(self, attr, default)

		
DagCtx = _DagCtx.get_instance()




class DagCtxManager:
	def __init__(self, dagctx = None, **kwargs):
		self.dagctx = dagctx or DagCtx
		self.settings = kwargs
		
	def __enter__(self):
		for setting, value in self.settings.items():
			old_value = getattr(self.dagctx, setting)
			setattr(self.dagctx, setting, value)
			self.settings[setting] = old_value

	def __exit__(self, type, value, traceback):
		for setting, value in self.settings.items():
				setattr(self.dagctx, setting, value)