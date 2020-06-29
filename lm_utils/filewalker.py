# -*- coding: utf-8 -*-
# for chinese chars used as placeholders
import re
import os
import random
import json

#Do not run this file directly, the run function is called from silviux_root/lm_utils.py

#This file maps to (roughly) their spoken equivalent for alphabet, programming mode, and removes junk text.
#ie in programming mode,
#somefile.js: function() {
#somefile.js.modified: function sue shi spay brace spike
#or in alphabet mode
#somefile.js: abc;
#somefile.js.modified: alpha bravo charlie semi

#see the run function at bottom of file, uncomment cat_files() and it concats all .modified files
#and writes the result to a single corpus file with a unique filename
#My workflow has been to start running this on a single repo so it runs fast and compare the original with the .modified file.
#When happy with the result run it on the entire repos directory (takes a few minutes to run).
#Then run the $ngram-count -write-vocab myvocab.txt -text corpusoutput.txt from the lm_utils/scripts/makelm.sh file
#and look for how much junk text is in the file. There will be lots of junk no matter what from temporary variable names
#and things like that but if it seems too extreme you can grep for the junk text in the .modified files to find where
#they're coming from and either remove the files or add in more regex rules for removing them.
#Also note that trimvocab.py can be used (see makelm.sh) to remove words from the vocabulary that appear less than n times
#My current LM for programming removed all words from corpus that only appeared once and that was pretty effective although
#there are quite a few false positive removals.

#TODO Write a parser to do this instead of regex tricks with placeholders and ordering complexity...
#ie match camelCaseWords into a camel node, single letters, chars, commands etc, then walk AST and build up string.
#Will still have to handle cases like 'aA' maps to 'camel a a', but we don't want 'a' in final output but vocab['a']
#Possibly will require multiple passes?
#Can use the keys.config to build the grammar dynamically so it stays in sync with silviux grammar

#Make sure you import the correct vocab!!
#programming mode uses closed keys
from silviux.config.keys.closed import vocab
# from silviux.config.keys.alphabet import vocab

# Run on single dir first to check output, it takes minutes on all the repos
# REPO_DIR = 'lm_utils/repos/react-native/RNTester/js/examples/Image'
REPO_DIR = 'lm_utils/repos'

#Map to individual letters, space vocab word, special chars (remove numbers)
#Note this means every letter gets mapped, if false a lone ' f ' still gets mapped to vocab['f']
ALPHABET = False

#split camel == True will remove all CamelCase and snake_case and dash-words and convert everything to lower case
#only set to false if you want a small library specific LM that includes in vocab SomeLibraryFunction, some_function etc
SPLIT_CAMEL = True

#replace spaces with the space vocab word, ie "def fun {" to "def space fun space brace"
SPACE_WORD = False

#do nothing but split camelCaseWords into "camel case words", remove unicode and numbers and map single characters to vocab
CAMEL_SPLIT_ONLY = False


#idea is to map over javascript files replacing special characters with their spoken word
#the full vocab object has lots of stuff in it so pull out what we want to replace
special_chars=["!","\"","#","$","%","&","'","(",")","*","+",",","-",".","/",":",";","<","=",">","?","@","[","]","^","_","`","{","|","}","~"]
alphabet = [a for a in "abcdefghijklmnopqrstuvwxyz"]
replace_with = {}
for k in special_chars:
    replace_with[k] = vocab[k]

alpha_replace_with = {}
if not ALPHABET:
    for k in alphabet:
        replace_with[" " + k + " "] = vocab[k]
        alpha_replace_with[k] = vocab[k]
else:
    for k in alphabet:
        replace_with[k] = vocab[k]

#I didn't use the actual backslash char as the key in the vocab obj
#pretty sure it is the only char not keyed by the actual character
#TODO low priority change this
replace_with["\\"] = vocab["backslash"]
    
# print json.dumps(replace_with, sort_keys=True, indent=4, separators=(',', ': '))
# print json.dumps(vocab, sort_keys=True, indent=4, separators=(',', ': '))
word_dict = {}

def pascal_split(match):
    match = match.group()
    #remove surrounding marker
    match = re.sub(r'帽', r'', match)
    return re.sub(r'([a-z])([A-Z])', r"\1帽\2", match)

