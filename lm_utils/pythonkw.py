import keyword
import builtins

#write all the python special chars to data/pycorpus
with open('exp/pycorpus', 'w') as f:
    for k in keyword.kwlist:
        f.write("%s\n" % k)
    for k in dir(builtins):
        f.write("%s\n" % k)
