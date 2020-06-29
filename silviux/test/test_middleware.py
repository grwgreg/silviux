import unittest
from silviux.middleware.handler import Handler, Context
from silviux.middleware.notify import Notify
from silviux.middleware.hold import Hold
from silviux.middleware.sleep import Sleep
from silviux.middleware.mode import Mode
from silviux.middleware.vim import Vim 
from silviux.middleware.history import History
from silviux.middleware.kaldi import Kaldi 
from silviux.middleware.optimistic import Optimistic 
from silviux.middleware.parse import Parse 
from silviux.middleware.execute import Execute 

import json
import copy
from queue import Queue
from multiprocessing import Pipe

from silviux.config.keys.command import keys, keysyms, vocab
from silviux.config.keys.closed import keys as closed_keys, keysyms as closed_keysyms, vocab as closed_vocab

class TestMiddleware(unittest.TestCase):

    def setUp(self):
        pass


    def make_handler(self):

        context = Context()

        from_mic, to_volume = Pipe(False)
        context.to_volume_monitor = to_volume
        context.test_only_volume_pipe = from_mic
        #note using thread queue here but these are process queues in code
        context.in_q = Queue()
        context.out_q = Queue()

        middleware = {
            "notify": Notify(context, for_test=True),
            "sleep": Sleep(context),
            "mode": Mode(context),
            "hold": Hold(context, for_test=True),
            "vim": Vim(context, for_test=True),
            "history": History(context),
            "kaldi": Kaldi(context),
            "parse": Parse(context),
            "optimistic": Optimistic(context),
            "execute": Execute(context)
        }

        handler = Handler()
        #order matters, can't use dict.values()
        for m in ['notify', 'sleep', 'mode', 'hold', 'vim', 'history', 'kaldi', 'parse', 'optimistic', 'execute']:
            handler.use(middleware[m])

        return handler, context, middleware

    def xdo(self, cmd):
        return '/usr/bin/xdotool ' + cmd

    def kaldi_msg(self, text, n, final):
        msg = {
            'result': {
                'hypotheses': [
                    {'transcript': text}
                ],
                'final': final
                },
            'segment': n
            }
        return msg

    def test_handler(self):
        handler = Handler()
        #note handle will add the .middleware method to the pipeline if you pass an object instead of a function
        def a(nxt):
            def aa(context):
                res = nxt(context + 'a')
                return res + 'g'
            return aa
        def b(nxt):
            def bb(context):
                res = nxt(context + 'b')
                return res + 'f'
            return bb
        def c(nxt):
            def cc(context):
                res = nxt(context + 'c')
                return res + 'e'
            return cc
        handler.nxt = lambda x: x+'d'
        handler.use(a)
        handler.use(b)
        handler.use(c)
        handler.init()
        res = handler.handle('')
        self.assertEqual(res, 'abcdefg')

    def test_modes(self):
        handler, context, _ = self.make_handler()
        handler.init()

        context.parser_manager.set_active('command')
        context.mode = 'command'

        context.msg = {'change_mode': 'alphabet'}
        handler.handle(context)
        self.assertEqual(context.mode, 'alphabet')
        self.assertEqual(context.parser_manager.active, 'alphabet')
        self.assertEqual(context.out_q.get(), json.dumps({'change_decoder': 'alphabet'}))

    #TODO need test for change_mode: 'remove', ie remove entirely from mode stack
    def test_mode_stack(self):
        handler, context, middleware = self.make_handler()
        handler.init()

        context.parser_manager.set_active('command')
        context.mode = 'command'

        context.msg = {'change_mode': 'alphabet'}
        handler.handle(context)
        self.assertEqual(context.mode, 'alphabet')
        self.assertEqual(context.parser_manager.active, 'alphabet')
        self.assertEqual(context.out_q.get(), json.dumps({'change_decoder': 'alphabet'}))

        context.msg = {'change_mode': 'english'}
        handler.handle(context)
        self.assertEqual(context.mode, 'english')
        self.assertEqual(context.parser_manager.active, 'english')
        self.assertEqual(context.out_q.get(), json.dumps({'change_decoder': 'english'}))

        context.msg = {'change_mode': 'pop'}
        handler.handle(context)
        self.assertEqual(context.mode, 'alphabet')
        self.assertEqual(context.parser_manager.active, 'alphabet')
        self.assertEqual(context.out_q.get(), json.dumps({'change_decoder': 'alphabet'}))

        context.msg = {'change_mode': 'push'}
        handler.handle(context)
        self.assertEqual(context.mode, 'english')
        self.assertEqual(context.parser_manager.active, 'english')
        self.assertEqual(context.out_q.get(), json.dumps({'change_decoder': 'english'}))

    def test_kaldi(self):
        handler, context, middleware = self.make_handler()
        def x(nxt):
            def xx(context):
                self.assertEqual(context.last_segment, 1)
                self.assertIsNotNone(context.executor.automator._last_command)
                self.assertEqual(context.parse_error, False)
                self.assertIsNotNone(context.ast)
                return nxt(context)
            return xx
        #add middleware to end of pipeline to check values before they're reset
        handler.use(x)
        handler.init()
        context.parser_manager.set_active('command')
        context.mode = 'command'
        self.assertEqual(context.last_segment, None)
        self.assertEqual(context.executor.automator._last_command, None)
        context.msg = self.kaldi_msg(vocab['a'], 1, True)
        handler.handle(context)
        self.assertEqual(context.ast, None)

        handler, context, _ = self.make_handler()
        def x(nxt):
            def xx(context):
                self.assertEqual(context.last_segment, 1)
                self.assertEqual(context.parse_error, True)
                self.assertEqual(context.ast, None)
                self.assertEqual(context.executor.automator._last_command, None)
                return nxt(context)
            return xx
        handler.use(x)
        handler.init()
        self.assertEqual(context.last_segment, None)
        self.assertEqual(context.executor.automator._last_command, None)
        context.msg = self.kaldi_msg('does not parse', 1, True)
        handler.handle(context)
        self.assertEqual(context.parse_error, False)

    #TODO this is unreadable and brittle, consider more targeted and high level tests?
    def test_optimistic(self):
        handler, context, middleware = self.make_handler()
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        handler.use(test_thing)
        handler.init()
        context.parser_manager.set_active('command')
        context.mode = 'command'
        self.assertEqual(context.optimistic, False)
        context.msg = {'toggle_optimistic': True}
        test_thing.check_context = lambda x: x
        handler.handle(context)
        self.assertEqual(context.optimistic, True)

        context.msg = self.kaldi_msg('%s %s' % (vocab['a'], vocab['b'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            #note tokens should always have END token
            #TODO end token woes
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key a key b')

        context.msg = self.kaldi_msg('%s %s %s' % (vocab['a'], vocab['b'], vocab['c'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 4)
            for t in context.last_tokens[:-2]:
                self.assertEqual(t.done, True)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 3)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key c')

        #if we get a parse error but its not a final transcript we just ignore it, no change
        #to last_tokens or output count
        context.msg = self.kaldi_msg('%s %s %s force parse error' % (vocab['a'], vocab['b'], vocab['c'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, True)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNone(context.ast)
            #TODO need way to test this isn't called
            #execute middleware never runs execute unless ast exists
            #maybe keep some internal counter for each executed command
            #self.assertIsNotNone(context.executor.automator._last_command)
            #last_tokens shouldnt be altered at all, so same as above
            self.assertEqual(len(context.last_tokens), 4)
            #no undo tokens on parse error unless final transcript
            self.assertEqual(len(context.undo_tokens), 0)
            for t in context.last_tokens[:-2]:
                self.assertEqual(t.done, True)
        test_thing.check_context = x
        handler.handle(context)
        #output count shouldnt change
        self.assertEqual(context.output_count, 3)

        #have to undo tokens when new transcript doesnt match before executing the new ast
        #the new ast will have tokens that are marked with .done attr so output isnt repeated
        context.msg = self.kaldi_msg('%s %s' % (vocab['a'], vocab['d'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            #self.assertIsNotNone(context.executor.automator._last_command)
            #TODO convert last_command to array so u can test
            #undo tokens forces this to be called but its overwritten by the 'd' output
            #self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key BackSpace key BackSpace ')
            self.assertEqual(len(context.last_tokens), 3)
            self.assertEqual(len(context.undo_tokens), 3)
            self.assertEqual(context.last_tokens[0].done, True)
            self.assertEqual(context.last_tokens[1].done, False)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key d')

        context.msg = self.kaldi_msg('%s %s %s %s' % (vocab['a'], vocab['d'], vocab['e'], vocab['f'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 5)
#TODO, ignore END token when building up undo tokens
            self.assertEqual(len(context.undo_tokens), 1)
            self.assertEqual(context.undo_tokens[0].type, 'END')
            for t in context.last_tokens[:2]:
                self.assertEqual(t.done, True)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 4)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key e key f')

        #if final transcript has parse error, we undo all previous output 
        #by calling executor.undo_by_backspaces with context.output_count
        context.msg = self.kaldi_msg('%s %s %s parseeoeoerror' % (vocab['a'], vocab['d'], vocab['e'],), 1, True)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, True)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, True)
            self.assertIsNone(context.ast)
            #these are reset after undo_by_backspaces called with previous value of 4
            self.assertEqual(len(context.last_tokens), 0)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 0)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key BackSpace key BackSpace key BackSpace key BackSpace ')

    def test_optimistic_undoes_failure(self):
        handler, context, middleware = self.make_handler()
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        handler.use(test_thing)
        handler.init()
        context.parser_manager.set_active('command')
        context.mode = 'command'
        self.assertEqual(context.optimistic, False)
        context.msg = {'toggle_optimistic': True}
        test_thing.check_context = lambda x: x
        handler.handle(context)
        self.assertEqual(context.optimistic, True)

        context.msg = self.kaldi_msg('%s %s' % (vocab['a'], vocab['b'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key a key b')

        context.msg = self.kaldi_msg('%s %s parseror' % (vocab['a'], vocab['b'],), 1, True)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, True)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, True)
            self.assertIsNone(context.ast)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key BackSpace key BackSpace ')

    def test_optimistic_reset_on_mode_change(self):
        handler, context, middleware = self.make_handler()
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        handler.use(test_thing)
        handler.init()
        context.parser_manager.set_active('command')
        context.mode = 'command'
        self.assertEqual(context.optimistic, False)
        context.msg = {'toggle_optimistic': True}
        test_thing.check_context = lambda x: x
        handler.handle(context)
        self.assertEqual(context.optimistic, True)

        context.msg = self.kaldi_msg('%s %s' % (vocab['a'], vocab['b'],), 99, False)
        def x(context):
            self.assertEqual(context.last_segment, 99)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key a key b')

        context.msg = {'change_mode': 'alphabet'}
        def x(context):
            self.assertEqual(len(context.last_tokens), 0)
            self.assertEqual(context.output_count, 0)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.optimistic, True)

        # TODO can import the alphabet vocab key config if this ever breaks
        # context.msg = self.kaldi_msg('%s %s' % (vocab['c'], vocab['d'],), 1, False)
        context.msg = self.kaldi_msg('c d', 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key c key d')

    def test_optimistic_ast(self):
        handler, context, middleware = self.make_handler()
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        handler.use(test_thing)
        handler.init()
        context.parser_manager.set_active('command')
        context.mode = 'command'
        self.assertEqual(context.optimistic, False)
        context.msg = {'toggle_optimistic': True}
        test_thing.check_context = lambda x: x
        handler.handle(context)
        self.assertEqual(context.optimistic, True)

        context.msg = self.kaldi_msg('%s %s' % (vocab['a'], vocab['b'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key a key b')

        context.msg = self.kaldi_msg('%s %s %s' % (vocab['a'], vocab['b'], vocab['left'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            #when ast has can_optimistic_update set to False, ast is set to None
            #to prevent execution unless final transcript
            self.assertIsNone(context.ast)
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)

        context.msg = self.kaldi_msg('%s %s %s %s' % (vocab['a'], vocab['b'], vocab['left'], vocab['down'],), 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNone(context.ast)
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 2)

        context.msg = self.kaldi_msg('%s %s %s %s' % (vocab['a'], vocab['b'], vocab['left'], vocab['down'],), 1, True)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, True)
            self.assertIsNotNone(context.ast)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key Left key Down')

    #careful of [ and < type characters where keysym doesn't match character itself showing up in transcripts
    #there is explicit handling of apostrophe for "it's" but not for <unk> or [noise]
    #quick fix was to just make them parse as null tokens
    def test_optimistic_english_mode(self):
        handler, context, middleware = self.make_handler()
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        handler.use(test_thing)
        handler.init()
        context.parser_manager.set_active('english')
        context.mode = 'english'
        self.assertEqual(context.optimistic, False)
        context.msg = {'toggle_optimistic': True}
        test_thing.check_context = lambda x: x
        handler.handle(context)
        self.assertEqual(context.optimistic, True)

        context.msg = self.kaldi_msg('hi Hi', 1, False)
        def x(context):
            self.assertEqual(context.last_segment, 1)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 3)
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 6)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key h key i key space key h key i key space')

        context.msg = self.kaldi_msg("it's", 2, False)
        def x(context):
            self.assertEqual(context.last_segment, 2)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 2)
            self.assertEqual(context.last_tokens[0].undo['len'], 5)

        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 5)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key i key t key apostrophe key s key space')

        context.msg = self.kaldi_msg("it is", 2, False)
        def x(context):
            self.assertEqual(context.last_segment, 2)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 3)
            self.assertEqual(len(context.undo_tokens), 2)
            self.assertEqual(context.undo_tokens[0].extra, "it's")

        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 6)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key i key t key space key i key s key space')

        context.msg = self.kaldi_msg("hi <unk>", 3, False)
        def x(context):
            self.assertEqual(context.last_segment, 3)
            self.assertEqual(context.parse_error, False)
            self.assertEqual(context.should_execute, True)
            self.assertEqual(context.final_transcript, False)
            self.assertIsNotNone(context.ast)
            self.assertIsNotNone(context.executor.automator._last_command)
            self.assertEqual(len(context.last_tokens), 3)
            self.assertEqual(context.last_tokens[0].undo['len'], 3)
            self.assertEqual(context.last_tokens[1].type, '<unk>')#scanned as a null token, not ANY

        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.output_count, 3)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key h key i key space')

    def test_optimistic_mode_change_before_final(self):
        pass
        #TODO oct2019 did I fix this or just learn to wait for final transcript before switching modes?
        #switching modes before final transcript comes in causes the incoming transcripts to execute in the new mode
        #ie english mode with optimistic finishes writing command "hello world", pop into programming mode, then final transcript
        #comes in and it outputs an additional "helloworld"
        #fix is to track the transcript id, current doing equality check with previous transcript (which is cleared on mode change)
        #maybe easier fix is to just not clear the previous transcript id and optimistic state?
        #possibly set to drop all kaldi packets with specific id for interval?

    def test_hold(self):
        handler, context, middleware = self.make_handler()
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        handler.use(test_thing)
        handler.init()

        context.parser_manager.set_active('command')
        context.mode = 'command'

        context.msg = self.kaldi_msg('%s %s' % (vocab['hold'], vocab['a'],), 1, True)
        test_thing.check_context = lambda x: x
        handler.handle(context)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool keydown a')
        self.assertEqual(context.in_q.get(), json.dumps({'hold': 'a'}))
        self.assertEqual(context.executor.release_list[0], 'a')

        context.msg = {'hold': 'a'}
        def x(context):
            from_pipe = context.test_only_volume_pipe.recv()
            self.assertEqual(from_pipe, 'NOTIFY_ON')
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.in_q.get(), json.dumps({'change_mode': 'hold'}))

        context.msg = {'change_mode': 'hold'}
        def x(context):
            pass
        test_thing.check_context = x
        handler.handle(context)

        #ignore kaldi and other messages when in hold mode
        context.msg = self.kaldi_msg('%s %s' % (vocab['a'], vocab['b'],), 2, True)
        called = False
        def x(context):
            called = True
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(called, False)
        #need better way to check if executor was called
        #TODO spies or better logging in executor
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool keydown a')

        context.msg = {'volume_monitor': 'SOUND_ON'}
        def x(context):
            self.assertIsNotNone(context.ast)
            self.assertEqual(context.test_only_volume_pipe.recv(), 'NOTIFY_OFF')
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.in_q.get(), json.dumps({'change_mode': 'pop'}))
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool keyup a')

    def test_hold_repeat(self):
        handler, context, middleware = self.make_handler()
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        handler.use(test_thing)
        handler.init()

        context.parser_manager.set_active('command')
        context.mode = 'command'

        context.msg = self.kaldi_msg('%s %s' % (vocab['repeat'], vocab['a'],), 1, True)
        test_thing.check_context = lambda x: x
        handler.handle(context)
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key a')
        self.assertEqual(context.in_q.get(), json.dumps({'hold_repeat': 'a'}))

        context.msg = {'hold_repeat': 'a'}
        def x(context):
            self.assertEqual(context.in_q.get(), json.dumps({'change_mode': 'hold_repeat'}))
            self.assertEqual(context.repeat_key, 'a')
            from_pipe = context.test_only_volume_pipe.recv()
            self.assertEqual(from_pipe, 'NOTIFY_ON')
        test_thing.check_context = x
        handler.handle(context)


        context.msg = {'change_mode': 'hold_repeat'}
        def x(context):
            pass
        test_thing.check_context = x
        handler.handle(context)

        context.msg = {'volume_monitor': 'SOUND_OFF'}
        def x(context):
            self.assertIsNotNone(context.ast)
        test_thing.check_context = x
        handler.handle(context)

        #ignore kaldi and other messages when in hold mode
        context.msg = self.kaldi_msg('%s %s' % (vocab['c'], vocab['b'],), 2, True)
        called = False
        def x(context):
            called = True
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(called, False)
        #need better way to check if executor was called
        #TODO spies or better logging in executor
        self.assertEqual(context.executor.automator._last_command, '/usr/bin/xdotool key a')

        context.msg = {'volume_monitor': 'SOUND_EXTENDED'}
        def x(context):
            self.assertIsNone(context.ast)
            self.assertEqual(context.test_only_volume_pipe.recv(), 'NOTIFY_OFF')
        test_thing.check_context = x
        handler.handle(context)
        self.assertEqual(context.in_q.get(), json.dumps({'change_mode': 'pop'}))

    def test_history(self):
        handler, context, middleware = self.make_handler()
        history_mw = middleware['history']
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        test_thing.check_context = lambda x: x
        handler.use(test_thing)
        handler.init()

        #{'change_mode': 'command'} changes these 2 context variables
        context.parser_manager.set_active('command')
        context.mode = 'command'
        self.assertEqual(context.last_segment, None)
        self.assertEqual(context.executor.automator._last_command, None)
        self.assertEqual(len(history_mw.history), 0)

        context.msg = self.kaldi_msg(vocab['a'], 1, True)
        handler.handle(context)

        self.assertEqual(len(history_mw.history), 1)
        self.assertEqual(history_mw.history[0]['segment'], 1)
        self.assertEqual(history_mw.history[0]['text'], vocab['a'])
        self.assertEqual(history_mw.history[0]['tokens'][0].type, vocab['a'])
        self.assertEqual(history_mw.history[0]['tokens'][0].undo['len'], 1)


        context.msg = self.kaldi_msg(vocab['b'], 2, False)
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 1)

        context.msg = self.kaldi_msg(vocab['b'] + " " + vocab['c'], 2, True)
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 2)
        self.assertEqual(history_mw.history[1]['segment'], 2)
        self.assertEqual(history_mw.history[1]['text'], vocab['b'] + " " + vocab['c'])
        self.assertEqual(history_mw.history[1]['tokens'][0].type, vocab['b'])
        self.assertEqual(len(history_mw.history[1]['tokens']), 2)

        context.msg = {'undo': 1}
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 2)
        self.assertEqual(history_mw.history[1]['segment'], 2)
        self.assertEqual(history_mw.history[1]['tokens'][0].type, vocab['b'])
        self.assertEqual(len(history_mw.history[1]['tokens']), 1)

        context.msg = self.kaldi_msg(vocab['d'] + " " + vocab['e'], 3, True)
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 3)
        self.assertEqual(history_mw.history[2]['segment'], 3)
        self.assertEqual(history_mw.history[2]['tokens'][0].type, vocab['d'])
        self.assertEqual(len(history_mw.history[2]['tokens']), 2)


        #if undo same amount as tokens or greater, should pop off history entirely
        #TODO should I add overflow so you can delete over multiple executed transcripts?
        context.msg = {'undo': 2}
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 2)
        self.assertEqual(history_mw.history[1]['segment'], 2)

        context.msg = self.kaldi_msg(vocab['f'] + " " + vocab['g'], 4, True)
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 3)
        self.assertEqual(history_mw.history[2]['segment'], 4)

        #undo with count -1 undoes entire thing
        context.msg = {'undo': -1}
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 2)
        self.assertEqual(history_mw.history[1]['segment'], 2)

    def test_history_replay(self):
        handler, context, middleware = self.make_handler()
        history_mw = middleware['history']
        class TestThing():
            def middleware(self, nxt):
                def xx(context):
                    self.check_context(context)
                    return nxt(context)
                return xx

        test_thing = TestThing()
        test_thing.check_context = lambda x: x
        handler.use(test_thing)
        handler.init()

        context.parser_manager.set_active('command')
        context.mode = 'command'
        self.assertEqual(context.last_segment, None)
        self.assertEqual(context.executor.automator._last_command, None)
        self.assertEqual(len(history_mw.history), 0)

        context.msg = self.kaldi_msg(vocab['a'], 1, True)
        handler.handle(context)

        self.assertEqual(len(history_mw.history), 1)
        self.assertEqual(history_mw.history[0]['segment'], 1)
        self.assertEqual(history_mw.history[0]['text'], vocab['a'])
        self.assertEqual(history_mw.history[0]['tokens'][0].type, vocab['a'])
        self.assertEqual(history_mw.history[0]['tokens'][0].undo['len'], 1)

        self.assertEqual(history_mw.history[0]['msg'], context.msg)

        context.msg = {"history": "replay"}
        handler.handle(context)

        replay_msg = self.kaldi_msg(vocab['a'], float('inf'), True)
        replay_msg['replay_segment'] = 1
        self.assertEqual(context.in_q.get(), json.dumps(replay_msg))

        context.msg = replay_msg
        handler.handle(context)
        self.assertEqual(len(history_mw.history), 2)
        self.assertEqual(history_mw.history[1]['segment'], float('inf'))
        self.assertEqual(history_mw.history[1]['text'], vocab['a'])
