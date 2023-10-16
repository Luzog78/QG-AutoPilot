import modules.logger as logger
from modules.socket_utils import Socket, ServerSocket, ClientSocket


def split_command(command: str) -> list[str] | None:
	length = len(command)
	args = []
	arg = None
	separator = None
	i = 0
	while i < length:
		if arg is None:
			arg = ""
			if command[i] in " '\"":
				separator = command[i]
			else:
				arg += command[i]
				separator = " "
		else:
			if command[i] == "\\" and len(command) >= i and command[i + 1] == separator:
				arg += separator
				i += 1
			elif command[i] == separator:
				if args != "" or separator != " ":
					args.append(arg)
				arg = None
			else:
				arg += command[i]
		i += 1
	if arg is None:
		pass
	elif separator == " ":
		if args != "":
			args.append(arg)
	else:
		return None
	return args


def parse_addr(address: str) -> tuple[str, int]:
	host = address
	port = 0
	if ":" in address:
		host = "".join(address.split(":")[:-1])
		try:
			port = int(address.split(":")[-1])
		except ValueError:
			pass
	return host, port


class Command:
	def __init__(self, name: str, *aliases: str, case_sensitive: bool = False,
				 description: str | None = None, syntax: str | list[str] | None = None):
		self.aliases = [name]
		for alias in aliases:
			self.aliases.append(alias)
		self.case_sensitive = case_sensitive
		self.description = description
		self.syntax = syntax
	
	def log_usage(self):
		description = "No more information." if self.description is None else self.description
		usage = f"{self.aliases[0]} [<args...>]" if self.syntax is None else self.syntax
		if isinstance(usage, list) or isinstance(usage, tuple):
			usage = "".join(f"\n  > {line}" for line in usage)
		logger.log(
			f"Description: {description}",
			f"Usage: {usage}"
		)
	
	def handle(self, sender: Socket | None, command: str) -> bool | None:
		splitted = split_command(command)
		if splitted is None or len(splitted) == 0:
			return None
		found = False
		for alias in self.aliases:
			if self.case_sensitive:
				if splitted[0] == alias:
					found = True
					break
			else:
				if splitted[0].lower() == alias.lower():
					found = True
					break
		if not found:
			return None
		return self.execute(sender, splitted[0], list(splitted[1:]))
	
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		return True


class ServerCommand(Command):
	def __init__(self, server: ServerSocket, name: str, *aliases: str, case_sensitive=False,
				 description: str | None = None, syntax: str | list[str] | None = None):
		super().__init__(name, *aliases, case_sensitive=case_sensitive,
			description=description, syntax=syntax)
		self.server = server


class ClientCommand(Command):
	def __init__(self, client: ClientSocket, name: str, *aliases: str, case_sensitive=False,
				 description: str | None = None, syntax: str | list[str] | None = None):
		super().__init__(name, *aliases, case_sensitive=case_sensitive,
			description=description, syntax=syntax)
		self.client = client
