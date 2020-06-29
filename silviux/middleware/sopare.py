import os
from multiprocessing import Process
import json
from ..ast import AST
import logging
import yaml

logger = logging.getLogger(__name__)

import socket
import subprocess
import threading

#TODO add udp listener middleware for both keras and sopare?
def udp_listen(q, UDP_IP, UDP_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        logger.info('udp_listen got message %s', data)
        q.put(data)

class Sopare():

    def __init__(self, context, for_test=False):

        conf = {}
        with open('./silviux/config/silviux.yaml') as f:
            conf = yaml.safe_load(f)
        #listen on udp port and run sopare (sopare plugin will send hits to udp)
        if not for_test:
            udp_thread = threading.Thread(target=udp_listen, args=(context.in_q, conf['sopare_ip'], conf['sopare_port']))
            udp_thread.daemon = True
            udp_thread.start()
            #would need to call subprocess.communicate or something to get stdout
            #run from another terminal if you need to debug, this is only a convenience
            subprocess.Popen([conf['sopare_dir'] + "/sopare.py", "-l"], cwd=conf['sopare_dir'])

    def middleware(self, nxt):
        def handle(context):
            msg = context.msg
            if not context.should_execute:
                if 'sopare' in msg:
                    context.notify(msg['sopare'], 'setSecondary')
                #check for wake up sound
                if 'sopare' in msg and msg['sopare'] == 'cliq':
                    context.in_q.put(json.dumps({'sleep': 'toggle'}))
                return nxt(context)

            if 'sopare' in msg:
                logger.info('sopare resonse %s', msg)

                if msg['sopare'] == 'blow':
                    context.in_q.put(json.dumps({'change_mode': 'pop'}))
                elif msg['sopare'] == 'shh':
                    context.in_q.put(json.dumps({'change_mode': 'push'}))
                elif msg['sopare'] == 'lok':
                    context.in_q.put(json.dumps({'change_mode': 'remove'}))
                elif msg['sopare'] == 'whistle':
                    context.in_q.put(json.dumps({'change_mode': 'remove'}))
                elif msg['sopare'] == 'ttt':
                    context.in_q.put(json.dumps({'toggle_optimistic': True}))
                elif msg['sopare'] == 'cliq':
                    context.in_q.put(json.dumps({'sleep': 'toggle'}))

                context.notify(msg['sopare'], 'setSecondary')

            return nxt(context)
        return handle
