import base64

class B64:
	"""
	A method-class containing simple b64 encode/decode functions
	"""

	def decode(text: str, codec: str = "utf-8") -> str:
		"""
		Takes a b64-encoded text and decodes it into a string

		:param text: The b64 text to decode
		:param codec: The coded via which the text should be decoded
		:returns: The b64-text decoded into a normal string
		"""

		return base64.b64decode(bytes(text, codec)).decode(codec)


	def encode(text: str, codec: str = "utf-8") -> str:
		"""
		Takes a given text and encodes into b64

		:param text: The text to encode into b64
		:param codec: The codec of the string being encoded
		:returns: The string encoded into b64
		"""

		return str(base64.b64encode(bytes(text, codec)), codec)
