import sys
sys.path.append(sys.path[0][:sys.path[0].rfind("/")])

import threading
import modules.logger as logger
from modules.socket_utils import ServerSocket, ClientSocket, Socket
from modules.command_utils import ServerCommand, Command, parse_addr


server = ServerSocket()
server.bind("", 1234)
server.listen(5)

logger.log_embed("Server is running...",
	f"  > Host: {server.sock.getsockname()[0]}",
	f"  > Port: {server.sock.getsockname()[1]}",
	f"  > Link: http://{server.sock.getsockname()[0]}:{server.sock.getsockname()[1]}/",
	f"  > Backlog: {server._backlog}",
	f"  > Clients: {len(server.clients)}",
	before=[], after=["", ""])


class HelpCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		logger.log(f"Available commands ({len(commands)}):")
		for command in commands:
			logger.log(f"  > {command.aliases[0]}: {command.description}")
		return True


class BroadcastCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		if len(args) == 0:
			logger.log("Error: Parameter '<command...>' is missing.", flag=logger.FLAG_ERROR)
			return False
		exceptions = []
		broadcast = " ".join(args)
		logger.log(f"Broadcasting to {len(server.clients)} clients:  {broadcast}")
		for client in server.clients:
			logger.log(f"  > Sending to {client.address}:  {broadcast}", flag=logger.FLAG_COMMAND)
			try:
				client.send_cmd(broadcast)
			except Exception as e:
				logger.log(f"  ### Fail. (See ERRO:{len(exceptions)}) ###", flag=logger.FLAG_ERROR)
				exceptions.append(e)
		if len(exceptions) > 0:
			logger.log()
		for i, e in enumerate(exceptions):
			logger.log_exception(e, f"Failings  -  ERRO:{i}", before=[])
		return True


class InfoCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		logger.log("Server is running...",
			f"  > Host: {server.sock.getsockname()[0]}",
			f"  > Port: {server.sock.getsockname()[1]}",
			f"  > Link: http://{server.sock.getsockname()[0]}:{server.sock.getsockname()[1]}/",
			f"  > Backlog: {server._backlog}",
			f"  > Clients: {len(server.clients)}")
		return True


class ListCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		logger.log(f"Clients ({len(server.clients)}):")
		for client in server.clients:
			logger.log(f"  > {client.address}")
		return True


class SendCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		if len(args) == 0:
			logger.log("Error: Parameter '<address>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 1:
			logger.log("Error: Parameter '<command...>' is missing.", flag=logger.FLAG_ERROR)
			return False
		address = parse_addr(args[0])
		command = "".join(args[1:])
		client: ClientSocket = None
		for c in server.clients:
			if c.address == address:
				client = c
				break
		if client is None:
			logger.log(f"Error: Client {address} not found.", flag=logger.FLAG_ERROR)
			return False
		logger.log(f"Sending to {address}:  {command}", flag=logger.FLAG_COMMAND)
		try:
			client.send_cmd(command)
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		return True


commands: list[Command] = [
	HelpCommand(server, "help", "?",
		description="Display all available commands", syntax="help"),
	BroadcastCommand(server, "broadcast", "bc",
		description="Send command to all clients",
		syntax="broadcast <command...>"),
	InfoCommand(server, "info", "infos",
		description="Display information about the server",
		syntax="info"),
	ListCommand(server, "list", "clients",
		description="Display the client list",
		syntax="info"),
	SendCommand(server, "send",
		description="Send command to someone",
		syntax="send <address> <command...>"),
]


def incoming_thread_func():
	while not server.is_closed():
		try:

			client = server.accept(add_to_clients=False)
			if server.is_closed():
				continue
			server.clients.append(client)
			logger.log(f"Connection accepted from {client.address}.", flag=logger.FLAG_LINK)
			client.send_msg(">>> Welcome to the server! <<<")
			threading.Thread(target=client_thread_func, args=(client,)).start()

		except ConnectionResetError as e:
			logger.log_exception(e)
		except BrokenPipeError as e:
			logger.log_exception(e)
		except Exception as e:
			logger.log_exception(e)


def client_thread_func(client: ClientSocket):
	try:

		while not server.is_closed():
			cmd = client.receive_cmd()
			if not server.is_closed():
				logger.log(f"Received from {client.address}:  {cmd}", flag=logger.FLAG_COMMAND)
			if cmd == "quit":
				server.clients.remove(client)
				if not server.is_closed():
					logger.log(f"Connection closed from {client.address}.", flag=logger.FLAG_LINK)
				try:
					client.send_cmd("end")
				except Exception:
					pass
				break
			else:
				command_found = False
				for command in commands:
					result = command.handle(client, cmd)
					if result is not None:
						command_found = True
						break
				if not command_found:
					logger.log(f"Command not found:  {cmd}", flag=logger.FLAG_ERROR)

	except Exception as e:
		logger.log_exception(e)


def input_thread_func():
	try:

		while not server.is_closed():
			cmd = input()
			if server.is_closed():
				break
			if not cmd:
				continue

			if cmd == "quit":
				host, port = server.sock.getsockname()
				server.close()
				closing_client = ClientSocket()
				closing_client.connect(host, port)
				break
			else:
				command_found = False
				for command in commands:
					result = command.handle(None, cmd)
					if result is not None:
						command_found = True
						break
				if not command_found:
					logger.log(f"Command not found:  {cmd}", flag=logger.FLAG_ERROR)

	except Exception as e:
		logger.log_exception(e)


incoming_thread = threading.Thread(target=incoming_thread_func)
input_thread = threading.Thread(target=input_thread_func)

try:

	incoming_thread.start()
	input_thread.start()

	incoming_thread.join()
	input_thread.join()

except KeyboardInterrupt:
	logger.log_embed("Keyboard interrupt. Closing client...",
		"Press enter to close...", flag=logger.FLAG_ERROR)

else:
	logger.log_embed("Closing server...", flag=logger.FLAG_ERROR)

server.close()
