import copy
import json
from silviux.config.keys.command import vocab

#TODO
#undo count is done by tokens even if they have no undo attr
#ie "sky alpha sky beta", "undo 2" should undo 2 letters but only undoes one and "sky" token is noop
#I think simple fix by simply checking for existence of a .undo attribute?

#TODO: dump history into file for logs/macros, beware of tests though, don't write file if test env or arg

#TODO: access history from vim instance, ability to save previous commands into macros

class History():

    def __init__(self, context):
        self.history = []

    def middleware(self, nxt):
        def handle(context):
            if not context.should_execute:
                return nxt(context)

            msg = context.msg
            if len(self.history) > 20:
                self.history = self.history[-10:]

            if 'history' in msg and msg['history'] == 'replay' and len(self.history) > 0:
              last = self.history[-1]
              replay_msg = copy.deepcopy(last['msg'])
              #kaldi middleware checks equality of segment with context.last_segment, so don't need to worry about ordering only equality
              #I don't think this will change because switching decoders can have lower segment numbers coming in
              replay_msg['segment'] = float('inf')
              if 'segment' in last['msg']:
                  replay_msg['replay_segment'] = last['msg']['segment']
              else:
                  replay_msg['replay_segment'] = None
              context.in_q.put(json.dumps(replay_msg))

            if 'undo' in msg and len(self.history) > 0:
                count = msg['undo']
                last = self.history.pop()
                last_tokens = last['tokens']
                if count == -1:
                    undo_tokens = last_tokens
                else:
                    count = min(len(last_tokens), count)
                    undo_tokens = last_tokens[len(last_tokens)-count:]
                    if len(undo_tokens) < len(last_tokens):
                        last['tokens'] = last_tokens[:len(last_tokens)-count]
                        self.history.append(last)
                
                c = context.executor.undo(undo_tokens)

            res = nxt(context)
            #IMPORTANT, if you put replay into the history can get infinite loop
            if context.final_transcript \
            and context.text != "" \
            and len(context.tokens) > 0 \
            and context.tokens[0].type != vocab['undo'] \
            and context.tokens[0].type != vocab['replay'] \
            and not context.parse_error:
                segment = context.last_segment
                data = {
                        'segment': segment,
                        'text': context.text,
                        'msg': context.msg,
                        #TODO these END tokens cause me trouble everywhere... are they required because of the grammar?
                        'tokens': [t for t in context.tokens if t.type != 'END']
                        }
                self.history.append(data)

            return res
        return handle
