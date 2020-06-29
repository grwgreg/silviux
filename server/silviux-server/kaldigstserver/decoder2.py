#Silviux modified to support changing decoders, write adaption state to files in /tmp
import gi

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

GObject.threads_init()
Gst.init(None)
import logging
import thread
import os
import json
import zlib
import base64
import copy

logger = logging.getLogger(__name__)

import pdb

class DecoderPipeline2(object):
    def __init__(self, conf={}):
        logger.info("Creating decoder using conf: %s" % conf)
        self.conf = conf
        self.create_pipeline(conf)
        self.outdir = conf.get("out-dir", None)
        if self.outdir and not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
            if not os.path.isdir(self.outdir):
                raise Exception("Output directory %s already exists as a file" % self.outdir)

        self.result_handler = None
        self.full_result_handler = None
        self.eos_handler = None
        self.error_handler = None
        self.request_id = "<undefined>"


    def create_pipeline(self, conf):

        #Need a deep copy because the way this was written mutates the config object
        conf = copy.deepcopy(conf)

        logger.info("Creating new pipeline: %s" % conf)
        self.appsrc = Gst.ElementFactory.make("appsrc", "appsrc")
        self.decodebin = Gst.ElementFactory.make("decodebin", "decodebin")
        self.audioconvert = Gst.ElementFactory.make("audioconvert", "audioconvert")
        self.audioresample = Gst.ElementFactory.make("audioresample", "audioresample")
        self.tee = Gst.ElementFactory.make("tee", "tee")
        self.queue1 = Gst.ElementFactory.make("queue", "queue1")
        self.filesink = Gst.ElementFactory.make("filesink", "filesink")
        self.queue2 = Gst.ElementFactory.make("queue", "queue2")
        self.asr = Gst.ElementFactory.make("kaldinnet2onlinedecoder", "asr")
        self.fakesink = Gst.ElementFactory.make("fakesink", "fakesink")

        # This needs to be set first
        if "use-threaded-decoder" in conf["decoder"]:
            self.asr.set_property("use-threaded-decoder", conf["decoder"]["use-threaded-decoder"])

        decoder_config = conf.get("decoder", {})
        if 'nnet-mode' in decoder_config:
          logger.info("Setting decoder property: %s = %s" % ('nnet-mode', decoder_config['nnet-mode']))
          self.asr.set_property('nnet-mode', decoder_config['nnet-mode'])
          del decoder_config['nnet-mode']

        for (key, val) in decoder_config.iteritems():
            if key != "use-threaded-decoder":
                logger.info("Setting decoder property: %s = %s" % (key, val))
                self.asr.set_property(key, val)


        self.appsrc.set_property("is-live", True)
        self.filesink.set_property("location", "/dev/null")
        logger.info('Created GStreamer elements')

        self.pipeline = Gst.Pipeline()
        for element in [self.appsrc, self.decodebin, self.audioconvert, self.audioresample, self.tee,
                        self.queue1, self.filesink,
                        self.queue2, self.asr, self.fakesink]:
            logger.debug("Adding %s to the pipeline" % element)
            self.pipeline.add(element)

        logger.info('Linking GStreamer elements')

        self.appsrc.link(self.decodebin)
        #self.appsrc.link(self.audioconvert)
        self.decodebin.connect('pad-added', self._connect_decoder)
        self.audioconvert.link(self.audioresample)

        self.audioresample.link(self.tee)

        self.tee.link(self.queue1)
        self.queue1.link(self.filesink)

        self.tee.link(self.queue2)
        self.queue2.link(self.asr)

        self.asr.link(self.fakesink)

        # Create bus and connect several handlers
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus.connect('message::eos', self._on_eos)
        self.bus.connect('message::error', self._on_error)
        #self.bus.connect('message::cutter', self._on_cutter)

        self.asr.connect('partial-result', self._on_partial_result)
        self.asr.connect('final-result', self._on_final_result)
        self.asr.connect('full-final-result', self._on_full_final_result)

        logger.info("Setting pipeline to READY")
        self.pipeline.set_state(Gst.State.READY)
        logger.info("Set pipeline to READY")

        #Setting adapation state has to be done after some of the stuff above, fails silently when set right after other asr properties
        #Previously it was set as last step in init_request
        #TODO are the adaptation state files identical for all decoders/models or should they be decoder specific?
        #for now each decoder gets its own adaption state
        adaptation_file = "./tmp/adaptation_state_%s.json" % (conf["default-decoder"],)
        if os.path.isfile(adaptation_file):
            try:
                with open(adaptation_file,"r") as f:
                    logger.info("Setting adaptation State")
                    saved_state = json.loads(f.read())
                    state = zlib.decompress(base64.b64decode(saved_state.get('value', '')))
                    self.set_adaptation_state(state)
            except:
                #NOTE when the gstreamer fails above it doesn't actually raise python exception, just fails silently
                logger.info("Setting adaptation state failed" % (sys.exc_info()[0],))
                raise
        else:
            logger.info("No saved adapatation state %s", os.getcwd())
            self.set_adaptation_state("")

    def _connect_decoder(self, element, pad):
        logger.info("%s: Connecting audio decoder" % self.request_id)
        pad.link(self.audioconvert.get_static_pad("sink"))
        logger.info("%s: Connected audio decoder" % self.request_id)


    def _on_partial_result(self, asr, hyp):
        logger.info("%s: Got partial result: %s" % (self.request_id, hyp.decode('utf8')))
        if self.result_handler:
            self.result_handler(hyp.decode('utf8'), False)

    def _on_final_result(self, asr, hyp):
        logger.info("%s: Got final result: %s" % (self.request_id, hyp.decode('utf8')))
        if self.result_handler:
            self.result_handler(hyp.decode('utf8'), True)

    def _on_full_final_result(self, asr, result_json):
        logger.info("%s: Got full final result: %s" % (self.request_id, result_json.decode('utf8')))
        if self.full_result_handler:
            self.full_result_handler(result_json)

    def _on_error(self, bus, msg):
        self.error = msg.parse_error()
        logger.error(self.error)
        self.finish_request()
        if self.error_handler:
            self.error_handler(self.error[0].message)

    def _on_eos(self, bus, msg):
        logger.info('%s: Pipeline received eos signal' % self.request_id)
        #self.decodebin.unlink(self.audioconvert)
        self.finish_request()
        if self.eos_handler:
            self.eos_handler[0](self.eos_handler[1])

    def get_adaptation_state(self):
        return self.asr.get_property("adaptation-state")

    def get_asr_property(self, property):
        return self.asr.get_property(property)

    def set_asr_property(self, property, value):
        return self.asr.set_property(property, value)

    #will get segfault if change the fst after created!
    #not using this currently but leaving this as it may be useful later
    def set_asr_properties(self, props):
        self.pipeline.set_state(Gst.State.PAUSED)
        self.asr.set_state(Gst.State.PAUSED)
        for key in props:
            self.asr.set_property(key, props[key])
        self.asr.set_state(Gst.State.PLAYING)
        self.pipeline.set_state(Gst.State.PLAYING)
        return

    def reset_pipeline(self, decoder):
        #TODO Currently mutating the loaded yaml config to keep track of the active decoder
        #change active decoder to instance variable and make a deep copy of config once at init
        #and give it a different name
        self.conf["decoder"] = self.conf["decoders"][decoder]

        self.save_adaptation_state()

        #TODO create_pipeline uses this for the filename of the adaption state
        #change to instance var or at least change name, 'default-decoder' being mutated is confusing
        self.conf["default-decoder"] = decoder


        self.result_handler = None
        self.full_result_handler = None
        self.eos_handler = None
        self.error_handler = None

        self.destroy()

        self.create_pipeline(self.conf)
        self.init_request(self._request_id, self.caps_str)


    def set_adaptation_state(self, adaptation_state):
        """Sets the adaptation state to a certian value, previously retrieved using get_adaptation_state()

        Should be called after init_request(..)
        """

        return self.asr.set_property("adaptation-state", adaptation_state)

    def finish_request(self):
        logger.info("%s: Resetting decoder state" % self.request_id)
        if self.outdir:
            self.filesink.set_state(Gst.State.NULL)
            self.filesink.set_property('location', "/dev/null")
            self.filesink.set_state(Gst.State.PLAYING)
        self.pipeline.set_state(Gst.State.NULL)
        self.request_id = "<undefined>"


    def init_request(self, id, caps_str):
        self.request_id = id
        self._request_id = id
        self.caps_str = caps_str 
        logger.info("%s: Initializing request" % (self.request_id))
        if caps_str and len(caps_str) > 0:
            logger.info("%s: Setting caps to %s" % (self.request_id, caps_str))
            caps = Gst.caps_from_string(caps_str)
            self.appsrc.set_property("caps", caps)
        else:
            #caps = Gst.caps_from_string("")
            self.appsrc.set_property("caps", None)
            #self.pipeline.set_state(Gst.State.READY)
            pass
        #self.appsrc.set_state(Gst.State.PAUSED)

        if self.outdir:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.filesink.set_state(Gst.State.NULL)
            self.filesink.set_property('location', "%s/%s.raw" % (self.outdir, id))
            self.filesink.set_state(Gst.State.PLAYING)

        #self.filesink.set_state(Gst.State.PLAYING)        
        #self.decodebin.set_state(Gst.State.PLAYING)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.filesink.set_state(Gst.State.PLAYING)
        # push empty buffer (to avoid hang on client diconnect)
        #buf = Gst.Buffer.new_allocate(None, 0, None)
        #self.appsrc.emit("push-buffer", buf)

        # reset adaptation state
        # silviux change: adaption state is now always set via create_pipeline
        # self.set_adaptation_state("")

    def process_data(self, data):
        logger.debug('%s: Pushing buffer of size %d to pipeline' % (self.request_id, len(data)))
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        self.appsrc.emit("push-buffer", buf)
        logger.debug('%s: Pushing buffer done' % self.request_id)


    def end_request(self):
        logger.info("%s: Pushing EOS to pipeline" % self.request_id)
        self.appsrc.emit("end-of-stream")

    def set_result_handler(self, handler):
        self.result_handler = handler

    def set_full_result_handler(self, handler):
        self.full_result_handler = handler

    def set_eos_handler(self, handler, user_data=None):
        self.eos_handler = (handler, user_data)

    def set_error_handler(self, handler):
        self.error_handler = handler

    #NOTE old (debian jessie apt package) python-gi library leaked significant amounts of memory with this identical code
    #calling gc.collect() and various gstreamer unref() type functions didn't help
    def destroy(self):
        self.appsrc.emit("end-of-stream")
        self.pipeline.set_state(Gst.State.NULL)
        for element in [self.appsrc, self.decodebin, self.audioconvert, self.audioresample, self.tee,
                        self.queue1, self.filesink,
                        self.queue2, self.asr, self.fakesink]:
            element.set_state(Gst.State.NULL)
            # setting state to null and removing references should be enough to clean up
            # element.unref()
        self.appsrc = None
        self.decodebin = None
        self.audioconvert = None
        self.audioresample = None
        self.tee = None
        self.queue1 = None
        self.filesink = None
        self.queue2 = None
        self.asr = None
        self.fakesink = None
        self.pipeline = None
        self.bus = None

    def cancel(self):
        logger.info("%s: Sending EOS to pipeline in order to cancel processing" % self.request_id)
        self.appsrc.emit("end-of-stream")
        #self.asr.set_property("silent", True)
        #self.pipeline.set_state(Gst.State.NULL)

        #if (self.pipeline.get_state() == Gst.State.PLAYING):
        #logger.debug("Sending EOS to pipeline")
        #self.pipeline.send_event(Gst.Event.new_eos())
        #self.pipeline.set_state(Gst.State.READY)
        logger.info("%s: Cancelled pipeline" % self.request_id)

    def save_adaptation_state(self):
        logger.info("%s: Saving adaptation state..." % (self.request_id))
        adaptation_state = self.get_adaptation_state()
        data = json.dumps({"value": base64.b64encode(zlib.compress(adaptation_state)), "type": "string+gzip+base64"})
        #note we mutate the self.conf["default-decoder"] to hold the current decoder
        adaptation_file = "./tmp/adaptation_state_%s.json" % (self.conf["default-decoder"],)
        with open(adaptation_file, "w") as f:
            f.write(data)
