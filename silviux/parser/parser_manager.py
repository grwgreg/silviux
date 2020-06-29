from .lm import get_terminals
from .parse import CoreParser
from silviux.config.parser import config
from .alphabet_parser import AlphabetParser
from .text_parser import TextParser
from .programming_parser import ProgrammingParser
from .closed_parser import ClosedParser
from .english_parser import EnglishParser
from .. import scan
from . import parse

class ParserManager:
    def __init__(self):
        #the value of 'decoder' is sent to the server, should match key in the yaml config with location of kaldi files
        self.modes = {
            'command': {
                'parser': CoreParser(config['command']),
                'decoder': 'command',
            },
            'alphabet': {
                'parser': AlphabetParser(config['alphabet']),
                'decoder': 'alphabet',
            },
            'english': {
                'parser': EnglishParser(config['closed']),
                'decoder': 'english',
            },
            'text': {
                'parser': TextParser(),
                #text mode outputs unparsed transcript text, so decoder should not change
                'decoder': None,
            },
            'closed': {
                'parser': ClosedParser(config['closed']),
                'decoder': 'closed',
            },
            'programming': {
                'parser': ProgrammingParser(config['programming']),
                'decoder': 'programming',
            },
            'phones': {
                'parser': TextParser(),
                'decoder': 'phones',
            },
        }

        #TODO, sync with context.mode on init? I think can't keep completely in sync because parser manager is unaware of hold and hold_repeat modes
        self.active = 'closed'

        self.terminals = {
            'command': get_terminals(self.modes['command']['parser']),
            'alphabet': get_terminals(self.modes['alphabet']['parser']),
            'english': get_terminals(self.modes['english']['parser']),
            'text': ['stop'],
            'closed': get_terminals(self.modes['closed']['parser']),
            'programming': get_terminals(self.modes['programming']['parser']),
            'phones': [],
        }

    def parse(self, tokens):
        return self.modes[self.active]['parser'].parse_mutate_tokens(tokens)

    def scan(self, text):
        tokens = scan.scan(text, self.terminals[self.active])
        if hasattr(self.modes[self.active]['parser'], 'post_scan'):
            tokens = self.modes[self.active]['parser'].post_scan(tokens)
        return tokens

    def set_active(self, parser):
        self.active = parser
