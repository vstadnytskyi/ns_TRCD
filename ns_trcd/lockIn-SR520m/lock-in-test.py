##how to connect
#from __future__ import division     #so that int(1)/int(2) = float(0.5) instead of int(0)
#from visual import *                #import vpython lib so that function calls don't have to be visual.function()
import visa                         #import NI-VISA wrapper (interface with equipment). Function calls are visa.function()
import sys                          #import system lib (system == python interpreter, not the os)
import numpy                      #import numeric library
import time                         #import time library
import os            #import operating system library
import matplotlib.pyplot as plt
import serial, sys, time, glob, struct
import h5py


sleeptau = 0.1
time_start =  time.clock()
plt.ion()
PEM_port = 'COM8'
Zaber_port = 'COM3'
LockIn_port = 'COM2'
Mercury_port = 'ASRL14::INSTR';
avg_per_point = 4
debug = False #True  = ON; False = OFF;
N_of_scans = 1
N_step = 90#16

phase_25 = 1;
phase_75 = 1;
##
## Wavelength table
#830 = 100120
#800 = 95300
start_wav = 760
start_pos = 49800
end_wav = 850
end_pos = 68800

cal_table_position = numpy.ones((N_step,2))
for counter in range(0,N_step):
    cal_table_position[counter,1] = round(start_wav + ((end_wav-start_wav)/(N_step-1))*counter,1)
    cal_table_position[counter,0] = int(round(start_pos + ((end_pos-start_pos)/(N_step-1))*counter,0))
print cal_table_position    
##cal_table_position = numpy.array([
##    [90000,768.8],
##    [100000,816.7],
##    [105000,843.5]
 ##                     ])
length_scan = len(cal_table_position[:,0])
print length_scan

try:
    scope.close()
except:
    pass
try:
    serZaber.close()
except:
    pass
try:
    serLockIn.close()
except:
    pass
try:
    serPEM.close()
except:
    pass

#try:
#    sys.stdout.write('\a')
#try:
#    sys.stdout.flush()



def IfPortsOpen():
	ser = serial.Serial(Zaber_port,9600, 8, 'N', 1, timeout=5)  
	if(ser.isOpen() == True):
		ser.close()
		print "Zaber Port was open and got closed"
	else:
		print "Zaber Port was  closed"	
		
	ser = serial.Serial(PEM_port,2400, 8, 'N', 1, timeout=5)  
	if(ser.isOpen() == True):
		ser.close()
		print "PEM Port was open and got closed"
	else:
		print "PEM Port was closed"	

	ser = serial.Serial(LockIn_port,9600, 8, 'N', 1, timeout=0.5) 
	if(ser.isOpen() == True):
		ser.close()
		print "LockIn Port was open and got closed"	
	else:
		print "LockIn Port was  closed"	






#################################################
##Communication with the SR 510 Lock-in##
#################################################


def lockinSend(command):
    serLockIn.flushInput()
    # send a packet using the specified device number, command number, and data
    # The data argument is optional and defaults to zero
    command_str = command+'\r\n'
    if debug == True:
        print command_str
    serLockIn.write(command_str)
    
    reply = serLockIn.readline()
    return reply

def SignalAcquire(avg_per_point):
    avgQ = 20
    sizeQ = avgQ*avg_per_point
    replyQ = numpy.zeros(sizeQ)
    replyX1 = numpy.zeros(avg_per_point)
    replyX2 = numpy.zeros(avg_per_point)
    for counter in range(avg_per_point):
        for iii in range(avgQ):
            command_str = 'Q \r\n'
            serLockIn.write(command_str)
            counter_1 = avgQ*counter+iii
            replyQ[counter_1] = float(serLockIn.readline())
        command_str = 'X1 \r\n'
        serLockIn.write(command_str)
        replyX1[counter] = float(serLockIn.readline())
        command_str = 'X2 \r\n'
        serLockIn.write(command_str)
        replyX2[counter] = float(serLockIn.readline())
        mean_Q = numpy.mean(replyQ)
        std_Q = numpy.std(replyQ)
        mean_X1 = numpy.mean(replyX1)
        std_X1 = numpy.std(replyX1)
        mean_X2 = numpy.mean(replyX2)
        std_X2 = numpy.std(replyX2)
    return mean_Q,std_Q,mean_X1,std_X1,mean_X2,std_X2
#################################################
#################################################

#################################################
##Communication with the Mercury ITC##
##################################################
def TempInitialize():
    rm = visa.ResourceManager()
    reslist=rm.list_resources()
    print 'List of Resources \n' ,reslist
    mercury = rm.open_resource(Mercury_port)
    print(mercury.query("*IDN?"))
    return mercury
    
def TempGet():
    flag = True
    while True:
        try:
            temperature = mercury.query("READ:DEV:MB1.T1:TEMP:SIG:TEMP\n")
            print 'attempt=',temperature[30:37]
            float(temperature[30:37])
        except:
            continue
        else:
         #the rest of the code
            break
    T_signal = float(temperature[30:37])
    return T_signal
print '----------------------------------------'


#################################################
#################################################

#################################################
##Communication with the Hinds PEM 100 controller##
##################################################
#make sure it is in a remote mode#


def pemSend(command):
    serPEM.flushInput()
    # send a packet using the specified device number, command number, and data
    # The data argument is optional and defaults to zero
    command_str = command+'\r\n'
    if debug == True:
        print command_str
    serPEM.write(command_str)
    time.sleep(sleeptau) # wait for 1 second
    reply = serPEM.read(10)
    print reply
