from ..ast import AST
from .parse import CoreParser

class EnglishParser(CoreParser):
    def __init__(self, config):
        CoreParser.__init__(self, config)

    def p_solo_commands(self, args):
        '''
            _solo_commands ::= _undo
            _solo_commands ::= _replay
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
            _single_command ::= _word_phrase
            _single_command ::= _custom_command 
            _single_command ::= _null
        '''
        return args[0]

    #override without the vocab['phrase'] prefix
    def r_word_phrase(self):
        return "\n".join((
            "_word_phrase ::= _word_repeat", 
        ))

    def p_word_phrase(self, args):
        for w in args[0].children:
            #w.meta is a token for the word
            length = len(w.meta.extra)

            w.meta.undo = {'key': True, 'len': length+1}

        return args[0]

    def p_null(self, args):
        '''
            _null ::= <unk>
            _null ::= [noise]
            _null ::= [laughter]
            _null ::= mhm
        '''
        return AST('null')
