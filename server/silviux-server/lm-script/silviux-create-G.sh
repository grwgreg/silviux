#!/usr/bin/env bash

if [ -f path.sh ]; then . ./path.sh; fi

#Possibly undesirable to remove the data/lang file each time?
#But -T merges files, so if you modify this to not remove data/lang, may end up with mix of files from different LMs so be careful
rm -rf data/lang
cp -rT data/local/silviuxlexfinal data/lang
mkdir -p data/local/lm/silviux

cp /silviux/mymodel.lm data/local/lm/silviux/mymodel.lm

#If we copy over each time better to remove it first? I don't like idea of G.fst getting out of sync with L.fst
rm -rf data/lang_test
mkdir -p data/lang_test

cp -rT data/lang data/lang_test

arpa2fst --disambig-symbol=#0 --read-symbol-table=data/lang_test/words.txt data/local/lm/silviux/mymodel.lm data/lang_test/G.fst

echo "$0 succeeded"
exit 1
