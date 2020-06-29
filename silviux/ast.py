# Represents a node containing some commands to execute.

class AST:
    def __init__(self, type, meta = None, children = None, token = None):
        self.type = type
        self.meta = meta
        self.children = children if children else []
        self.command = ''
        self.token = token
        self.can_optimistic_execute = True

    def __repr__(self):
        if self.meta:
            return str(self.type) + " " + str(self.meta)
        else:
            return str(self.type)

    def __getitem__(self, i): 
        return self.children[i]
    def __len__(self):
        return len(self.children)
    def __setslice__(self, low, high, seq):
        self.children[low:high] = seq 
    def __cmp__(self, o): 
        return cmp(self.type, o)

def printAST(ast, level=0):
    if level > 10: return

    print('    ' * level, end=' ')
    if ast and len(ast) > 0:
        print(ast, '{')
        for child in ast:
            printAST(child, level + 1)
        print('    ' * level, '}')
    else:
        print(ast)
