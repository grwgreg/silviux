from .spark import GenericASTBuilder
from ..ast import AST
from .parse import GrammaticalError
from .parse import CoreParser
import string

#The decoder for closed mode is not mixed with the english LM, so the transcripts should produce no 'ANY' tokens.
#The vim grammar may still be set up for assinging registers to ANY tokens, so if you want to use that style
#You manually have to add words to the language model that will scan as ANY. An easy way to do this is by adding
#words to the meta_actions null tokens, then use the parser_utils scripts to output the terminals from the grammar
#then comment out the lines from the grammar so the words scan as ANY instead of as terminals.
class ClosedParser(CoreParser):
    def __init__(self, config):
        CoreParser.__init__(self, config)

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
    def p_meta_actions(self, args):
        self.can_optimistic_execute = True
        return AST('null')
