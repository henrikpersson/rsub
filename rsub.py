import sublime, sublime_plugin
import SocketServer
import signal, os, tempfile, socket
from threading import Thread

'''
Problems:
Double line breaks on Windows.
If rmate doesn't open a file in the working dir the slashes will mess up our tempfile.
'''

SESSIONS = {}

def say(msg):
    #sublime.status_message("[rsub] " + msg)
    print '{rsub] ' + msg

class Session:
    def __init__(self, socket):
        self.env = {}
        self.file = ""
        self.file_size = 0
        self.in_file = False
        self.parse_done = False
        self.socket = socket
        self.temp_path = None
    
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
                self.env[k] = v.strip()
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
        self.socket.send("close\n")
        self.socket.send("token: " + self.env['token'] + "\n")
        self.socket.send("\n")

    def send_save(self):
        self.socket.send("save\n")
        self.socket.send("token: " + self.env['token'] + "\n")
        temp_file = open(self.temp_path, "rU")
        new_file = ""
        for line in temp_file:
            new_file += line
        temp_file.close()
        self.socket.send("data: " + str(len(new_file)) + "\n")
        self.socket.send(new_file)
        self.socket.send("\n")


    def on_done(self):
        # Create temp file
        self.temp_path = tempfile.gettempdir() + self.env['display-name'];

        temp_file = open(self.temp_path, "w+")
        temp_file.write(self.file.strip())
        temp_file.flush()
        temp_file.close()

        # Open it within sublime
        view = sublime.active_window().open_file(self.temp_path)
        SESSIONS[view.id()] = self

    def close_connection(self, view):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        del SESSIONS[view.id()]
            

class ConnectionHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        say('New connection from ' + str(self.client_address))

        session = Session(self.request)
        self.request.send("Sublime Text 2 (rsub plugin)\n")

        socket_fd = self.request.makefile()
        while True:
            line = socket_fd.readline()
            if(len(line) == 0): break
            session.parse_input(line)

        #self.request.close()
        say('Connection close..')


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
            say('Killing server...')
            server.shutdown()
            server.server_close()

    def on_post_save(self, view):
        if(SESSIONS.has_key(view.id())):
            sess = SESSIONS[view.id()]
            sess.send_save()
            say('Saved ' + sess.env['display-name'])

    def on_close(self, view):
        if(SESSIONS.has_key(view.id())):
            sess = SESSIONS[view.id()]
            sess.send_close()
            os.unlink(sess.temp_path)
            sess.close_connection(view)
            say('Closed ' + sess.env['display-name'])


# Load settings
settings = sublime.load_settings("rsub.sublime-settings")
port = settings.get("port", 52698)
host = settings.get("host", "localhost")

# Start server thread
server = TCPServer((host, port), ConnectionHandler)
Thread(target=start_server, args=[]).start()
say('Server running on ' + host + ':' + str(port) + '...')