#TODO this is soooooooo slow 
#is it possible to move regex's outside loop, ie compile the regex state machine thing once like in js?
def modify(words):
    #ORDER MATTERS!!! splitting camelCase has to be done after removing long text strings or won't catch jibberish jajfajAJDajfAJDaAJFKDAFJdalAFJ
    #because it will split on all lower/upper boundries

    #remove long strings (usually junk or long compound words, minified js sometimes if not manually removed)
    #\b is word boundry
    words = re.sub(r'\b[\w\+\/]{20,}\b', r'', words) 
    #remove stuff like ######## from comments 
    #comments are a problem in general, consider parsing with js lib and removing comment nodes? TODO
    #Or do we actually want some of the vocab from comments in the LM??
    words = re.sub(r'(.)\1{4,}', r'', words)

    if ALPHABET:
        return modify_alphabet(words)
    elif CAMEL_SPLIT_ONLY:
        return modify_camel_only(words)

    #Problem is we want to map "def someFunctionThing" to "def space camel some function thing"
    #So split the camelcase word but instead of spaces use chinese characters as placeholders. We then can
    #replace all the spaces with the space keyword, then finally convert the placeholders back to real spaces.
    #example:
    #1: def someFunctionThing
    #2: def spay camel骆some骆function骆thing
    #3: def spay camel some function thing
    #This logic also is used to preserve snake case and dash case while still replace other instances of underscore and dash.
    #ie for js package LM I wanted Some_Thing to stay but replace all other instances of _ with the vocab word
    if SPLIT_CAMEL:
        #PascalCase: first surround with special character, 帽PascalCase帽
        #then match on word between our special char, otherwise primitive (lower)(upper) matches camel and pascal
        #note the inserted space because $ReadOnly will map to $帽Read帽Only because \b matches $+= chars
        words = re.sub(r'\b([A-Z][a-z]+)([A-Z])([^\s]+)', r"帽\1\2\3帽", words)
        words = re.sub(r'(帽\S+帽)', pascal_split, words)

        #camelCase,snake_case,dashed-case
        words = re.sub(r'([a-z])([A-Z])', r"\1骆\2", words)
        words = re.sub(r'([a-z])_([a-z])', r"\1字\2", words)
        words = re.sub(r'([a-z])-([a-z])', r"\1⺙\2", words)
        words = words.lower()
    else:
        #to retain snake_case and dashed-words, convert to snake字case, then later restore after mapping over vocab
        words = re.sub(r"([a-z])_([a-z])", r"\1字\2", words)
        words = re.sub(r"([a-z])-([a-z])", r"\1⺙\2", words)

    #remove numbers, makes more sense to interpolate numbers vocab, especially if we're adding special commands to lm anyway
    words = re.sub(r'\d+', r'', words)

    #clean up whitespace, regex is so don't overwrite new line char
    words = re.sub(r'[^\S\n]+', r" ", words)

    #replace spaces with space vocab word, careful that split camel case doesn't get space word inserted between words
    if SPACE_WORD:
        #strip whitespace at start of line, insert space word at any space character that isn't \n
        words = re.sub(r'^\s+', r"", words)
        words = re.sub(r'[^\S\n]+', r" " + vocab["space"] + r" ", words)

    #must come after inserting space word or all lines end with vocab['space'] vocab['return']
    #add return character at new lines
    words = re.sub(r'\n+', r" %s\n" %  (vocab['return'],), words)

    for k,v in list(replace_with.items()):
        words = words.replace(k, r' ' + v + r' ')

    if SPLIT_CAMEL:
        #add in prefix word for camels
        words = re.sub(r'\b(\w+帽[\w帽]+)\b', vocab['pascal case'] + r" \1", words)
        words = re.sub(r'\b(\w+骆[\w骆]+)\b', vocab['camel case'] + r" \1", words)
        words = re.sub(r'\b(\w+字[\w字]+)\b', vocab['snake case'] + r" \1", words)
        words = re.sub(r'\b(\w+⺙[\w⺙]+)\b', vocab['dashed case'] + r" \1", words)
        #restore camel case
        words = re.sub(r'([a-z])帽([a-z])', r"\1 \2", words)
        words = re.sub(r'([a-z])骆([a-z])', r"\1 \2", words)
        words = re.sub(r'([a-z])字([a-z])', r"\1 \2", words)
        words = re.sub(r'([a-z])⺙([a-z])', r"\1 \2", words)
    else:
        #restore snake and dash case
        words = re.sub(r"([a-z])字([a-z])", r"\1_\2", words)
        words = re.sub(r"([a-z])⺙([a-z])", r"\1-\2", words)


    ##remove unicode and random \n and \b junk
    if SPLIT_CAMEL:
    #careful of removing _ and -, if you want those retained for snake_case_words
        words = re.sub(r'[^a-zA-Z\n\s]+', r" ", words)
    else:
        words = re.sub(r'[^a-zA-Z\n\s_-]+', r" ", words)

    #TODO gross, do a second pass because we miss single letters because ?q=query doesn't have spaces around 'q' until after '?' and '=' get replaced
    #also any random unicode stuff in place of space on either side leaves it in
    #this is important because 'r' will show up in lexicon and mess up 'are'
    #don't use when doing single alphabet letters only because 'a' maps to 'ash' to 'ash sock ham'
    if not ALPHABET:
        for k,v in list(alpha_replace_with.items()):
            #TODO pull out alphabet from replace_with for above too since it doesn't work
            words = re.sub(r'\b' + k + r'\b', r' ' + v + r' ', words)


    return words

