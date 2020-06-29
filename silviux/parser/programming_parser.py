from ..ast import AST
from .parse import CoreParser

class ProgrammingParser(CoreParser):
    def __init__(self, config):
        CoreParser.__init__(self, config)

    def p_solo_commands(self, args):
        '''
            _solo_commands ::= _undo
            _solo_commands ::= _replay
            _solo_commands ::= _sleep
            _solo_commands ::= _mode
            _solo_commands ::= _release
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
            _single_command ::= _programming
            _single_command ::= _word
            _single_command ::= _word_phrase
            _single_command ::= _custom_command 
            _single_command ::= _meta_actions
        '''
        return args[0]


    def p_word(self, args):
        '''
            _word ::= ANY
        '''
        args[0].undo = {'key': True, 'len': len(args[0].extra)}
        return AST('sequence', args[0].extra, token=args[0])

    #Note the use of left recursive rules with earley parser https://en.wikipedia.org/wiki/Earley_parser
    #When grammar is right recurive it would parse 'camel a b c' correctly as (camel (a) (b) (c))
    #but 'camel a b c dot' as (camel a) (b) (c) (dot)
    #Uncertain if this will mess up future additions, the lone _word instead of _word_repeat is what broke camelCase
    #grep 'ambiguity' in spark.py
    def p_chained_commands(self, args):
        '''
            _chained_commands ::= _single_command
            _chained_commands ::= _chained_commands _single_command
        '''
        if(len(args) == 1):
            return AST('chain', None, [ args[0] ])
        else:
            args[0].children.append(args[1])
            return args[0]
