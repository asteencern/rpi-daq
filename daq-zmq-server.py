import zmq,yaml
import ctypes,struct,datetime,time
import rpi_daq, unpacker
import skiroc2cms_bit_string as sk2conf

if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    pusher=context.socket(zmq.PUSH)
    pusher.bind("tcp://*:5556")

    daq_options=yaml.YAMLObject()
    
    theDaq=0
    packer=0
    
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
                dataSize=30786 # 30784 + 2 for injection value
                if daq_options['compressRawData']==True:
                    dataSize=15394 # 30784/2 + 2 for injection value
                packer=struct.Struct('B'*dataSize)
                
            elif content[0] == "CONFIGURE":
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
                    the_bit_string.Print()
                    c_uchar_p=the_bit_string.get_48_unsigned_char_p()
                    for j in range(len(c_uchar_p)):
                        the_bits_c_uchar_p[48*chip+j]=c_uchar_p[j]

                outputBitString=theDaq.configure_4chips(the_bits_c_uchar_p)
                print( "chip 0 ",[hex(outputBitString[0][i]) for i in range(48)] )
                print( "chip 1 ",[hex(outputBitString[1][i]) for i in range(48)] )
                print( "chip 2 ",[hex(outputBitString[2][i]) for i in range(48)] )
                print( "chip 3 ",[hex(outputBitString[3][i]) for i in range(48)] )
                msg=''
                for i in range(4):
                    for j in range(48):
                        msg=msg+hex(outputBitString[i][j])+' '
                socket.send(msg)
                
            elif content[0] == "PROCESS_EVENT":
                rawdata=theDaq.processEvent()
                pdata=packer.pack(*rawdata)
                socket.send(pdata)

            elif content[0] == "PROCESS_AND_PUSH_N_EVENTS":
                socket.send("start to process and push the events")
                print("start to process and push the events")
                for i in xrange(daq_options['nEvent']):
                    rawdata=theDaq.processEvent()
                    pdata=packer.pack(*rawdata)
                    pusher.send(pdata)
                print("finish to process and push the events")

            elif content[0] == "END_OF_RUN":
                pusher.close()
                socket.send("CLOSING_SERVER")
                socket.close()
                context.term()
                break
                
    except KeyboardInterrupt:
        print('\nClosing server')
        pusher.close()
        socket.close()
        context.term()