def modify_alphabet(words):
    #remove numbers
    words = re.sub(r'\d+', r'', words)

    words = words.lower()

    #strip whitespace at start of line
    words = re.sub(r'^\s+', r"", words)
    
    #insert placeholder that will be replaced with vocab space word after mapping letters
    #ie we don't want to map "space" to "s p a c e" vocab words
    words = re.sub(r'[^\S\n]+', r"⺙", words)

    result = ""
    for l in words:
        if (l in replace_with):
            result += " " + replace_with[l] + " "
        else:
            #should only be spaces and unicode stuff that we remove later, if corpus has junk in it look here
            result += l

    result = re.sub(r"⺙", r" " + vocab["space"] + r" ", result)

    #add return character at new lines
    result = re.sub(r'\n+', r" %s\n" %  (vocab['return'],), result)

    #remove unicode junk
    result = re.sub(r'[^a-zA-Z\n\s]+', r" ", result)

    return result

def modify_camel_only(words):
    #remove numbers
    words = re.sub(r'\d+', r' ', words)

    words = re.sub(r'([a-z])([A-Z])', r"\1 \2", words)
    words = words.lower()

    #remove unicode junk
    words = re.sub(r'[^a-zA-Z\n\s]+', r' ', words)

    #remove all single letter chars because 'ash', 'biz' words used in parser
    #TODO consolidate with global stuff at top of file
    alphabet = [a for a in 'abcdefghijklmnopqrstuvwxyz']
    a_replace_with = {}
    for k in alphabet:
        a_replace_with[' ' + k + ' '] = vocab[k]

    for k,v in list(a_replace_with.items()):
        words = words.replace(k, r' ' + v + r' ')

    return words


#skip_fn is a filter function for what files to ignore
#ie for javascript repos we only want .js files and not .min.js files
def map_files(skip_fn):
    for path, dirs, files in os.walk(REPO_DIR):
        for f in files:
            if skip_fn(f):
                continue
            p = os.path.join(path, f)
            modified = p + '.modified'
            with open(p, 'r') as ff:
                with open(modified, 'w+') as newfile:
                    print(p)
                    text = ff.readline()
                    while text:
                        if text.strip() != "":
                            newfile.write(modify(text))
                        text = ff.readline()

def cat_files():
    version = str(random.random())[1:]
    print("version " + version)
    with open('lm_utils/exp/corpus'+version, 'w+') as newfile:
        for path, dirs, files in os.walk(REPO_DIR):
            for f in files:
                if f[-9:] == '.modified':
                    p = os.path.join(path, f)
                    with open(p, 'r') as ff:
                        text = ff.read()
                        newfile.write(text)
                        newfile.write("\n")

def run():
    # print replace_with
    # print vocab
    #note scripts/rmmodified is bash script to remove *.modified files
    #although this script will simply overwrite existing .modified files
    def js_skip_file(f):
        return f[-7:] == '.min.js' or f[-3:] != '.js'
    #use this to skip no files
    def wiki_skip_file(f):
        return False
    map_files(js_skip_file)
    # map_files(wiki_skip_file)
    cat_files()
