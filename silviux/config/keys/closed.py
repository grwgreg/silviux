from .command import keys as k
from .command import commands as c
from .command import modes as m
import copy

#note config/parser.py is the config for the modes ie
#the specific config for vocab, modes, keysyms, custom commands
#which is passed along to the parser/parser_manger.py

keys = copy.deepcopy(k)
commands = copy.deepcopy(c)
modes = copy.deepcopy(m)

keys['a']['word'] = 'air'
keys['b']['word'] = 'biz'
keys['c']['word'] = 'cell'
keys['d']['word'] = 'dish'
keys['e']['word'] = 'eek'
keys['f']['word'] = 'fox'
keys['g']['word'] = 'gum'
keys['h']['word'] = 'ham'
keys['i']['word'] = 'ink'
keys['j']['word'] = 'jill'
keys['k']['word'] = 'kick'
keys['l']['word'] = 'luck'
keys['m']['word'] = 'mike'
keys['n']['word'] = 'nuke'
keys['o']['word'] = 'oak'
keys['p']['word'] = 'punt'
keys['q']['word'] = 'quack'
keys['r']['word'] = 'rick'
keys['s']['word'] = 'sock'
keys['t']['word'] = 'tay'
keys['u']['word'] = 'uzi'
keys['v']['word'] = 'vick'
keys['w']['word'] = 'wolf'
keys['x']['word'] = 'x'
keys['y']['word'] = 'yell'
keys['z']['word'] = 'zack'

keys['0']['word'] = 'zero'
keys['1']['word'] = 'one'
keys['2']['word'] = 'dose'
keys['3']['word'] = 'three'
keys['4']['word'] = 'quatro'
keys['5']['word'] = 'five'
keys['6']['word'] = 'six'
keys['7']['word'] = 'seven'
keys['8']['word'] = 'eight'
keys['9']['word'] = 'nine'

keys['up']['word'] = 'nitz'
keys['down']['word'] = 'ditz'
keys['left']['word'] = 'litz'
keys['right']['word'] = 'ritz'
keys['escape']['word'] = 'scape'
keys['delete']['word'] = 'dell'
keys['escape']['word'] = 'scape'
keys[':']['word'] = 'cola'
keys[';']['word'] = 'sem'
keys["'"]['word'] = 'boat'
keys['"']['word'] = 'quote'
keys['-']['word'] = 'minus'
keys['space']['word'] = 'spay'
keys['tab']['word'] = 'tab'
keys['&']['word'] = 'andre'
keys['@']['word'] = 'atlas'
keys['*']['word'] = 'star'
keys['.']['word'] = 'dot'
keys['/']['word'] = 'slash'
keys['backslash']['word'] = 'butter'
keys['!']['word'] = 'bang'
keys['+']['word'] = 'plus'
keys['(']['word'] = 'sue'
keys[')']['word'] = 'shi'
keys['{']['word'] = 'brace'
keys['}']['word'] = 'mace'
keys['[']['word'] = 'shock'
keys[']']['word'] = 'tock'
keys['<']['word'] = 'lane'
keys['>']['word'] = 'grain'
keys['|']['word'] = 'bark'

keysyms = {}
for k,v in list(keys.items()):
    keysyms[v['word']] = v['keysym']

vocab = {}
for k,v in list(keys.items()):
    vocab[k] = v['word']
for k,v in list(commands.items()):
    vocab[k] = v
