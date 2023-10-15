import sys
sys.path.append(sys.path[0][:sys.path[0].rfind("/")])

import traceback
import threading
from modules.socket_utils import ClientSocket


client = ClientSocket()
try:
	client.connect("", 1234)
except ConnectionRefusedError:
	print("Connection refused.")
	sys.exit(1)
server_close_order = False

print(client.receive(22).decode("utf-8"))


def receive_thread_func():
	global server_close_order

	while not client.is_closed():
		try:

			cmd = client.receive_cmd()
			if not cmd:
				break
			print(f"Received command '{cmd}'.")
			if cmd == "quit":
				server_close_order = True
				client.close()
				print()
				print()
				print("#####################################")
				print("Server order. Closing client...")
				print("Press enter to close...")
				print("#####################################")
				break

		except Exception as e:
			print()
			print()
			print("#####################################")
			print(f"[Exception occured] {e.__class__.__name__}: '{e}'.")
			print()
			traceback.print_exc()
			print("#####################################")


def input_thread_func():
	while not client.is_closed():
		try:

			inp = input()
			if client.is_closed():
				break
			if not inp:
				continue
			if inp == "quit":
				client.close()
				break
			client.send_cmd(inp)

		except Exception as e:
			print()
			print()
			print("#####################################")
			print(f"[Exception occured] {e.__class__.__name__}: '{e}'.")
			print()
			traceback.print_exc()
			print("#####################################")


receive_thread = threading.Thread(target=receive_thread_func)
input_thread = threading.Thread(target=input_thread_func)

try:

	receive_thread.start()
	input_thread.start()

	receive_thread.join()
	input_thread.join()

except KeyboardInterrupt:
	print()
	print()
	print("#####################################")
	print("Keyboard interrupt. Closing client...")
	print("Press enter to close...")
	print("#####################################")

else:
	if not server_close_order:
		print()
		print()
		print("#####################################")
		print("Closing client...")
		print("#####################################")

if not client.is_closed():
	client.close()
