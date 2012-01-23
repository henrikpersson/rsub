import sublime, sublime_plugin
import SocketServer
import signal, os, tempfile
from threading import Thread

''' RECAP: view.set_name crashes when opened with a file. Test without tempfile? Other way to set name? '''

class Session:
	def __init__(self, socket):
		self.env = {}
		self.file = ""
		self.file_size = 0
		self.in_file = False
		self.parse_done = False
		self.socket = socket
		self.tmp_file = None
	
	def parse_input(self, input_line):
		if(input_line.strip() == "open" or self.parse_done == True): return

		if(self.in_file == False):
			input_line = input_line.strip()
			if(input_line == ""): return
			k, v = input_line.split(":", 1)
			if(k == "data"):
				self.file_size = int(v)
				self.in_file = True
			else:
				self.env[k] = v
		else:
			self.parse_file(input_line)

	def parse_file(self, line):
		if(len(self.file) > self.file_size and line == ".\n"):
			self.in_file = False
			self.parse_done = True
			sublime.set_timeout(self.on_done, 0)
		else:
			self.file += line
	
	def send_close(self):
		self.socket.send("close\r\n")
		self.socket.send("token: " + self.env['token'] + "\r\n")
		self.socket.send("\r\n")

	def send_save(self):
		self.socket.send("save\r\n")
		self.socket.send("token: " + self.env['token'] + "\r\n")
		self.socket.send("data: " + str(self.file.__len__()) + "\r\n")
		self.socket.send(self.file)
		self.socket.send("\r\n")

	def on_done(self):
		# Create temp file
		self.tmp_file = tempfile.NamedTemporaryFile()

		print '[rsub] Temp name: ' + self.tmp_file.name

		# Open it within sublime
		view = sublime.active_window().open_file(self.tmp_file.name)
		#view.set_name(self.env['display-name'])
		view.set_name('koko')
			

class ConnectionHandler(SocketServer.BaseRequestHandler):
	def handle(self):
		print '[rsub] New connection from ' + str(self.client_address)

		session = Session(self.request)
		self.request.send("Sublime Text 2 (rsub plugin)\r\n")

		socket_fd = self.request.makefile()
		while True:
			line = socket_fd.readline()
			if(len(line) == 0): break
			session.parse_input(line)

		self.request.close()
		print '[rsub] Connection close..'


class TCPServer(SocketServer.ThreadingTCPServer):
	allow_reuse_address = True


def start_server():
	server.serve_forever()


class RSubEventListener(sublime_plugin.EventListener):
	def on_pre_save(self, view):
		# Used during development to kill the server on save.
		# TODO: How do we kill the server live?
		global server
		if(os.path.basename(view.file_name()) == "rsub.py"):
			print '[rsub] Killing server...'
			server.shutdown()
			server.server_close()

##### Main #####

# Load settings
settings = sublime.load_settings("rsub.sublime-settings")
port = settings.get("port", 4444)
host = settings.get("host", "localhost")

# Start server thread
server = TCPServer((host, port), ConnectionHandler)
Thread(target=start_server, args=[]).start()
print '[rsub] Server running on port ' + host + ':' + str(port) + '...'

