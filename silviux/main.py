from .middleware.handler import Handler, Context
from .middleware.notify import Notify
from .middleware.hold import Hold
from .middleware.sleep import Sleep
from .middleware.sopare import Sopare
from .middleware.mode import Mode
from .middleware.vim import Vim 
from .middleware.history import History
from .middleware.kaldi import Kaldi 
from .middleware.optimistic import Optimistic 
from .middleware.parse import Parse 
from .middleware.execute import Execute 

import json
import logging

logger = logging.getLogger(__name__)

def loop(in_q, out_q):

    context = Context()

    context.in_q = in_q
    context.out_q = out_q

    handler = Handler()
    handler.use(Notify(context))
    handler.use(Sleep(context))
    handler.use(Mode(context))
    handler.use(Hold(context))
    handler.use(Sopare(context))
    handler.use(Vim(context))
    handler.use(History(context))
    handler.use(Kaldi(context))
    handler.use(Parse(context))
    handler.use(Optimistic(context))
    handler.use(Execute(context))
    handler.init()

    try:
        while True:
            data = in_q.get()
            context.msg = json.loads(data)
            logger.info('main loop got msg %s', context.msg)
            handler.handle(context)

    except KeyboardInterrupt:
        context.msg = {'clear_notify': True}
        handler.handle(context)

        #release shift/control/super or anything from hold mode
        context.msg = {'release_all': True}
        handler.handle(context)

        logger.warning('KeyboardInterrupt')
