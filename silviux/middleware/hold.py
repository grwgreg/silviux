import json
from multiprocessing import Pipe
from ..ast import AST
from ..mic.volume_monitor import VolumeMonitor
import logging

logger = logging.getLogger(__name__)

class Hold():

    def __init__(self, context, for_test=False):
        context.repeat_key = None

        if not for_test:
            from_controller, to_volume_monitor = Pipe(False)
            context.to_volume_monitor = to_volume_monitor
            volume_monitor = VolumeMonitor(from_controller=from_controller, main_q=context.in_q)


    def middleware(self, nxt):
        def handle(context):
            msg = context.msg
            if 'hold' in msg:
                logger.info('main got hold msg %s', msg)
                context.last_tokens = []
                if not context.should_execute:
                    return nxt(context)
                context.to_volume_monitor.send('NOTIFY_ON')
                context.in_q.put(json.dumps({'change_mode': 'hold'}))

            if context.mode == 'hold':
                logger.debug('main in hold mode')
                if 'volume_monitor' in msg and msg['volume_monitor'] == 'SOUND_ON':
                    logger.info('main loop got sound on event')
                    context.to_volume_monitor.send('NOTIFY_OFF')
                    # putting back onto the queue is too slow!!! have to call release asap
                    # would a higher priority (like microtask queue in js) fix latency?
                    # creating an AST node like this inline is hacky af
                    # context.in_q.put(json.dumps({'release_all': True}))
                    context.final_transcript = True
                    context.last_tokens = []
                    context.ast = AST('release') 
                    context.in_q.put(json.dumps({'change_mode': 'pop'}))
                    return nxt(context)
                return 'in hold mode, skipping all downstream handlers'

            if 'hold_repeat' in msg:
                logger.info('main got hold_repeat msg %s', msg)
                #TODO dont love this, need to reset last_tokens so we don't undo anything
                #maybe some type of explicit reset function/msg is way to go?
                context.last_tokens = []
                if not context.should_execute:
                    return nxt(context)
                context.repeat_key = msg['hold_repeat']
                context.to_volume_monitor.send('NOTIFY_ON')
                context.in_q.put(json.dumps({'change_mode': 'hold_repeat'}))

            if context.mode == 'hold_repeat':
                logger.info('main in hold repeat mode')
                if 'volume_monitor' in msg and msg['volume_monitor'] == 'SOUND_OFF':
                    logger.info('main loop got sound off event')
                    context.last_tokens = []
                    context.ast = AST('raw_char', [context.repeat_key]) 
                    context.final_transcript = True
                    res = nxt(context)
                    context.ast = None
                    return res

                if 'volume_monitor' in msg and msg['volume_monitor'] == 'SOUND_EXTENDED':
                    logger.info('got extended event!!!!!!! turning off volume monitor')
                    context.in_q.put(json.dumps({'change_mode': 'pop'}))
                    context.to_volume_monitor.send('NOTIFY_OFF')
                    return nxt(context)

                logger.info('ignoring msg because in hold_repeat mode')
                return 'in hold mode, skipping all downstream handlers'

            #TODO there is a note in executor about moving release_list into middleware
            #I think I held off on that because custom_commands currently add to release list
            #ie the window switcher
            #can always convert that into a msg sent to main loop though, ie executor.q.put({add_release: key})
            if 'release_all' in msg:
                context.final_transcript = True
                context.last_tokens = []
                context.ast = AST('release') 
            return nxt(context)
        return handle
