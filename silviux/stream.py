#based on the silvius microphone client, Tanel's kaldi-gstreamer-server client.py 

import argparse
from ws4py.client.threadedclient import WebSocketClient
import threading
from multiprocessing import Process, Queue, Pipe
from queue import Queue as ThreadQueue
from threading import Event
import sys
import urllib.request, urllib.parse, urllib.error
import json
import time
import audioop
import logging
import yaml

logger = logging.getLogger(__name__)

from .main import loop

from .mic.mic_source import MicSource

mic_source = MicSource()
reconnect_mode = True

class MyClient(WebSocketClient):

    def __init__(self, url, protocols=None, extensions=None, heartbeat_freq=None, byterate=16000,
                 show_hypotheses=True,
                 save_adaptation_state_filename=None, send_adaptation_state_filename=None, audio_gate=0, out_q=None,in_q=None):
        super(MyClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.show_hypotheses = show_hypotheses
        self.byterate = byterate
        self.save_adaptation_state_filename = save_adaptation_state_filename
        self.send_adaptation_state_filename = send_adaptation_state_filename
        self.chunk = 0
        #note setting a gate value seems to mess with the adaption state and lead to poor recognition
        self.audio_gate = audio_gate
        self.out_q = out_q
        self.in_q = in_q

    def send_data(self, data):
        self.send(data, binary=True)

    def opened(self):
        self.from_mic, self.to_websocket = Pipe(False)
        mic_source.listeners['websock'] = self.to_websocket
        if self.out_q: self.out_q.put(json.dumps({'notify': 'Connected to Kaldi'}))
        def mic_to_ws():
            try:
                logger.info("LISTENING TO MICROPHONE")
                last_state = None
                while True:
                    if self.in_q and not self.in_q.empty():
                        change_decoder_msg = self.in_q.get()
                        self.send(change_decoder_msg)
                    try:
                        data = self.from_mic.recv_bytes()
                    except EOFError as e:
                        #careful of order of cleaning up for reconnections or you
                        #try to read from a closed pipe
                        logger.exception("error reading from_mic pipe")
                    if self.audio_gate > 0:
                        rms = audioop.rms(data, 2)
                        if rms < self.audio_gate:
                            data = '\00' * len(data)
                    #old silvius stuff, has always been commented out afaik
                    #sample_rate = self.byterate
                    # if sample_chan == 2:
                    #     data = audioop.tomono(data, 2, 1, 1)
                    # if sample_rate != self.byterate:
                    #    (data, last_state) = audioop.ratecv(data, 2, 1, sample_rate, self.byterate, last_state)

                    self.send_data(data)
            except IOError as e:
                # usually a broken pipe
                logger.warning("IOError")
            except AttributeError:
                # currently raised when the socket gets closed by main thread
                logger.warning("AttributeError, likely socket closed by main thread")
                pass

            # to voluntarily close the connection, we would use
            #self.send_data("")
            #self.send("EOS")

            try:
                self.remove_mic_listener()
                self.close()
            except IOError:
                logger.warning("IOError, likely socket closed by main thread")
                pass

        threading.Thread(target=mic_to_ws).start()

    def remove_mic_listener(self):
        logger.info('removing web socket mic listener')
        self.from_mic.close()
        self.to_websocket.close()
        self.from_mic = None
        self.to_websocket = None
        del mic_source.listeners['websock']

    def received_message(self, m):
        logger.debug("websocket received message %s", m)
        response = json.loads(str(m))

        if response['status'] == 0:
            sys.stdout.flush()
            if self.out_q:
                self.out_q.put(str(m))
            else:
                # text = response['result']['hypotheses'][0]['transcript']
                print(response)

            #Silviux: adaption state is entirely handled on server now
            # if 'adaptation_state' in response:
            #     if self.save_adaptation_state_filename:
            #         logger.info("Saving adaptation state to %s", self.save_adaptation_state_filename)
            #         with open(self.save_adaptation_state_filename, "w") as f:
            #             f.write(json.dumps(response['adaptation_state']))
        else:
            logger.error("Received error from server (status %d)", response['status'])
            if 'message' in response:
                logger.error("Error message: %s",  response['message'])
            

    def closed(self, code, reason=None):
        logger.info("Websocket closed() called %s %s", code, reason)
        pass


def setup():
    content_type = "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1"
    path = 'client/ws/speech'

    conf = {}
    with open('./silviux/config/silviux.yaml') as f:
        conf = yaml.safe_load(f)

    parser = argparse.ArgumentParser(description='Microphone client for silviux')
    parser.add_argument('-s', '--server', default=conf['stream']['server'], dest="server", help="Speech-recognition server")
    parser.add_argument('-p', '--port', default=conf['stream']['port'], dest="port", help="Server port")
    parser.add_argument('-r', '--rate', default=conf['stream']['byterate'], dest="byterate", type=int, help="Rate in bytes/sec at which audio should be sent to the server.")
    parser.add_argument('-d', '--device', default=conf['stream']['device'], dest="device", type=int, help="Select a different microphone (give device ID)")
    parser.add_argument('-k', '--keep-going', default=True, action="store_true", help="Keep reconnecting to the server after periods of silence")
    #Note the adaption state stuff now lives on server, don't use these args, TODO remove them?
    parser.add_argument('--save-adaptation-state', help="Save adaptation state to file")
    parser.add_argument('--send-adaptation-state', help="Send adaptation state from file")
    parser.add_argument('--content-type', default=content_type, help="Use the specified content type (default is " + content_type + ")")
    parser.add_argument('--hypotheses', default=True, type=int, help="Show partial recognition hypotheses (default: 1)")
    parser.add_argument('-g', '--audio-gate', default=0, type=int, help="Audio-gate level to reduce detections when not talking")
    parser.add_argument('-o', '--no-parse', action="store_true", help="Don't send the response data to the parser")
    args = parser.parse_args()

    in_q = None
    out_q = None
    if not args.no_parse:
        out_q = Queue()
        in_q = Queue()
        p = Process(target=loop, args=(out_q, in_q))
        p.start()

    mic_source.start_stream(mic=args.device, byterate=args.byterate)

    if (args.keep_going):
        global reconnect_mode
        reconnect_mode = True
        while(mic_source.fatal_error == False):
            logger.warning("Reconnecting...")
            try:
                run(args, content_type, path, out_q, in_q)
            except:
                if out_q: out_q.put(json.dumps({'notify': 'No kaldi server connection, reconnecting...'}))
            time.sleep(5)
        logger.error("There was a fatal mic error")
        #TODO possibly good idea to send msg to main loop for cleanup here, think decoder/mode sync issues
    else:
        run(args, content_type, path, out_q, in_q)

def run(args, content_type, path, out_q, in_q):
    uri = "ws://%s:%s/%s?%s" % (args.server, args.port, path, urllib.parse.urlencode([("content-type", content_type)]))
    logger.info('Connecting to %s', uri)

    ws = MyClient(uri, byterate=args.byterate, show_hypotheses=args.hypotheses,
                  save_adaptation_state_filename=args.save_adaptation_state, send_adaptation_state_filename=args.send_adaptation_state, audio_gate=args.audio_gate, out_q=out_q, in_q=in_q)
    ws.connect()
    ws.run_forever()

def main():
    try:
        setup()
    except KeyboardInterrupt:
        logger.warning('KeyboardInterrupt, exiting')

if __name__ == "__main__":
    main()

