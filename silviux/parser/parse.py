# Parser, based on John Aycock's SPARK examples

from .spark import GenericParser
from .spark import GenericASTBuilder
from ..ast import AST
import string
import json
import copy
import logging

logger = logging.getLogger(__name__)

class GrammaticalError(Exception):
    def __init__(self, string):
        self.string = string
    def __str__(self):
        return self.string

class CoreParser(GenericParser):
    def __init__(self, config):
        self.keysyms = config['keysyms']
        self.vocab = config['vocab']
        self.modes = config['modes']
        self.custom_commands = config['custom_commands']
        self.can_optimistic_execute = True

        #Dynamically add methods for the custom grammar before calling super
        self.init_custom_command_grammar()
        GenericParser.__init__(self, '_single_input')

    def parse_mutate_tokens(self, ts):
        #TODO consider putting can_optimistic onto the tokens themselves
        #then iterate through after parsing to check if any token opted out/in of optimsitic
        self.can_optimistic_execute = True
        ast = self.parse(ts)
        ast.can_optimistic_execute = self.can_optimistic_execute
        return ast

    def typestring(self, token):
        return token.type

    def error(self, token):
        raise GrammaticalError(
            "Unexpected token `%s' (word number %d)" % (token, token.word_index))

    #TODO post_scan possibly should be dependent on mode and not the parser it uses
    def post_scan(self, tokens):
      result = []
      for i,t in enumerate(tokens):
        if i > 0 and tokens[i-1].type == self.vocab['escape token']:
            t.extra = t.type
            t.type = 'ANY'
        if t.type != self.vocab['escape token']:
            result.append(t)
      return result


    def p_single_input(self, args):
        '''
            _single_input ::= END
            _single_input ::= _chained_commands END
            _single_input ::= _solo_commands END
        '''
        if len(args) > 0:
            return args[0]
        else:
            return AST('')

    def p_solo_commands(self, args):
        '''
            _solo_commands ::= _undo
            _solo_commands ::= _replay
            _solo_commands ::= _sleep
            _solo_commands ::= _mode
            _solo_commands ::= _release
            _solo_commands ::= _hold
        '''
        if(len(args) == 1):
            return AST('chain', None, [ args[0] ])
        else:
            args[1].children.insert(0, args[0])
            return args[1]

    def p_chained_commands(self, args):
        '''
            _chained_commands ::= _single_command
            _chained_commands ::= _single_command _chained_commands
        '''
        if(len(args) == 1):
            return AST('chain', None, [ args[0] ])
        else:
            args[1].children.insert(0, args[0])
            return args[1]

    def p_single_command(self, args):
        '''
            _single_command ::= _letter
            _single_command ::= _uppercase_letter
            _single_command ::= _number_rule
            _single_command ::= _movement
            _single_command ::= _character
            _single_command ::= _editing
            _single_command ::= _modifiers
            _single_command ::= _english
            _single_command ::= _word_sentence
            _single_command ::= _word_phrase
            _single_command ::= _custom_command 
            _single_command ::= _meta_actions
            _single_command ::= _programming
            _single_command ::= _null
        '''
        return args[0]

    def r_movement(self):
        return "\n".join((
            "_movement ::= %s _repeat" % (self.vocab['up'],), 
            "_movement ::= %s _repeat" % (self.vocab['down'],), 
            "_movement ::= %s _repeat" % (self.vocab['left'],), 
            "_movement ::= %s _repeat" % (self.vocab['right'],), 
            "_movement ::= %s _repeat" % (self.vocab['pageup'],), 
            "_movement ::= %s _repeat" % (self.vocab['pagedown'],), 
        ))

    def p_movement(self, args):
        self.can_optimistic_execute = False
        if args[1] != None:
            return AST('repeat', [ args[1] ], [
                AST('movement', [ self.keysyms[args[0].type] ])
            ])
        else:
            return AST('movement', [ self.keysyms[args[0].type] ])

    def p_repeat(self, args):
        '''
            _repeat ::=
            _repeat ::= _number
        '''
        if len(args) > 0:
            return int(args[0])
        else:
            return None

    def r_number_rule(self):
        return "\n".join((
            "_number_rule ::= %s _number" % (self.vocab['number'],), 
            ))
    def p_number_rule(self, args):
        self.can_optimistic_execute = False
        return AST('sequence', str(args[1]))

    def p_number(self, args):
        '''
            _number ::= _single_number
            _number ::= _single_number _number
        '''
        if(len(args) == 1):
            return args[0]
        else:
            return str(args[0]) + str(args[1])

    def r_single_number(self):
        return "\n".join(
            ["_single_number ::= %s" % (self.vocab[str(i)],) for i in range(10)]
        )

    def p_single_number(self, args):
        return int(self.keysyms[args[0].type])

    def r_english_numbers(self):
        return "\n".join(
            ["_english_numbers ::= %s %s" % (self.vocab['english number'], self.vocab[str(i)],) for i in range(10)]
        )

    def p_english_numbers(self, args):
        #TODO this isn't implemented yet, there are libs that could be used here
        #ie 'sixty thousand three hundred => 60,300'
        logger.debug('in english nums %s', args)
        self.can_optimistic_execute = False
        return AST('null', [ ])

    def r_uppercase_letter(self):
        return "\n".join((
            "_uppercase_letter ::= %s _letter" % (self.vocab['uppercase'],),
        ))

    def p_uppercase_letter(self, args):
        ast = args[1]
        ast.meta[0] = ast.meta[0].upper()
        return ast

    def r_letter(self):
        return "\n".join(
            ["_letter ::= %s" % (self.vocab[c],) for c in string.ascii_lowercase]
        )

    def p_letter(self, args):
        args[0].undo = {'key': True, 'len': 1}
        return AST('raw_char', [ self.keysyms[args[0].type] ], token=args[0])

    def r_character(self):
        return "\n".join((
            "_character ::= %s" % (self.vocab['escape'],), 
            "_character ::= %s" % (self.vocab[':'],), 
            "_character ::= %s" % (self.vocab[';'],), 
            "_character ::= %s" % (self.vocab["'"],), 
            "_character ::= %s" % (self.vocab['"'],), 
            "_character ::= %s" % (self.vocab['='],), 
            "_character ::= %s" % (self.vocab['space'],), 
            "_character ::= %s" % (self.vocab['tab'],), 
            "_character ::= %s" % (self.vocab['!'],), 
            "_character ::= %s" % (self.vocab['#'],), 
            "_character ::= %s" % (self.vocab['$'],), 
            "_character ::= %s" % (self.vocab['%'],), 
            "_character ::= %s" % (self.vocab['^'],), 
            "_character ::= %s" % (self.vocab['&'],), 
            "_character ::= %s" % (self.vocab['*'],), 
            "_character ::= %s" % (self.vocab['('],), 
            "_character ::= %s" % (self.vocab[')'],), 
            "_character ::= %s" % (self.vocab['-'],), 
            "_character ::= %s" % (self.vocab['_'],), 
            "_character ::= %s" % (self.vocab['+'],), 
            "_character ::= %s" % (self.vocab['backslash'],), 
            "_character ::= %s" % (self.vocab['.'],), 
            "_character ::= %s" % (self.vocab['/'],), 
            "_character ::= %s" % (self.vocab['?'],), 
            "_character ::= %s" % (self.vocab[','],), 
            "_character ::= %s" % (self.vocab['>'],), 
            "_character ::= %s" % (self.vocab['<'],), 
            "_character ::= %s" % (self.vocab['['],), 
            "_character ::= %s" % (self.vocab[']'],), 
            "_character ::= %s" % (self.vocab['{'],), 
            "_character ::= %s" % (self.vocab['}'],), 
            "_character ::= %s" % (self.vocab['|'],), 
            "_character ::= %s" % (self.vocab['`'],), 
            "_character ::= %s" % (self.vocab['~'],), 
            "_character ::= %s" % (self.vocab['@'],), 
            "_character ::= %s" % (self.vocab['home'],), 
            "_character ::= %s" % (self.vocab['end'],), 
            "_character ::= %s" % (self.vocab['capslock'],), 
        ))

    def p_character(self, args):
        args[0].undo = {'key': True, 'len': 1}
        return AST('raw_char', [ self.keysyms[args[0].type] ], token=args[0])

    def r_editing(self):
        return "\n".join((
            "_editing ::= %s _repeat" % (self.vocab['return'],), 
            "_editing ::= %s _repeat" % (self.vocab['backspace'],), 
            "_editing ::= %s _repeat" % (self.vocab['delete'],), 
        ))

    def p_editing(self, args):
        self.can_optimistic_execute = False
        if args[1] != None:
            return AST('repeat', [ args[1] ], [
                AST('raw_char', [ self.keysyms[args[0].type] ])
            ])
        else:
            return AST('raw_char', [ self.keysyms[args[0].type] ])

    def r_modifiers(self):
        return "\n".join((
            "_modifiers ::= %s _single_command" % (self.vocab['control'],), 
            "_modifiers ::= %s _single_command" % (self.vocab['alt'],), 
            "_modifiers ::= %s _single_command" % (self.vocab['shift'],), 
            "_modifiers ::= %s _single_command" % (self.vocab['super'],), 
        ))

    def p_modifiers(self, args):
        self.can_optimistic_execute = False
        if(args[1].type == 'mod_plus_key'):
            args[1].meta.insert(0, self.keysyms[args[0].type])
            return args[1]
        else:
            return AST('mod_plus_key', [ self.keysyms[args[0].type] ], [ args[1] ] )

    def r_english(self):
        return "\n".join((
            "_english ::= %s ANY" % (self.vocab['word'],), 
        ))

    def p_english(self, args):
        args[1].undo = {'key': True, 'len': len(args[1].extra)}
        return AST('sequence', args[1].extra, token=args[1])

    def r_word_sentence(self):
        return "\n".join((
            "_word_sentence ::= %s _word_repeat" % (self.vocab['sentence'],), 
        ))

    def p_word_sentence(self, args):
        if(len(args[1].children) > 0):
            args[1].children[0].meta = args[1].children[0].meta.capitalize()
        return args[1]

    def r_word_phrase(self):
        return "\n".join((
            "_word_phrase ::= %s _word_repeat" % (self.vocab['phrase'],), 
        ))

    def p_word_phrase(self, args):
        for w in args[1].children:
            #note- w.meta is a token for the word
            length = len(w.meta.extra)

            w.meta.undo = {'key': True, 'len': length+1}

        return args[1]

    def r_programming(self):
        return "\n".join((
            "_programming ::= %s _word_repeat" % (self.vocab['pascal case'],), 
            "_programming ::= %s _word_repeat" % (self.vocab['camel case'],), 
            "_programming ::= %s _word_repeat" % (self.vocab['snake case'],), 
            "_programming ::= %s _word_repeat" % (self.vocab['join case'],), 
            "_programming ::= %s _word_repeat" % (self.vocab['dashed case'],), 
            "_programming ::= %s _word_repeat" % (self.vocab['caps case'],), 
            "_programming ::= %s _word_repeat" % (self.vocab['lowcaps case'],), 
            "_programming ::= %s _word_repeat" % (self.vocab['spaced case'],), 
        ))

    def p_programming(self, args):

        #TODO I want to unify all the AST nodes that produce keyboard output
        #I think it would simplify executor and also allow for more general operators
        #It may be nice to use the 'spaced case' operator on both words and characters
        #ie 'spaced var x quill value' to produce 'var x = value'
        #currently it would output 'var x=value' because parsed (space: [var,x])(char: =)(word: value)
		#instead of (space: [var,x,=,value])

        #args[1] is _word_repeat match which is a word_sequence AST
        args[1].type = 'programming'
        args[1].meta = args[0]

        for i, w in enumerate(args[1].children):

            #FormatLikeThis
            if args[0] == self.vocab['pascal case']:
                w.meta.extra = w.meta.extra[0].upper() + w.meta.extra[1:]

            #formatLikeThis
            if args[0] == self.vocab['camel case'] and i != 0:
                w.meta.extra = w.meta.extra[0].upper() + w.meta.extra[1:]

            #format_like_this
            if args[0] == self.vocab['snake case'] and i != 0:
                w.meta.extra = "_" + w.meta.extra

            #format-like-this
            if args[0] == self.vocab['dashed case'] and i != 0:
                w.meta.extra = "-" + w.meta.extra

            #format like this
            if args[0] == self.vocab['spaced case'] and i != 0:
                w.meta.extra = " " + w.meta.extra

            #FORMATLIKETHIS
            if args[0] == self.vocab['caps case']:
                w.meta.extra = w.meta.extra.upper()

            #formatlikethis (used to remove uppercase chars sometimes present in vocab)
            if args[0] == self.vocab['lowcaps case']:
                w.meta.extra = w.meta.extra.lower()

            #else, this is joincase, only need this from command mode, programming mode is joined by default
            #formatlikethis

            #note- w.meta is a token for the word
            length = len(w.meta.extra)

            w.meta.undo = {'key': True, 'len': length}

        return args[1]


    def p_word_repeat(self, args):
        '''
            _word_repeat ::= ANY
            _word_repeat ::= ANY _word_repeat
        '''
        if(len(args) == 1):
            return AST('word_sequence', None,
                [ AST('null', args[0], token=args[0]) ])
        else:
            args[1].children.insert(0, AST('null', args[0], token=args[0]))
            return args[1]

    def r_release(self):
        return "\n".join((
            "_release ::= %s" % (self.vocab['release'],), 
        ))

    def p_release(self, args):
        # faster we release the better?
        # self.can_optimistic_execute = False
        return AST('release')

    def r_undo(self):
        return "\n".join((
            "_undo ::= %s" % (self.vocab['undo'],), 
            "_undo ::= %s _number" % (self.vocab['undo'],), 
        ))

    def p_undo(self, args):
        self.can_optimistic_execute = False
        if len(args) == 1:
            return AST('undo', -1)
        return AST('undo', int(args[1]))

    def r_replay(self):
        return "\n".join((
            "_replay ::= %s" % (self.vocab['replay'],), 
        ))

    def p_replay(self, args):
        self.can_optimistic_execute = False
        return AST('replay', args[0])

    def r_meta_actions(self):
        return "\n".join((
            "_meta_actions ::= %s" % (self.vocab['escape token'],), 
            "_meta_actions ::= mud", 
            # "_meta_actions ::= sneeze", 
            # "_meta_actions ::= cat", 
            # "_meta_actions ::= dog", 
            # "_meta_actions ::= fish", 
            # "_meta_actions ::= king", 
            # "_meta_actions ::= monk", 
        ))

    #currently for null/noop tokens
    def p_meta_actions(self, args):
        # self.can_optimistic_execute = False
        return AST('null')

    def p_null(self, args):
        '''
            _null ::= !sil
            _null ::= <unk>
        '''
        # self.can_optimistic_execute = False
        return AST('null')

    def r_sleep(self):
        return "\n".join((
            "_sleep ::= %s" % (self.vocab['sleep'],), 
            "_sleep ::= %s" % (self.vocab['wakeup'],), 
        ))

    def p_sleep(self, args):
        self.can_optimistic_execute = False
        if args[0].type == self.vocab['sleep']:
            return AST('sleep', 'sleep')
        return AST('sleep', 'wakeup')

    def r_mode(self):
        rules = [ 
            "_mode ::= %s _number" % (self.vocab['mode'],), 
            "_mode ::= %s %s" % (self.vocab['mode'], self.vocab['uppercase'],), 
            ]
        for w in list(self.modes['words'].keys()):
            rules.append("_mode ::= %s %s" % (self.vocab['mode'], w))
        return "\n".join(rules)

    def p_mode(self, args):
        self.can_optimistic_execute = False
        if args[1] == self.vocab['uppercase']:
            return AST('mode', ['optimistic', args[1]])

        if type(args[1]) == int:
            return AST('mode', ['parser', self.modes['numbers'][int(args[1])]])
        return AST('mode', ['parser', self.modes['words'][args[1].type]])

    def r_hold(self):
        return "\n".join((
            "_hold ::= %s _letter" % (self.vocab['hold'],), 
            "_hold ::= %s _uppercase_letter" % (self.vocab['hold'],), 
            "_hold ::= %s _character" % (self.vocab['hold'],), 
            "_hold ::= %s _movement" % (self.vocab['hold'],), 
            "_hold ::= %s _letter" % (self.vocab['repeat'],), 
            "_hold ::= %s _uppercase_letter" % (self.vocab['repeat'],), 
            "_hold ::= %s _character" % (self.vocab['repeat'],), 
            "_hold ::= %s _movement" % (self.vocab['repeat'],), 
        ))

    def p_hold(self, args):
        self.can_optimistic_execute = False
        if args[0] == self.vocab['hold']:
            return AST('hold', args[1].meta[0])
        else:
            return AST('hold_repeat', args[1].meta[0])

    #self.init_custom_command_grammar() dynamically builds _custom_command rules to be returned by self.r_custom_command()
    #and also dynamically sets r_, p_custom_command_{key} functions for each key in the self.custom_commands dict (see config/custom_commands.py)
    #
    #custom_command['mycommand'] = {'grammar': ['hello _number','hello friend'], 'handler': mycallback}
    #will add rule to grammar:
    #  _custom_command ::= _custom_command_mycommand
    #via the r_custom_command() return string.
    #Also created are the p_ and r_ functions for the _custom_command_mycommand rule
    #self.r_custom_command_mycommand will return this string:
    #_custom_command_mycommand ::= hello _number
    #_custom_command_mycommand ::= hello friend
    #
    #The p_custom_command_mycommand function will return an AST of type 'custom_command'
    #AST('custom_command', [key, matches, self.custom_commands])
    #key is the name used in the custom command config, 'mycommand' in this example (needed by the executor to find correct handler to invoke)
    #matches are the arguments from the p_ function, passed along to our handler from the executor
    #self.custom_commands is the entire custom_commands config (needed by the executor to find correct handler to invoke)
    #
    #If the custom command config has a 'matcher' callback that will get called from the p_custom_command_mycommand function
    #giving an opportunity to mutate the tokens (add undo meta data) and set the parsers can_optimistic_execute attribute
    #
    #This is complicated but a flat expansion of the custom rules won't work because spark invokes the p_custom_command 
    #callback with the matched rule tokens/AST nodes without any context on what rule matched other than the tokens themselves.
    #ie there is no simple way to get a reference to the correct handler to invoke for the matched tokens. By adding a p_ function
    #for each custom_command config grouping we have the context of what custom_command created the matched rule.
    def init_custom_command_grammar(self):
        rules = [] 
        child_rules_dict = {}
        for k,v in list(self.custom_commands.items()):
            rules.append("_custom_command ::= _custom_command_%s" % (k,))
            child_rules = []
            for r in v['grammar']:
                child_rules.append("_custom_command_%s ::= %s" % (k, r,))
            child_rules_dict[k] = "\n".join(child_rules)

            #creating lambdas in for loop is annoying because loop variable k is free and will point to final item,
            #by invoking another fn we bind the value we want
            def make_r_fn(key):
                return lambda x: child_rules_dict[key]
            def make_p_fn(key):
                #matcher is just a p_fn, so above signature is p_fn(self, args), here changed names to (parser, matches) for clarity
                def matcher(parser, matches):
                    if 'matcher' in self.custom_commands[key]:
                        #give custom command an opportunity to add undo meta and allow for optimistic execution
                        #TODO maybe add an option for setting whether a custom_config is optimistic?
                        self.custom_commands[key]['matcher'](parser, matches)
                    else:
                        self.can_optimistic_execute = False
                    return AST('custom_command', [key, matches, self.custom_commands])
                return matcher

            setattr(self.__class__, "r_custom_command_%s" % (k,), make_r_fn(k))
            setattr(self.__class__, "p_custom_command_%s" % (k,), make_p_fn(k))

        setattr(self.__class__, "r_custom_command", lambda _: "\n".join(rules))

    def p_custom_command(self, args):
        # self.can_optimistic_execute = False
        #TODO now if a custom_command config has a matcher, it is optimistic by default
        return args[0]
