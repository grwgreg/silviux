# See https://github.com/jcsilva/docker-kaldi-gstreamer-server
# if anything breaks from kaldi updates there will probably be open issues and pull requests
# This dockerfile is similar but doesn't delete kaldi files and git repo
# and is based on ubuntu bionic because debian9's python-gi package leaks memory when changing decoders
# also pass compiler flag to explicitly use ATLAS as kaldi math lib and install the gfortan package dependency
FROM ubuntu:bionic
MAINTAINER Greg Weisman <greg@weisman.dev>

RUN apt-get update && apt-get install -y  \
    procps \
    autoconf \
    automake \
    bzip2 \
    g++ \
    git \
    gstreamer1.0-plugins-good \
    gstreamer1.0-tools \
    gstreamer1.0-pulseaudio \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-ugly  \
    libgstreamer1.0-dev \
    gstreamer1.0-libav \
    libatlas3-base \
    libtool-bin \
    make \
    python2.7 \
    python3 \
    python-pip \
    python-yaml \
    python-simplejson \
    python-gi \
    subversion \
    unzip \
    wget \
    build-essential \
    python-dev \
#tmux and locales-all for shell, not a kaldi/gst dep
    tmux \
    locales-all \
    gfortran \
    sox \
    zlib1g-dev && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    pip install ws4py==0.3.2 && \
    pip install tornado && \
    ln -s -f bash /bin/sh

WORKDIR /opt

RUN wget http://www.digip.org/jansson/releases/jansson-2.7.tar.bz2 && \
    bunzip2 -c jansson-2.7.tar.bz2 | tar xf -  && \
    cd jansson-2.7 && \
    ./configure && make -j $(nproc) && make check &&  make install && \
    echo "/usr/local/lib" >> /etc/ld.so.conf.d/jansson.conf && ldconfig && \
    rm /opt/jansson-2.7.tar.bz2 && rm -rf /opt/jansson-2.7

RUN git clone https://github.com/kaldi-asr/kaldi && \
#working as of June 2020, if anything breaks try checking out this commit
#cd /opt/kaldi && git checkout 6b0938a61d597ca248f5e7eab97995cfbbe20d85
    cd /opt/kaldi/tools && \
    make -j $(nproc) && \
    ./install_portaudio.sh && \
    cd /opt/kaldi/src && ./configure --mathlib=ATLAS --shared && \
    sed -i '/-g # -O0 -DKALDI_PARANOID/c\-O3 -DNDEBUG' kaldi.mk && \
    make clean -j $(nproc) && make -j $(nproc) depend && make -j $(nproc) && \
    cd /opt/kaldi/src/online && make depend -j $(nproc) && make -j $(nproc) && \
    cd /opt/kaldi/src/gst-plugin && \
    sed -i 's/-lmkl_p4n//g' Makefile && \
    make depend -j $(nproc) && make -j $(nproc) && \
    cd /opt && \
    git clone https://github.com/alumae/gst-kaldi-nnet2-online.git && \
#working as of Oct 2019, if anything breaks try checking out this commit
#cd /opt/gst-kaldi-nnet2-online && git checkout cb227ef43b66a9835c14eb0ad39e08ee03c210ad
    cd /opt/gst-kaldi-nnet2-online/src && \
    sed -i '/KALDI_ROOT?=\/home\/tanel\/tools\/kaldi-trunk/c\KALDI_ROOT?=\/opt\/kaldi' Makefile && \
    make depend -j $(nproc) && make -j $(nproc)

