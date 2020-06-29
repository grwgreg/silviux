import unittest
from ..scan import Token
from ..execute import Automator
from ..execute import ExecuteCommands
from ..ast import AST
from ..ast import printAST
from silviux.middleware.optimistic import Optimistic
from ..parser import parser_manager

from silviux.middleware.handler import Handler, Context

import json
import queue
from vim_server.server import VimServer
vim_server = VimServer()

from silviux.config.keys.command import keys, keysyms, vocab, modes
from silviux.config.keys.closed import keys as closed_keys, keysyms as closed_keysyms, vocab as closed_vocab

class TestGrammar(unittest.TestCase):

    def setUp(self):
        self.pm = parser_manager.ParserManager()
        self.pm.set_active('command')

    def parse_and_execute(self, text, with_q=False):
        tokens = self.pm.scan(text)
        ast = self.pm.parse(tokens)
        automator = Automator()
        if with_q:
            main_loop_q = queue.Queue()
            executor = ExecuteCommands(automator, main_loop_q)
            executor.execute(ast)
            return [automator, executor, ast, tokens, main_loop_q]
        else:
            executor = ExecuteCommands(automator)
            executor.execute(ast)
            return [automator, executor, ast, tokens]

    def test_scan(self):
        result = self.pm.scan(vocab['a'] + " somewordnotinvocab " + vocab['t'])
        expected = [vocab['a'], "ANY", vocab['t'], "END"]
        self.assertEqual(result, expected)

    def test_scan_escape_word(self):
        result = self.pm.scan(vocab['4'])
        expected = [vocab['4'], "END"]
        self.assertEqual(result, expected)
        self.assertEqual(result[0].type, vocab['4'])

        result = self.pm.scan(vocab['escape token'] + ' ' + vocab['4'])
        expected = ["ANY", "END"]
        self.assertEqual(result, expected)
        self.assertEqual(result[0].type, 'ANY')
        self.assertEqual(result[0].extra, vocab['4'])

    def test_parser_chars(self):
        tokens = self.pm.scan(vocab['a'] + ' ' + vocab['t'])
        ast = self.pm.parse(tokens)
        self.assertEqual(ast.type, 'chain')
        self.assertEqual(len(ast), 2)
        self.assertEqual(ast[0].type, 'raw_char')
        self.assertEqual(ast[0].meta[0], 'a')

        self.assertEqual(ast[1].type, 'raw_char')
        self.assertEqual(ast[1].meta[0], 't')

    def test_parser_repeat(self):
        tokens = self.pm.scan(vocab['up'] + ' ' + vocab['3'])
        ast = self.pm.parse(tokens)
        self.assertEqual(ast.type, 'chain')
        self.assertEqual(len(ast), 1)
        self.assertEqual(ast[0].type, 'repeat')
        self.assertEqual(ast[0].meta[0], 3)

        ast = ast[0]
        self.assertEqual(len(ast), 1)
        self.assertEqual(len(ast[0]), 0)
        self.assertEqual(ast[0].type, 'movement')
        self.assertEqual(ast[0].meta[0], 'Up')

    def test_parser_phrase(self):
        tokens = self.pm.scan("%s i can jump" % (vocab['phrase'],))
        ast = self.pm.parse(tokens)
        self.assertEqual(ast.type, 'chain')
        self.assertEqual(len(ast), 1)
        self.assertEqual(len(ast[0]), 3)
        self.assertEqual(ast[0].type, 'word_sequence')
        self.assertEqual(ast[0][0].meta.extra, 'i')
        self.assertEqual(ast[0][1].meta.extra, 'can')
        self.assertEqual(ast[0][2].meta.extra, 'jump')

    def test_execute_char(self):
        automator, executor, ast, tokens = self.parse_and_execute(vocab['t'])
        self.assertEqual(automator._last_command, '/usr/bin/xdotool key t')

    def test_execute_upperchar(self):
        automator, executor, ast, tokens = self.parse_and_execute("%s %s" % (vocab['uppercase'], vocab['t'],))
        self.assertEqual(automator._last_command, '/usr/bin/xdotool key T')

    def test_execute_phrase(self):
        automator, executor, ast, tokens = self.parse_and_execute("%s I can jump" % (vocab['phrase'],))
        command = '/usr/bin/xdotool key i key space key c key a key n key space key j key u key m key p key space'

        self.assertEqual(automator._last_command, command)

    def test_nautilus(self):
        automator, executor, ast, tokens = self.parse_and_execute("mango "+vocab['right'])
        command = '/usr/bin/xdotool key ctrl+Next'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute("mango "+vocab['left'])
        command = '/usr/bin/xdotool key ctrl+Prior'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute("mango "+vocab['left']+ ' '+vocab['3'])
        command = '/usr/bin/xdotool key ctrl+Prior key ctrl+Prior key ctrl+Prior'
        self.assertEqual(automator._last_command, command)

    #this was moved to a custom command
    #TODO the custom commands config doesnt use config vocab so command words are hard coded in tests still
    def test_window(self):
        automator, executor, ast, tokens = self.parse_and_execute('windy')
        command = '/usr/bin/xdotool key super key Down'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute("windy "+vocab['6'])
        command = '/usr/bin/xdotool key super+6'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute('caddy')
        command = '/usr/bin/xdotool keydown Alt key Tab'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(executor.release_list[0], 'Alt')

        automator, executor, ast, tokens = self.parse_and_execute('moody')
        command = '/usr/bin/xdotool key Alt+Tab'
        self.assertEqual(automator._last_command, command)

    def test_parser_tmux(self):
        automator, executor, ast, tokens = self.parse_and_execute("timex cloudy")
        command = '/usr/bin/xdotool key Ctrl+a key bracketleft'
        self.assertEqual(automator._last_command, command)


        automator, executor, ast, tokens = self.parse_and_execute('timex %s' % (vocab['2']))
        command = '/usr/bin/xdotool key Ctrl+a key 2'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute("timex caddy")
        command = '/usr/bin/xdotool key Ctrl+a Ctrl+a'
        self.assertEqual(automator._last_command, command)


    def test_release(self):
        tokens = self.pm.scan(vocab['release'])
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.add_release('Alt')
        executor.add_release('Control')
        executor.execute(ast)
        command = '/usr/bin/xdotool keyup Alt Control'
        self.assertEqual(automator._last_command, command)

    #this is now a custom command
    def test_floppy(self):
        automator, executor, ast, tokens = self.parse_and_execute("floppy "+vocab['7'] + " " + vocab['9'])
        command = '/usr/bin/xdotool key F79'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute("floppy %s" % vocab['4'])
        command = '/usr/bin/xdotool key F4'
        self.assertEqual(automator._last_command, command)

    def test_modifiers(self):
        automator, executor, ast, tokens = self.parse_and_execute("%s %s" % (vocab['control'], vocab['g'],))
        command = '/usr/bin/xdotool key ctrl+g'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute("%s %s %s" % (vocab['control'], vocab['shift'], vocab['g'],))
        command = '/usr/bin/xdotool key ctrl+Shift+g'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute("%s %s" % (vocab['super'], vocab['left'],))
        command = '/usr/bin/xdotool key super+Left'
        self.assertEqual(automator._last_command, command)

    def test_letters(self):
        automator, executor, ast, tokens = self.parse_and_execute('%s %s' % (vocab['i'], vocab['b'],))
        command = '/usr/bin/xdotool key i key b'
        self.assertEqual(automator._last_command, command)

    def test_chars(self):
        automator, executor, ast, tokens = self.parse_and_execute('%s %s' % (vocab['('], vocab[')'],))
        command = '/usr/bin/xdotool key parenleft key parenright'
        self.assertEqual(automator._last_command, command)

    def test_movements(self):
        automator, executor, ast, tokens = self.parse_and_execute('%s %s %s' % (vocab['left'], vocab['1'], vocab['1'],))
        command = '/usr/bin/xdotool key Left key Left key Left key Left key Left key Left key Left key Left key Left key Left key Left'
        self.assertEqual(automator._last_command, command)

    def test_word(self):
        automator, executor, ast, tokens = self.parse_and_execute("%s bye" % (vocab['word'],))
        command = '/usr/bin/xdotool key b key y key e'
        self.assertEqual(automator._last_command, command)

    def test_phrase_single(self):
        automator, executor, ast, tokens = self.parse_and_execute("%s to" % (vocab['phrase'],))
        command = '/usr/bin/xdotool key t key o key space'
        self.assertEqual(automator._last_command, command)

    def test_phrase_multiple(self):
        automator, executor, ast, tokens = self.parse_and_execute("%s to the back" % (vocab['phrase'],))
        command = '/usr/bin/xdotool key t key o key space key t key h key e key space key b key a key c key k key space'
        self.assertEqual(automator._last_command, command)

    def test_parser_numbers(self):
        automator, executor, ast, tokens = self.parse_and_execute('%s %s' % (vocab['number'], vocab['6'],))
        command = '/usr/bin/xdotool key 6'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute('%s %s %s' % (vocab['number'], vocab['6'], vocab['7'],))
        command = '/usr/bin/xdotool key 6 key 7'
        self.assertEqual(automator._last_command, command)

        automator, executor, ast, tokens = self.parse_and_execute('%s %s %s' % (vocab['number'], vocab['0'], vocab['7'],))
        command = '/usr/bin/xdotool key 0 key 7'
        self.assertEqual(automator._last_command, command)

    def test_parser_repeat_numbers(self):
        automator, executor, ast, tokens = self.parse_and_execute('%s %s %s' % (vocab['left'], vocab['1'], vocab['1'],))
        command = '/usr/bin/xdotool key Left key Left key Left key Left key Left key Left key Left key Left key Left key Left key Left'
        self.assertEqual(automator._last_command, command)

