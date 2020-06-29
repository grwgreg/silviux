from ..ast import AST
from .parse import CoreParser

class AlphabetParser(CoreParser):
    def __init__(self, config):
        CoreParser.__init__(self, config)

    def p_solo_commands(self, args):
        '''
            _solo_commands ::= _undo
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
            _single_command ::= _meta_actions
        '''
        return args[0]

    #null tokens helpful for outputting stubborn single letters ie 'dog m pop' outputs just 'm'
    def p_meta_actions(self, args):
        '''
            _meta_actions ::= mud
            _meta_actions ::= sneeze
            _meta_actions ::= dog
            _meta_actions ::= pop
            _meta_actions ::= king
            _meta_actions ::= fish
            _meta_actions ::= cat
        '''
        self.can_optimistic_execute = True
        return AST('null')
