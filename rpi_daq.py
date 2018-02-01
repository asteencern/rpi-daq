import ctypes
import sys
import yaml
from time import sleep

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
    DAC_HIGH_WORD     = 0x42
    DAC_LOW_WORD      = 0x0A
    TRIGGER_DELAY     = 0x07# 0x00 to 0x07
    PULSE_DELAY       = 0x50# minimum value = 30 (0x1e), maximum value 127
    bcmlib=ctypes.CDLL("/usr/local/lib/libbcm2835.so", mode = ctypes.RTLD_GLOBAL)
    gpio=ctypes.CDLL("/usr/local/lib/gpiolib.so")
    eventID=0
    daq_options=yaml.YAMLObject()
    
    def __init__(self,yaml_options,DAC_HIGH_WORD=0x42,DAC_LOW_WORD=0x0A,TRIGGER_DELAY=0x07):
        print("Init rpi-daq")
        
        self.DAC_HIGH_WORD     = DAC_HIGH_WORD     
        self.DAC_LOW_WORD      = DAC_LOW_WORD      
        self.TRIGGER_DELAY     = TRIGGER_DELAY
        self.daq_options=yaml_options
        
        print("\t init RPI")
        if self.bcmlib.bcm2835_init()!=1 :
            print("bcm2835 can not init -> exit")
            sys.exit(1)
        else:
            res = self.gpio.set_bus_init()
            ##empty the fifo:
            for i in range(0,33000):
                res = self.gpio.read_local_fifo();	

            if self.daq_options['externalChargeInjection']==False:
                res = self.gpio.set_trigger_delay(self.TRIGGER_DELAY);
            else:
                res = self.gpio.set_trigger_delay(self.daq_options['pulseDelay']);
            res = self.gpio.send_command(self.CMD_RSTBPULSE);
            res = self.gpio.send_command(self.CMD_SETSELECT | 1);
                
        print("Init completed")

    ##########################################################

    def configure(self,bit_string):
        print("Configure rpi-daq")

        self.eventID=0
        
        print "\t send bits string to chips:\t",
        outputBitString=(ctypes.c_ubyte*48)()
        if len(bit_string)==384:
            outputBitString=(ctypes.c_ubyte*384)()
            print "try to prog with 384 bytes:\t",
            self.gpio.progandverify384(bit_string,outputBitString);
            print "completed"
        elif len(bit_string)==48:
            print "try to prog with 48 bytes:\t",
            self.gpio.progandverify48(bit_string,outputBitString);
            print "completed"
        else:
            print("size of bit string not correct : should be 48 or 384 instead of ",len(bit_string),"\t-> exit")
            sys.exit(1)

        print("outputBitString = ",outputBitString)

        res=self.gpio.send_command(self.CMD_SETSELECT)
        sleep(0.01)

        print("Configure completed")
        return outputBitString

        # print("Configure completed")

    ##########################################################

    def processEvent(self):
        print("Start events acquisition")
        dac_ctrl=0
        dac_fs=0xFFF
        if self.daq_options['acquisitionType']=="sweep":
            dac_ctrl = int(dac_fs * float(self.eventID) / float(self.daq_options['nEvent']))
            print("dac_ctrl = %d" % dac_ctrl)
            res = self.gpio.set_dac_high_word((dac_ctrl & 0xFF0)>>4)
            print("dac_high_word = %d" % ((dac_ctrl & 0xFF0)>>4))
            res = self.gpio.set_dac_low_word(dac_ctrl & 0x00F)
            print("dac_low_word = %d" % (dac_ctrl & 0x00F))
        elif self.daq_options['acquisitionType']=="const_inj":
            dac_ctrl = self.daq_options['injectionDAC']
            print("dac_ctrl = %d" % dac_ctrl)
            res = self.gpio.set_dac_high_word((dac_ctrl & 0xFF0)>>4)
            print("dac_high_word = %d" % ((dac_ctrl & 0xFF0)>>4))
            res = self.gpio.set_dac_low_word(dac_ctrl & 0x00F)
            print("dac_low_word = %d" % (dac_ctrl & 0x00F))            
        else:
            res = self.gpio.set_dac_high_word(self.DAC_HIGH_WORD)
            res = self.gpio.set_dac_low_word(self.DAC_LOW_WORD)	

        res = self.gpio.send_command(self.CMD_RESETPULSE)
        sleep(0.0001);
        if self.daq_options['acquisitionType']=="fixed":
            res = self.gpio.fixed_acquisition()
        else:
            res = self.gpio.send_command(self.CMD_SETSTARTACQ | 1)
            if self.daq_options['externalChargeInjection']==False:
                res = self.gpio.send_command(self.CMD_SETSTARTACQ)  ## <<<+++   THIS IS THE TRIGGER ##
            else:
                res = self.gpio.calib_gen()

        res = self.gpio.send_command(self.CMD_STARTCONPUL)
        sleep(0.003)
        res =self.gpio.send_command(self.CMD_STARTROPUL)
        sleep(0.0001)

        rawdata=[]
        t = self.gpio.read_local_fifo()
        if self.daq_options['compressRawData']==True:
            for i in range(0,15392):
                t = self.gpio.read_local_fifo()
                byte=(t & 0xf)<<4
                t = self.gpio.read_local_fifo()
                byte|=(t & 0xf)
                rawdata.append( byte )
        else:
            for i in range(0,30784):
                t = self.gpio.read_local_fifo()
                rawdata.append(t & 0xff)

        if self.daq_options['externalChargeInjection']==True:
            rawdata.append(dac_ctrl&0xff)
            rawdata.append((dac_ctrl>>8)&0xff)
        else :
            rawdata.append(0xab)
            rawdata.append(0xcd)

        self.eventID=self.eventID+1
        return rawdata
    
