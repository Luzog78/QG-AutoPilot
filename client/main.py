import sys
sys.path.append(sys.path[0][:sys.path[0].rfind("/")])

import threading
import modules.logger as logger
from modules.socket_utils import ClientSocket


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


def receive_thread_func():
	global server_close_order

	while not client.is_closed():
		try:

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

		except Exception as e:
			logger.log_exception(e)


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
			logger.log(f"Sending:  {inp}", flag=logger.FLAG_COMMAND)
			client.send_cmd(inp)

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
