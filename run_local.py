import datetime,ctypes,yaml
import rpi_daq, unpacker
import skiroc2cms_bit_string as sk2conf

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
        
if __name__ == "__main__":
    conf=yaml_config()
    daq_options=conf.yaml_opt['daq_options']
    glb_options=conf.yaml_opt['glb_options']

    print "daq options = "+yaml_dump(daq_options)
    print "Global options = "+yaml.dump(glb_options)

    the_bit_string=sk2conf.bit_string()
    the_bit_string.Print()
    if daq_options['externalChargeInjection']==True:
        if len(daq_options['channelIds'])>0:
            the_bit_string.set_channels_for_charge_injection(daq_options['channelIds'])
            the_bit_string.Print()
        else:
            print("Option channelIds should not be empty if charge injection is set")
        

    if len(daq_options['channelIdsMask'])>0:
        the_bit_string.set_channels_to_mask(daq_options['channelIdsMask'])
        
    if len(daq_options['channelIdsDisableTOT'])>0:
        the_bit_string.set_channels_to_disable_trigger_tot(daq_options['channelIdsDisableTOT'])

    if len(daq_options['channelIdsDisableTOT'])>0:
        the_bit_string.set_channels_to_disable_trigger_toa(daq_options['channelIdsDisableTOA'])

    the_bits_c_uchar_p=the_bit_string.get_48_unsigned_char_p()
    print( [hex(the_bits_c_uchar_p[i]) for i in range(48)] )


    the_time=datetime.datetime.now()
    fileName="./Data/Module"+str(glb_options['moduleNumber'])+"_"
    fileName=fileName+str(the_time.day)+"-"+str(the_time.month)+"-"+str(the_time.year)+"_"+str(the_time.hour)+"-"+str(the_time.minute)
    fileName=fileName+".raw"
    theDaq=rpi_daq.rpi_daq()
    print("\t open output file : ",fileName)
    outputFile = open(fileName,'wb')

    outputBitString=theDaq.configure(the_bits_c_uchar_p,daq_options)
    print("\t write bits string in output file")
    byteArray = bytearray(outputBitString)
    outputFile.write(byteArray)

    data_unpacker=unpacker.unpacker(daq_options['compressRawData'])
    for event in range(daq_options['nEvent']):
        rawdata=theDaq.processEvent(daq_options['compressRawData'])
        data_unpacker.unpack(rawdata)
        data_unpacker.showData(event)
    
        byteArray = bytearray(rawdata)
        outputFile.write(byteArray)
        
        if event%10==0:
            print("event number ",event)
