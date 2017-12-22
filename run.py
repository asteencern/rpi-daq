##GPIOLIB.SO : gcc -c -I ./RPi_software/bcm2835-1.52/src ./RPi_software/bcm2835-1.52/src/bcm2835.c -fPIC gpiolib.c; gcc -shared -o gpiolib.so gpiolib.o
## example : python run.py --moduleNumber=63 --nEvent=1000 --acquisitionType=sweep --externalChargeInjection --channelIds=0,10,50,34 --compressRawData --channelIdsMask=22 --channelIdsDisableTOT=22  --channelIdsDisableTOA=22

from optparse import OptionParser
import rpi_daq, unpacker, datetime
import skiroc2cms_bit_string as sk2conf
import ctypes

def get_comma_separated_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

parser = OptionParser()

parser.add_option("-a", "--compressRawData",dest="compressRawData",action="store_true",
                  help="option to compress (ie remove the '1000' before each word) raw data",default=False)

parser.add_option("-b", "--moduleNumber", dest="moduleNumber",type="int",action="store",
                  help="moduleNumber", default=63)

parser.add_option("-c", "--nEvent", dest="nEvent",type="int",
                  help="number of event",default=100)

parser.add_option("-d", "--externalChargeInjection", dest="externalChargeInjection",action="store_true",
                  help="set to use external injection",default=False)

parser.add_option("-e", "--acquisitionType", dest="acquisitionType",choices=["standard","sweep","fixed"],
                  help="method for injection", default="standard")

parser.add_option('-f', '--channelIds', dest="channelIds",action="callback",type=str,
                  help="channel Ids for charge injection", callback=get_comma_separated_args, default=[])

parser.add_option('-g', '--channelIdsMask', dest="channelIdsMask",action="callback",type=str,
                  help="channel Ids to mask ie disable the preamp", callback=get_comma_separated_args, default=[])

parser.add_option('-i', '--channelIdsDisableTOT', dest="channelIdsDisableTOT",action="callback",type=str,
                  help="disable trigger TOT in channelIdsDisableTOT", callback=get_comma_separated_args, default=[])

parser.add_option('-j', '--channelIdsDisableTOA', dest="channelIdsDisableTOA",action="callback",type=str,
                  help="disable trigger TOA in channelIdsDisableTOA", callback=get_comma_separated_args, default=[])

(options, args) = parser.parse_args()
print(options)

DEBUG=False
compressRawData=options.compressRawData
moduleNumber=options.moduleNumber
nEvent=options.nEvent
externalChargeInjection=options.externalChargeInjection
acquisitionType=options.acquisitionType
channelIds=[int(chan) for chan in options.channelIds] 
channelIdsMask=[int(chan) for chan in options.channelIdsMask]
channelIdsDisableTOT=[int(chan) for chan in options.channelIdsDisableTOT]
channelIdsDisableTOA=[int(chan) for chan in options.channelIdsDisableTOA]

the_bit_string=sk2conf.bit_string()
the_bit_string.Print()
if externalChargeInjection==True:
    the_bit_string.set_channels_for_charge_injection(channelIds)
    the_bit_string.Print()

# the_bit_string.set_channels_to_mask(channelIdsMask)
# the_bit_string.set_channels_to_disable_trigger_tot(channelIdsDisableTOT)
# the_bit_string.set_channels_to_disable_trigger_toa(channelIdsDisableTOA)
# the_bit_string.Print()

the_bits_c_uchar_p=the_bit_string.get_48_unsigned_char_p()
print( [hex(the_bits_c_uchar_p[i]) for i in range(48)] )


the_time=datetime.datetime.now()
fileName="./Data/Module"+str(moduleNumber)+"_"
fileName=fileName+str(the_time.day)+"-"+str(the_time.month)+"-"+str(the_time.year)+"_"+str(the_time.hour)+"-"+str(the_time.minute)
fileName=fileName+".raw"
theDaq=rpi_daq.rpi_daq()
print("\t open output file : ",fileName)
outputFile = open(fileName,'wb')

outputBitString=theDaq.configure(the_bits_c_uchar_p,acquisitionType,externalChargeInjection,nEvent)
print("\t write bits string in output file")
byteArray = bytearray(outputBitString)
outputFile.write(byteArray)

data_unpacker=unpacker.unpacker()
for event in range(nEvent):
    rawdata=theDaq.processEvent(compressRawData)

    data_unpacker.unpack(rawdata)
    data_unpacker.showData(event)
    
    byteArray = bytearray(rawdata)
    outputFile.write(byteArray)
        
    if event%10==0:
        print("event number ",event)
