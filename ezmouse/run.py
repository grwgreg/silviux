#this will work as script without silviux
from subprocess import Popen, PIPE
import os
import sys
import time

ezmouse_path = os.path.join(os.getcwd(), 'ezmouse/ezmouse.py')

def run_ezmouse():
#get the current window id
    process = Popen(["xdotool", "getactivewindow"], stdout=PIPE)
    (wid_before, err) = process.communicate()
    process.wait()
    print('wid before: ')
    print(wid_before)

    #ezmouse.py is still python2
    process = Popen(["python", ezmouse_path], stdout=PIPE)
    (output, err) = process.communicate()
    process.wait()

    data = output.split(b"\n")
    # print('returned')
    # print(data)
    # sys.exit()
    if len(data) < 5: 
        print('something went wrong')
        print(data)
        sys.exit()

    x = data[0]
    y = data[1]
    digit = int(data[2])
    upper = data[3]
    print(x)
    print(y)
    print(digit)
    print(upper)

#default is single click
    xdo_command = ["xdotool", "mousemove", x, y, "click", "1"]

#uppercase is 2nd mouse button
    if upper == b'True':
        xdo_command = ["xdotool", "mousemove", x, y, "click", "3"]
#any digit overrides case, 1 just moves, 2 double clicks
    if digit == 1:
        xdo_command = ["xdotool", "mousemove", x, y]
    if digit == 2:
        xdo_command = ["xdotool", "mousemove", x, y, "click", "--repeat", "2", "1"]

#wait for gtk window to go away
    while True:
        time.sleep(0.001)
        print('waiting for new wid')
        process = Popen(["xdotool", "getactivewindow"], stdout=PIPE)
        (wid_current, err) = process.communicate()
        process.wait()
        print('got wid:')
        print(wid_current)
        if wid_before == wid_current: break

#Even though the xdotool getactivewindow picks up the change
#we still need to sleep for significant amount of time or gnome doesnt pick up mouse click :(
#TODO there are better ways to get events from gnome? this is silly
    time.sleep(0.2)

    print(xdo_command)
    process = Popen(xdo_command, stdout=PIPE)
    (output, err) = process.communicate()
    process.wait()

if __name__ == '__main__':
    run_ezmouse()
