observables = {}


def is_observable_registered(observable):
	return observable in observables

def register_observable(observable):
	observables[observable] = []



class Observer:
	def __init__(self, observable):
		global observables

		if not is_observable_registered(observable):
			register_observable(observable)
			self.__process_observable(observable)

		observables[observable].append(self)



	def __notify(self, name, item):
		pass



def make_method_observable(observable, methodname):
	oldmethod = getattr(observable, methodname)
	def newmethod(self, name, value):
		for observer in observables[observable]:
			observer.__notify(name, value)

		oldmethod(name, value)

	setattr(observable, methodname, newmethod)




class AttrObserver(Observer):
	def __process_observable(self, observable):
		make_method_observable(observable, "__setattr__")




class IdxObserver(Observer):
	def __process_observable(self, observable):
		make_method_observable(observable, "__setidx__")