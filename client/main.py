import sys
sys.path.append(sys.path[0][:sys.path[0].rfind("/")])

import os
import json
import threading
import modules.logger as logger
from modules.socket_utils import Socket, ClientSocket
from modules.command_utils import Command, ClientCommand


client = ClientSocket()
try:
	client.connect("", 1234)
except ConnectionRefusedError:
	logger.log("Connection refused.", "Aborting.", flag=logger.FLAG_ERROR)
	sys.exit(1)
server_close_order = False

logger.log_embed(f"Connected as {client.sock.getsockname()},",
				 f" to {client.sock.getpeername()}",
				 before=[], after=["", ""])

logger.log(client.receive_msg(), "")


config = {
	"sd-path": "/home/luzog/Desktop/QG Workspace/stable-diffusion-webui",
	"sd-port": 9876,
}


class HelpCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		logger.log(f"Available commands ({len(commands)}):")
		for command in commands:
			logger.log(f"  > {command.aliases[0]}: {command.description}")
		return True


class InfoCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		logger.log("Server is running...",
			f"  > Host: {self.server.sock.getsockname()[0]}",
			f"  > Port: {self.server.sock.getsockname()[1]}",
			f"  > Link: http://{self.server.get_llink()}/",
			f"  > Backlog: {self.server._backlog}",
			f"  > Clients: {len(self.server.clients)}")
		return True


class SendCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		if len(args) == 0:
			logger.log("Error: Parameter '<command...>' is missing.", flag=logger.FLAG_ERROR)
			return False
		command = "".join(args)
		logger.log(f"Sending:  {command}", flag=logger.FLAG_COMMAND)
		try:
			self.client.send_cmd(command)
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		return True


class FileTransferCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		if len(args) == 0:
			logger.log("Error: Parameter '<src_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 1:
			logger.log("Error: Parameter '<dst_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		src_path = args[0]
		dst_path = args[1]
		logger.log(f"Sending file:",
			 f"  from {self.client.sock.getsockname()}:  {src_path}",
			 f"  to {self.client.sock.getpeername()}:  {dst_path}", flag=logger.FLAG_COMMAND)
		try:
			client.send_cmd("filereceive")
			client.send_file(src_path, dst_path)
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		return True


class FileReceiveCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		try:
			result = self.client.receive_file()
			logger.log(f"Received file:  {result[0]} ({result[1]} bytes)")
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		except KeyboardInterrupt:
			logger.log("Command exited.")
			return False
		return True


class ConfigCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		if len(args) == 0:
			logger.log("Error: Parameter 'all | list | <key>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if args[0] == "all":
			logger.log(f"Current config:")
			dumped = json.dumps(config, indent=2)
			for line in dumped.split("\n"):
				logger.log(line)
			return True
		if args[0] == "list":
			logger.log("Available config keys:")
			for key in config:
				logger.log(f"  > {key}")
			return True
		if args[0] not in config:
			logger.log(f"Error: Unknown key '{args[0]}'.", flag=logger.FLAG_ERROR)
			return False
		key = args[0]
		if len(args) > 1:
			value = args[1] if len(args) > 1 else None
			logger.log(f"Setting config:",
				f"  key: {key}",
				f"  value: {value}")
			config[key] = value
		else:
			logger.log(f"Current config:",
				f"  key: {key}",
				f"  value: {config[key]}")
		return True


class LaunchCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		logger.log(f"Launching stable-diffusion...")
		os.system(f"gnome-terminal -- sh '/home/luzog/Desktop/QG Workspace/QG-AutoPilot/client/launch.sh' '{config['sd-path']}' --port {config['sd-port']} --api")
		return True


class SendCommand(ClientCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		if len(args) == 0:
			logger.log("Error: Parameter '<command...>' is missing.", flag=logger.FLAG_ERROR)
			return False
		cmd = ""
		for arg in args:
			cmd += "'" + arg.replace("'", "\'") + "'"
		try:
			logger.log(f"Sending:  {cmd}", flag=logger.FLAG_COMMAND)
			self.client.send_cmd(cmd)
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		return True


commands: list[Command] = [
	HelpCommand(client, "help", "?",
		description="Display all available commands", syntax="help"),
	InfoCommand(client, "info", "infos",
		description="Display information about the client",
		syntax="info"),
	SendCommand(client, "send",
		description="Send command to server",
		syntax="send <command...>"),
	FileTransferCommand(client, "filesend", "fs",
		description="Transfer file to server",
		syntax="filesend <src_path> <dst_path>"),
	FileReceiveCommand(client, "filereceive", "fr",
		description="Waiting for file from server",
		syntax="filereceive"),
	ConfigCommand(client, "config", "c",
		description="Set config value",
		syntax=["config all","config list", "config <key> [<value>]"]),
	LaunchCommand(client, "launch", "l",
		description="Launch stable-diffusion",
		syntax="launch"),
	SendCommand(client, "send", "s",
		description="Send command to server",
		syntax="send <command...>"),
]


def receive_thread_func():
	global server_close_order

	try:
		while not client.is_closed():

			cmd = client.receive_cmd()
			if not cmd or cmd == "end":
				break
			logger.log(f"Received:  {cmd}", flag=logger.FLAG_COMMAND)
			if cmd == "quit":
				server_close_order = True
				client.close()
				logger.log_embed("Server order. Closing client...",
					"Press enter to close...", flag=logger.FLAG_ERROR)
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
	while not client.is_closed():
		try:

			cmd = input()
			if client.is_closed():
				break
			if not cmd:
				continue
			if cmd == "quit":
				client.close()
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


receive_thread = threading.Thread(target=receive_thread_func)
input_thread = threading.Thread(target=input_thread_func)

try:

	receive_thread.start()
	input_thread.start()

	receive_thread.join()
	input_thread.join()

except KeyboardInterrupt:
	logger.log_embed("Keyboard interrupt. Closing client...",
		"Press enter to close...", flag=logger.FLAG_ERROR)

else:
	if not server_close_order:
		logger.log_embed("Closing client...", flag=logger.FLAG_ERROR)

if not client.is_closed():
	client.close()
