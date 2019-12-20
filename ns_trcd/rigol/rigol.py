from __future__ import division     #so that int(1)/int(2) = float(0.5) instead of int(0)
from visual import *                #import vpython lib so that function calls don't have to be visual.function()
import visa                         #import NI-VISA wrapper (interface with equipment). Function calls are visa.function()
import sys                          #import system lib (system == python interpreter, not the os)
import numpy                        #import numeric library
import time                         #import time library
import os                           #import operating system library
import matplotlib.pyplot as plt
import serial, sys, time, glob, struct
import h5py

readSleepTime = .1 #s

def scopeInitialize():
    rm = visa.ResourceManager()
    reslist=rm.list_resources()
    print 'List of Resources \n' ,reslist
    rigol = rm.open_resource('USB0::0x1AB1::0x0488::DS1BA130200020::INSTR')
    print(rigol.query("*IDN?"))
    return rigol
def AcqDataScope(channel):   
    print 'Channel selected:' , channel
    #channel = "CHAN2"
    command = ':WAVeform:SOURce ' + channel
    scope.write(command)
    scope.write(":WAV:FORM ASCII") 
    # Get the timescale
    timescale = float(scope.query(":TIM:SCAL?"))
    scope.write(":WAV:POIN:MODE RAW")
    # Get the timescale offset
    timeoffset = float(scope.query(":TIM:OFFS?"))
    command = ':' + channel + ':SCAL?'
    voltscale = float(scope.query(command))

    # And the voltage offset
    command = ":" + channel + ":OFFS?"
    voltoffset = float(scope.query(command))

    command = ':WAV:DATA? ' + channel
    print ':WAV:DATA? ' + channel
    rawdata = scope.query(command)
    bs = rawdata.encode('ascii','ignore')
    bbs = bs[12:].replace(' ','')
    bbbs = [float(i) for i in bbs.split(',')]
    
    data_size = len(rawdata)
    command = ":ACQ:SRAT? " + channel
    sample_rate = float(scope.query(command))

    print 'Data size in ', channel,':', data_size, "Sample rate in channel " ,channel,':', sample_rate

    scope.write(":KEY:FORCE")
    
    data = bbbs
    return data,timescale,timeoffset,voltscale,voltoffset
 
scope = scopeInitialize()
scope.write(":SINGLE")
data3,timescale,timeoffset,voltscale,voltoffset = AcqDataScope('CHAN3')
data2,timescale,timeoffset,voltscale,voltoffset = AcqDataScope('CHAN2')
data1,timescale,timeoffset,voltscale,voltoffset = AcqDataScope('CHAN1')
signal_mean_ref = numpy.mean(data1)
signal_mean_probe = numpy.mean(data2)
print signal_mean_ref,signal_mean_probe
#data3,timescale,timeoffset,voltscale,voltoffset = AcqDataScope('CHAN3')
#data2 = AcqDataScope('CHAN2')
# for i in xrange(data_size):
    # # ## NOTE: 8-bit overflow is still a problem (changed int() to float() below to counter act this (untested)) ##
    # # #dataRUN_AVG.append(int(dataRUN_AVG_blah[i]) / N_avg)                           #divided by N and convert to 32-bit int to avoid overflow of 8-bit ints
    # data.append(float(data_blah[i])) 
    
# Walk through the data, and map it to actual voltages
# This mapping is from Cibo Mahto
# First invert the data
#data = data * -1 + 255
#data = (data-101)*-1
# Now, we know from experimentation that the scope display range is actually
# 30-229.  So shift by 130 - the voltage offset in counts, then scale to
# get the actual voltage.
#data1 = (data1 - 130.0 - voltoffset/voltscale*25) / 25 * voltscale

# Now, generate a time axis.
time = numpy.arange(0.0, len(data1), 1)
 
# See if we should use a different time axis

 
# Plot the data
plt.plot(time, data1,time, data2,time, data3)
plt.title("Oscilloscope Channel 1")
plt.ylabel("Voltage (V)")
plt.xlabel("Time")
plt.xlim(time[0], time[-100])
plt.show()



scope.close()