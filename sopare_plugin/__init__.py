#!/usr/bin/env python
# -*- coding: utf-8 -*-

#For use with sopare, https://github.com/bishoph/sopare
#Add the sopare_plugin directory to the /plugins dir in the sopare project
#silviux/config/silviux.yaml is where to set the IP,PORT if not using the defaults

import json
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def run(readable_results, data, rawbuf):
    #sometimes this will return more than 1 result... in such case at least 1 is a false positive so ignore it
    #Todo could possibly look through data for more info to make decision, ie pick one with highest similarity
    if len(readable_results) == 1:
        #result will be name from training, ie $sopare.py -t name
        msg = json.dumps({"sopare": readable_results[0]})
        sock.sendto(msg, (UDP_IP, UDP_PORT))
