from threading import Thread
import json
import logging

from silviux.config.keys.command import vocab
from ezmouse.run import run_ezmouse
from vim_server.server import VimServer

logger = logging.getLogger(__name__)
vim_server = VimServer() 

#Custom commands config is for simple mappings of grammar to executor side effects.
#ie you want to map spoken 'special' to a bash command $~/myspecialcommand.sh
#This file is messy in part because I created it by extracting out my worst code
#from the executor. But that's kind of the point. Add sloppy one off code here without breaking
#everything else.

#TODO pass the callbacks the parser's config, then you can replace the hardcoded vocab words
#ie you could add a 'windowjump' command to the config object then do config['vocab']['windowjump']
#tests currently rely on these vocab words not being changed


#custom_commands = {
# 'some_arbitrary_name': {
#   'grammar': [
#     'rhs of grammar rule',#the rule will be _custom_command_some_arbitrary_name ::= rhs of grammar rule
#     'terminal1 terminal2',#the rule will be _custom_command_some_arbitrary_name ::= terminal1 terminal2
#     ]
#   'handler': exector_callback
#   'matcher': parser_callback

#The "handler" function gets passed the executor instance and the tokens/ast nodes from the parser's p_ function arguments
#The "matcher" function gets passed the parser instance and the tokens/ast nodes from the parser's p_ function arguments


def window_handler(executor, matches):
    if matches[0] == 'windy':
        if (len(matches) == 2):
            executor.automator.mod_plus_key(['super'], str(matches[1]))
        else:
            executor.automator.raw_key('super')
            executor.automator.raw_key('Down')
    elif matches[0] == 'folly':
        #gnome 3 is weird/janky about timing of some things
        executor.automator.command('/usr/bin/xdotool key super+m && sleep 0.5 && /usr/bin/xdotool key Right key Right key Down')
    elif matches[0] == 'cloudy':
        # grave is the ~ key, asciitilde is something else
        # executor.automator.command('/usr/bin/xdotool keydown Alt key asciitilde')
        # executor.add_release('Alt')
        return
    elif matches[0] == 'caddy':
        executor.automator.command('/usr/bin/xdotool keydown Alt key Tab')
        executor.add_release('Alt')
    elif matches[0] == 'jumpy':
        executor.automator.command('/usr/bin/xdotool key Alt+grave')
    elif matches[0] == 'moody':
        executor.automator.mod_plus_key(['Alt'], 'Tab')
    else:
        logger.error('unknown value in window_handler')

custom_commands = {
  'window': {
    'grammar': [
       'windy', 
       'windy _number',
       'caddy',
       'cloudy',
       'jumpy',
       'moody',
       'folly'
    ],
    'handler': window_handler
  }
} 

def tmux_handler(executor, matches):
    if matches[1] == 'jumpy':
        executor.automator.command('/usr/bin/xdotool key Ctrl+a key w')
    elif matches[1] == 'moody':
        executor.automator.command('/usr/bin/xdotool key Ctrl+a key percent')
    elif matches[1] == 'windy':
        executor.automator.command('/usr/bin/xdotool key Ctrl+a key quotedbl')
    elif matches[1] == 'cloudy':
        executor.automator.command('/usr/bin/xdotool key Ctrl+a key bracketleft')
    elif matches[1] == 'caddy':
        executor.automator.command('/usr/bin/xdotool key Ctrl+a Ctrl+a')
    elif isinstance(matches[1], int):
        executor.automator.command('/usr/bin/xdotool key Ctrl+a key ' + str(matches[1]))
    else:
        logger.error('bad token in tmux handler %s', matches)

custom_commands['tmux'] = {
    'grammar': [
        'timex jumpy',
        'timex moody',
        'timex windy',
        'timex cloudy',
        'timex caddy',
        'timex _number'
    ],
    'handler': tmux_handler
}

def mouse_handler(executor, matches):
    # self.automator.command('/usr/bin/xdotool click 1')
    # self.automator.command('/usr/bin/xdotool click 3')
    # self.automator.command('/usr/bin/xdotool click --repeat 2 1')
        
    Thread(target=run_ezmouse).start()

custom_commands['mouse'] = {
    'grammar': [
        'moose',
    ],
    'handler': mouse_handler
}


#haha this code was simple before adding support for single word register replacements and optimistic mode support
#TODO needs a full rewrite, fix:
#1. It handles both the cases of using 'reggie ANY' and lone terminal tokens as register word, combining support for both in 1 function resulted in too many conditionals
#2. The register specific terminals should be declared elsewhere, its confusing for no benefit and makes whole custom command a leaky abstraction
def vim_handler(executor, matches):
    if len(matches) == 1:
        register_name = matches[0].type
        token = matches[0]
        msg = ["call", "GetRegister", [register_name], -1]
        register_value = vim_server.send_and_get(json.dumps(msg))
        logger.debug("return value from vim: %s", register_value)
        #set undo attribute for optimistic, must be done before returning because new tokens each time
        token.undo = {'key': True, 'len': len(register_value)}
        if token.done: return
        if register_value.find("NotFoundError:") == 0: return
        for l in register_value:
            #can look up in keys config for most, not 'space' 'backslash' and a few others
            if l == ' ':
                l = 'space'
            executor.automator.xdo('key ' + l)

    if matches[0] == 'reggie':
        if len(matches) == 2:
            msg = ["call", "GetRegister", [matches[1].extra], -1]
            register_value = vim_server.send_and_get(json.dumps(msg))
            logger.debug("return value from vim: %s", register_value)
            #set undo attribute for optimistic, must be done before returning because new tokens each time
            matches[1].undo = {'key': True, 'len': len(register_value)}
            if matches[1].done: return
        else:
            #TODO matches[2] is either ANY or match from _custom_command_vim_programming
            #the match from the custom command stuff is a custom command AST node so we have to drill way down to find the actual register word
            if hasattr(matches[2], 'meta'):
                msg = ["call", "SetRegister", [matches[2].meta[1][0].type], -1]
            else:
                msg = ["call", "SetRegister", [matches[2].extra], -1]
            vim_server.send_and_get(json.dumps(msg))
            vim_server.activate_window()
            return
        
        if register_value.find("NotFoundError:") == 0: return
