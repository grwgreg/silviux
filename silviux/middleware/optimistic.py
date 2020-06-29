class Optimistic():

    def __init__(self, context):
        context.optimistic = False
        context.last_tokens = []
        context.undo_tokens = []
        context.output_count = 0

    def middleware(self, nxt):
        def handle(context):

            if not context.should_execute:
                return nxt(context)

            if 'toggle_optimistic' in context.msg:
                context.optimistic = not context.optimistic
                txt = 'optimistic' if context.optimistic else 'on'
                context.notify(txt, 'setParserStyle')

            if 'set_optimistic' in context.msg:
                context.optimistic = context.msg['set_optimistic'] == "True"
                txt = 'optimistic' if context.optimistic else 'on'
                context.notify(txt, 'setParserStyle')

            if context.optimistic:

                if 'change_mode' in context.msg:
                    #we need to reset the last tokens state
                    context.output_count = 0
                    context.last_tokens = []

                if context.parse_error and context.final_transcript:
                    context.executor.undo_by_backspaces(context.output_count) 
                    context.output_count = 0
                    context.last_tokens = []
                elif context.final_transcript or (context.ast and context.ast.can_optimistic_execute):
                    context.undo_tokens = Optimistic.diff_and_mark_tokens(context.last_tokens, context.tokens)
                    #note .undo calls automator.flush
                    context.output_count -= context.executor.undo(context.undo_tokens)
                    context.last_tokens = context.tokens
                elif context.ast and not context.ast.can_optimistic_execute:
                    #need to unset .ast to prevent execution
                    context.ast = None
            else:

              #unset the ast to prevent execution if optimistic mode is off
              if (not context.final_transcript):
                    context.ast = None

            res = nxt(context)
            #TODO tracking all these individual variables is too complex, figure out a way to have
            #did_execute, force_execute type of flags
            if context.optimistic and (context.ast != None and context.ast.can_optimistic_execute):
                context.output_count += context.executor.automator.output_count
            context.undo_tokens = []
            return res
        return handle

    @staticmethod
    def diff_and_mark_tokens(last, current):
    # add the .done flag to prevent repeated execution in optimistic mode
    # returns the tokens which were previously in the transcript
    # but not in the current one, which will have to be undone before execution
        min_length = min(len(last), len(current))
        for i in range(0,min_length):
            if last[i] == current[i] and last[i].extra == current[i].extra:
            #TODO can I remove these END tokens from the grammar?
            #if last[i] == current[i] and last[i].extra == current[i].extra and last[i].type != 'END':
                current[i].done = True
            else:
                return last[i:]
        return last[min_length:]

