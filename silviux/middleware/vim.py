from vim_server.server import VimServer

class Vim():

    def __init__(self, context, for_test=False):
        if not for_test:
            vim_server = VimServer()
            vim_server.start_vim_server(context.in_q)

    def middleware(self, nxt):
        def handle(context):
            msg = context.msg

            if 'macro' in msg:
                context.text = msg['macro']
                context.final_transcript = True
            return nxt(context)

        return handle
