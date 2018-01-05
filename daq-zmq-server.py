import zmq
import yaml
import rpi_daq, unpacker, datetime
import skiroc2cms_bit_string as sk2conf
import ctypes

if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    daq_options=yaml.YAMLObject()
    
    theDaq=0

    try:
        while True:
            string = socket.recv()
            print("Received request: %s" % string)
            content = string.split()

            if content[0] == "DAQ_CONFIG":
                socket.send("READY_FOR_CONFIG")
                yamlstring=socket.recv()
                print yamlstring
                yaml_conf=yaml.safe_load(yamlstring)
                socket.send(yaml.dump(yaml_conf))
                daq_options=yaml_conf['daq_options']
                theDaq=rpi_daq.rpi_daq(daq_options)#can modify global daq parameter here (DAC_HIGH_WORD,DAC_LOW_WORD,TRIGGER_DELAY)

            elif content[0] == "CONFIGURE":
                the_bit_string=sk2conf.bit_string()
                if daq_options['externalChargeInjection']==True:
                    the_bit_string.set_channels_for_charge_injection(daq_options['channelIds'])
                    
                the_bit_string.set_channels_to_mask(daq_options['channelIdsToMask'])
                the_bit_string.set_channels_to_disable_trigger_tot(daq_options['channelIdsDisableTOT'])
                the_bit_string.set_channels_to_disable_trigger_toa(daq_options['channelIdsDisableTOA'])
                the_bits_c_uchar_p=the_bit_string.get_48_unsigned_char_p()
                outputBitString=theDaq.configure(the_bits_c_uchar_p)
                msg=''
                for i in range(48):
                    msg=msg+hex(outputBitString[i])+' '
                socket.send(msg)
                
            elif content[0] == "PROCESS_EVENT":
                rawdata=theDaq.processEvent()
                data=" "
                for i in rawdata:
                    data=data+hex(i)+" "
                socket.send(data)

            elif content[0] == "END_OF_RUN":
                socket.send("CLOSING_SERVER")
                socket.close()
                context.term()
                break
                
    except KeyboardInterrupt:
        print('\nClosing server')
        socket.close()
        context.term()
