#!/usr/bin/env bash

rm -rf data/local/silviuxlex data/local/silviuxlextmp data/local/silviuxlexfinal
cp -r data/local/dict data/local/silviuxlex
rm -f data/local/silviuxlex/lexiconp.txt
#aspire uses lexicon file in all lowercase, including phonemes and <unk> instead of <UNK>
cp /silviux/mylexicon.txt data/local/silviuxlex/lexicon.txt
utils/prepare_lang.sh data/local/silviuxlex "<unk>" data/local/silviuxlextmp data/local/silviuxlexfinal
