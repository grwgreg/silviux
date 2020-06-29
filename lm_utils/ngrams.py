import sys
#This file takes as input a vocab file (1 word per line) at writes out all possible bigrams
#note there is a way to generate the real ngrams from build_n_grams function in parser/lm.py
#TODO try using the original build_n_grams output and see if recognition is better?

#Note the reason I use bigrams is because from kaldi, <s> myword, ie silence then 'myword',
#seems to be what is used. When I make decoders from simple 1grams the recognition even on single
#spoken words isn't good and chained words are hopeless.

#terminals from parser_utils.py ie get_terminals(parser) output
terminals = sys.argv[1]
f = open(terminals)
lines = f.read()
corpus = [x for x in lines.split("\n") if x]
ngrams = []
for a in corpus:
    ngrams.append(a)
for a in corpus:
    for b in corpus:
        ngrams.append(" ".join([a,b]))
# for a in corpus:
#     for b in corpus:
#         for c in corpus:
#             ngrams.append(" ".join([a,b,c]))
print(("\n".join(ngrams)))
