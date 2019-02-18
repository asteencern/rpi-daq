import datetime,ctypes,yaml
import rpi_daq, unpacker
import skiroc2cms_bit_string as sk2conf
from optparse import OptionParser

class yaml_config:
    yaml_opt=yaml.YAMLObject()
    
    def __init__(self,fname="default-config.yaml"):
        with open(fname) as fin:
            self.yaml_opt=yaml.safe_load(fin)
            
    def dump(self):
        return yaml.dump(self.yaml_opt)

    def dumpToYaml(self,fname="config.yaml"):
        with open(fname,'w') as fout:
            yaml.dump(self.yaml_opt,fout)
        
def get_comma_separated_args(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

if __name__ == "__main__":
    
    parser = OptionParser()
    parser.add_option("-d", "--externalChargeInjection", dest="externalChargeInjection",action="store_true",
                      help="set to use external injection",default=False)
    choices_m=["standard","sweep","fixed","const_inj","instrumental_trigger","external_trigger"]
    parser.add_option("-e", "--acquisitionType", dest="acquisitionType",choices=choices_m,
                      help="acquisition method, valid choices are:\t%s"%(choices_m), default="standard")
    parser.add_option('-f', '--channelIds', dest="channelIds",action="callback",type=str,
                      help="channel Ids for charge injection", callback=get_comma_separated_args, default=[])
    parser.add_option('-g','--injectionDAC',dest="injectionDAC",type="int",action="store",default=1000,
                      help="DAC setting for injection when acquisitionType is const_inj")
    parser.add_option('-i','--dataNotSaved',dest="dataNotSaved",action="store_true",default=False,
                      help="set to throw the data away")
    parser.add_option('-s','--showRawData',dest="showRawData",action="store_true",default=False,
                      help="set to decode and print raw data")
    (options, args) = parser.parse_args()
    print(options)

    conf=yaml_config()
    conf.yaml_opt['daq_options']['acquisitionType'] = options.acquisitionType
    conf.yaml_opt['daq_options']['externalChargeInjection'] = options.externalChargeInjection
    conf.yaml_opt['daq_options']['injectionDAC'] = options.injectionDAC
    for i in options.channelIds:
        conf.yaml_opt['daq_options']['channelIds'].append(int(i))

    daq_options=conf.yaml_opt['daq_options']
    glb_options=conf.yaml_opt['glb_options']

    
    print "daq options = "+yaml.dump(daq_options)
    print "Global options = "+yaml.dump(glb_options)

    the_bits_c_uchar_p=(ctypes.c_ubyte*192)()
    for chip in range(4):
        the_bit_string=sk2conf.bit_string()
        if daq_options['externalChargeInjection']==True:
            the_bit_string.set_channels_for_charge_injection(daq_options['channelIds'])
        if daq_options['preampFeedbackCapacitance']>63:
            print("!!!!!!!!! WARNING :: preampFeedbackCapacitance should not be higher than 63 !!!!!!!")
            the_bit_string.set_preamp_feedback_capacitance(daq_options['preampFeedbackCapacitance'])
        #change bit string in chip:
        nchannelsToMask = len(daq_options['channelIdsToMask'][chip])
        print daq_options['channelIdsToMask'][chip]
        if nchannelsToMask > 0:
            the_bit_string.set_channels_to_mask(daq_options['channelIdsToMask'][chip])
            the_bit_string.set_channels_to_disable_trigger_tot(daq_options['channelIdsToMask'][chip])
            the_bit_string.set_channels_to_disable_trigger_toa(daq_options['channelIdsToMask'][chip])
        the_bit_string.set_lg_shaping_time(daq_options['shapingTime'])
        the_bit_string.set_hg_shaping_time(daq_options['shapingTime'])
        the_bit_string.set_tot_dac_threshold(daq_options['totDACThreshold'])
        the_bit_string.set_toa_dac_threshold(daq_options['toaDACThreshold'])
        c_uchar_p=the_bit_string.get_48_unsigned_char_p()
        for j in range(len(c_uchar_p)):
            the_bits_c_uchar_p[48*chip+j]=c_uchar_p[j]

    outputBitString=theDaq.configure_4chips(the_bits_c_uchar_p)
    print( "chip 0 ",[hex(outputBitString[0][i]) for i in range(48)] )
    print( "chip 1 ",[hex(outputBitString[1][i]) for i in range(48)] )
    print( "chip 2 ",[hex(outputBitString[2][i]) for i in range(48)] )
    print( "chip 3 ",[hex(outputBitString[3][i]) for i in range(48)] )

    
    the_time=datetime.datetime.now()
    if glb_options['storeYamlFile'] and not options.dataNotSaved:
        yamlFileName=glb_options['outputYamlPath']+"/Module"+str(glb_options['moduleNumber'])+"_"
        yamlFileName=yamlFileName+str(the_time.day)+"-"+str(the_time.month)+"-"+str(the_time.year)+"_"+str(the_time.hour)+"-"+str(the_time.minute)
        yamlFileName=yamlFileName+".yaml"
        print("\t save yaml file : ",yamlFileName)
        conf.dumpToYaml(yamlFileName)

    outputFile=0
    if not options.dataNotSaved:
        rawFileName=glb_options['outputRawDataPath']+"/Module"+str(glb_options['moduleNumber'])+"_"
        rawFileName=rawFileName+str(the_time.day)+"-"+str(the_time.month)+"-"+str(the_time.year)+"_"+str(the_time.hour)+"-"+str(the_time.minute)
        rawFileName=rawFileName+".raw"
        print("\t open output file : ",rawFileName)
        outputFile = open(rawFileName,'wb')
        print("\t write bits string in output file")
        byteArray = bytearray(outputBitString)
        outputFile.write(byteArray)

    data_unpacker=unpacker.unpacker(daq_options['compressRawData'])
    for event in range(daq_options['nEvent']):
        rawdata=theDaq.processEvent()
        if options.showRawData:
            data_unpacker.unpack(rawdata)
            data_unpacker.showData(event)
        if not options.dataNotSaved:
            byteArray = bytearray(rawdata)
            outputFile.write(byteArray)
