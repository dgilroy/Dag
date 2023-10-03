import uuid
import dag

class DagUUID(uuid.UUID):
	def __init__(self, text = ""):
		if isinstance(text, uuid.UUID):
			text = text.hex

		with dag.catch() as e:
			return super().__init__(text)


	def __hash__(self):
		return hash(self.hex)


	def _dag_resource_repr(self):
		return f"<c #800 / {super().__str__()}>"


	def _dag_filt_value(self, operator, other):
		selfvalue = self

		if isinstance(other, int):
			other = str(other)

		if isinstance(other, str):
			selfvalue = str(self)

		return operator(selfvalue, other)


def uuid4():
	 	id = uuid.uuid4()
	 	return DagUUID(id)


@dag.oninit
def _():
	@dag.cmd("uuid4")
	def _uuid4():
		return uuid4()