#################################################
#################################################

    

##############################################
## Zaber communcation and commands start   ###
##############################################
def zaberInitialize(port):
    try:
        serZaber = serial.Serial(port, 9600, 8, 'N', 1, timeout=5)   
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
    return 'Zaber initialization complete', device, serZaber

def zaberScan():
    # scan for available ports. return a list of tuples (num, name)
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append( (i, s.portstr))
            s.close()
        except serial.SerialException:
            pass
    return available

def zaberSend(device, command, data=0):
    # send a packet using the specified device number, command number, and data
    # The data argument is optional and defaults to zero
    packet = struct.pack('<BBl', device, command, data)
    serZaber.write(packet)
    time.sleep(sleeptau) # wait for 1 second
    reply = zaberReceive()
    return reply
def zaberReceive():
    # return 6 bytes from the receive buffer
    # there must be 6 bytes to receive (no error checking)
    r = [0,0,0,0,0,0]
    for i in range (6):
        r[i] = ord(serZaber.read(1))
    return r
def zaberCleanBuffer():
    # return 6 bytes from the receive buffer
    # there must be 6 bytes to receive (no error checking)
    r = []
    flag = True
    while flag:
        if serZaber.read(1) == '':
            print 'cleaning buffer', serZaber.read(1)
            flag = False
    
def zaberMoveToAbs(moveto,device):
    command = 20
    packet = struct.pack('<BBl', device, command, moveto)
    serZaber.write(packet)
    a, CurPos = zaberCurrentPosition(1)
    print 'Current Position=',CurPos
    while moveto <> CurPos:
        a, CurPos = zaberCurrentPosition(device)
    print 'done moving', CurPos
    return  'True', CurPos
    
def zaberCurrentPosition(device):
    commandLocal = 60
    packet = struct.pack('<BBl', device, commandLocal, 0)
    serZaber.write(packet)
    reply = zaberReceive()
    if debug == True:
        print 'sent command=',commandLocal,' and  waiting for a reply'
    replyData = (256.0**3.0*reply[5]) + (256.0**2.0*reply[4]) + (256.0*reply[3]) + (reply[2])
    if reply[5] > 127:
        replyData -= 256.0**4
    if debug == True:
        print replyData
    return reply, replyData
def phaseAcquire():
    serLockIn.readline()
    serLockIn.readline()
    command_str = 'P \r\n'
    serLockIn.write(command_str)
    phase = float(serLockIn.readline())
    return phase

def phaseSet(command):
    serLockIn.readline()
    serLockIn.readline()
    command_str = 'P ' + str(command) + '\r\n'
    serLockIn.write(command_str)
    phase = serLockIn.readline()
    return phase

#################################
## Zaber communication end 
#################################

############################
## MAIN loop 
##########################
print '------- Initialize Mercury -------'
mercury = TempInitialize()
mercury.read_termination = '\n'
mercury.write_termination = '\n'
print(mercury.query("READ:SYS:CAT?"))


if debug == True:
    print 'Debugging mode is ON'
else:
    print 'Debugging mode is OFF'

IfPortsOpen()	
	
###############Initialize Zaber
print '------- Initialize Zaber -------'
try:
    serZaber = serial.Serial(Zaber_port, 9600, 8, 'N', 1, timeout=5)   
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
print("Zaber initialized Succesfully on port:" + serZaber.portstr)
#text, device, serZaber = zaberInitialize('COM4')
#print text
###############Initialize Lock-in
print "------- Initialize Lock-In -------"
try:
    serLockIn = serial.Serial(LockIn_port, 9600, 8, 'N', 1, timeout=0.05)   
except:
    print("Error opening com port. Quitting.")
    serZaber.close()
    serLockIn.close()
    serPEM.close()
    sys.exit(0)
print("Opening " + serLockIn.portstr)
print("Lock-in initialized Succesfully on port:" + serLockIn.portstr)

print "------- Initialize PEM -------"
try:
    serPEM = serial.Serial(PEM_port, 2400, 8, 'N', 1, timeout=5)   
except:
    print("Error opening com port. Quitting.")
    sys.exit(0)
print("Opening " + serPEM.portstr)
print("PEM initialized Succesfully on port:" +  serPEM.portstr)


# if debug == True:
    # pemSend('R:0250')
    # pemSend('F?')
    # print "acquire value from Lock-In"
# signalMean,signalStd = SignalAcquire(avg_per_point)
# print "mean=", signalMean, "STD=", signalStd



timestamp = int(time.time())


N_of_scans = 1
N_step = 90#16
avgQ = 2000
sizeQ = avgQ*avg_per_point
replyQ = numpy.zeros(sizeQ)
replyX1 = numpy.zeros(avg_per_point)
replyX2 = numpy.zeros(avg_per_point)
# for counter in range(avgQ):
    # serLockIn.readline()
    # command_str = 'Q \r'
    # serLockIn.write(command_str)
    # counter_1 = avgQ*counter
    # a = serLockIn.readline()
    # print a
    # replyQ[counter] = float(a)
    # plt.clf()
    # plt.plot(replyQ[:])
    # plt.pause(sleeptau*2) 
    #raw_input('press enter to measure the sample')
position = 0
Status, CurPos = zaberMoveToAbs(position,device)	




# serZaber.close()
# serLockIn.close()
# serPEM.close()
# sys.stdout.write('\a')
# sys.stdout.flush()

time_end =  time.clock()
delta_t = (-time_start + time_end)/60
print 'time in minutes', delta_t











