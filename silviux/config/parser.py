from .keys import command
from .keys import closed
from .keys import alphabet
from .custom_commands import custom_commands

def pick(keys):
    return {k: custom_commands[k] for k in keys}

config = {
        'command': {
            'keysyms': command.keysyms,
            'vocab': command.vocab,
            'custom_commands': custom_commands,
            'modes': command.modes
        },
        'closed': {
            'keysyms': closed.keysyms,
            'vocab': closed.vocab,
            'custom_commands': custom_commands,
            'modes': closed.modes
        },
        'alphabet': {
            'keysyms': alphabet.keysyms,
            'vocab': alphabet.vocab,
            'custom_commands': custom_commands,
            'modes': alphabet.modes
        },
        'programming': {
            'keysyms': closed.keysyms,
            'vocab': closed.vocab,
            'custom_commands': pick(['vim_programming']),
            'modes': closed.modes
        }
    }
