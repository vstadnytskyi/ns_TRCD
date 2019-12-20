from __future__ import division     #so that int(1)/int(2) = float(0.5) instead of int(0)
from visual import *                #import vpython lib so that function calls don't have to be visual.function()
import visa                         #import NI-VISA wrapper (interface with equipment). Function calls are visa.function()
import sys                          #import system lib (system == python interpreter, not the os)
import numpy                        #import numeric library
import time                         #import time library
import os                           #import operating system library

##often modified global variables

#fileName = "Chl a and b in 3to2 meoh_eth glyc"
fileName = "__Ru 4 tpy bpy__new sample_2mm path_shaken9_digital filter block 22p5-27p5MHz"
fileExt = ".csv"    #file extention (saveSpectrum() saves as a CSV format)
pump = 345          #pump wavelength (for file comments)
probe = 532         #probe wavelength (for file comments)
probe_dia = 2 #mm
pump_dia = 3 #mm
q_switch = 300

vertS = 2

N_avg = 4          #number of shots to average (then end program)


###################
## plot spectrum ##
###################
def plot(spectrum,scaleVert,timescaleScale): ## this function should try to use "matplotlib" instead of "visual" (matplotlib causes issues on my laptop)
    data = spectrum[0][0]
    dMin = spectrum[0][1]
    dMax = spectrum[0][2]
    dRange = dMax-dMin
        
    time = spectrum[1][0]
    tPoints = len(time)
    zeroIndex = spectrum[1][3]
    
    N = len(data)
    N_tick = 500 #int(N/10)

    curvePoints = []
    axisTicks = []
    axisTickLabels = []

    for i in xrange(N):
        curvePoints.append((i,data[i]*scaleVert*tPoints/dRange))    #voltages scaled for display
        t = time[i] 
        
        if (i-int(zeroIndex))%N_tick == 0:                          #place a tick and label on horizontal axis every N_tick points (adjusted for t=0)
            axisTicks.append((i,0))
            _text = "%.3f" % (t*timescaleScale) 
            axisTickLabels.append(label(pos=(i,1),text=_text,border=1,box=False))
        
    c = curve(pos=curvePoints)
    ticks = points(pos=axisTicks)
###################
###################

##############################################
## update running average of collected data ##
##############################################
def averageData(runningAvg, newData, N_avg):
    len1 = len(runningAvg)
    len2 = len(newData)
    if len1 != len2:
        print "Arrays not equal length"
        sys.exit(-1)
    s = []
    for i in xrange(len1):
        ## NOTE: 8-bit overflow is still a problem (changed int() to float() below to counter act this (untested)) ##
        #s.append(runningAvg[i]+int(newData[i])/N_avg)   #convert newData to 32-bit int and add to average
        s.append(float(runningAvg[i])+float(newData[i])/N_avg)   #convert newData to 32-bit float and add to average
    return s
##############################################
##############################################

############################################################
## convert data from raw scope format to voltage and time ##
############################################################
def formatData(dataRAW,sample_rate,timeoffset):
    N_points = len(dataRAW)
    zeroTime = (N_points/2)/sample_rate     #t=0 ignoring "timeoffset" 

    time = []
    
    for i in xrange(len(dataRAW)):
        ###########################################
        ## voltage scaling. stolen from internet ##
        ###########################################
        # Walk through the data, and map it to actual voltages
        # This mapping is from Cibo Mahto
        # First invert the data
        dataRAW[i] = (dataRAW[i]*-1) + 255
        # Now, we know from experimentation that the scope display range is actually
        # 30-229.  So shift by 130 - the voltage offset in counts, then scale to
        # get the actual voltage.
        dataRAW[i] = (dataRAW[i] - 130.0 - voltoffset/voltscale*25) / 25 * voltscale

        ## time scaling ##
        t = (i/sample_rate) - (zeroTime - timeoffset)   #time corrected for offset
        time.append(t)

    startTime = min(time) 
    step = i/sample_rate                                #dt
    zeroIndex = (zeroTime-timeoffset)*sample_rate       #array index of t=0

    #spectrum format spectrum = [[DATA],[TIME]] --> [DATA] = [voltage points array, min volt, max volt]. [TIME] = [time points array, T_start, array index of t=0]
    return [[dataRAW,min(dataRAW),max(dataRAW)],[time,startTime,step,zeroIndex]]
############################################################
############################################################

