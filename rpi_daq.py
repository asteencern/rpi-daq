import ctypes
import sys
import yaml
from time import sleep

import os
path = os.path.dirname(os.path.realpath(__file__))

class rpi_daq:
    CMD_IDLE          = 0x80
    CMD_RESETPULSE    = 0x88
    CMD_WRPRBITS      = 0x90
    CMDH_WRPRBITS     = 0x12 
    CMD_SETSTARTACQ   = 0x98
    CMD_STARTCONPUL   = 0xA0
    CMD_STARTROPUL    = 0xA8
    CMD_SETSELECT     = 0xB0
    CMD_RSTBPULSE     = 0xD8
    CMD_READSTATUS    = 0xC0
    CMDH_READSTATUS   = 0x18
    CMD_LOOPBRFIFO    = 0xF0
    CMDH_LOOPBRFIFO   = 0x1E
    CMD_LOOPBACK      = 0xF8
    CMDH_LOOPBACK     = 0x1F
    PULSE_DELAY       = 0x50# minimum value = 30 (0x1e), maximum value 127    

    bcmlib = ctypes.CDLL(path+"/lib/libbcm2835.so", mode = ctypes.RTLD_GLOBAL)
    gpio   = ctypes.CDLL(path+"/lib/libgpiohb.so")

    eventID = 0
    daq_options = yaml.YAMLObject()
    rawdata = []
    daq_ctrl = 0
    
    def __init__(self,yaml_options,DAC_HIGH_WORD=0x42,DAC_LOW_WORD=0x0A,TRIGGER_DELAY=0x07):
        print("Init rpi-daq")
        
        self.DAC_WORD     = DAC_HIGH_WORD << 4 | DAC_LOW_WORD      
        self.TRIGGER_DELAY     = TRIGGER_DELAY
        self.daq_options       = yaml_options
        
        print("\t init RPI")
        if self.bcmlib.bcm2835_init()!=1 :
            print("bcm2835 can not init -> exit")
            sys.exit(1)

        self.gpio.set_bus_init()

        ##empty the fifo by reading it in full plus one position
        for i in xrange( (1<<15) + 1 ):
            self.gpio.read_local_fifo()

        if self.daq_options['externalChargeInjection']==False:
            self.gpio.set_trigger_delay(self.TRIGGER_DELAY)
        else:
            self.gpio.set_trigger_delay(self.daq_options['pulseDelay'])

        self.gpio.send_command(self.CMD_RSTBPULSE)
        self.gpio.send_command(self.CMD_SETSELECT | 1)

        if self.daq_options['acquisitionType']=="const_inj":
            self.dac_ctrl = self.daq_options['injectionDAC']
            self.gpio.set_dac_word(self.dac_ctrl)
        else:
            self.dac_ctrl = self.DAC_WORD
            self.gpio.set_dac_word(self.DAC_WORD)

                
        if self.daq_options['compressRawData']==True:
            # 15392 bytes of data + 2 bytes for injetion value
            self.rawdata = [0] * 15394 
        else:
            # 30784 bytes of data + 2 bytes for injetion value
            self.rawdata = [0] * 30786 

        print("Init completed")

    ##########################################################

    def configure(self,bit_string):
        print("Configure rpi-daq")

        self.eventID = 0
        
        print "\t send bitstring to chips:\t",
        outputBitString=(ctypes.c_ubyte*48)()
        if len(bit_string)==384:
            outputBitString=(ctypes.c_ubyte*384)()
            print "try to prog with 384 bytes:\t",
            self.gpio.progandverify384(bit_string,outputBitString)
            print "completed"
        elif len(bit_string)==48:
            print "try to prog with 48 bytes:\t",
            self.gpio.progandverify48(bit_string,outputBitString)
            print "completed"
        else:
            print("size of bit string not correct: should be 48 or 384 instead of ",len(bit_string),"bytes\t-> exit")
            sys.exit(1)

        print("outputBitString = ",outputBitString)

        res=self.gpio.send_command(self.CMD_SETSELECT)
        sleep(0.01)

        print("Configure completed")
        return outputBitString

    ##########################################################

    def configure_4chips(self,bit_string):
        print("Configure rpi-daq")

        self.eventID = 0

        print "\t send different bits string to the 4 chips:\t",
        outputBitString=(ctypes.c_ubyte*48*4)()
        if len(bit_string)==384*4:
            outputBitString=(ctypes.c_ubyte*384*4)()
            print "try to prog with 384*4 bytes:\t",
            self.gpio.progandverify384_4chips(bit_string,outputBitString)
            print "completed"
        elif len(bit_string)==48*4:
            print "try to prog with 48*4 bytes:\t",
            self.gpio. progandverify48_4chips(bit_string,outputBitString)
            print "completed"
        else:
            print("size of bit string not correct : should be 48*4 or 384*4 instead of ",len(bit_string),"\t-> exit")
            sys.exit(1)

        print("outputBitString = ",outputBitString)

        res=self.gpio.send_command(self.CMD_SETSELECT)
        sleep(0.01)

        print("Configure completed")
        return outputBitString

    ##########################################################

    def acquire(self):

        acqType = self.daq_options['acquisitionType']

        if acqType in ("instrumental_trigger", "external_trigger"):
            res = self.gpio.send_command(self.CMD_SETSTARTACQ | 1)
          
            if acqType=="instrumental_trigger":
                # firmware sets the trigger to the pin -> external device
                # (e.g. pulse generator) -> external trigger
                res = self.gpio.instrumental_trigger()

        else:
            if acqType=="fixed":
                res = self.gpio.fixed_acquisition()
                
            elif acqType=="standard":
                res = self.gpio.send_command(self.CMD_SETSTARTACQ | 1)
                sleep(0.00001)
                # This stops the acquisition
                res = self.gpio.send_command(self.CMD_SETSTARTACQ)  

            elif acqType in ("sweep", "const_inj"):
                res = self.gpio.send_command(self.CMD_SETSTARTACQ | 1)
                sleep(0.00001)
                #Generate calibration pulse and stop acquisition (two-in-one)
                res = self.gpio.calib_gen()

            # Perform conversion (CON) and readout (RO) manually
            res = self.gpio.send_command(self.CMD_STARTCONPUL)
            sleep(0.003) # 3 ms
            res =self.gpio.send_command(self.CMD_STARTROPUL)
            
        # Wait for data to be present in the FIFO
        while ( self.gpio.read_fifo_status() == 0xfe ):
            # 0xfe means empty, 0xfc means used
            #print(self.gpio.read_fifo_status(),self.gpio.read_usedw())
            pass

    def processEvent(self):
        print("Start acquisition of event {}".format(self.eventID))

        if self.daq_options['acquisitionType']=="sweep":
            # DAC full range is 0xfff
            self.dac_ctrl = int( float(0Xfff) * self.eventID/self.daq_options['nEvent'] )
            res = self.gpio.set_dac_word(self.dac_ctrl)

        res = self.gpio.send_command(self.CMD_RESETPULSE)
        sleep(0.0001)

        # start acquisition, stop it (trigger), convert, and readout SK->HB->TS
        self.acquire()
        
        #Perform the readout TS->here
        self.gpio.read_local_fifo() # skip first word, 0xff; should in fact be checked        
        if self.daq_options['compressRawData']:
            for i in xrange(15394):
                t1 = self.gpio.read_local_fifo()
                t2 = self.gpio.read_local_fifo()
                self.rawdata[i] = (t1 & 0xf)<<4 | (t2 & 0xf)
        else:
            for i in xrange(30786):
                t = self.gpio.read_local_fifo()
                self.rawdata[i] = t & 0xff

        #Append the injection DAC value
        if self.daq_options['externalChargeInjection']:
            self.rawdata[len(self.rawdata)-2]=   self.dac_ctrl    & 0xff
            self.rawdata[len(self.rawdata)-1]= (self.dac_ctrl>>8) & 0xff
            print "dac_ctrl = ", self.dac_ctrl
        else :
            self.rawdata[len(self.rawdata)-2]=0xab
            self.rawdata[len(self.rawdata)-1]=0xcd

        self.eventID = self.eventID + 1
        return self.rawdata
    
