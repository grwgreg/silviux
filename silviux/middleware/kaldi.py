class Kaldi():

    def __init__(self, context):
        context.tokens = []
        context.last_segment = None
        context.text = ""
        context.final_transcript = False

    def middleware(self, nxt):
        def handle(context):

            msg = context.msg

            if 'result' in msg:
                context.text = msg['result']['hypotheses'][0]['transcript']
                context.notify(context.text.replace("'", "'\"'\"'"))
                if msg['result']['final']:
                    context.final_transcript = True
            if 'segment' in msg:
                if context.last_segment != msg['segment']:
                    context.last_tokens = []
                    context.last_segment = msg['segment']
                    context.output_count = 0

            return nxt(context)
        return handle

    def after(self, context):
        context.tokens = []
        context.final_transcript = False
        context.text = ""
