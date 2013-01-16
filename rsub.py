import sublime
import sublime_plugin
import SocketServer
import os
import tempfile
import socket
from threading import Thread

'''
Problems:
Double line breaks on Windows.
'''

SESSIONS = {}


def say(msg):
    print '[rsub] ' + msg


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
        if (input_line.strip() == "open" or self.parse_done is True):
            return

        if(self.in_file is False):
            input_line = input_line.strip()
            if (input_line == ""):
                return
            k, v = input_line.split(":", 1)
            if(k == "data"):
                self.file_size = int(v)
                self.in_file = True
            else:
                self.env[k] = v.strip()
        else:
            self.parse_file(input_line)

    def parse_file(self, line):
        if(len(self.file) >= self.file_size and line == ".\n"):
            self.in_file = False
            self.parse_done = True
            sublime.set_timeout(self.on_done, 0)
        else:
            self.file += line

    def close(self):
        self.socket.send("close\n")
        self.socket.send("token: " + self.env['token'] + "\n")
        self.socket.send("\n")
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        os.unlink(self.temp_path)
        os.rmdir(self.temp_dir)

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
        # Create a secure temporary directory, both for privacy and to allow
        # multiple files with the same basename to be edited at once without
        # overwriting each other.
        try:
            self.temp_dir = tempfile.mkdtemp(prefix='rsub-')
        except OSError as e:
            sublime.error_message('Failed to create rsub temporary directory! Error: %s' % e)
            return
        self.temp_path = os.path.join(self.temp_dir, os.path.basename(self.env['display-name']))
        try:
            temp_file = open(self.temp_path, "w+")
            temp_file.write(self.file[:self.file_size])
            temp_file.flush()
            temp_file.close()
        except IOError, e:
            # Remove the file if it exists.
            if os.path.exists(self.temp_path):
                os.remove(self.temp_path)
            try:
                os.rmdir(self.temp_dir)
            except OSError:
                pass

            sublime.error_message('Failed to write to temp file! Error: %s' % str(e))

        # Open it within sublime
        view = sublime.active_window().open_file(self.temp_path)
        SESSIONS[view.id()] = self

        # Bring sublime to front
        if(sublime.platform() == 'osx'):
            from ScriptingBridge import SBApplication
            subl_window = SBApplication.applicationWithBundleIdentifier_("com.sublimetext.2")
            subl_window.activate()


class ConnectionHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        say('New connection from ' + str(self.client_address))

        session = Session(self.request)
        self.request.send("Sublime Text 2 (rsub plugin)\n")

        socket_fd = self.request.makefile()
        while True:
            line = socket_fd.readline()
            if(len(line) == 0):
                break
            session.parse_input(line)

        say('Connection close.')


class TCPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True


def start_server():
    server.serve_forever()


class RSubEventListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        # Used during development to kill the server on save.
        global server
        if(os.path.basename(view.file_name()) == "rsub.py"):
            say('Killing server...')
            server.shutdown()
            server.server_close()

    def on_post_save(self, view):
        if (view.id() in SESSIONS):
            sess = SESSIONS[view.id()]
            sess.send_save()
            say('Saved ' + sess.env['display-name'])

    def on_close(self, view):
        if(view.id() in SESSIONS):
            sess = SESSIONS.pop(view.id())
            sess.close()
            say('Closed ' + sess.env['display-name'])


# Load settings
settings = sublime.load_settings("rsub.sublime-settings")
port = settings.get("port", 52698)
host = settings.get("host", "localhost")

# Start server thread
server = TCPServer((host, port), ConnectionHandler)
Thread(target=start_server, args=[]).start()
say('Server running on ' + host + ':' + str(port) + '...')
