from ..execute import ExecuteCommands, Automator

class Execute():

    def __init__(self, context):
        automator = Automator()
        executor = ExecuteCommands(automator, context.in_q)
        context.executor = executor

    def middleware(self, nxt):
        def handle(context):
            if context.ast != None:
                context.notify('parsed', 'setTextStyle')
                context.executor.execute(context.ast, context.should_execute)

            res = nxt(context)
            return res
        return handle
