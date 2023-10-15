import sys
sys.path.append(sys.path[0][:sys.path[0].rfind("/")])

import traceback
import threading
from modules.socket_utils import ServerSocket, ClientSocket


server = ServerSocket()
server.bind("", 1234)
server.listen(5)


print("#####################################")
print("Server is running...")
print("  > Host:", server.sock.getsockname()[0])
print("  > Port:", server.sock.getsockname()[1])
print("  > Backlog:", server._backlog)
print("#####################################")
print()
print()

def incoming_thread_func():
	while not server.is_closed():
		try:

			client = server.accept(add_to_clients=False)
			if server.is_closed():
				continue
			server.clients.append(client)
			print(f"Connection accepted from {client.address}.")
			client.send(bytes("Welcome to the server!", "utf-8"), 22)
			threading.Thread(target=client_thread_func, args=(client,)).start()

		except Exception as e:
			print()
			print()
			print("#####################################")
			print(f"[Exception occured] {e.__class__.__name__}: '{e}'.")
			print("Closing server...")
			print()
			traceback.print_exc()
			print("#####################################")


def client_thread_func(client: ClientSocket):
	try:

		while not server.is_closed():
			cmd = client.receive_cmd()
			if not server.is_closed():
				print(f"Received command '{cmd}' from {client.address}.")
			if cmd == "quit":
				server.clients.remove(client)
				if not server.is_closed():
					print(f"Connection closed from {client.address}.")
				try:
					client.send_cmd("end")
				except Exception:
					pass
				break

	except Exception as e:
		print()
		print()
		print("#####################################")
		print(f"[Exception occured] {e.__class__.__name__}: '{e}'.")
		print("Closing server...")
		print()
		traceback.print_exc()
		print("#####################################")


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
				for client in server.clients:
					client.send_cmd(broadcast)

			elif inp.startswith("info"):
				print("Server is running...")
				print("  > Host:", server.sock.getsockname()[0])
				print("  > Port:", server.sock.getsockname()[1])
				print("  > Backlog:", server._backlog)

			elif inp.startswith("clients"):
				print(f"Clients ({len(server.clients)}):")
				for client in server.clients:
					print(f"  > {client.address}")

			else:
				print(f"Received input '{inp}'.")

	except Exception as e:
		print()
		print()
		print("#####################################")
		print(f"[Exception occured] {e.__class__.__name__}: '{e}'.")
		print("Closing server...")
		print()
		traceback.print_exc()
		print("#####################################")


incoming_thread = threading.Thread(target=incoming_thread_func)
input_thread = threading.Thread(target=input_thread_func)

try:

	incoming_thread.start()
	input_thread.start()

	incoming_thread.join()
	input_thread.join()

except KeyboardInterrupt:
	print()
	print()
	print("#####################################")
	print("Keyboard interrupt. Closing server...")
	print("Press enter to close...")
	print("#####################################")

else:
	print()
	print()
	print("#####################################")
	print("Closing server...")
	print("#####################################")

server.close()
