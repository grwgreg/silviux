# See ":help channel-demo" in vim, based on $VIMRUNTIME/tools/demoserver.py
#
# Server that will accept connections from a Vim channel.
# Run this server and then in Vim you can open the channel:
#  :let handle = ch_open('localhost:8765')
#
# Then Vim can send requests to the server:
#  :let response = ch_sendexpr(handle, 'hello!')
#
# This requires Python 2.6 or later.


import json
import socket
import sys
import os
import threading
import time
import queue
import time
import yaml
from subprocess import Popen, PIPE, call
import logging

logger = logging.getLogger(__name__)

try:
    # Python 3
    import socketserver
    logger.debug('in python 3')
except ImportError:
    # Python 2
    import socketserver as socketserver
    logger.debug('in python 2')

_vim_server = None
def VimServer():
    global _vim_server
    if (not _vim_server):
        _vim_server = _VimServer()
    return _vim_server

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        logger.info("=== vim socket opened ===")
        global _vim_server
        _vim_server.thesocket = self.request

        _vim_server.thesocket.sendall('["call", "Animate", []]'.encode('utf-8'))
        while True:
            try:
                logger.debug('vim server while loop waiting on data')
                data = self.request.recv(4096).decode('utf-8')
            except socket.error:
                logger.exception("=== vim socket error ===")
                break
            except IOError:
                logger.exception("=== vim socket closed ===")
                break
            if data == '':
                logger.warning("=== vim socket closed ===")
                break
            try:
                decoded = json.loads(data)
                logger.info('vim server handle got data: %s', decoded)
                #First value is sequence number
                #When we send to vim server it echoes the seq number back to us
                #So -1 means we sent it so put on internal queue so we can handle from within _VimServer
                #Other values were initialized by vim so pass along to the main loop queue
                if decoded[0] == -1:
                    _vim_server.internal_q.put(decoded[1])
                elif _vim_server.main_loop_q:
                    _vim_server.main_loop_q.put(decoded[1])
                else:
                    logger.error('vim server got msg but no queue')

            except ValueError:
                logger.exception("vim server json decoding failed")

        #if we get here, the vim window was probably closed or something closed the channel
        #TODO probably shouldn't let this fail silently, might end up blocking main loop waiting for vim response that will never come...
        logger.warning('vim server connection closed')
        _vim_server.thesocket = None

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

#Sorry, this is super hacky and was made as an experiment
#registers would be real easy to implement as just a dict in memory that gets saved as a json file or something
#and for sending msgs to the main loop, silviux now listens on UDP so the 2 way tcp connection isn't really necessary
#TODO consider replacing
class _VimServer():
    def start_vim_server(self, q):
        self.main_loop_q = q
        self.internal_q = queue.Queue()
        self.thesocket = None
        self.wid = None

        conf = {}
        with open('./silviux/config/silviux.yaml') as f:
            conf = yaml.safe_load(f)

        HOST, PORT = conf['vim']['host'], conf['vim']['port']

        #https://docs.python.org/2/library/socketserver.html
        #set reuse_address, socket.SO_REUSEADDR
        ThreadedTCPServer.allow_reuse_address = True
        server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
        ip, port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)

        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        logger.info("Server loop running in thread: %s", server_thread.name)
        logger.info("Listening on port %d", PORT)

        # get the current window id
        process = Popen(["xdotool", "getactivewindow"], stdout=PIPE)
        (wid_before, err) = process.communicate()
        process.wait()
        logger.debug('wid before: %d', wid_before)

        # open vim in new window and run vim commands (-c) that select and eval the contents of the init file
        # and then run the SilviuxInit function to open the channel
        # man X, search "geometry" for docs on this arg
        # on ubuntu with gnome it's auto resizing to half the screen and ignoring this arg :(
        cmd = 'gnome-terminal --geometry=400x400+0+0 --working-directory ' + os.getcwd() + '/vim_server -- vim init.silviux -c "normal! ggVG\\"ay" -c "@a" -c "call SilviuxInit()"'
        call(cmd, shell=True)

        # wait for gnome terminal running vim to become active window and grab the window id
        # TODO use the real API instead of this hack
        while True:
            time.sleep(0.1)
            logger.debug('waiting for new wid')
            process = Popen(["xdotool", "getactivewindow"], stdout=PIPE)
            (wid_current, err) = process.communicate()
            process.wait()
            if wid_before != wid_current: break
        logger.debug('got wid: %d', wid_current)
        self.wid = int(wid_current)

        # wait for vim to open channel which will invoke handler
        while True:
            if self.thesocket is None:
                logger.debug("No socket yet")
                time.sleep(0.1)
            else:
                break

        # rename Terminal
        call('xdotool set_window --name "SILVIUX TERMINAL" %d' % (self.wid,), shell=True)

        # let vim know what its wid is so it can maximize and focus its own window for setting registers etc
        self.thesocket.sendall(('["call", "SetWid", ["%d"],]' % (self.wid,)).encode('utf-8'))

    def close_vim_server(self):
        server.shutdown()
        server.server_close()

    # blocks until result returns
    # need to use -1 as seq number for handler to put result on internal_q
    #  msg = ["call", "GetRegister", "someregname", -1]
    def send_and_get(self, msg):
        self.thesocket.sendall(msg.encode('utf-8'))
        result = self.internal_q.get()
        logger.info('got result from vimserver %s', result)
        return result

    def send(self, msg):
        self.thesocket.sendall(msg.encode('utf-8'))

    def activate_window(self):
        if not self.wid: return
        call('xdotool windowactivate ' + str(self.wid), shell=True)

    def _set_for_test(self, socket, q):
        self.thesocket = socket
        self.internal_q = q
        self.wid = None
