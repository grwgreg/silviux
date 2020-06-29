#!/bin/bash
#This script creates the model directory and all needed files for a kaldi-gst-server decoder.
#Note you have to manually create an entry in the server's yaml config for the decoder if it does not yet exist.
#The key in the yaml config should match $modelname, the file locations and names will be consistent so all you
#have to do is copy an existing entry and change the model name.

#This script requires an arpa languge model file, named mymodel.lm in the container's "/silviux" dir (silviux/server should be mounted here)
#Also required is a lexicon file named mylexicon.txt in the same location.
#Before running this you must run the ./silviux.sh script to download and create the aspire english model
#docker exec -it silviuxcontainername /silviux/$serverdir/lm-script/silviux-mkgraph.sh $modelname
modelname=$1
outdir=exp/$modelname
serverdir=/silviux/silviux-server/
destdir=$serverdir/models/

if [ -z "$modelname" ]; then
    echo "Missing arg: model name for output directory required!"
		exit
fi

if [ -d "$destdir$modelname" ]; then
    echo "Model by name of $modelname already exists at $destdir"
		exit
fi

if [ ! -f "/opt/kaldi/egs/aspire/s5/local/silviux-create-L.sh" ]; then
	cp "$serverdir/lm-script/silviux-create-L.sh" /opt/kaldi/egs/aspire/s5/local
fi

if [ ! -f "/opt/kaldi/egs/aspire/s5/local/silviux-create-G.sh" ]; then
	cp "$serverdir/lm-script/silviux-create-G.sh" /opt/kaldi/egs/aspire/s5/local
fi

cd /opt/kaldi/egs/aspire/s5
local/silviux-create-L.sh
local/silviux-create-G.sh

#stuff for online decoding:
#Usage: $0 [options] <lang-dir> [<ivector-extractor-dir>] <nnet-dir> <output-dir>
steps/online/nnet3/prepare_online_decoding.sh --mfcc-config conf/mfcc_hires.conf data/lang_test exp/nnet3/extractor exp/chain/tdnn_7b $outdir

#make the final graph
#echo "Usage: utils/mkgraph.sh [options] <lang-dir> <model-dir> <graphdir>"
utils/mkgraph.sh --self-loop-scale 1.0 data/lang_test $outdir $outdir/graph
mv $outdir $destdir

#import changes the file paths in config files, don't forget this!!!
cd $destdir
./import.sh $modelname

echo "success"