#TODO never implemented english numbers, ie 'three hundred and five', run through lib to get int(305)
#    def xtest_english_numbers(self):
#        tokens = self.pm.scan("%s three four five" % (vocab['english number'],))
#        ast = self.pm.parse(tokens)
#        automator = Automator()
#        executor = ExecuteCommands(automator)
#        executor.execute(ast)
#        command = '/usr/bin/xdotool key 6'
#        #self.assertEqual(automator._last_command, command)

    def test_undo_tokens(self):
        tokens = self.pm.scan('%s %s %s foo' % (vocab['t'], vocab['i'], vocab['word'],))
        ast = self.pm.parse(tokens)
        self.assertEqual(tokens[0].undo['key'], True)
        self.assertEqual(tokens[0].undo['len'], 1)
        self.assertEqual(tokens[3].undo['key'], True)
        self.assertEqual(tokens[3].undo['len'], 3)
        self.assertEqual(hasattr(tokens[2], 'undo'), False)

        tokens = self.pm.scan("%s this is hard" % (vocab['phrase'],))
        ast = self.pm.parse(tokens)
        self.assertEqual(tokens[1].undo['len'], 5)
        self.assertEqual(tokens[2].undo['len'], 3)
        self.assertEqual(tokens[3].undo['len'], 5)


    def test_diff_tokens(self):
        a = self.pm.scan("%s it will joe work" % (vocab['phrase'],))
        b = self.pm.scan("%s it will go work" % (vocab['phrase'],))
        res = Optimistic.diff_and_mark_tokens(a,b)
