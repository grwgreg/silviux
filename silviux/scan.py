# Lexer that produces a sequence of tokens (keywords + ANY).

class Token:
    def __init__(self, type, word_index=-1, extra=''):
        self.type = type
        self.extra = extra
        self.word_index = word_index
        self.done = False

    def __eq__(self, o):
        return self.type == o

    def __repr__(self):
        return str(self.type)

def scan(line, keywords):
    tokens = []
    word_index = 0
    for t in line.lower().split():
        if(t in keywords):
            tokens.append(Token(t, word_index))
        else:
            tokens.append(Token('ANY', word_index, t))
        word_index += 1
    tokens.append(Token('END'))
    return tokens
