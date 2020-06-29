from .closed import keys as k
from .closed import commands as c
from .closed import modes as m
import copy

keys = copy.deepcopy(k)
commands = copy.deepcopy(c)
modes = copy.deepcopy(m)

keys['a']['word'] = 'a'
keys['b']['word'] = 'b'
keys['c']['word'] = 'c'
keys['d']['word'] = 'd'
keys['e']['word'] = 'e'
keys['f']['word'] = 'f'
keys['g']['word'] = 'g'
keys['h']['word'] = 'h'
keys['i']['word'] = 'i'
keys['j']['word'] = 'j'
keys['k']['word'] = 'k'
keys['l']['word'] = 'l'
keys['m']['word'] = 'm'
keys['n']['word'] = 'n'
keys['o']['word'] = 'o'
keys['p']['word'] = 'p'
keys['q']['word'] = 'q'
keys['r']['word'] = 'r'
keys['s']['word'] = 's'
keys['t']['word'] = 't'
keys['u']['word'] = 'u'
keys['v']['word'] = 'v'
keys['w']['word'] = 'w'
keys['x']['word'] = 'x'
keys['y']['word'] = 'y'
keys['z']['word'] = 'z'

keysyms = {}
for k,v in list(keys.items()):
    keysyms[v['word']] = v['keysym']

vocab = {}
for k,v in list(keys.items()):
    vocab[k] = v['word']
for k,v in list(commands.items()):
    vocab[k] = v
