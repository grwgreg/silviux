# Low-level execution of AST commands using xdotool.

import os
import json
import logging

logger = logging.getLogger(__name__)

class ExecuteCommands:
    def __init__(self, automator, q = None):
        self.automator = automator
        self.q = q
        self.release_list = []

    def add_release(self, key):
        self.release_list.append(key)

    #This method was implemented in GenericASTTraversal, ExecuteCommands no longer inherits from it
    def typestring(self, node):
            return node.type

    #should_execute is false when in sleep mode
    #While in sleep mode, we still have to walk the AST because sleep command is handled in executor.
    #For tests we also still execute to build up the xdo commands, enqueue msgs, etc and only bail
    #before actually running the os command by checking for an env variable, SILVIUX_ENV=='test' 
    def execute(self, ast, should_execute=True):
        self.ast = ast
        self.should_execute = should_execute
        self.automator.set_should_execute(should_execute)
        self.automator.output_count = 0
        self.postorder_flat()
        self.automator.flush()
        logger.debug('in executor, post execution output_count: %d', self.automator.output_count)
        return self.automator.output_count

    def postorder_flat(self, node=None):
        if node is None:
            node = self.ast

        name = 'n_' + self.typestring(node)
        if hasattr(self, name):
            func = getattr(self, name)
            func(node)
        else:
            self.default(node)

    def n_chain(self, node):
        for n in node.children:
            self.postorder_flat(n)

    def n_char(self, node):
        if node.token and node.token.done: return
        self.automator.key(node.meta[0])

    def n_raw_char(self, node):
        if node.token and node.token.done: return
        self.automator.raw_key(node.meta[0])

    def n_mod_plus_key(self, node):
        self.automator.mod_plus_key(node.meta, node.children[0].meta[0])

    def n_movement(self, node):
        self.automator.raw_key(node.meta[0])

    def n_sequence(self, node):
        if node.token and node.token.done: return
        for c in node.meta:
            self.automator.raw_key(c)

    def n_word_sequence(self, node):
        n = len(node.children)
        for i in range(0, n):
            if node.children[i].meta.done: continue
            word = node.children[i].meta.extra
            for c in word:
                self.automator.raw_key(c)
            self.automator.raw_key('space')

    def n_programming(self, node):
        n = len(node.children)

        for i in range(0, n):
            if node.children[i].meta.done: continue
            word = node.children[i].meta.extra
            #TODO I don't like having this type of logic spread out all over between executor callbacks and automator
            #there should be one AST node for all text output, maybe all keysym mapping belongs in parser
            #ie the programming mode should set AST.meta = map_to_keysym('some_parsed_snake_case_output')
            for c in word:
                if c == " ": c = "space"
                self.automator.raw_key(c)

    def n_null(self, node):
        pass

    def n_repeat(self, node):
        #TODO explore other methods of repeating output, only motions are repeatable but its common to want repeatable chars, spaces, enters.
        #Currently if we were to make character output repeatable it doesn't work with undo
        #Why not just loop through range and repeatedly invoke the postorder_flat method? instead of repeating xdo?
        self.postorder_flat(node.children[0])
        xdo = self.automator.xdo_list[-1]
        for n in range(1, node.meta[0]):
            self.automator.xdo(xdo)

    def n_custom_command(self, node):
        if not self.should_execute: return
        custom_type, ast_node, custom_commands = node.meta
        custom_commands[custom_type]['handler'](self, ast_node)
        
    def n_raw_string(self, node):
        self.automator.command('/usr/bin/xdotool type "' + node.meta + '"')

    #TODO release list state might belong in middleware
    #note the hold middleware handles its own releasing
    #unfortunate that xdotool doesnt have some release all command, you must specify keysyms
    def n_release(self, node):
        if len(self.release_list) == 0: return
        command = '/usr/bin/xdotool keyup' + ' '
        command += ' '.join(self.release_list)
        self.automator.command(command)
        self.release_list = []

    def n_undo(self, node):
        msg = json.dumps({'undo': node.meta})
        self.q.put(msg)

    def n_replay(self, node):
        msg = json.dumps({'history': 'replay'})
        self.q.put(msg)

    def n_mode(self, node):
        if not self.should_execute: return
        msg_type, data = node.meta
        if msg_type == 'parser':
            msg = json.dumps({'change_mode': data})
            self.q.put(msg)
        elif msg_type == 'optimistic':
            msg = json.dumps({'toggle_optimistic': True})
            self.q.put(msg)

    def n_sleep(self, node):
        msg = json.dumps({'sleep': node.meta})
        self.q.put(msg)

    def n_hold(self, node):
        msg = json.dumps({'hold': node.meta})
        self.q.put(msg)
        self.add_release(node.meta)
        self.automator.command('/usr/bin/xdotool keydown ' + node.meta)

    def n_hold_repeat(self, node):
        msg = json.dumps({'hold_repeat': node.meta})
        self.q.put(msg)
        self.automator.raw_key(node.meta)

    def undo(self, tokens):
        count = 0
        for i in range(len(tokens)-1, -1, -1):
            t = tokens[i]
            if hasattr(t, 'undo'):
                count += t.undo['len']
        if count == 0: return 0
        self.undo_by_backspaces(count)
        return count

    def undo_by_backspaces(self, count):
        if count < 0:
            logger.error("count is less than zero: %d", count)
            raise ValueError
        if count == 0: return
        command = '/usr/bin/xdotool '
        for i in range(count):
            command += 'key BackSpace '
        self.automator.command(command)
        self.automator.flush()
        return

    def default(self, node):
        pass

class Automator:
    def __init__(self):
        self.xdo_list = []
        self.command_list = []
        self.output_count = 0
        self._last_command = None

    def set_should_execute(self, should_execute):
        self.should_execute = should_execute

    def xdo(self, xdo):
        self.xdo_list.append(xdo)

    def command(self, command):
        self.command_list.append(command)

    def flush(self):
        if len(self.xdo_list) > 0:
          command = '/usr/bin/xdotool' + ' '
          command += ' '.join(self.xdo_list)
          self.execute(command)
          self.xdo_list = []
        if len(self.command_list) > 0:
          for c in self.command_list:
            self.execute(c)
          self.command_list = []


    def execute(self, command):
        if command == '': return
        self._last_command = command
        if self.should_execute and os.environ.get('SILVIUX_ENV') != 'test':
            os.system(command)

    #TODO, I want all keysym stuff in AST's, this is still used from programming AST nodes
    def raw_key(self, k):
        if(k == "'"): k = 'apostrophe'
        elif(k == '.'): k = 'period'
        elif(k == '-'): k = 'minus'
        elif(k == '_'): k = 'underscore'
        self.xdo('key ' + k)
        self.output_count += 1

    def mod_plus_key(self, mods, k):
        command = 'key '
        command += '+'.join(mods)
        k = str(k)
        command += '+' + k
        self.xdo(command)
