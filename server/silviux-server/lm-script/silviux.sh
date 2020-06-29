#!/bin/bash

#This script must be ran before silviux-mkgraph.sh, which depends on the aspire model files
#Running this will download and create the english decoder, copying the english decoder into the models dir
#docker exec -it <silviux container> /silviux/silviux.sh

silv_server_dir=/silviux/silviux-server

#download aspire chain model into volume mounted at /silviux
#about 500mb, see https://kaldi-asr.org/models/m1
aspire_model=https://kaldi-asr.org/models/1/0001_aspire_chain_model.tar.gz

if [ ! -f /silviux/0001_aspire_chain_model.tar.gz ]; then
	echo "Download kaldi aspire chain model..."
	wget $aspire_model -P /silviux/
fi

if [ ! -d /opt/kaldi/egs/aspire/s5/exp/chain ]; then
	tar -xf /silviux/0001_aspire_chain_model.tar.gz --directory /opt/kaldi/egs/aspire/s5
fi

##run steps from the aspire model README to build the graph
##this takes a few minutes and possibly > 8gb ram
cd /opt/kaldi/egs/aspire/s5
steps/online/nnet3/prepare_online_decoding.sh \
    --mfcc-config conf/mfcc_hires.conf data/lang_chain exp/nnet3/extractor exp/chain/tdnn_7b exp/tdnn_7b_chain_online
utils/mkgraph.sh --self-loop-scale 1.0 data/lang_pp_test exp/tdnn_7b_chain_online exp/tdnn_7b_chain_online/graph_pp

#keep config location files consistent with tedlium for silviux
mv exp/tdnn_7b_chain_online/graph_pp/HCLG.fst exp/tdnn_7b_chain_online/HCLG.fst
mv exp/tdnn_7b_chain_online/graph_pp/words.txt exp/tdnn_7b_chain_online/words.txt

#rename and move output model dir to silviux-backend, call import.sh to adjust config paths
#the yaml file should already have an english section with these file paths
mv exp/tdnn_7b_chain_online/ exp/english/
mv exp/english/ $silv_server_dir/models
cd $silv_server_dir/models
./import.sh english
