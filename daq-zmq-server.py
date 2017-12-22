import zmq
import yaml
import rpi_daq, unpacker, datetime
import skiroc2cms_bit_string as sk2conf
import ctypes

class yaml_config:
    yaml_opt=yaml.YAMLObject()
    
    def __init__(self,fname="default-config.yaml"):
        with open(fname) as fin:
            self.yaml_opt=yaml.safe_load(fin)
        #print yaml.dump(self.yaml_opt)
            
    def dump(self):
        return yaml.dump(self.yaml_opt)

    def dumpToYaml(self,fname="config.yaml"):
        with open(fname,'w') as fout:
            yaml.dump(self.yaml_opt,fout)
        

if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    conf=yaml_config()
    daq_options=conf.yaml_opt['daq_options']
    
    theDaq=rpi_daq.rpi_daq()

    try:
        while True:
            string = socket.recv()
            print("Received request: %s" % string)
            content = string.split()

            if content[0] == "READ_CONFIG":
                conf=yaml_config(content[1])
                socket.send(conf.dump())
                daq_options=conf.yaml_opt['daq_options']
                theDaq=rpi_daq.rpi_daq()#can modify global daq parameter here (DAC_HIGH_WORD,DAC_LOW_WORD,TRIGGER_DELAY)

            elif content[0] == "CONFIGURE":
                the_bit_string=sk2conf.bit_string()
                if daq_options['externalChargeInjection']==True:
                    the_bit_string.set_channels_for_charge_injection(daq_options['channelIds'])
                    
                the_bit_string.set_channels_to_mask(daq_options['channelIdsToMask'])
                the_bit_string.set_channels_to_disable_trigger_tot(daq_options['channelIdsDisableTOT'])
                the_bit_string.set_channels_to_disable_trigger_toa(daq_options['channelIdsDisableTOA'])
                the_bits_c_uchar_p=the_bit_string.get_48_unsigned_char_p()
                outputBitString=theDaq.configure(the_bits_c_uchar_p,daq_options['acquisitionType'],daq_options['externalChargeInjection'],daq_options['nEvent'])
                msg=''
                for i in range(48):
                    msg=msg+hex(outputBitString[i])+' '
                socket.send(msg)
                
            elif content[0] == "PROCESS_EVENT":
                rawdata=theDaq.processEvent(daq_options['compressRawData'])
                data=" "
                for i in rawdata:
                    data=data+hex(i)+" "
                socket.send(data)
    except KeyboardInterrupt:
        print('\nClosing server')
        socket.close()
        context.term()
