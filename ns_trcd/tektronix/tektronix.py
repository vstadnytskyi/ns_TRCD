##how to connect
from __future__ import division     #so that int(1)/int(2) = float(0.5) instead of int(0)
from visual import *                #import vpython lib so that function calls don't have to be visual.function()
import visa                         #import NI-VISA wrapper (interface with equipment). Function calls are visa.function()
import sys                          #import system lib (system == python interpreter, not the os)
import numpy                        #import numeric library
import time                         #import time library
import os            #import operating system library
import matplotlib.pyplot as plt


#example commands
##tek.query('ACQ:STATE?')
##tek.write('ACQ:STATE RUN')
##tek.query("DATa:ENCdg?")
##tek.query('DATa:SOUrce?') - show which waveform is selected
##tek.write('DATa:SOUrce CH2') - select waveform

def temp():
    print(tek.query('ACQ:STATE?'))
    print(tek.query("*IDN?"))
    tek.write('*IDN?')
    print(tek.read_raw())

    tek.write('DATa:SOUrce CH4') #Select channel 2
    print(tek.query('DATa:SOUrce?')) #check if channel 2 is selected
    tek.write('DATa:ENCdg ASCii')
    print('Encoding of data',tek.query('DATa:ENCdg?'))
    tek.write('WFMOutpre:BYT_Nr 4')
    print('This is the number of bytes per data point', tek.query('WFMOutpre:BYT_Nr?'))

    tek.write('DATa:STARt 1')
    tek.write('DATa:STOp 10000')
    print('Start=',tek.query('DATa:STARt?'))
    print('Stop=',tek.query('DATa:STOp?'))

    waveform_parameters = tek.query('WFMOutpre?')
    print('OUT parameters',waveform_parameters)
    waveform_parameters_num = numpy.array(waveform_parameters)

    #data = tek.query('CURVe?')
    #print('length of data file',len(data))
    #values = tek.query_binary_values('CURV?', datatype='l', is_big_endian=True)
    values = tek.query_ascii_values('CURV?', separator = ',')
    print('values length = ',len(values))
    data = numpy.array(values)

    print('Waveform data point format = ',tek.query("WFMOutpre:PT_Fmt?"))
    print('Acquisition parameters for the waveform = ',tek.query("WFMOutpre:WFId?"))
    y_mult_factor_str =tek.query("WFMOutpre:YMULt?")
    print 'type of y_mult_factor_str', type(y_mult_factor_str)
    print('Vertical scale factor = ',y_mult_factor_str)
    y_mult_factor_num = float(y_mult_factor_str)
    print y_mult_factor_num

    tek.write('ACQ:STATE RUN')

#################################################
## Initialize connection ##
#################################################
def Initialize():
    rm = visa.ResourceManager()
    reslist=rm.list_resources()
    print 'List of Resources \n' ,reslist
    tek = rm.open_resource('TCPIP::192.168.20.4::gpib0,1::INSTR')
    print(tek.query("*IDN?"))
    return tek

#################################################
#################################################


#################################################
## Select waveform to download ##
#################################################
def WaveformSelect(channel,tek):
    command_str = ''.join(['DATa:SOUrce ', channel])
    tek.write(command_str)
    response_str = tek.query('DATa:SOUrce?')
    if debug == True:
        print channel, response_str
    if channel == response_str:
        print 'channel succesfully selected', channel
    tek.write('DATa:ENCdg ASCii')
    if debug == True:
        print('Encoding of data',tek.query('DATa:ENCdg?'))
    tek.write('WFMOutpre:BYT_Nr 4')
    if debug == True:
        print('This is the number of bytes per data point', tek.query('WFMOutpre:BYT_Nr?'))
    #tek.query('WFMOutpre:BYT_Nr?')
    tek.write('DATa:STARt 1')
    tek.write('DATa:STOp 50000')
#################################################
#################################################

#################################################
## Acquire parameters of the selected waveform ##
#################################################
def WaveformAcquireParameters(tek,print_flag):
    x_length = 0
    x_step = 0
    y_scale_factor = 0
    ###Horizontal length
    x_length_str =tek.query("WFMOutpre:NR_Pt?")
    x_length = float(x_length_str)
    ##Horizontal sampling interval
    x_step_str =tek.query("WFMOutpre:XINcr?")
    x_step = float(x_step_str)
    ###Vertical scale factor
    y_scale_factor_str =tek.query("WFMOutpre:YMULt?")
    y_scale_factor= float(y_scale_factor_str)
    ### Number of bits per data point
    num_bits_str = tek.query('WFMOutpre:BYT_Nr?')
    num_bits= float(num_bits_str)
    num_offset_str = tek.query('WFMOutpre:YZEro?')
    num_offset= float(num_offset_str)
    
    if print_flag == True:
        print 'y scale factor(in Volts) = ',  y_scale_factor
        print 'x step(in seconds) = ', x_step
        print 'x length(in counts) = ', x_length
        print 'Number of Bits per data point = ', num_bits
    return y_scale_factor,x_step, x_length, num_bits, num_offset
