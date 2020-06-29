#!/bin/bash
#http://www.speech.sri.com/projects/srilm/manpages/
#https://cmusphinx.github.io/wiki/tutoriallmadvanced/
#"For example, for book-like texts you need to use Knesser-Ney discounting. For command-like texts you should use Witten-Bell discounting or Absolute discounting."

#To create a kaldi decoder with the silviux scripts you need 2 files, a lexicon and a language model.
#The lexicon lists all the words and their pronunciations
#The LM is the output of the srilm (or other lm software) command ngram-count, see https://cmusphinx.github.io/wiki/tutoriallm/
#The command "ngram" is also used in this file for pruning and mixing lms, outputting a new lm

#Lexicon creation
#First you need a plain text file to use as training data
#We can extract out the vocab (a list of all the words contained in the training data)
#ngram-count -write-vocab myvocab.txt -text trainingdata.txt

#Now we need to get pronunciation for each word, use http://www.speech.cs.cmu.edu/tools/lextool.html
#The online lextool is easy to use but not as good as newer g2p toolkits, see https://github.com/cmusphinx/g2p-seq2seq
#The cmu toolkit outputs a .dict file but it needs to be lowercased and modified to remove the (N) which is appended to words with
#N different pronunciations
#ie the cmu g2p outputs something like
#WORD w eh r d
#WORD(2) w ah r d
#but we need
#word w eh r d
#word w ah r d

#may have to manually remove the <unk> and silence tokens at very top of file before running this
#python3 lexicon-format.py thelexicon.dict myvocab.txt mylexicon.txt

#LM creation
#Make an lm with all words and no smoothing
# ngram-count -text trainingdata.txt -lm mymodel.lm 

#Make an lm which will replace words not present in vocab with <unk>
# ngram-count -vocab myvocab.txt -text trainingdata.txt -lm mymodel.lm 

#Use -kndiscount for Kneser–Ney smoothing
# ngram-count -kndiscount -vocab myvocab.txt -text trainingdata.txt -lm mymodel.lm 

#Use -wbdiscount for Witten Bell smoothing, cmu tutorial said this is better for commands (ie "go up")
# ngram-count -wbdiscount -vocab myvocab.txt -text trainingdata.txt -lm mymodel.lm 

#Mixing an lm trained on lots of data with a big vocab with a small bigram lm of command words helps
#boost recognition of command words
#note "$ngram" not "$ngram-count"
# ngram -lm $lm1 -mix-lm $lm2 -lambda 0.2 -write-lm $output

#More than 2 lms can be mixed http://mailman.speech.sri.com/pipermail/srilm-user/2017q3/001777.html
#ie programming with spaces, programming without spaces, flat programming vocab, command words
#this is 40% prog with spaces, 40% without spaces, 20% command bigram:
# ngram \
#  -lm exp/prog.lm  -lambda 0.4 \
#  -mix-lm  exp/prognospaces.lm \
#  -mix-lm2 exp/progngram.lm -mix-lambda2 0.2 \
#  -write-lm exp/progmix.lm

#Pruning LM, remove low probability ngrams to decrease size (kaldi can handle giant LMs but mkgraph will be slow and might exceed 16gb ram) 
#note "$ngram" not "$ngram-count"
# ngram -lm exp/mymodel.lm -prune 1e-6 -write-lm exp/pruned.lm

#Create vocab with words that appear more than n times (see trimvocab.py, I extract a smaller vocab from the corpus to limit the lexicon to 25k words)
#get counts of all words, remove rare words, remove unwanted output that gets included with arpa files
# ngram-count -write1 exp/ones.lm -text exp/corpus.*
# python3 trimvocab.py exp/ones.lm
# the lm output has <s> and </s> tokens, need to remove them!
# cant have empty lines in lexicon!
# sed -i -e 's/<s>//g' exp/ones.lm.trim
# sed -i -e 's/<\/s>//g' exp/ones.lm.trim
# sed -i -r '/^\s*$/d' exp/ones.lm.trim
# ngram-count -write-vocab exp/myfinal.vocab -text exp/ones.lm.trim

#Merge two lexicons and remove duplicate lines (or merge vocabs before getting lexicon)
# cat exp/termlexicon.txt exp/jslexicon.txt > exp/merged.txt
# sort exp/merged.txt | uniq > exp/mylexicon.txt

#Create simple lm from a parser's terminals, 'closed' made this way, useful for mixing to boost recognition of important words
#cd ../
##parser_utils.py takes name of parser, output can be used to make lexicon
#python3 parser_utils.py programming > lm_utils/exp/terminals
#cd lm_utils
#python3 ngrams.py exp/terminals > exp/corpus.ngrams
# ngram-count -wbdiscount -text exp/corpus.ngrams -lm exp/progngram.lm 

#Common
# ngram-count -write-vocab exp/js.vocab -text exp/corpus.*
# ngram-count -kndiscount -vocab exp/js.vocab -text exp/corpus.* -lm gregjs.lm 
# ngram-count -wbdiscount -vocab exp/vocabtrim -text exp/corpus.* -lm exp/jstrim.lm 

########################
########################
#Experiment Below
########################
########################

#copy above commands down here for running to keep a reference
