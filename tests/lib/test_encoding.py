import base64
import pytest

from dag.lib import encoding

@pytest.fixture
def b64():
	return encoding.B64


class TestB64:
	TESTSTR = "TEXT"
	TEST_CODEC = "utf-8"
	TEST_ENCODED = str(base64.b64encode(bytes(TESTSTR, TEST_CODEC)), TEST_CODEC)

	def test_b64_encode(self, b64):
		ecoded = b64.encode(self.TESTSTR)
		assert encoded == self.TEST_ENCODED
		assert isinstance(encoded, str)

		with pytest.raises(ValueError):
			b64.encode(self.TESTSTR, "INVALID_CODEC")

	def test_b64_encode(self, b64):
		decoded = b64.decode(self.TEST_ENCODED)
		assert decoded == self.TESTSTR

		with pytest.raises(LookupError):
			b64.decode(self.TEST_ENCODED, "INVALID_CODEC")