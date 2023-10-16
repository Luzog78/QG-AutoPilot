import socket
import modules.logger as logger

BUFFER_256 = 256
BUFFER_512 = 512
BUFFER_1KB = 1024
BUFFER_10KB = 10240
BUFFER_100KB = 102400
BUFFER_1MB = 1048576
BUFFER_10MB = 10485760

BUFFER_CMD = BUFFER_256

class Socket:
	def __init__(self, sock: socket.socket = None):
		if sock is None:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		else:
			self.sock = sock
		
	def __repr__(self) -> str:
		return str(self)
	
	def __str__(self) -> str:
		return f"Socket({self.sock})"
	
	def close(self):
		self.sock.close()
	
	def is_closed(self) -> bool:
		return self.sock._closed

	def send(self, data: bytes, length: int, buffer_size: int = -1):
		if buffer_size == -1:
			buffer_size = length
		totalsent = 0
		while totalsent < length:
			sent = self.sock.send(data[totalsent:totalsent + buffer_size])
#			logger.log(f"  *** Sent {sent} bytes ***")
			if sent == 0:
				raise RuntimeError(f"Socket connection broken. Total sent: {totalsent} bytes.")
			totalsent = totalsent + sent

	def receive(self, length: int, buffer_size: int = -1):
		if buffer_size == -1:
			buffer_size = length
		chunks = []
		bytes_recd = 0
		while bytes_recd < length:
			chunk = self.sock.recv(min(length - bytes_recd, buffer_size))
			if chunk == b'':
				raise RuntimeError(f"Socket connection broken. Total received: {bytes_recd} bytes.")
			chunks.append(chunk)
			bytes_recd = bytes_recd + len(chunk)
		return b''.join(chunks)

	def send_cmd(self, cmd: str, buffer_size: int = BUFFER_CMD):
		data = cmd.encode("utf-8")
		length = len(data)
		if length < BUFFER_CMD:
			data += b'\0' * (BUFFER_CMD - length)
		self.send(data, BUFFER_CMD, buffer_size)
	
	def receive_cmd(self, buffer_size: int = BUFFER_CMD) -> str:
		data = self.receive(BUFFER_CMD, buffer_size)
		return data.decode("utf-8").rstrip('\0')
	
	def send_msg(self, msg: str, encoding: str = "utf-8", buffer_size: int = BUFFER_1KB):
		data = msg.encode(encoding)
		length = len(data)
		self.send_cmd(f"length={length}")
		self.send_cmd(f"encoding={encoding}")
		self.send(data, length, buffer_size)

	def receive_msg(self, buffer_size: int = BUFFER_1KB) -> str:
		length = int(self.receive_cmd().removeprefix("length="))
		encoding = self.receive_cmd().removeprefix("encoding=")
		data = self.receive(length, buffer_size)
		return data.decode(encoding)

	def send_file(self, file_path: str, dest_path: str, buffer_size: int = BUFFER_1MB):
		self.send_cmd(f"dest_path={dest_path}")
		length = 0
		with open(file_path, "rb") as file:
			while True:
				data = file.read(buffer_size)
				if not data:
					break
				length += len(data)
		self.send_cmd(f"length={length}")
		sent = 0
		with open(file_path, "rb") as file:
			while sent < length:
				data = file.read(buffer_size)
				if not data:
					raise RuntimeError(f"File reading error. Total sent: {sent} bytes.")
				self.send(data, len(data))
				sent += len(data)
	
	def receive_file(self, buffer_size: int = BUFFER_1MB):
		dest_path = self.receive_cmd().removeprefix("dest_path=")
		length = int(self.receive_cmd().removeprefix("length="))
		received = 0
		with open(dest_path, "wb") as file:
			while received < length:
				data = self.receive(min(length - received, buffer_size))
				if not data:
					raise RuntimeError(f"File receive error. Total received: {received} bytes.")
				file.write(data)
				received += len(data)


class ClientSocket(Socket):
	def __init__(self, sock: socket.socket = None, address: tuple[str, int] = None):
		super().__init__(sock)
		self.address = address
	
	def __str__(self):
		return f"ClientSocket(addr={self.address})"
	
	def close(self):
		self.send_cmd("quit")
		super().close()

	def connect(self, host: str, port: str):
		self.sock.connect((host, port))


class ServerSocket(Socket):
	def __init__(self, sock: socket.socket = None):
		super().__init__(sock)
		self._backlog = None
		self.clients = []

	def __str__(self):
		return f"ClientSocket(addr={self.sock.getsockname()}, backlog={self._backlog}, clients_nb={len(self.clients)}, clients={self.clients})"
	
	def close(self):
		self.sock._closed = True
		for client in self.clients:
			client.close()
		super().close()

	def bind(self, host: str, port: int):
		self.sock.bind((host, port))

	def listen(self, backlog: int):
		self.sock.listen(backlog)
		self._backlog = backlog

	def accept(self, add_to_clients: bool = True) -> ClientSocket:
		client_socket, client_address = self.sock.accept()
		client = ClientSocket(client_socket, client_address)
		if add_to_clients:
			self.clients.append(client)
		return client
