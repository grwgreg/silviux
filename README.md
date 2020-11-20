# Silviux

Silviux is a fork of the [silvius](https://github.com/dwks/silvius) voice to code project with many added features and tools for working with kaldi.  

[![silviux demo](https://img.youtube.com/vi/eBe0p9slFdI/0.jpg)](http://www.youtube.com/watch?v=eBe0p9slFdI)


## Features
                                                                                                                                                                         
- Switch between multiple parsers on the client and models/decoders on the server (model and decoder are used interchangeably in this project)                                                                                              
- Scripts for creating models using the newer kaldi nnet3 [aspire chain model](https://kaldi-asr.org/models/m1) in place of the tedlium nnet2 model                                                                                                                                                                                                                        
- Lower time to keyboard output by optimistically executing key strokes from partial transcripts                                                                                                                             
- Registers and macros for on the fly vocab/output mappings                                                                                                          
- Undo keyboard output by individual words or full commands                          
- Hold and repeat key presses using the microphone volume                                                                                                             
- Gnome extension for displaying the transcripts and program state in the top bar                                                                                                                  
- Easymotion style overlay for mouse movement and clicking                                                                                                                          
- Dockerfile for easy kaldi and server setup                                                                                                                         
- Scripts for creating language models specifically for the programming grammar
- Adaption states for each decoder are now automatically saved and loaded on the server                                                                                                                           
- Sound recognition with [sopare](https://github.com/bishoph/sopare) for low latency mode toggling (current parser,sleeping)                                                 
- Ability to add simple functionality in one place via "custom commands" (no more directly modifying the grammar, AST nodes and executor methods)                                                                                                                                                             
- Interact with the program from a vim instance for runtime debugging and manual state management                                                                                                                
- Client code converted to python3

## Recommendation
If you don't have any experience with a voice to code system I strongly recommend you try out other projects first. While this project is definitely usable it is still mostly an experiment in using multiple small vocabulary speech decoders instead of a more verbose grammar. The idea is that with a smaller vocabulary you get a boost in recognition accuracy and the parsers can use less verbose commands. This comes at the cost of having to manually manage which mode is active. In addition, as modifications are made to the grammar for a parser, the decoder will have to be rebuilt in order for kaldi to recognize the new words. There are scripts to ease this process but it may be helpful to learn a bit about [language models](https://cmusphinx.github.io/wiki/tutoriallm/#language-models) if for no other reason than to understand the basic terminology used in the script comments.

## Requirements
- Xorg and xdotool (if you're using wayland you may be able to swap in [ydotool](https://github.com/ReimuNotMoe/ydotool))
- Gnome, the transcripts are displayed via a gnome extension. The notify middleware simply uses the 'gdbus' command to communicate with the extension so this could be swapped out for another display method. 
- Vim compiled with [channel](https://vimhelp.org/channel.txt.html) support
- [sopare](https://github.com/bishoph/sopare) for sound recognition
- docker for installing the server
- Kaldi uses about 1-2gb of ram when in use, building your own model uses around 10gb of ram

Note that you can disable the sopare and vim code by not including them in the message pipeline,

```
   #silviux/main.py
   handler = Handler()
   handler.use(Notify(context))
   handler.use(Sleep(context))    
   handler.use(Mode(context))         
   handler.use(Hold(context))  
   #handler.use(Sopare(context))
   #handler.use(Vim(context))    
   handler.use(History(context))
   handler.use(Kaldi(context))
   handler.use(Parse(context))
   handler.use(Optimistic(context))
   handler.use(Execute(context))
   handler.init()
```
The notify middleware is required but you may simply comment out the part of the notify code that invokes os.command if you're trying to run the program without gnome.

The client code is now python3 and depends on the PyAudio and ws4py packages.

## Setup

See the README in server/silviux-server for the server installation using docker. The client will connect to either the silvius server or the [kaldi gstreamer server](https://github.com/alumae/kaldi-gstreamer-server) but only the silviux-server supports changing the decoder.

The server's silviux.yaml file contains the paths to the kaldi decoders. You will either need to create these yourself or download the ones I have prepared at [https://silviux.weisman.dev](https://silviux.weisman.dev/). The model creation scripts place the created models into the server/models directory. The servers yaml file expects the models to be at server/silviux-server/models, so this directory is a symlink to the models directory above it.

The program uses [sopare](https://github.com/bishoph/sopare) for switching between modes. Install this program and train it on the sounds found in the middleware/sopare.py file. Place the sopare_plugin directory into the plugins directory of sopare.

See silviux/config/silviux.yaml for configuring which port the server is listening on, where the sopare program is installed, which microphone to use etc. The main program will still accept the same command line args as silvius (see silviux/stream.py) to override the options in the yaml file.

```
$ python3 test.py
$ python3 main.py
```

## Project Overview

- ezmouse/ This is a standalone program that displays an overlay for controlling the mouse. It is invoked by a custom command
- gnome-extension/ The gnome extension for displaying transcripts (install by copying into ~/.local/share/gnome-shell/extensions and enable from https://extensions.gnome.org/local/)
- lm_utils/ Scripts for creating language models and lexicons
- server/ This directory should be mounted by the docker container, contains kaldi models and server code
- silviux/ The client code
- silviux/config/ The word to keysym mappings and vocabulary used by the parsers, silviux.yaml contains the microphone, stream and sopare config
- silviux/config/custom_commands.py The vim, ezmouse and some example custom commands
- silviux/middleware/ How the program's state is updated in response to incoming messages (see silviux/test/test_middleware.py)
- silviux/parser/ The parser manager instantiates the parsers in this directory and tracks which is currently active
- sopare_plugin/ This should be placed into the sopare projects plugin directory
- vim_server/ Code for opening a gnome-terminal running vim and connecting using a vim channel (tcp)


## Creating Decoders

The contents of the lm_utils/ directory are not imported or used at all during the normal (main.py) execution of the client code. It contains scripts for creating the needed language model and lexicon files for creating a kaldi decoder. For the 'programming' language model, the goal is to create a corpus of text that is the spoken equivalent of some original code.

```
#somefile.js
function() {
  return "hello";
}
```
We wish to map the above text into the spoken words we would say to produce that text.
```
#key config
{"space": "spay", "(": "brace", ")": "mace, "enter": "spike", ";": "sem"}
```

```
#somefile.js.modified
function sue shi spay brace spike
return spay quote hello quote sem spike
mace spike
```
We can then train a language model on these files to help improve recognition accuracy. The workflow is something like this:

- lm_utils/dlrepos.py this downloads projects from github into lm_utils/repos/
- lm_utils/filewalker.py this maps the files to our language and concats them into a single file (read the comments and code in this file before running it)
- lm_utils/scripts/makelm.sh Use the commands in this file to create the language model and lexicon (read the comments in this file)
- You now have a language model and a lexicon, name them mymodel.lm and mylexicon.txt and place them in the server/ directory which should be mounted by the kaldi server docker volume
- If you haven't yet, read the README in the server dir and the comments in server/silviux-server/lm-script/silviux-mkgraph.sh (the lm-script/silviux.sh script must be run first to download the aspire model and copy some scripts into place within the kaldi installation)
- Within the container run $ /silviux/silviux-server/lm-script/silviux-mkgraph.sh mynewmodel
- This script should create the model and copy it into the server/models dir
- Add a 'mynewmodel' entry to the server's yaml config (copy paste another models config and search replace with 'mynewmodel')
- You should now be able to send a {"change_decoder": "mynewmodel"} message to the kaldi server and test the new decoder

Note that when you first use a new decoder, it takes about a minute for kaldi to set the adaption state. This means your first impression will often be that it isn't working well and you may try changing the volume or tone of your voice to "help" it with the recognition. Try not to do this and just speak naturally for the first minute or so before making a determination.

## Language Model Example

You should read the comments in the lm_utils/scripts/makelm.sh file. This file is a collection of commands used in the creation of language models and the formatting of lexicon files so they will work with kaldi. As an example, here I will walk through the commands for creating a new 'command' decoder which will be a mix of the english model downloaded from the kaldi website and the terminal words from our 'command' grammar.

First you will need the lm and lexicon from the [aspire chain model](https://kaldi-asr.org/models/m1). If you ran the server's silviux.sh install script you already have these files within the docker container's /opt/kaldi/egs/aspire/s5/ directory. The LM can be found in data/local/lm/4gram-mincount/lm_unpruned.gz. Extract the 'lm_unpruned' file into the lm_utils/exp/ directory. The lexicon file can be found at data/local/dict/lexicon2_raw.txt, also copy this to the lm_utils/exp directory.

Now we need to create a small language model from our command grammar to mix with the english lm and lexicon. We're going to run a script for outputting the terminals from our grammar and use it to create a lexicon and a bigram corpus to create a language model.

```
# From the silviux project root
$ python3 parser_utils.py command > lm_utils/exp/terminals
$ python3 lm_utils/ngrams.py lm_utils/exp/terminals > lm_utils/exp/bigrams
$ ngram-count -wbdiscount -text lm_utils/exp/bigrams -lm lm_utils/exp/command.lm

```
We now have a language model for our terminal words at lm_utils/exp/command.lm. We're also going to need a lexicon for these terminal words. Upload the lm_utils/exp/terminals file to http://www.speech.cs.cmu.edu/tools/lextool.html (use the 'word file' option then hit 'compile). Save the .dict file to lm_utils/exp/command.dict. We're now going to format this file and combine it with the english lexicon and finish off by removing any duplicate lines (kaldi won't compile our decoder with duplicates).

```
$ cd lm_utils
$ python3 lexicon-format.py exp/command.dict exp/terminals exp/commandlexicon.txt
$ cat exp/commandlexicon.txt exp/lexicon2_raw.txt > exp/merged.txt
$ sort exp/merged.txt | uniq > exp/mylexicon.txt
```
We now have the lexicon file, exp/mylexicon.txt, which we will use with the decoder creation script. The final step is to mix our command bigram language model with the english language model. 

```
ngram -lm exp/lm_unpruned -mix-lm exp/command.lm -lambda 0.2 -write-lm exp/mymodel.lm
```
The exp/mylexicon.txt and exp/mymodel.lm files can now be placed into server/ (or whatever directory the docker container is mounted to) for running the decoder creation scripts.