#it returns the tokens to undo and modifies current tokens which have already been
#seen by adding .done = True
        self.assertEqual(res[0], a[3])
        self.assertEqual(res[1], a[4])
        self.assertEqual(b[0].done, True)
        self.assertEqual(b[1].done, True)
        self.assertEqual(b[2].done, True)
        self.assertEqual(b[3].done, False)

        #TODO, I think this is here because I was unhappy with how END token
        #was always returned as a new token or something with optimistic
        #look at middleware tests, always returning END makes it annoying
        #to test if new token is in next transcript
        a = self.pm.scan(vocab['i'])
        b = self.pm.scan(vocab['i'])
        res = Optimistic.diff_and_mark_tokens(a,b)
        self.assertEqual(b[0].done, True)

    def test_done_token_executor(self):
        tokens = self.pm.scan('%s %s %s' % (vocab['t'], vocab['i'], vocab['p'],))
        tokens[0].done = True
        tokens[1].done = True
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast, tokens)
        command = '/usr/bin/xdotool key p'
        self.assertEqual(command, automator._last_command)


        #this will never happen, not sure this test is needed
        #all tokens to left of first difference will be marked done
        tokens = self.pm.scan('%s %s %s' % (vocab['t'], vocab['*'], vocab['~'],))
        tokens[1].done = True
        tokens[2].done = True
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast, tokens)
        command = '/usr/bin/xdotool key t'
        self.assertEqual(command, automator._last_command)


        tokens = self.pm.scan("%s %s moooooooogrooooooooooooooooo %s" % (vocab['t'], vocab['word'], vocab['e'],))

        tokens[0].done = True
        tokens[1].done = True
        tokens[2].done = True

        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast, tokens)
        command = '/usr/bin/xdotool key e'
        self.assertEqual(command, automator._last_command)

        tokens = self.pm.scan("%s this is me" % (vocab['phrase'],))

        tokens[0].done = True
        tokens[1].done = True
        tokens[2].done = True

        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast, tokens)
        command = '/usr/bin/xdotool key m key e key space'
        self.assertEqual(command, automator._last_command)


    def test_can_optimistic_execute_parser(self):
        #delete/backspace don't have an undoable action
        #same for things like switching windows, etc
        tokens = self.pm.scan('%s %s %s' % (vocab['t'], vocab['delete'], vocab[')'],))
        ast = self.pm.parse(tokens)
        self.assertEqual(ast.can_optimistic_execute, False)
        
        tokens = self.pm.scan('%s %s %s' % (vocab['t'], vocab['space'], vocab[')'],))
        ast = self.pm.parse(tokens)
        self.assertEqual(ast.can_optimistic_execute, True)

    def test_parser_manager_scan(self):
        pm = parser_manager.ParserManager()
        tokens = pm.scan("moose boop %s hello" % (vocab['word'],))
        self.assertEqual(len(tokens), 5)
        self.assertEqual(tokens[0], 'moose')
        self.assertEqual(tokens[0].__class__, Token)

        pm.set_active('alphabet')
        tokens = pm.scan("a b hello")
        self.assertEqual(len(tokens), 4)
        self.assertEqual(tokens[0], 'a')
        self.assertEqual(tokens[1], 'b')
        self.assertEqual(tokens[2], 'ANY')
        self.assertEqual(tokens[0].__class__, Token)

    def test_parser_programming(self):
        automator, executor, ast, tokens = self.parse_and_execute("%s does this work" % (vocab['pascal case'],))
        command = '/usr/bin/xdotool key D key o key e key s key T key h key i key s key W key o key r key k'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 4)


        automator, executor, ast, tokens = self.parse_and_execute("%s does this work" % (vocab['camel case'],))
        command = '/usr/bin/xdotool key d key o key e key s key T key h key i key s key W key o key r key k'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 4)

        automator, executor, ast, tokens = self.parse_and_execute("%s does this work" % (vocab['join case'],))
        command = '/usr/bin/xdotool key d key o key e key s key t key h key i key s key w key o key r key k'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 4)

        automator, executor, ast, tokens = self.parse_and_execute("%s does this work" % (vocab['snake case'],))
        command = '/usr/bin/xdotool key d key o key e key s key underscore key t key h key i key s key underscore key w key o key r key k'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 5)

        automator, executor, ast, tokens = self.parse_and_execute("%s does this work" % (vocab['dashed case'],))
        command = '/usr/bin/xdotool key d key o key e key s key minus key t key h key i key s key minus key w key o key r key k'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 5)

        automator, executor, ast, tokens = self.parse_and_execute("%s does this work" % (vocab['spaced case'],))
        command = '/usr/bin/xdotool key d key o key e key s key space key t key h key i key s key space key w key o key r key k'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 5)

        automator, executor, ast, tokens = self.parse_and_execute("%s does this work" % (vocab['caps case'],))
        command = '/usr/bin/xdotool key D key O key E key S key T key H key I key S key W key O key R key K'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 4)

        automator, executor, ast, tokens = self.parse_and_execute("%s DoeS THIS wOrk" % (vocab['lowcaps case'],))
        command = '/usr/bin/xdotool key d key o key e key s key t key h key i key s key w key o key r key k'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(tokens[1].undo['len'], 4)
        self.assertEqual(tokens[3].undo['len'], 4)

        # DO NOT REMOVE
        # This is the case to use when developing operators that work on words and characters
        # automator, executor, ast, tokens = self.parse_and_execute("%s does this %s work" % (vocab['spaced case'], vocab['=']))
        # command = '/usr/bin/xdotool key d key o key e key s key space key t key h key i key s key space key w key o key r key k'
        # self.assertEqual(automator._last_command, command)
        # self.assertEqual(tokens[1].undo['len'], 4)
        # self.assertEqual(tokens[3].undo['len'], 5)
        
    #TODO this custom command type stuff should be separated into another test file
    def test_parser_register(self):
        tokens = self.pm.scan("reggie rosie")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)

        class MockSocket:
            def sendall(self, msg):
                self.msg = msg            
        
        socket = MockSocket()
        q = queue.Queue()
        #vim.server.send_and_get blocks until vim sends result and its put on queue
        q.put('bar')
        vim_server._set_for_test(socket, q)

        executor.execute(ast)
        msg = b'["call", "GetRegister", ["rosie"], -1]'
        self.assertEqual(msg, socket.msg)
        command = '/usr/bin/xdotool type "bar"'
        self.assertEqual(automator._last_command, command)

		#set register
        tokens = self.pm.scan("reggie sun foo")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        q.put('success')
        executor.execute(ast)
        msg = b'["call", "SetRegister", ["foo"], -1]'
        self.assertEqual(msg, socket.msg)

    def test_parser_register_progmode(self):
        self.pm.set_active('programming')
        tokens = self.pm.scan("seattle")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)

        class MockSocket:
            def sendall(self, msg):
                self.msg = msg            
        
        socket = MockSocket()
        q = queue.Queue()
        #vim.server.send_and_get blocks until vim sends result and its put on queue
        q.put('bar')
        vim_server._set_for_test(socket, q)

        executor.execute(ast)
        msg = b'["call", "GetRegister", ["seattle"], -1]'
        self.assertEqual(msg, socket.msg)
        command = '/usr/bin/xdotool key b key a key r'
        self.assertEqual(automator._last_command, command)

		##set register
        tokens = self.pm.scan("reggie sun seattle")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        q.put('success')
        executor.execute(ast)
        msg = b'["call", "SetRegister", ["seattle"], -1]'
        self.assertEqual(msg, socket.msg)
        self.pm.set_active('command')

    def test_parser_register_optimistic(self):

        #not necessary but just to make sure
        self.pm.modes[self.pm.active]['parser'].can_optimistic_execute = False

        tokens = self.pm.scan("reggie rosie")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)

        class MockSocket:
            def sendall(self, msg):
                self.msg = msg            
        
        socket = MockSocket()
        q = queue.Queue()
        #vim.server.send_and_get blocks until vim sends result and its put on queue
        q.put('bar')
        vim_server._set_for_test(socket, q)

        executor.execute(ast)

        self.assertEqual(tokens[1].undo['len'], 3)
        self.assertEqual(tokens[1].undo['key'], True)
        self.assertEqual(self.pm.modes[self.pm.active]['parser'].can_optimistic_execute, True)

		#set register
        #this can't be optimistic because it pops up the vim terminal
        tokens = self.pm.scan("reggie sun foo")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        q.put('success')
        executor.execute(ast)

        self.assertEqual(self.pm.modes[self.pm.active]['parser'].can_optimistic_execute, False)

    def test_parser_macro(self):
        tokens = self.pm.scan("mackey rosie")
        ast = self.pm.parse(tokens)
        automator = Automator()
        main_loop_q = queue.Queue()
        executor = ExecuteCommands(automator, main_loop_q)

        class MockSocket:
            def sendall(self, msg):
                self.msg = msg            
        
        socket = MockSocket()
        q = queue.Queue()
        #vim.server.send_and_get blocks until vim sends result and its put on queue
        q.put('atlas bravo')
        vim_server._set_for_test(socket, q)

        executor.execute(ast)
        msg = b'["call", "GetMacro", ["rosie"], -1]'
        self.assertEqual(msg, socket.msg)
        result_on_q = main_loop_q.get()
        expected = json.dumps({"macro": "atlas bravo"})
        self.assertEqual(expected, result_on_q)

		#set macro
        tokens = self.pm.scan("mackey sun foo")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        q.put('success')
        executor.execute(ast)
        msg = b'["call", "SetMacro", ["foo"], -1]'
        self.assertEqual(msg, socket.msg)

    def test_parser_script(self):
        tokens = self.pm.scan("tennis rosie")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)

        class MockSocket:
            def sendall(self, msg):
                self.msg = msg            
        
        socket = MockSocket()
        q = queue.Queue()
        #vim.server.send_and_get blocks until vim sends result and its put on queue
        q.put('xdotool key g')
        vim_server._set_for_test(socket, q)

        executor.execute(ast)
        msg = b'["call", "GetScript", ["rosie"], -1]'
        self.assertEqual(msg, socket.msg)
        self.assertEqual(automator._last_command, 'xdotool key g')

		#set script
        tokens = self.pm.scan("tennis sun foo")
        ast = self.pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        q.put('success')
        executor.execute(ast)
        msg = b'["call", "SetScript", ["foo"], -1]'
        self.assertEqual(msg, socket.msg)

    def test_parser_raw_string(self):
        ast = AST('raw_string', 'this works')
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast)
        command = '/usr/bin/xdotool type "this works"'
        self.assertEqual(automator._last_command, command)

    def test_text_parser(self):
        self.pm.set_active('text')
        automator, executor, ast, tokens = self.parse_and_execute("does this work")
        command = '/usr/bin/xdotool key d key o key e key s key space key t key h key i key s key space key w key o key r key k key space key space'
        self.assertEqual(automator._last_command, command)


        #TODO hardcoded 'stop' as the word to pop mode, rewrite text_parser entirely if this breaks
        self.pm.set_active('text')
        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute("does this stop work", True)
        command = '/usr/bin/xdotool key d key o key e key s key space key t key h key i key s key space key w key o key r key k key space key space'
        self.assertEqual(automator._last_command, command)

        msg = json.dumps({'change_mode': 'pop'})
        self.assertEqual(msg, main_loop_q.get())

        #TODO have to reset after test which isn't great, either have test file per mode or don't share obj between tests
        self.pm.set_active('command')

    def test_sleep(self):
        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute(vocab['sleep'], True)

        msg = json.dumps({'sleep': 'sleep'})
        self.assertEqual(msg, main_loop_q.get())

        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute(vocab['wakeup'], True)

        msg = json.dumps({'sleep': 'wakeup'})
        self.assertEqual(msg, main_loop_q.get())

    def test_modes(self):
        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute('%s %s' % (vocab['mode'], vocab['0'],), True)

        msg = json.dumps({'change_mode': 'command'})
        self.assertEqual(msg, main_loop_q.get())

        ivocab = {v:k for k,v in list(modes['words'].items())}
        text_word = ivocab['text']
        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute('%s %s' % (vocab['mode'], text_word), True)

        msg = json.dumps({'change_mode': 'text'})
        self.assertEqual(msg, main_loop_q.get())

        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute("%s %s" % (vocab['mode'], vocab['uppercase'],), True)

        msg = json.dumps({'toggle_optimistic': True})
        self.assertEqual(msg, main_loop_q.get())

    def test_holder(self):
        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute('%s %s' % (vocab['hold'], vocab['a']), True)
        command = '/usr/bin/xdotool keydown a'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(executor.release_list[0], 'a')

        msg = json.dumps({'hold': 'a'})
        self.assertEqual(msg, main_loop_q.get())

        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute('%s %s' % (vocab['hold'], vocab['left']), True)
        command = '/usr/bin/xdotool keydown Left'
        self.assertEqual(automator._last_command, command)
        self.assertEqual(executor.release_list[0], 'Left')

        msg = json.dumps({'hold': 'Left'})
        self.assertEqual(msg, main_loop_q.get())

    def test_hold_repeater(self):
        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute('%s %s' % (vocab['repeat'], vocab['a']), True)
        command = '/usr/bin/xdotool key a'
        self.assertEqual(automator._last_command, command)

        msg = json.dumps({'hold_repeat': 'a'})
        self.assertEqual(msg, main_loop_q.get())

    def test_null_ast(self):
        pm = parser_manager.ParserManager()
        pm.set_active('closed')

        tokens = pm.scan('<UNK> %s' % (closed_vocab['a']))
        ast = pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast)
        command = '/usr/bin/xdotool key a'
        self.assertEqual(automator._last_command, command)

        tokens = pm.scan("!SIL %s <UNK>" % closed_vocab['a'])
        ast = pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast)
        command = '/usr/bin/xdotool key a'
        self.assertEqual(automator._last_command, command)

    def test_prog_parser(self):
        pm = parser_manager.ParserManager()
        pm.set_active('programming')

        tokens = pm.scan('%s def %s some %s function' % (closed_vocab['a'], closed_vocab['space'], closed_vocab['space'],))
        ast = pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast)
        command = '/usr/bin/xdotool key a key d key e key f key space key s key o key m key e key space key f key u key n key c key t key i key o key n'
        self.assertEqual(automator._last_command, command)

        tokens = pm.scan('%s some words here' % (vocab['snake case'],))
        ast = pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast)
        command = '/usr/bin/xdotool key s key o key m key e key underscore key w key o key r key d key s key underscore key h key e key r key e'
        self.assertEqual(automator._last_command, command)

        #make sure shortest RHS!!! had to reverse order of chained command in grammar
        tokens = pm.scan('%s some words here dot' % (vocab['snake case'],))
        ast = pm.parse(tokens)
        automator = Automator()
        executor = ExecuteCommands(automator)
        executor.execute(ast)
        command = '/usr/bin/xdotool key s key o key m key e key underscore key w key o key r key d key s key underscore key h key e key r key e key period'
        self.assertEqual(automator._last_command, command)

    def test_undo(self):
        self.pm.set_active('command')
        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute('%s' % (vocab['undo']), True)
        msg = json.dumps({'undo': -1})
        self.assertEqual(msg, main_loop_q.get())

        automator, executor, ast, tokens, main_loop_q = self.parse_and_execute('%s %s' % (vocab['undo'], vocab['2']), True)
        msg = json.dumps({'undo': 2})
        self.assertEqual(msg, main_loop_q.get())