################################
## save spectrum  to csv file ##
################################
def saveSpectrum(spectrum, fileName, commentString=""):
    path = os.getcwd()                  #get current working directory
    data = spectrum[0][0]               #Y
    time = spectrum[1][0]               #X
    N = len(data)
    outFile = open(path+"\\"+fileName, 'w')  #create output file in current directory

    if commentString != "":
        outFile.write(commentString)

    end_of_line = "\n"
    for i in xrange(N):
        if i == N-1:
            end_of_line = ""
        
        outFile.write(str(time[i]) + "," + str(data[i]) + end_of_line)

    outFile.close()
    print "Spectrum saved as: ", path+fileName
################################
################################

##########################
## initialize osc scope ##
##########################
def init_Scope():
    instruments = visa.get_instruments_list()
    usb = filter(lambda x: 'USB' in x, instruments)
    if len(usb) != 1:
        print 'Bad instrument list', instruments
        sys.exit(-1)
    scope = visa.instrument(usb[0], timeout=15, chunk_size=1024000) # use bigger timeout for deep mem (i.e. collecting 1e6 points)
    return scope
##########################
##########################

####################################
## compute delta A from intensity ##
####################################
def deltaA(spectrum):
    data = spectrum[0][0]
    time = spectrum[1][0]
    zeroIndex = int(spectrum[1][3])
    
    I_noPump = sum(data[:zeroIndex-1])/len(data[:zeroIndex-1])  #average of trans intensity before pump pulse

    dA = []
    N_points = len(data)

    for i in xrange(N_points):
        dA.append(-numpy.log10(data[i]/I_noPump))               #delta A

    return [[dA,min(dA),max(dA)],spectrum[1]]
####################################
####################################



##########
## MAIN ##
##########

scene.autocenter = True # Vpython stuff
readSleepTime = .1 #s

## note that interacting with scope autolocks the front pannel keys. you must unlock them when done with software command or reboot scope
## init oscilloscope
scope = init_Scope() 

## set scope trigger mode and start
scope.write(":TRIG:MODE EDGE")      #trigger on edge
scope.write(":TRIG:EDGE:SWE SING")  #single trigger mode
scope.write(":RUN")                 #start scope
time.sleep(readSleepTime) ## needed???

## Get the horizontal and vertial scales and offsets
#horizontal
timescale = scope.ask_for_values(":TIM:SCAL?")[0]
timeoffset = scope.ask_for_values(":TIM:OFFS?")[0]
#vertical
voltscale = scope.ask_for_values(':CHAN1:SCAL?')[0]
voltoffset = scope.ask_for_values(":CHAN1:OFFS?")[0]

print "N averages = ", N_avg, "\n---Ready---"

wP = " with pump"
woP = " without pump"
###################
## Read 1st shot ##
###################

scope.write(":TRIG:EDGE:SWE SING")              #reset trigger mode to single (seems to need this)
time.sleep(readSleepTime)
while scope.ask(":TRIG:STAT?") != "STOP":       # wait for scope to be triggered and finish data collection
    #print scope.ask(":TRIG:STAT?")
    wait = 1                                    # "wait = 1" is probably not needed, it's just that an empty loop scares me.
scope.write(":WAV:POIN:MODE MAX")               #set waveform point mode to max (returns ~8000 points)
rawdata = scope.ask(":WAV:DATA? CHAN1")[10:]    # retrieve raw data (note 1st 10 points are unneeded header information)
time.sleep(readSleepTime)   #needed??
print "1" + wP                                       #shot #1 recorded
data_size = len(rawdata)
sample_rate = scope.ask_for_values(":ACQ:SRAT? CHAN1")[0]   #samples per second

dataRUN_AVG_blah_WP = numpy.frombuffer(rawdata, dtype="int8")       #convert buffered raw scope data to 8-bit array
dataRUN_AVG_WP = [] # stupid read only python lists

## without pump
scope.write(":RUN")
time.sleep(readSleepTime)
scope.write(":TRIG:EDGE:SWE SING")              
time.sleep(readSleepTime)
while scope.ask(":TRIG:STAT?") != "STOP":      
    wait = 1
scope.write(":WAV:POIN:MODE MAX")               
rawdata = scope.ask(":WAV:DATA? CHAN1")[10:]    
time.sleep(readSleepTime)   
print "1" + woP                                   
data_size = len(rawdata)
sample_rate = scope.ask_for_values(":ACQ:SRAT? CHAN1")[0]   

dataRUN_AVG_blah_WOP = numpy.frombuffer(rawdata, dtype="int8")      
dataRUN_AVG_WOP = [] # stupid read only python lists

