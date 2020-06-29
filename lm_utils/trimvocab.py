import os
import sys
import re

#Read a counts file(output from $ngram-count -write1 countsfile.lm -text corpus.txt) and only write words to new file with a >= count than MIN_COUNT.
#Currently using this because vocab on 30 js repos is about 75k words, removing words with count of 1 drops to around 25k
#This method removes many real words but it mostly gets junk.
MIN_COUNT = 2

filepath = sys.argv[1]
with open(filepath) as fp:
    with open(filepath+'.trim', 'w+') as trimmed:
        line = fp.readline()
        while line:
            line = fp.readline()
            split = line.split()
            if len(split) > 1 and int(split[1]) >= MIN_COUNT:
                trimmed.write(split[0])
                trimmed.write("\n")

            
