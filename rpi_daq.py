import ctypes
import sys
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
    DEBUG             = False
    outputFileName    = "./Data/rawdata.raw"
    outputFile        = 0
    bcmlib=ctypes.CDLL("/usr/local/lib/libbcm2835.so", mode = ctypes.RTLD_GLOBAL)
    gpio=ctypes.CDLL("./gpiolib.so")

    def __init__(self,outputFileName,DEBUG=False,DAC_HIGH_WORD=0x42,DAC_LOW_WORD=0x0A,TRIGGER_DELAY=0x07):
        print("Init rpi-daq")
        
        self.DAC_HIGH_WORD     = DAC_HIGH_WORD     
        self.DAC_LOW_WORD      = DAC_LOW_WORD      
        self.TRIGGER_DELAY     = TRIGGER_DELAY
        self.DEBUG             = DEBUG
        self.outputFileName=outputFileName

        print("\t init RPI")
        if self.bcmlib.bcm2835_init()!=1 :
            print("bcm2835 can not init -> exit")
            sys.exit(1)
        else:
            res = self.gpio.set_bus_init()
            ##empty the fifo:
            for i in range(0,33000):
                res = self.gpio.read_local_fifo();	
            res = self.gpio.set_trigger_delay(self.TRIGGER_DELAY);
            res = self.gpio.send_command(self.CMD_RSTBPULSE);
            res = self.gpio.send_command(self.CMD_SETSELECT | 1);
 
        print("\t open output file : ",outputFileName)
        self.outputFile = open(outputFileName,'wb')

        print("Init completed")

    ##########################################################

    def configure(self,bit_string):
        print("Configure rpi-daq")
        
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
        if self.DEBUG==True:
            print("outputBitString = ",outputBitString)

        res=self.gpio.send_command(self.CMD_SETSELECT)
        sleep(0.01)

        print("\t write bits string in output file")
        byteArray = bytearray(outputBitString)
        self.outputFile.write(byteArray)

        print("Configure completed")

    ##########################################################

    def run(self,nEvent,acquisitionType,externalChargeInjection,compressRawData):
        print("Start events acquisition")
        dac_ctrl=0
        dac_fs=0xFFF
        for event in range(0,nEvent):
            if acquisitionType=="sweep":
                dac_ctrl = int(dac_fs * float(event) / float(nEvent))
                res = self.gpio.set_dac_high_word((dac_ctrl & 0xFF0)>>4)
                res = self.gpio.set_dac_low_word(dac_ctrl & 0x00F)
            else:
                res = self.gpio.set_dac_high_word(self.DAC_HIGH_WORD)
                res = self.gpio.set_dac_low_word(self.DAC_LOW_WORD)	
            res = self.gpio.send_command(self.CMD_RESETPULSE)
            sleep(0.0001);
            if acquisitionType=="fixed":
                res = self.gpio.fixed_acquisition()
            else:
                res = self.gpio.send_command(self.CMD_SETSTARTACQ | 1)
                if externalChargeInjection==False:
                    res = self.gpio.send_command(self.CMD_SETSTARTACQ)  ## <<<+++   THIS IS THE TRIGGER ##
                else:
                    res = self.gpio.calib_gen()
            res = self.gpio.send_command(self.CMD_STARTCONPUL)
            sleep(0.003)
            res =self.gpio.send_command(self.CMD_STARTROPUL)
            sleep(0.0001)

            #read and write the raw data
            rawdata=[]
            t = self.gpio.read_local_fifo()
            if compressRawData==True:
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

            if self.DEBUG==True:
                #decode raw data :
                ev=[ [0 for i in range(1924)] for sk in range(4) ]
                if compressRawData==False:
                    for i in range(1924):
                        for j in range(16):
                            x = rawdata[i*16 + j]
                            x = x & 0xf
                            for sk in range(4):
                                ev[sk][i] = ev[sk][i] | (((x >> (3 - sk) ) & 1) << (15 - j))
                else:
                    for i in range(1924):
                        for j in range(8):
                            x = rawdata[i*8 + j]
                            y = (x >> 4) & 0xf
                            x = x & 0xf
                            for sk in range(4):
                                ev[sk][i] = ev[sk][i] | (((x >> (3 - sk) ) & 1) << (14 - j*2))
                                ev[sk][i] = ev[sk][i] | (((y >> (3 - sk) ) & 1) << (15 - j*2))
                ############################################
                #    Gray to binary conversion
                ############################################
                for sk in range(4):
                    for i in range(128*15):
                        bith = ev[sk][i] & 0x8000
                        t = ev[sk][i] & 0x7fff
                        bit11 = (t >> 11) & 1
                        bit10 = bit11 ^ ((t >>10) &1)
                        bit9 = bit10 ^ ((t >>9) &1)
                        bit8 = bit9 ^ ((t >>8) &1)
                        bit7 = bit8 ^ ((t >>7) &1)
                        bit6 = bit7 ^ ((t >>6) &1)
                        bit5 = bit6 ^ ((t >>5) &1)
                        bit4 = bit5 ^ ((t >>4) &1)
                        bit3 = bit4 ^ ((t >>3) &1)
                        bit2 = bit3 ^ ((t >>2) &1)
                        bit1 = bit2 ^ ((t >>1) &1)
                        bit0 = bit1 ^ ((t >>0) &1)
                        ev[sk][i] =  bith | ((bit11 << 11) + (bit10 << 10) + (bit9 << 9) + (bit8 << 8) + (bit7 << 7) + (bit6 << 6) + (bit5 << 5) + (bit4 << 4) + (bit3  << 3) + (bit2 << 2) + (bit1  << 1) + bit0)
                        ev[sk][i] = ev[sk][i] & 0x0FFF
            
                dati=[[[0 for sca in range(15)] for ch in range(128)] for sk in range(4)]
                for sk in range(4):
                    for ch in range(128):
                        for sca in range(0,15):
                            dati[sk][ch][sca] = ev[sk][sca*128+ch]

                for sk in range(4):
                    print "Event = "+str(event)+"\t Chip = "+str(sk)+"\t RollMask = "+hex(ev[sk][1920])+"\t DacInj = ",str(dac_ctrl)
                    for ch in range(128):
                        stream=""
                        for sca in range(15):
                            stream=stream+" "+str(dati[sk][ch][sca])
                        print stream

            if externalChargeInjection==True:
                rawdata.append(dac_ctrl&0xff)
                rawdata.append((dac_ctrl>>8)&0xff)
            else :
                rawdata.append(0xab)
                rawdata.append(0xcd)
            byteArray = bytearray(rawdata)
            self.outputFile.write(byteArray)
            if event%10==0:
                print("event number ",event)
