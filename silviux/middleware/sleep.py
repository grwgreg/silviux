class Sleep():
    def __init__(self, context):
        context.should_execute = True

    def middleware(self, nxt):
        def handle(context):
            msg = context.msg

            if 'sleep' in msg:
                set_sleep_on = msg['sleep'] == 'sleep'

                if msg['sleep'] == 'toggle':
                    set_sleep_on = context.should_execute

                if set_sleep_on:
                    context.should_execute = False
                    context.notify('off', 'setParserStyle')
                    context.notify('')
                    context.notify('parsed', 'setTextStyle')
                else:
                    context.should_execute = True
                    txt = 'optimistic' if context.optimistic else 'on'
                    context.notify(txt, 'setParserStyle')

            return nxt(context)
        return handle
