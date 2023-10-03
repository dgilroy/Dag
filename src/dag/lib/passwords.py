import secrets, string, random

def generate_password(length: int = 17, spchars: str = "!@#$%^&:~+-_.") -> str:
	if length < 1:
		return ""

	spchar_pos = 0
	spchar = ""

	if spchars:
		spchar_pos = random.randrange(length)
		spchar = secrets.choice(spchars)
	if not spchars:
		length += 1

	# printing lowercase
	letters = string.ascii_letters + string.digits + spchars
	pw = secrets.choice(string.ascii_letters) + ''.join(secrets.choice(letters) for i in range(length-2))
	return pw[:spchar_pos] + spchar + pw[spchar_pos:]
