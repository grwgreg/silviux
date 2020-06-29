from ..parser.parser_manager import ParserManager
from ..parser.parse import GrammaticalError
import logging

logger = logging.getLogger(__name__)

class Parse():

    def __init__(self, context):
        context.parser_manager = ParserManager()
        context.ast = None
        context.parse_error = False

    def middleware(self, nxt):
        def handle(context):

            #tokens can be replayed from upstream, so only scan if they aren't already set
            if context.text != "" and len(context.tokens) == 0:
                context.tokens = context.parser_manager.scan(context.text)

            #Current setup always parses, even if not final transcript
            #This can be helpful for noticing parse errors early in utterance from text color change in taskbar
            #The optimistic middleware will unset the .ast if not final transcript, so if the optimistic middleware is disabled
            #you will need to add a check for the final_transcript somewhere before execution
            if len(context.tokens) == 0:
                return nxt(context)
            try:
                context.ast = context.parser_manager.parse(context.tokens)
                context.notify('parsed', 'setTextStyle')
                logger.debug('parse success: %s', context.text)

            except GrammaticalError as e:
                logger.info('parse error %s', context.text)
                context.parse_error = True
                context.notify('error', 'setTextStyle')

            result = nxt(context)

            if (not context.parse_error and context.final_transcript):
                context.notify('final', 'setTextStyle')

            return result

        return handle

    def after(self, context):
        context.ast = None
        context.parse_error = False
