import json
import logging

logger = logging.getLogger(__name__)

class Mode():

    def __init__(self, context):
        #TODO config for starting mode
        context.mode = 'closed'
        #Temporary hack until keras sound recognition is working again (which mapped single sound to single mode for sensible mode switching) via 'change_mode' msg
        #The idea is we can toggle between 3 common modes via sopare sounds, with push/pop sounds. In addition we can use the spoken commands to switch to a
        #less used mode and then have it on the stack for temporary use with same push/pop sounds. The 'remove' sound then deletes our temp mode from the stack.
        #A better implementation may be [mode1, mode2, mode3] and use pointer % mode_length into the list of modes, this 2 stack implementation was an accident.
        self.mode_stack = ['alphabet', 'closed', 'programming', 'alphabet', 'closed', 'programming', 'alphabet', 'closed', 'programming', 'alphabet', context.mode]
        self.popped = ['alphabet', 'programming', 'closed', 'alphabet', 'programming', 'closed', 'alphabet', 'programming','closed', 'alphabet', 'programming']
        context.notify('on', 'setParserStyle')
        context.notify(context.mode, 'setParser')

    def middleware(self, nxt):
        def handle(context):
            if not context.should_execute: return nxt(context)

            msg = context.msg

            next_parser = False
            if 'change_mode' in msg:
                if len(self.mode_stack) == 20:
                    self.mode_stack = self.mode_stack[15:]
                if msg['change_mode'] == 'pop':
                    if len(self.mode_stack) > 1:
                        popped = self.mode_stack.pop()
                        if (popped != 'hold' and popped != 'hold_repeat'):
                            self.popped.append(popped)
                        context.mode = self.mode_stack[-1]
                        next_parser = context.mode
                    else:
                        logger.warning('no mode to pop to')
                        context.notify('no mode to pop to')
                        return nxt(context)
                elif msg['change_mode'] == 'remove':
                    if len(self.mode_stack) > 1:
                        popped = self.mode_stack.pop()
                        context.mode = self.mode_stack[-1]
                        next_parser = context.mode
                    else:
                        logger.warning('no mode to pop to')
                        context.notify('no mode to pop to')
                        return nxt(context)
                elif msg['change_mode'] == 'push':
                    if len(self.popped) >= 1:
                        self.mode_stack.append(self.popped.pop())
                        context.mode = self.mode_stack[-1]
                        next_parser = context.mode
                    else:
                        logger.warning('nothing on popped stack')
                        context.notify('nothing on popped stack')
                        return nxt(context)
                elif msg['change_mode'] in context.parser_manager.modes:
                    context.mode = msg['change_mode']
                    self.mode_stack.append(context.mode)
                    next_parser = msg['change_mode']

                else:
                    #get here if change_mode is 'holder' or 'holder_repeater', we don't want to change parser
                    context.mode = msg['change_mode']
                    self.mode_stack.append(context.mode)
                context.notify('')
                #TODO rename to setMode in gnome extension
                context.notify(context.mode, 'setParser')

            if next_parser:
                context.parser_manager.set_active(next_parser)

                #TODO this probably should be in parser_manager.set_active? does the pm not have out_q?
                if next_parser in context.parser_manager.modes:
                    decoder = context.parser_manager.modes[next_parser]['decoder']
                    #send message to kaldi server to change the decoder
                    if decoder: context.out_q.put(json.dumps({'change_decoder': decoder}))

            return nxt(context)
        return handle

