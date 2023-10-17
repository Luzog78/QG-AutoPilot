import sys
sys.path.append(sys.path[0][:sys.path[0].rfind("/")])

import threading
import modules.logger as logger
from modules.socket_utils import Socket, ServerSocket, ClientSocket
from modules.command_utils import Command, ServerCommand, parse_addr
from modules.video_utils import crop_video, join_video, FOURCC_MP4, FOURCC_MOV, FOURCC_XVID


server = ServerSocket()
server.bind("", 1234)
server.listen(5)

logger.log_embed("Server is running...",
	f"  > Host: {server.sock.getsockname()[0]}",
	f"  > Port: {server.sock.getsockname()[1]}",
	f"  > Link: http://{server.get_llink()}/",
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
		logger.log(f"Broadcasting to {len(self.server.clients)} clients:  {broadcast}")
		for client in self.server.clients:
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
			f"  > Host: {self.server.sock.getsockname()[0]}",
			f"  > Port: {self.server.sock.getsockname()[1]}",
			f"  > Link: http://{self.server.get_llink()}/",
			f"  > Backlog: {self.server._backlog}",
			f"  > Clients: {len(self.server.clients)}")
		return True


class ListCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		logger.log(f"Clients ({len(self.server.clients)}):")
		for client in self.server.clients:
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
		for c in self.server.clients:
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


class FileTransferCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		if len(args) == 0:
			logger.log("Error: Parameter '<address>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 1:
			logger.log("Error: Parameter '<src_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 2:
			logger.log("Error: Parameter '<dst_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		address = parse_addr(args[0])
		src_path = args[1]
		dst_path = args[2]
		client: ClientSocket = None
		for c in self.server.clients:
			if c.address == address:
				client = c
				break
		if client is None:
			logger.log(f"Error: Client {address} not found.", flag=logger.FLAG_ERROR)
			return False
		logger.log(f"Sending file:",
			 f"  from {self.server.sock.getsockname()}:  {src_path}",
			 f"  to {address}:  {dst_path}", flag=logger.FLAG_COMMAND)
		try:
			client.send_cmd("filereceive")
			client.send_file(src_path, dst_path)
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		return True


class FileReceiveCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		try:
			result = self.server.receive_file()
			logger.log(f"Received file:  {result[0]} ({result[1]} bytes)")
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		except KeyboardInterrupt:
			logger.log("Command exited.")
			return False
		return True


class VideoCropCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		codec = FOURCC_MP4
		for i in range(len(args) - 1):
			if args[i].lower() == "-c":
				codec = args[i + 1]
				args.pop(i)
				args.pop(i + 1)
				break
		if codec == "-mp4":
			codec = FOURCC_MP4
		elif codec == "-mov":
			codec = FOURCC_MOV
		elif codec == "-xvid":
			codec = FOURCC_XVID
		if len(args) == 0:
			logger.log("Error: Parameter '<src_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 1:
			logger.log("Error: Parameter '<dst_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 2:
			logger.log("Error: Parameter '<from_frame>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 3:
			logger.log("Error: Parameter '<to_frame>' is missing.", flag=logger.FLAG_ERROR)
			return False
		src_path = args[0]
		dst_path = args[1]
		from_frame = args[2]
		try:
			from_frame = int(from_frame)
		except ValueError:
			logger.log("Error: Parameter '<from_frame>' is incorrect.", flag=logger.FLAG_ERROR)
			return False
		to_frame = args[3]
		try:
			to_frame = int(to_frame)
		except ValueError:
			logger.log("Error: Parameter '<to_frame>' is incorrect.", flag=logger.FLAG_ERROR)
			return False
		logger.log(f"Cropping vido",
			 f"  from path:  {src_path}",
			 f"  to path:  {dst_path}",
			 f"  frames: {from_frame} to {to_frame}")
		try:
			crop_video(src_path, dst_path, codec, from_frame, to_frame)
		except Exception as e:
			logger.log_exception(e, before=[], after=[])
			return False
		return True


class VideoJoinCommand(ServerCommand):
	def execute(self, sender: Socket | None, label: str, args: list[str]) -> bool:
		if len(args) > 0 and (args[0] == "?" or args[0].lower() == "help"):
			self.log_usage()
			return True
		codec = FOURCC_MP4
		for i in range(len(args) - 1):
			if args[i].lower() == "-c":
				codec = args[i + 1]
				args.pop(i)
				args.pop(i + 1)
				break
		if codec == "-mp4":
			codec = FOURCC_MP4
		elif codec == "-mov":
			codec = FOURCC_MOV
		elif codec == "-xvid":
			codec = FOURCC_XVID
		if len(args) == 0:
			logger.log("Error: Parameter '<srcs_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		if len(args) == 1:
			logger.log("Error: Parameter '<dst_path>' is missing.", flag=logger.FLAG_ERROR)
			return False
		srcs_path = args[:-1]
		dst_path = args[-1]
		logger.log(f"Joining video",
			 f"  from path:  {srcs_path}",
			 f"  to path:  {dst_path}")
		try:
			join_video(srcs_path, dst_path, codec)
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
		description="Send command to client",
		syntax="send <address> <command...>"),
	FileTransferCommand(server, "filesend", "fs",
		description="Transfer file to client",
		syntax="filesend <address> <src_path> <dst_path>"),
	FileReceiveCommand(server, "filereceive", "fr",
		description="Waiting for file from clients",
		syntax="filereceive"),
	VideoCropCommand(server, "videocrop", "vc",
		description="Crop video by frame",
		syntax=[
			"videocrop <src_path> <dst_path> <from_frame> <to_frame> [-c <codec>]",
			"Codec can be: -mp4, -mov, -xvid, or <custom_codec>",
			f"Default codec: '{FOURCC_MP4}'"
		]),
	VideoJoinCommand(server, "videojoin", "vj",
		description="Join videos",
		syntax=[
			"videojoin <srcs_path...> <dst_path> [-c <codec>]",
			"Codec can be: -mp4, -mov, -xvid, or <custom_codec>",
			f"Default codec: '{FOURCC_MP4}'"
		]),
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
