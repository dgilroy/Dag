import pytest

from dag.lib import registration_table


internal_data = {"hi": "bye", "dog": "cat", "wow": 5.1}

class MockObj:
	def __init__(self):
		self.internal_data = internal_data


@pytest.fixture
def rt():
	return registration_table.RegistrationTable

