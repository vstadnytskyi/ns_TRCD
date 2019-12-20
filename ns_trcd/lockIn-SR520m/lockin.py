##how to connect
from __future__ import division     #so that int(1)/int(2) = float(0.5) instead of int(0)
#from visual import *                #import vpython lib so that function calls don't have to be visual.function()
import visa                         #import NI-VISA wrapper (interface with equipment). Function calls are visa.function()
import sys                          #import system lib (system == python interpreter, not the os)
import numpy                      #import numeric library
import time                         #import time library
import os            #import operating system library
import matplotlib.pyplot as plt
import serial, glob, struct


print 'Boom!'

time_start =  time.clock()
plt.ion()
PEM_port = 'COM2'
Zaber_port = 'COM1'
LockIn_port = 'COM4'
avg_per_point = 20
debug = False #True  = ON; False = OFF;

#################################################
##Communication with the SR 510 Lock-in##
#################################################


def lockinInitialize(port):
    try:
        ser = serial.Serial(port, 2400, 8, 'N', 1, timeout=1)   
    except:
        print("Error opening com port. Quitting.")
        sys.exit(0)
    print("Opening " + serZaber.portstr)

    device = 1
    command = 52
    data = 0
    print('Sending instruction. Device: %i, Command: %i, Data: %i' % (device, command, data))
    reply = zaberSend(device, command, data)

    print 'reply from command = ',command, 'with reply =', reply
    return 'HINDS PEM initialization complete', device, ser

def lockinSend(command):
    serLockIn.flushInput()
    # send a packet using the specified device number, command number, and data
    # The data argument is optional and defaults to zero
    command_str = command+'\r\n'
    if debug == True:
        print command_str
    serLockIn.write(command_str)
    time.sleep(1) # wait for 1 second
    reply = serLockIn.read(10)
    return reply
def SignalAcquire(avg_per_point):
    sum_array= numpy.ones(avg_per_point)
    sum_array_probe= numpy.ones(avg_per_point)
    sum_array_ref= numpy.ones(avg_per_point)
    for counter in range(0,avg_per_point):
        sum_array[counter]  = float(lockinSend("Q"))
        sum_array_probe[counter] = AcqDataScope('CHAN1')
        sum_array_ref[counter] = AcqDataScope('CHAN2')
        signal_mean = numpy.mean(sum_array)
        signal_std = numpy.std(sum_array)
        signal_probe = numpy.mean(sum_array_probe)
        signal_ref = numpy.mean(sum_array_ref)
    return signal_mean, signal_std, signal_probe, signal_ref
#################################################
#################################################

#################################################
##Communication with the Hinds PEM 100 controller##
##################################################
#make sure it is in a remote mode#

############################
## MAIN loop 
##########################


if debug == True:
    print 'Debugging mode is ON'
else:
    print 'Debugging mode is OFF'

###############Initialize Lock-in
print "Initialize Lock-In"
try:
    serLockIn = serial.Serial('COM2', 9600, 8, 'N', 1, timeout=0.05)   
except:
    print("Error opening com port. Quitting.")
    serZaber.close()
    serLockIn.close()
    serPEM.close()
    sys.exit(0)
print("Opening " + serLockIn.portstr)
print("Lock-in initialized Succesfully on port:" + serLockIn.portstr)
serLockIn.flush()

# send a packet using the specified device number, command number, and data
# The data argument is optional and defaults to zero
scan = 10
replyQ = numpy.zeros(scan)
replyX1 = numpy.zeros(scan)
replyX2 = numpy.zeros(scan)
for i in range(scan):
    print  'time=', time.clock()
    #serLockIn.flushInput()
    #serLockIn.flushOutput()
    # command_str = 'Q'  +'\r\n'
    # #if debug == True:
        # # print command_str
    # serLockIn.write(command_str)
     # # # wait for 1 second
    
    
    # replyQ = serLockIn.read(11)
    # time.sleep(0.05)
    
    command_str = 'Q \r\n'
    serLockIn.write(command_str)
    replyQ[i] = serLockIn.readline()
    command_str = 'X1 \r\n'
    serLockIn.write(command_str)
    replyX1[i] = float(serLockIn.readline())
    command_str = 'X2 \r\n'
    serLockIn.write(command_str)
    replyX2[i] = float(serLockIn.readline())
    
print 'Q=',replyQ,'X1=', replyX1,'X2=', replyX2
meanQ = numpy.mean(replyQ)
stdQ = numpy.std(replyQ);
print meanQ
print stdQ

serLockIn.close()





