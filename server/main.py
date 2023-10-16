import sys
sys.path.append(sys.path[0][:sys.path[0].rfind("/")])

import threading
import modules.logger as logger
from modules.socket_utils import ServerSocket, ClientSocket


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

	except Exception as e:
		logger.log_exception(e)


def input_thread_func():
	try:

		while not server.is_closed():
			inp = input()
			if server.is_closed():
				break
			if not inp:
				continue

			if inp == "quit":
				host, port = server.sock.getsockname()
				server.close()
				closing_client = ClientSocket()
				closing_client.connect(host, port)
				break

			elif inp.startswith("broadcast "):
				broadcast = inp.removeprefix("broadcast ")
				logger.log(f"Broadcasting to {len(server.clients)} clients:  {broadcast}")
				for client in server.clients:
					logger.log(f"  > Sending to {client.address}:  {broadcast}", flag=logger.FLAG_COMMAND)
					client.send_cmd(broadcast)
				logger.log()

			elif inp.startswith("info"):
				logger.log("Server is running...",
					f"  > Host: {server.sock.getsockname()[0]}",
					f"  > Port: {server.sock.getsockname()[1]}",
					f"  > Link: http://{server.sock.getsockname()[0]}:{server.sock.getsockname()[1]}/",
					f"  > Backlog: {server._backlog}",
					f"  > Clients: {len(server.clients)}",
					"")

			elif inp.startswith("clients"):
				logger.log(f"Clients ({len(server.clients)}):")
				for client in server.clients:
					logger.log(f"  > {client.address}")
				logger.log()

			else:
				logger.log(f"Command not found:  {inp}", flag=logger.FLAG_ERROR)

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
