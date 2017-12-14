##GPIOLIB.SO : gcc -c -I ./RPi_software/bcm2835-1.52/src ./RPi_software/bcm2835-1.52/src/bcm2835.c -fPIC gpiolib.c; gcc -shared -o gpiolib.so gpiolib.o
import ctypes
from optparse import OptionParser
from time import sleep

parser = OptionParser()

parser.add_option("-r", "--compressRawData",dest="compressRawData",action="store_true",
                  help="option to compress (ie remove the '1000' before each word) raw data",default=False)

parser.add_option("-m", "--moduleNumber", dest="moduleNumber",type="int",
                  help="moduleNumber", default=63)

parser.add_option("-n", "--nEvent", dest="nEvent",type="int",
                  help="number of event",default=100)

parser.add_option("-e", "--externalChargeInjection", dest="externalChargeInjection",action="store_true",
                  help="set to use external injection",default=False)


parser.add_option("-c", "--channelIds", dest="channelIds",
                  help="channel Ids for charge injection", default=[36])

parser.add_option("-i", "--acquisitionType", dest="acquisitionType",choices=["standard","sweep","fixed"],
                  help="method for injection", default="standard")


(options, args) = parser.parse_args()
print(options)

compressRawData=options.compressRawData
moduleNumber=options.moduleNumber
nEvent=options.nEvent
externalChargeInjection=options.externalChargeInjection
channelIds=options.channelIds
acquisitionType=options.acquisitionType

bcmlib=ctypes.CDLL("/usr/local/lib/libbcm2835.so", mode = ctypes.RTLD_GLOBAL)
gpio=ctypes.CDLL("/home/pi/arnaud-dev/rpi-daq/gpiolib.so")
res=bcmlib.bcm2835_init()
print("coucou",res)

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

prog_string_no_sign=[ 0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
                      0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x1F,0xFF,
                      0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
                      0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
                      0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25 ]

prog_string_to_c_uchar_p = (ctypes.c_ubyte*48)()
for i in range(0,48):
    prog_string_to_c_uchar_p[i]=prog_string_no_sign[i]

#Initialize RPI
res=gpio.set_bus_init()
print(res)

res = gpio.send_command(CMD_RESETPULSE);
print(res)


# empty local fifo by forcing extra reads, ignore results
for i in range(0,10):
    res = gpio.read_local_fifo()

res = gpio.set_trigger_delay(TRIGGER_DELAY);

res = gpio.send_command(CMD_RSTBPULSE);
res = gpio.send_command(CMD_SETSELECT | 1);
print("\n\n####################################################\n")
print("Compress Raw Data: ",compressRawData,"\nExternal Pulse Injection: ", externalChargeInjection,"\nFixed Acquisition type: ",acquisitionType,"\n");
print("####################################################\n");

outputBytes=(ctypes.c_ubyte*48)()
if externalChargeInjection!=True:
    print("\nConfiguration read from SK2\n");	
    gpio.progandverify48(prog_string_to_c_uchar_p,outputBytes); 
    print([hex(outputBytes[i]) for i in range(0,48)])
else:
    print("\nConfiguration read from SK2\n");	
    gpio.progandverify48(prog_string_to_c_uchar_p,outputBytes); 
    print([hex(outputBytes[i]) for i in range(0,48)])

outputFile = open('Data/filename.raw','wb')
byteArray = bytearray(outputBytes)
outputFile.write(byteArray)
    
res = gpio.send_command(CMD_SETSELECT)
sleep(0.1)
print("\nFinished Configuration\n")

print("\nStart events acquisition\n")
rawData=[]
dac_ctrl=0
dac_fs=0xFFF
for i in range(0,nEvent):
    print("event number ",i)
    if acquisitionType=="sweep":
        dac_ctrl = int(dac_fs * float(i) / float(nEvent))
        res = gpio.set_dac_high_word((dac_ctrl & 0xFF0)>>4)
        res = gpio.set_dac_low_word(dac_ctrl & 0x00F)
    else:
        res = gpio.set_dac_high_word(DAC_HIGH_WORD)
        res = gpio.set_dac_low_word(DAC_LOW_WORD)	
    res = gpio.send_command(CMD_RESETPULSE)
    sleep(0.0001);
    if acquisitionType=="fixed":
        res = gpio.fixed_acquisition()
    else:	
        res = gpio.send_command(CMD_SETSTARTACQ | 1)
    if externalChargeInjection:
        res = gpio.send_command(CMD_SETSTARTACQ)  ## <<<+++   THIS IS THE TRIGGER ##
    else:
        gpio.calib_gen()
    res = gpio.send_command(CMD_STARTCONPUL)
    sleep(0.003)
    res = gpio.send_command(CMD_STARTROPUL)
    sleep(0.0001)
    #read the raw data
    if compressRawData==True:
        for i in range(0,30785):
            t = gpio.read_local_fifo()
            if i%2==0:
                rawData.append( (t & 0xf)<<4 )
            else:
                rawData[int(i/2)] |= (t & 0xf)
    else:
        for i in range(0,30785):
            t = gpio.read_local_fifo()
            rawData.append(t & 0xff)

    rawData.append(dac_ctrl&0xff)
    rawData.append((dac_ctrl>>8)&0xff)
    byteArray = bytearray(rawData)
    outputFile.write(byteArray)
