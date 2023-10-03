from collections import UserDict
from typing import Any

class RegisteredItems(UserDict):
	def register(self, name: str, item: Any):
		self.data[name] = item

	def __getattr__(self, attr: str) -> Any:
		try:
			return self.data[attr]
		except KeyError as e:
			raise AttributeError(f"No item found with name \"{attr}\"") from e