#################################################
#################################################

#################################################
## Obtain waveform ##
#################################################
def WaveformGet(tek,x_length):
    values = tek.query_ascii_values('CURV?', separator = ',')
    if len(values) == x_length:
        if debug == True:
            print 'Succesful extraction! ','values length = ',len(values)
    data = numpy.array(values)
    return data

#################################################
#################################################

#################################################
## Save CH1, CH2, CH3, CH4 in a file##
#################################################
def WaveformSaveToFile (tek,counter,filename):
    WaveformSelect('CH1',tek)
    [yScaleFactor,xStep, xLength, nBits, offSet] = WaveformAcquireParameters(tek,False)
    yDataArray = numpy.ones((xLength))
    xDataArray = numpy.ones((xLength))
    xyDataArray = numpy.ones((xLength,5))

    if debug == True:
        print 'Selected channel = ',tek.query('DATa:SOUrce?')
    
    if debug == True:
        print 'y scale factor(in Volts) = ', yScaleFactor
        print 'x step(in seconds) = ', xStep
        print 'x length(in counts) = ', xLength 
        print 'Number of Bits per data point = ', nBits
        print 'offset = ', offSet



    yDataArray = WaveformGet(tek,xLength)
    for j in range(0, int(xLength)):
        xDataArray[j] = j*xStep
        
    for j in range(0, int(xLength)):
        xyDataArray[j,0] = xDataArray[j]
        xyDataArray[j,1] = yDataArray[j]*yScaleFactor + offSet

    WaveformSelect('CH2',tek)
    [yScaleFactor,xStep, xLength, nBits, offSet] = WaveformAcquireParameters(tek,False)
    yDataArray = WaveformGet(tek,xLength)
    for j in range(0, int(xLength)):
        xyDataArray[j,2] = yDataArray[j]*yScaleFactor + offSet

    WaveformSelect('CH3',tek)
    [yScaleFactor,xStep, xLength, nBits, offSet] = WaveformAcquireParameters(tek,False)
    yDataArray = WaveformGet(tek,xLength)
    for j in range(0, int(xLength)):
        xyDataArray[j,3] = yDataArray[j]*yScaleFactor + offSet

    WaveformSelect('CH4',tek)
    [yScaleFactor,xStep, xLength, nBits, offSet] = WaveformAcquireParameters(tek,False)
    yDataArray = WaveformGet(tek,xLength)
    for j in range(0, int(xLength)):
        xyDataArray[j,4] = yDataArray[j]*yScaleFactor + offSet

        
    file_name = ''.join(['data\data_',filename,'_', str(counter),'.txt'])
    numpy.savetxt(file_name, xyDataArray, delimiter=',') 

#################################################
#################################################

###################################
## Wait for trigger ready
#################################

############################
## MAIN BODY 
##########################
debug = True #True  = ON; False = OFF;
if debug == True:
    print 'Debugging mode is ON'
else:
    print 'Debugging mode is OFF'
    

tek = Initialize()
#tek.write('ACQ:STATE RUN')
TrigState = tek.query('TRIGger:STATE?')
if TrigState == 'SAVE\n':
    tek.write('ACQ:STATE RUN')
print 'Prepare to measure: Trigger state = ', TrigState
time_gstart = time.clock()

#for j in range(0,100):
j = 1
while True:
    TrigState = tek.query('TRIGger:STATE?')
    if TrigState == 'SAVE\n':
        tek.write('ACQ:STATE RUN')
    flagTrig = True
    while flagTrig == True:
        TrigStateA = tek.query('TRIGger:STATE?')
        if TrigStateA == 'READY\n':
            flagTrig = False
            print 'counter = ', j ,'\n', 'Ready to measure: TriggerState = ',TrigStateA
    flagTrig = True
    while flagTrig == True:
        TrigStateA = tek.query('TRIGger:STATE?')
        if TrigStateA == 'SAVE\n':
            flagTrig = False
            print 'Trigger occured: TriggerState = ',TrigStateA
    time_start = time.clock()
    WaveformSaveToFile(tek,j,'FMO_825nm_pos_')
    time_finish = time.clock()
    delta_t = time_finish - time_start
    print 'Elapsed time in seconds = ' , delta_t
    print '\n \n'
    j=j+1
time_gfinish = time.clock()
delta_t = time_gfinish - time_gstart
print 'Elapsed time in seconds = ' , delta_t