#important! if you have a register with a value of $what bash thinks it is an env variable
#so be careful, quotes -- && etc are a problem and have to be escaped
#TODO probably an easy fix by using different python command than os.system
        executor.automator.command('/usr/bin/xdotool type "' + register_value + '"')
    if matches[0] == 'mackey':
        if len(matches) == 2:
            if matches[1] == 'ANY':
                macro_name = matches[1].extra
            else:
                macro_name = matches[1].meta[1][0].type
            msg = ["call", "GetMacro", [macro_name], -1]
            macro_value = vim_server.send_and_get(json.dumps(msg))
            logger.debug("return value from vim: %s", macro_value)
            if macro_value.find("NotFoundError:") == 0: return
            val = json.dumps({"macro": macro_value})
            executor.q.put(val)
        else:
            if matches[2] == 'ANY':
                macro_name = matches[2].extra
            else:
                macro_name = matches[2].meta[1][0].type
            msg = ["call", "SetMacro", [macro_name], -1]
            vim_server.send_and_get(json.dumps(msg))
            vim_server.activate_window()
            return
    if matches[0] == 'tennis':
        #TODO this will break in programming mode
        if len(matches) == 2:
           msg = ["call", "GetScript", [matches[1].extra], -1]
           script_value = vim_server.send_and_get(json.dumps(msg))
           logger.debug("return value from vim: %s", script_value)
           if script_value.find("NotFoundError:") == 0: return
           executor.automator.command(script_value)
        else:
           msg = ["call", "SetScript", [matches[2].extra], -1]
           vim_server.send_and_get(json.dumps(msg))
           vim_server.activate_window()
           return

#only optimistic execute when getting register value
#all these conditionals go away if split the vim grammar into their own custom_command
#and add a way for adding terminals TODO if we make handler optional then adding
#a config with only a grammar would be a way... token would be _custom_command_keyofconfig
def vim_matcher(parser, matches):
    if len(matches) == 2 and matches[0] == 'reggie':
        #set register
        pass
    elif len(matches) == 1:
        #terminal
        pass
    else:
        parser.can_optimistic_execute = False


custom_commands['vim'] = {
    'grammar': [
        'reggie ANY',
        'reggie sun ANY',
        'mackey ANY',
        'mackey sun ANY',
        'tennis ANY',
        'tennis sun ANY',
    ],
    'matcher': vim_matcher,
    'handler': vim_handler
}
custom_commands['vim_programming'] = {
    'grammar': [
        'philly',
        'queens',
        'pittsburgh',
        'seattle',
        'washington',
        'columbia',
        'denver',
        'miami',
        'london',
        'elephant',
        'zebra',
        'dolphin',
        # you can recursively define rules here but the match is a 'custom_command' ast node not a simple token
        # likely a better option would be to have the above register names in a list and build it up programatically
        # note as written 'reggie sun reggie sun mackey any' would parse into a single AST and the handler would try
        # to set the 'reggie' register because its the 3rd match token
        # Cleaner option would be a new custom_commands entry with the single tokens and noop executor handler
        # Or even better add support for a new config that is a simple list of terminal tokens to be used within custom commands
        # 'reggie sun ANY',
        'reggie sun _custom_command_vim_programming',
        'mackey _custom_command_vim_programming',
        'mackey sun _custom_command_vim_programming',
        'tennis _custom_command_vim_programming',
        'tennis sun _custom_command_vim_programming',
    ],
    'matcher': vim_matcher,
    'handler': vim_handler
}

def nautilus_handler(executor, matches):
    if matches[2] == None:
        matches[2] = 1
    for _ in range(matches[2]):
        if matches[1] == vocab['left']:
            executor.automator.mod_plus_key(['ctrl'], 'Prior')
        elif matches[1] == vocab['right']: 
            executor.automator.mod_plus_key(['ctrl'], 'Next')

#TODO _repeat just matches a number, we get no repeat functionality from the executor
#Look in parser.py, r_repeat just returns a number and the r_motion returns repeat AST nodes
#I guess if we want to use the executor's repeat ability we have to somehow wrap the custom command AST node
#in a repeat node so the postorder_flat fn invokes our handler callback n times? not sure if thats desirable...
#would be simple enough to manually loop using the _repeat value from our handler function.
custom_commands['nautilus'] = {
    'grammar': [
        "mango %s _repeat" % (vocab['left'],), 
        "mango %s _repeat" % (vocab['right'],), 
    ],
    'handler': nautilus_handler
}

def fkey_handler(executor, matches):
    fkey = 'F' + ''.join([str(n) for n in matches[1:]])
    executor.automator.raw_key(fkey)

custom_commands['fkey'] = {
    'grammar': [
        'floppy _number',
        'floppy _number _number',
    ],
    'handler': fkey_handler
}

