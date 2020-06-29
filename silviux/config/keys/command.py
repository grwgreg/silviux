#http://xahlee.info/linux/linux_show_keycode_keysym.html
#$xev
#type '*' key and it will output data about the key we pressed
#console ouput: state 0x1, keycode 17 (keysym 0x2a, asterisk), same_screen YES
#either 'asterisk' or the hex value will work as the 'keysym' value:

#This old vocab was from the tedlium model which had poor accuracy
#and needed multiple syllable words.
#The other config objects deep copy and change the 'word' attr, so this is the only place keysyms
#are defined for the keys config
keys = {
    'up': {
        'keysym': 'Up',
        'word': 'uptake',
    },
    'down': {
        'keysym': 'Down',
        'word': 'dove',
    },
    'left': {
        'keysym': 'Left',
        'word': 'lady',
    },
    'right': {
        'keysym': 'Right',
        'word': 'ritzy',
    },
    'pageup': {
        'keysym': 'Prior',
        'word': 'upshot',
    },
    'pagedown': {
        'keysym': 'Next',
        'word': 'dovetail',
    },
    '0': {
        'keysym': '0',
        'word': 'zoey',
    },
    '1': {
        'keysym': '1',
        'word': 'winner',
    },
    '2': {
        'keysym': '2',
        'word': 'doozy',
    },
    '3': {
        'keysym': '3',
        'word': 'trio',
    },
    '4': {
        'keysym': '4',
        'word': 'quatro',
    },
    '5': {
        'keysym': '5',
        'word': 'fiver',
    },
    '6': {
        'keysym': '6',
        'word': 'sicko',
    },
    '7': {
        'keysym': '7',
        'word': 'seuss',
    },
    '8': {
        'keysym': '8',
        'word': 'ochoa',
    },
    '9': {
        'keysym': '9',
        'word': 'neato',
    },
    'a': {
        'keysym': 'a',
        'word': 'atlas',
    },
    'b': {
        'keysym': 'b',
        'word': 'bravo',
    },
    'c': {
        'keysym': 'c',
        'word': 'charlie',
    },
    'd': {
        'keysym': 'd',
        'word': 'dagger',
    },
    'e': {
        'keysym': 'e',
        'word': 'elmo',
    },
    'f': {
        'keysym': 'f',
        'word': 'foxy',
    },
    'g': {
        'keysym': 'g',
        'word': 'garden',
    },
    'h': {
        'keysym': 'h',
        'word': 'hotel',
    },
    'i': {
        'keysym': 'i',
        'word': 'itchy',
    },
    'j': {
        'keysym': 'j',
        'word': 'jolly',
    },
    'k': {
        'keysym': 'k',
        'word': 'kilo',
    },
    'l': {
        'keysym': 'l',
        'word': 'ladder',
    },
    'm': {
        'keysym': 'm',
        'word': 'monkey',
    },
    'n': {
        'keysym': 'n',
        'word': 'ninja',
    },
    'o': {
        'keysym': 'o',
        'word': 'oscar',
    },
    'p': {
        'keysym': 'p',
        'word': 'papa',
    },
    'q': {
        'keysym': 'q',
        'word': 'quincy',
    },
    'r': {
        'keysym': 'r',
        'word': 'rambo',
    },
    's': {
        'keysym': 's',
        'word': 'sizzle',
    },
    't': {
        'keysym': 't',
        'word': 'tango',
    },
    'u': {
        'keysym': 'u',
        'word': 'umpire',
    },
    'v': {
        'keysym': 'v',
        'word': 'victor',
    },
    'w': {
        'keysym': 'w',
        'word': 'whiskey',
    },
    'x': {
        'keysym': 'x',
        'word': 'exam',
    },
    'y': {
        'keysym': 'y',
        'word': 'yankee',
    },
    'z': {
        'keysym': 'z',
        'word': 'zebra',
    },
    'escape': {
        'keysym': 'Escape',
        'word': 'casper',
    },
    ':': {
        'keysym': 'colon',
        'word': 'cola',
    },
    ';': {
        'keysym': 'semicolon',
        'word': 'coca',
    },
    "'": {
        'keysym': 'apostrophe',
        'word': 'chile',
    },
    '"': {
        'keysym': 'quotedbl',
        'word': 'cuda',
    },
    '=': {
        'keysym': 'equal',
        'word': 'quill',
    },
    'space': {
        'keysym': 'space',
        'word': 'stomp',
    },
    'tab': {
        'keysym': 'Tab',
        'word': 'tabby',
    },
    '!': {
        'keysym': 'exclam',
        'word': 'banjo',
    },
    '#': {
        'keysym': 'numbersign',
        'word': 'crunch',
    },
    '$': {
        'keysym': 'dollar',
        'word': 'dolly',
    },
    '%': {
        'keysym': 'percent',
        'word': 'purse',
    },
    '^': {
        'keysym': 'asciicircum',
        'word': 'carrot',
    },
    '&': {
        'keysym': 'ampersand',
        'word': 'andre',
    },
    '*': {
        'keysym': 'asterisk',
        'word': 'aster',
    },
    '(': {
        'keysym': 'parenleft',
        'word': 'lio',
    },
    ')': {
        'keysym': 'parenright',
        'word': 'rio',
    },
    '-': {
        'keysym': 'minus',
        'word': 'minty',
    },
    '_': {
        'keysym': 'underscore',
        'word': 'uncle',
    },
    '+': {
        'keysym': 'plus',
        'word': 'pluto',
    },
    'backslash': {
        'keysym': 'backslash',
        'word': 'butter',
    },
    '.': {
        'keysym': 'period',
        'word': 'ditzy',
    },
    '/': {
        'keysym': 'slash',
        'word': 'slash',
    },
    '?': {
        'keysym': 'question',
        'word': 'quest',
    },
    ',': {
        'keysym': 'comma',
        'word': 'comma',
    },
    '>': {
        'keysym': 'greater',
        'word': 'gravy',
    },
    '<': {
        'keysym': 'less',
        'word': 'leather',
    },
    '[': {
        'keysym': 'bracketleft',
        'word': 'bottle',
    },
    ']': {
        'keysym': 'bracketright',
        'word': 'rocket',
    },
    '{': {
        'keysym': 'braceleft',
        'word': 'spoon',
    },
    '}': {
        'keysym': 'braceright',
        'word': 'swoop',
    },
    '|': {
        'keysym': 'bar',
        'word': 'tender',
    },
    '`': {
        'keysym': 'grave',
        'word': 'tickle',
    },
    '~': {
        'keysym': 'asciitilde',
        'word': 'tiger',
    },
    '@': {
        'keysym': 'at',
        'word': 'attic',
    },
    'home': {
        'keysym': 'Home',
        'word': 'homer',
    },
    'end': {
        'keysym': 'End',
        'word': 'endear',
    },
    'capslock': {
        'keysym': 'Caps_Lock',
        'word': 'capstone',
    },
    'return': {
        'keysym': 'Return',
        'word': 'spike',
    },
    'backspace': {
        'keysym': 'BackSpace',
        'word': 'scratch',
    },
    'delete': {
        'keysym': 'Delete',
        'word': 'deli',
    },
    'control': {
        'keysym': 'ctrl',
        'word': 'cozy',
    },
    'alt': {
        'keysym': 'alt',
        'word': 'ankle',
    },
    'super': {
        'keysym': 'super',
        'word': 'sour',
    },
    'shift': {
        'keysym': 'Shift',
        'word': 'shirk',
    },
}

