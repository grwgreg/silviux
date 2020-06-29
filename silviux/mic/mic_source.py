import threading
import pyaudio
import sys
import logging

logger = logging.getLogger(__name__)

_mic_source = None

#TODO I extracted out the mic code because I couldn't call pyaudio.PyAudio().open() from multiple
#threads/processes without getting "PortAudioError -9993 Illegal combination of I/O devices"
#The idea was to share mic data by looping over many listeners and sending data via pipes.
def MicSource():
    global _mic_source
    if (not _mic_source):
        _mic_source = _MicSource()
    return _mic_source

class _MicSource:

    def __init__(self):
        #TODO, listeners is modified directly by outside code
        #Nervous about concurrency, is it possible that a thread will remove a pipe from .listeners
        #while we're looping through it to send data?
        #the volume monitor adds and removes itself (currently it uses its own mic source, it used to share with sopare and never caused issue)
        self.listeners = {}
        self.fatal_error = False

    def start_stream(self, mic=-1, byterate=16000):
        pa = pyaudio.PyAudio()
        stream = None 
        sample_rate = byterate

        while stream is None:
            try:
                # try adjusting this if you want fewer network packets
                # silviux note vol monitor would require changes because expects x sequential chunks to be y seconds
                # chunk = 2048 * 2 * sample_rate / byterate
                chunk = 2048 * 2 * sample_rate // byterate

                if mic == -1:
                    mic = pa.get_default_input_device_info()['index']
                    logger.info("Selecting default mic")
                logger.info("Using mic # %s", mic)
                stream = pa.open(
                    rate = sample_rate,
                    format = pyaudio.paInt16,
                    channels = 1,
                    input = True,
                    input_device_index = mic,
                    frames_per_buffer = chunk)
            except IOError as e:
                logger.exception('IOError while attempting to open mic')
                if(e.errno == -9997 or e.errno == 'Invalid sample rate'):
                    new_sample_rate = int(pa.get_device_info_by_index(mic)['defaultSampleRate'])
                    if(sample_rate != new_sample_rate):
                        sample_rate = new_sample_rate
                        continue
                logger.error("Could not open microphone. Please try a different device.")
                self.fatal_error = True
                sys.exit(0)

        logger.info('Have mic stream')
        def mic_to_listeners():
            try:
                logger.info("LISTENING TO MICROPHONE")
                while True:
                    data = stream.read(chunk)
                    for id, p in list(self.listeners.items()):
                        p.send_bytes(data)
            except IOError as e:
                # usually a broken pipe
                logger.exception('got IOError in mic_to_listeners thread')
            except AttributeError:
                # currently raised when the socket gets closed by main thread
                logger.exception('mic died, AttributeError')
                pass

            logger.error('lost mic stream')

        t = threading.Thread(target=mic_to_listeners)
        t.daemon = True
        t.start()