for i in xrange(data_size):
    ## NOTE: 8-bit overflow is still a problem (changed int() to float() below to counter act this (untested)) ##
    #dataRUN_AVG.append(int(dataRUN_AVG_blah[i]) / N_avg)                           #divided by N and convert to 32-bit int to avoid overflow of 8-bit ints
    dataRUN_AVG_WP.append(float(dataRUN_AVG_blah_WP[i]) / N_avg)                           #divided by N and convert to 32-bit float to avoid overflow of 8-bit ints
    dataRUN_AVG_WOP.append(float(dataRUN_AVG_blah_WOP[i]) / N_avg)

data_size = len(dataRUN_AVG_blah_WOP)
#############################
## Read next N_avg-1 shots ##
#############################

i=0
while i < (N_avg-1):
    scope.write(":RUN")                             #start scope
    scope.write(":TRIG:EDGE:SWE SING")              #reset single trigger mode
    while scope.ask(":TRIG:STAT?") != "STOP":       #wait for scope to be triggered and finish data collection
        wait = 1
    rawdata = scope.ask(":WAV:DATA? CHAN1")[10:]    # retrieve raw data
    time.sleep(readSleepTime)   #needed?
    dataNEW_WP = numpy.frombuffer(rawdata, dtype="int8")
    dataRUN_AVG_WP = averageData(dataRUN_AVG_WP,dataNEW_WP,N_avg)    #update running average
    print str(i+2) + wP   #shot #(i) recorded

    scope.write(":RUN")                             #start scope
    scope.write(":TRIG:EDGE:SWE SING")              #reset single trigger mode
    while scope.ask(":TRIG:STAT?") != "STOP":       #wait for scope to be triggered and finish data collection
        wait = 1
    rawdata = scope.ask(":WAV:DATA? CHAN1")[10:]    # retrieve raw data
    time.sleep(readSleepTime)   #needed?
    dataNEW_WOP = numpy.frombuffer(rawdata, dtype="int8")
    dataRUN_AVG_WOP = averageData(dataRUN_AVG_WOP,dataNEW_WOP,N_avg)    #update running average
    print str(i+2) + woP   #shot #(i) recorded

    i+=1
    
scope.write(":KEY:LOCK DIS")    #unlock front pannel keys
scope.close()                   #close connection to scope


timescaleSCALE = 1e6 # 1e3
vertScale = 0.2

spectrum_WP = formatData(dataRUN_AVG_WP,sample_rate,timeoffset)   #format data to voltage and time
spectrum_dA_WP = deltaA(spectrum_WP)          #compute dA
#plot(spectrum_dA_WP,vertScale,timescaleSCALE)   #plot dA
spectrum_WOP = formatData(dataRUN_AVG_WOP,sample_rate,timeoffset)   #format data to voltage and time
spectrum_dA_WOP = deltaA(spectrum_WOP)          #compute dA
#plot(spectrum_dA_WOP,vertScale,timescaleSCALE)   #plot dA

spectrum_DIFF_data = []
for i in xrange(data_size):
    spectrum_DIFF_data.append(spectrum_dA_WP[0][0][i]-spectrum_dA_WOP[0][0][i])

spectrum_DIFF = [[spectrum_DIFF_data,min(spectrum_DIFF_data),max(spectrum_DIFF_data)],spectrum_dA_WP[1]]

plot(spectrum_DIFF,vertScale*vertS,timescaleSCALE)   #plot dA

## generate full file name and file comment string ##
t = time.localtime()
date_time = str(t.tm_mon)+"-"+str(t.tm_mday)+"-"+str(t.tm_year)+"_"+str(t.tm_hour)+"h"+str(t.tm_min)+"m"+str(t.tm_sec)+"s"
pump_probe = str(pump)+"pump, " + str(probe)+"probe"
averagesStr = str(int(N_avg)) + " averages"
pump_probe_dia = "Diameter" + str(pump_dia)+"mm pump, " + str(probe_dia)+"mm probe"
q_switch_STR = "Q switch = " + str(q_switch)

fileName = fileName + "_" + pump_probe + "_" + averagesStr + "_" + date_time + fileExt

commentString = pump_probe + "\n" + pump_probe_dia + "\n" + q_switch_STR + "\n" + averagesStr + "\n" + date_time + "\nData points = " + str(data_size) + "\nSample rate = " + str(sample_rate) + " samples/second\nSeconds/div = " + str(timescale) + " s\nVolts/div = " + str(voltscale) + " V\n"
saveSpectrum(spectrum_DIFF, fileName, commentString)

print commentString
