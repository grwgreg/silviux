#For outputting unmodified text directly from kaldi transcripts (for macros)
from ..ast import AST

#TODO replace this with a real parser, use _word rule from programming parser
class TextParser:
    def parse_mutate_tokens(self, tokens):
        ast = AST('chain', None)
        ast.can_optimistic_execute = False

        words = AST('word_sequence', None)
        for t in tokens:
            if t != 'stop': words.children.append(AST('null', t))
        ast.children.append(words)

        if 'stop' in tokens: 
            ast.children.append(AST('mode', ['parser', 'pop']))
        return ast
