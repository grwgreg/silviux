#!/bin/bash

options=(
    --splice-config --cmvn-config --lda-matrix --global-cmvn-stats
    --diag-ubm --ivector-extractor --mfcc-config
    --ivector-extraction-config
)

model=$1
if [ ! -d "$model" ]; then
    echo "Usage: $0 new-speech-model-path"
    echo "The model must be in the same path as this script, models/"
    exit 1
fi

for file in $model/conf/*.conf; do
    echo "fixing $file..."
    /bin/cp $file $file.orig
    for option in "${options[@]}"; do
        perl -i -pe "s{^$option=.*(ivector_extractor|conf/[^/]+)}{$option=models/$model/\$1}" $file
    done
done

#move around aspire model files to be consistent with tedlium
if [ ! -f  $model/HCLG.fst ]; then
  /bin/cp $model/graph/HCLG.fst $model/HCLG.fst
fi
if [ ! -f  $model/words.txt ]; then
  /bin/cp $model/graph/words.txt $model/words.txt
fi

echo "updating latest symlink to $model"
/bin/rm -f latest
/bin/ln -f -s $model latest
