from .lm import *
import sys
import json
from .parser_manager import ParserManager

#NOTE All this does is concat result of p_ and r_ on parser object.
#Because we use inheritance this means this will show rules that are actually unreachable from the starting rule.
#ie main parser uses all custom commands, they will show up as _custom_command_whatever ::= whatever
#but _custom_command_whatever won't be in the _custom_commands ::= rules
#TODO see collectRules method in spark lib, it walks the rules from top level so won't hit unreachable rules
def get_grammar(parser):
    rules = []
    for name in dir(parser):
        if name[:2] == 'p_':
            func = getattr(parser, name)
            doc = func.__doc__
            if not doc:
                rule_fn = getattr(parser, "r_" + name[2:])
                doc = rule_fn()
            #remove whitespace from docstrings to align indentation
            trimmed = [r.strip() for r in doc.split("\n") if r.strip()]
            rules.append("\n".join(trimmed))
    return "\n".join(rules)


# $python parser_utils.py $parser_name > terminals.txt
# can then concat with vocab file before passing to g2p to get a lexicon file
def run():
    pm = ParserManager()
    parser_name = sys.argv[1]
    parser = pm.modes[parser_name]['parser']

    #output the grammar for a parser
    #$python parser_utils.py $parser_name grammar
    if len(sys.argv) == 3 and sys.argv[2] == 'grammar':
        # note this can list unreachable rules, try looking at actual rules object if need help debugging
        # print 'rules'
        # print json.dumps(parser.rules, indent=4, sort_keys=False)
        print(get_grammar(parser))
        return

    #output the ngrams for a parser
    #$python parser_utils.py $parser_name ngrams 2
    if len(sys.argv) == 4 and sys.argv[2] == 'ngrams':
        build_n_grams(parser.rules, int(sys.argv[3]))
        return

    terminals = get_terminals(parser)
    #silence words should map to silence phoneme in lexicon, careful they're not the same in fisher english and tedlium
    print("\n".join([v for v in terminals if v != "<unk>" and v != "!sil"]))


    #investigate: spark has method to resolve ambiguity, unsure how often it must be applied but potentially useful
    #for debugging problems with grammar
    # parser.ambiguity(r)