commands = {
    'undo': 'shank',
    'replay': 'batman',
    'release': 'leash',
    'number': 'numb',
    'english number': 'qpxzdontusethis',
    'word': 'wordy',
    'sentence': 'sentence',
    'phrase': 'sax',
    'pascal case': 'rock',
    'camel case': 'camel',
    'snake case': 'snake',
    'dashed case': 'dashed',
    'join case': 'cheese',
    'caps case': 'captain',
    'lowcaps case': 'lizard',
    'spaced case': 'yoda',
    'sleep': 'snooze',
    'wakeup': 'awake',
    'uppercase': 'sky',
    'mode': 'moon',
    'hold': 'joker',
    'repeat': 'pete',
    'escape token': 'jamaica',
}


keysyms = {}
for k,v in list(keys.items()):
    keysyms[v['word']] = v['keysym']

vocab = {}
for k,v in list(keys.items()):
    vocab[k] = v['word']

for k,v in list(commands.items()):
    vocab[k] = v

#grammar still supports "vocab[mode] vocab[1]" to switch to modes[numbers][1]
#or "vocab[mode] Token('someword') to switch to modes[words]['someword']
#note you can currently use sopare sounds to switch modes
modes = {
    'numbers': {
        0: 'command',
        1: 'english',
        2: 'alphabet',
        3: 'text',
        4: 'closed',
        5: 'programming',
    },
    'words': {
        'ted': 'text',
        'cheese': 'command',
        'cloudy': 'closed',
    }
}
