import threading
from threading import Event
from multiprocessing import Pipe
import sys
import json
import time
import audioop
import logging
import yaml

logger = logging.getLogger(__name__)

from .mic_source import MicSource

class VolumeMonitor:
    def __init__(self, from_controller, main_q):
        self.conf = {}
        with open('./silviux/config/silviux.yaml') as f:
            self.conf = yaml.safe_load(f)
        self.mic_source = MicSource()
        self.mic_source.start_stream(mic=self.conf['stream']['device'], byterate=self.conf['stream']['byterate'])
        self.main_q = main_q
        self.from_controller = from_controller
        self.stop_thread = Event()
        self.notify_thread = None
        t = threading.Thread(target=self.on_msg)
        t.daemon = True
        t.start()

    def on_msg(self):
        logger.debug('volume monitor on_msg thread started')
        while True:
            msg = self.from_controller.recv()
            logger.info('volume monitor got msg %s', str(msg))
            if msg == 'NOTIFY_ON':
                logger.debug('vm on_msg got notify on event')
                if not self.notify_thread:
                    logger.info('starting the notify sound thread *')
                    self.notify_thread = threading.Thread(target=self.notify_sound)
                    self.notify_thread.daemon = True
                    self.notify_thread.start()
                else:
                    logger.warning('got NOTIFY_ON msg but VolumeMonitor thread already running')
                    pass
            elif msg == 'NOTIFY_OFF':
                if self.notify_thread:
                    self.stop_thread.set()
                    self.notify_thread.join()
                    self.stop_thread.clear()
                    self.notify_thread = None
                    logger.info('on msg method just stopped the notify thread')
                else:
                    logger.warn('in volume monitor notify thread already stopped ')
            else:
                logger.error('unknown msg in VolumeMonitor %s', str(msg))

    def notify_sound(self):
        #false arg makes unidirectional connection
        from_mic, to_volume = Pipe(False)
        self.mic_source.listeners['volume'] = to_volume
        last_rms = False
        logger.info('notify sound thread started')
        sound_count = 0
        volume_threshold = self.conf['volume_threshold']
        while not self.stop_thread.is_set():
            data = from_mic.recv_bytes()
            rms = audioop.rms(data, 2)
            logger.debug('notify sound got rms %d', rms)

            if rms > volume_threshold:
                sound_count += 1
                logger.debug('incrementing sound_count %s', sound_count)
            #idea is if 3 consecutive .recv_bytes are above threshold
            #we send message (this is to exit out of hold_repeater mode)
            #if you modify the config for the mic this may be too long or too short
            if rms > volume_threshold and sound_count >= 3:
                logger.debug('got extended sound, sending SOUND_EXTENDED msg to main q')
                msg = json.dumps({"volume_monitor": "SOUND_EXTENDED"})
                self.main_q.put(msg)
            if rms > volume_threshold and not last_rms:
                last_rms = True
                logger.debug("got first loud rms: %d",  rms)
                msg = json.dumps({"volume_monitor": "SOUND_ON"})
                self.main_q.put(msg)
            if rms <= volume_threshold and last_rms:
                last_rms = False
                sound_count = 0
                logger.debug("got quiet: %d", rms)
                msg = json.dumps({"volume_monitor": "SOUND_OFF"})
                self.main_q.put(msg)
            else:
                logger.debug("got rms: %d", rms)
        #note- if getting odd bugs it's probably a race condition here
        del self.mic_source.listeners['volume']
        to_volume.close()
        from_mic.close()
        to_volume = None
        from_mic = None
        logger.info('notify sound thread stopped')
