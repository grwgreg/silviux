#Idea is use "middleware" pattern from web servers (rack, expressjs)
#This allows pre and post processing of messages and ability to return early to prevent middleware from ever receiving message.
#For example, post processing is required by optimistic middleware, which needs to check a property on the executor
#after execution. The history middleware also only adds a previous command if no parse error was thrown on the final transcript.
#see test_handler in test_middleware.py for simple example
class Handler:
    def __init__(self):
        self.middleware = []
        self.afterware = []
        self.nxt = lambda context: context

    def init(self):
        self.middleware.reverse()
        monkey_patched_nxt = self.nxt
        for m in self.middleware:
            monkey_patched_nxt = m(monkey_patched_nxt)
        self.nxt = monkey_patched_nxt

    def use(self, middleware):
        if hasattr(middleware, '__call__'):
            self.middleware.append(middleware)
        elif hasattr(middleware, 'middleware'):
            self.middleware.append(middleware.middleware)

        if hasattr(middleware, 'after'):
            self.afterware.append(middleware.after)

    def handle(self, context):
        res = self.nxt(context)
        self.after(context)
        return res

    def after(self, context):
        for fn in self.afterware:
            fn(context)

class Context:
    pass
