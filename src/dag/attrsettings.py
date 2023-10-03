import copy

import dag



class SetSettingsAttr:
	def __init__(self, settings):
		self.settings = settings

	def __get__(self, obj, cls):
		try:
			newobj = copy.copy(obj) # Done this way so that "dag.get.CACHE(url) works. 
		except:
			newobj = obj
			
		newobj.settings |= self.settings
		return newobj



class AttrSettable:
	def __init__(self, **settings):
		self.settings = dag.DotDict(settings)


	def set_settings_attr(self, attrname, settingname, value, default = dag.UnfilledArg, is_create_no = True):
		# Creates setting so iomethod.ATTRNAME makes iomethod.kwargs.settingname = value
		setattr(type(self), attrname, SetSettingsAttr({settingname: value}))

		# Creates setting so iomethod.NOATTRNAME undoes iomethod.ATTRNAME
		if is_create_no:
			default = default if default is not dag.UnfilledArg else not value
			setattr(type(self), "NO_" + attrname, SetSettingsAttr({settingname: default}))


	def set_settings_attr_dict(self, attrname, settings):
		setattr(type(self), attrname, SetSettingsAttr(settings))