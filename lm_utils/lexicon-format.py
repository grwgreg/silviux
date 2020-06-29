#Use this to create lexicon, http://www.speech.cs.cmu.edu/tools/lextool.html
#This file takes a cmu g2p lexicon and creates new lexicon file with the format we need (lowercase, duplicate pronuncations don't have (N) appended on)
#It also replaces some common bad pronunciations (JSON) that the cmu tool outputs using the json mappings in lexiconfix.txt instead.
#If you can set up another g2p program you should, the lextool is not good compared to newer models.

#For the most basic case this was a very simple script but I started trying to conserve case when making programming lib specific LMs so that a spoken
#"create component" would output "createComponent". The problem was "createcomponent", "createComponent", "CreateComponent" all often show up in training data
#and the cmu g2p uppercased them all in the final output, so I had to restore their original case.

#TODO This file wouldn't be needed if I could find a g2p model that doesn't change the case of our input vocab in the output lexicon...
import re
import json
import os
import sys

#when generate vocab file via ngram-count it includes tokens that don't belong in lexicon file
#current workflow is to leave them in when getting the phonemes and remove them here when formatting case etc
#skiplines is the number of lines to skip at the top of the file, often has <unk> and other junk
# skiplines = 4
skiplines = 0
def clean_lex(lexicon, tmp):
    with open(lexicon, 'r') as old:
        with open(tmp, 'w') as f:
            #aspire and tedlium use different phoneme names for noise, mhm, laughter etc
            # with open('symbols.txt', 'r') as s:
            with open('symbolsaspire.txt', 'r') as s:
                f.write(s.read())
        with open(tmp, 'a') as f:
            data = old.readlines()
            result = []
            for d in data[skiplines:]:
                #no clue what this first whitespace char is but this works
                d = re.sub(r'[^\S\n]', r' ', d)
                ds = d.split(" ")
                #aspire wants lowercase phonemes, cmu output is uppercase
                result.append(' '.join(ds).lower())
            f.writelines(result)

#to restore case we need to keep track of how many times we've seen the word already and
#increment the counter but only if it doesn't match (\d)
def make_vocab_dict(vocab):
    uncased = {}
    with open(vocab, 'r') as fp:
        line = fp.readline()
        while line:
            # print("{}".format(line.strip()))
            word = line.strip()
            if word.lower() not in uncased:
                uncased[word.lower()] = {"i": -1, "vals": []}
            uncased[word.lower()]["vals"].append(word)
            line = fp.readline()
    return uncased

def map_lex(tmp, vocab, output):
    uncased = make_vocab_dict(vocab)
    with open(tmp, 'r') as old:
        with open(output, 'w') as f:
            data = old.readline()
            while data:
                ds = data.split(" ")
                # note if <unk> makes it into vocab this throws index error, this is good because <unk> needs to map to unknown phoneme "noise"
                # otherwise the create_L.sh script will throw error later on (simply remove offending tokens from lexicon to fix)
                # print ds[0]

                key = re.sub(r'\(\d\)', r'', ds[0])
                if key in uncased:
                    #don't increment on additional pronunciations ie word(2), word(3)
                    inc = not bool(re.search(r'\(\d\)', ds[0]))
                    if inc:
                        uncased[key]["i"] += 1
                    val = uncased[key]["vals"][uncased[key]["i"]]
                    # ds[0] = uncased[ds[0]].pop(0)
                    ds[0] = val
                f.write(' '.join(ds))
                data = old.readline()


def lex_fix(output):
    with open('lexiconfix.txt', 'r') as f:
        d = f.read()
        fixes = json.loads(d)
        for word,new in list(fixes.items()):
            #-i in place
            #-E extended, must be capital E
            os.system("sed -i -E 's/^" + word + "\s.+/"+word+' '+new +"/' " + output)



#python lexicon-format.py exp/mydict.dict exp/prog.vocab exp/proglexicon.txt
def main():

    #lexicon is cmu lexicon output file http://www.speech.cs.cmu.edu/tools/lextool.html
    lexicon = sys.argv[1]

    #vocab is vocab output from srilm -write-vocab, just a file of single words on each line
    #make sure <unk> and other symbols are not in vocab file
    vocab = sys.argv[2]

    #file to write to
    output = sys.argv[3]

    #intermediate file, was original output now is intermediate output between clean and map
    tmp = 'exp/tmp.txt'

    clean_lex(lexicon, tmp)
    map_lex(tmp, vocab, output)
    lex_fix(output)

main()
