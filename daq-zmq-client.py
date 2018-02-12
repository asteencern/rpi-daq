import zmq,yaml
import os,time,datetime
import bitarray,struct
import unpacker
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
    parser.add_option("-a", "--externalChargeInjection", dest="externalChargeInjection",action="store_true",
                      help="set to use external injection",default=False)
    parser.add_option("-b", "--acquisitionType", dest="acquisitionType",choices=["standard","sweep","fixed","const_inj"],
                      help="method for injection", default="standard")
    parser.add_option('-c', '--channelIds', dest="channelIds",action="callback",type=str,
                      help="channel Ids for charge injection", callback=get_comma_separated_args, default=[])
    parser.add_option('-d','--injectionDAC',dest="injectionDAC",type="int",action="store",default=1000,
                      help="DAC setting for injection when acquisitionType is const_inj")
    parser.add_option('-e','--dataNotSaved',dest="dataNotSaved",action="store_true",default=False,
                      help="set to true if you don't want to save the data (and the yaml file)")
    parser.add_option("-f", "--pulseDelay", dest="pulseDelay",type="int",action="store",
                      help="pulse delay (arbitrary unit) w.r.t. the trigger",default=72)
    (options, args) = parser.parse_args()
    print(options)

    conf=yaml_config()
    conf.yaml_opt['daq_options']['acquisitionType']=options.acquisitionType
    conf.yaml_opt['daq_options']['externalChargeInjection']=options.externalChargeInjection
    conf.yaml_opt['daq_options']['injectionDAC']=options.injectionDAC
    conf.yaml_opt['daq_options']['pulseDelay']=options.pulseDelay
    for i in options.channelIds:
        conf.yaml_opt['daq_options']['channelIds'].append(int(i))
    
    daq_options=conf.yaml_opt['daq_options']
    glb_options=conf.yaml_opt['glb_options']

    print "Global options = "+yaml.dump(glb_options)

    if glb_options['startServerManually']==False:
        os.system("ssh -T pi@"+glb_options['serverIpAdress']+" \"nohup python "+glb_options['serverCodePath']+"/daq-zmq-server.py > log.log 2>&1& \"")
    
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    print("Send request to server")
    socket.connect("tcp://"+glb_options['serverIpAdress']+":5555")

    cmd="DAQ_CONFIG"
    print cmd
    socket.send(cmd)
    status=socket.recv()
    if status=="READY_FOR_CONFIG":
        socket.send(conf.dump())
        the_config=socket.recv()
        print("Returned DAQ_CONFIG:\n%s"%the_config)
    else:
        print "WRONG STATUS -> exit()"
        exit()

    dataSize=30786 # 30784 + 2 for injection value
    if daq_options['compressRawData']==True:
            dataSize=15394 # 30784/2 + 2 for injection value
    dataStringUnpacker=struct.Struct('B'*dataSize)
        
    outputFile=0
    if options.dataNotSaved==False:
        while True:
            the_time=datetime.datetime.now()
            rawFileName=glb_options['outputRawDataPath']+"/Module"+str(glb_options['moduleNumber'])+"_"
            rawFileName=rawFileName+str(the_time.day)+"-"+str(the_time.month)+"-"+str(the_time.year)+"_"+str(the_time.hour)+"-"+str(the_time.minute)
            rawFileName=rawFileName+".raw"
            if os.path.exists(rawFileName):
                continue
            else:
                print("open output file : ",rawFileName)
                outputFile = open(rawFileName,'wb')
                if glb_options['storeYamlFile']==True:
                    yamlFileName=glb_options['outputYamlPath']+"/Module"+str(glb_options['moduleNumber'])+"_"
                    yamlFileName=yamlFileName+str(the_time.day)+"-"+str(the_time.month)+"-"+str(the_time.year)+"_"+str(the_time.hour)+"-"+str(the_time.minute)
                    yamlFileName=yamlFileName+".yaml"
                    print("save yaml file : ",yamlFileName)
                    conf.dumpToYaml(yamlFileName)
                break
            
    cmd="CONFIGURE"
    print cmd
    socket.send(cmd)
    return_bitstring = socket.recv()
    print("Returned bit string = %s" % return_bitstring)
    bitstring=[int(i,16) for i in return_bitstring.split()]
    print("\t write bits string in output file")
    byteArray = bytearray(bitstring)
    if options.dataNotSaved==False:
        outputFile.write(byteArray)
    
    #data_unpacker=unpacker.unpacker(daq_options['compressRawData'])

    # for i in xrange(0,daq_options['nEvent']):
    #     cmd="PROCESS_EVENT"
    #     socket.send(cmd)
    #     str_data=socket.recv()
    #     rawdata=dataStringUnpacker.unpack(str_data)
    #     print("Receive event %d",i)
    #     #data_unpacker.unpack(rawdata)
    #     #data_unpacker.showData(i)
    #     byteArray = bytearray(rawdata)
    #     if options.dataNotSaved==False:
    #         outputFile.write(byteArray)

    cmd="PROCESS_AND_PUSH_N_EVENTS"
    socket.send(cmd)
    mes=socket.recv()
    print(mes)
    puller=context.socket(zmq.PULL)
    puller.connect("tcp://"+glb_options['serverIpAdress']+":5556")
    for i in xrange(0,daq_options['nEvent']):
        str_data=puller.recv()
        rawdata=dataStringUnpacker.unpack(str_data)
        print("Receive event %d",i)
        byteArray = bytearray(rawdata)
        if options.dataNotSaved==False:
            outputFile.write(byteArray)
    puller.close()
    
    socket.send("END_OF_RUN")
    if socket.recv()=="CLOSING_SERVER":
        socket.close()
        context.term()


