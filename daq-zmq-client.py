import yaml
import zmq,time
import bitarray
import unpacker, datetime

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
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    print("Send request to server")
    socket.connect("tcp://localhost:5555")

    conf=yaml_config()
    daq_options=conf.yaml_opt['daq_options']

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

    the_time=datetime.datetime.now()
    fileName="./Data/Module"+str(daq_options['moduleNumber'])+"_"
    fileName=fileName+str(the_time.day)+"-"+str(the_time.month)+"-"+str(the_time.year)+"_"+str(the_time.hour)+"-"+str(the_time.minute)
    fileName=fileName+".raw"
    print("\t open output file : ",fileName)
    outputFile = open(fileName,'wb')

    cmd="CONFIGURE"
    print cmd
    socket.send(cmd)
    return_bitstring = socket.recv()
    print("Returned bit string = %s" % return_bitstring)
    bitstring=[int(i,16) for i in return_bitstring.split()]
    print("\t write bits string in output file")
    byteArray = bytearray(bitstring)
    outputFile.write(byteArray)
    
    data_unpacker=unpacker.unpacker()
    for i in range(0,daq_options['nEvent']):
        cmd="PROCESS_EVENT"
        socket.send(cmd)
        str_data=socket.recv()
        rawdata=str_data.split()
        print "Size of the data = "+str(len(rawdata))+" bytes"
        data=[int(i,16) for i in rawdata]
        data_unpacker.unpack(data)
        data_unpacker.showData(i)
        byteArray = bytearray(data)
        outputFile.write(byteArray)

    socket.close()
    context.term()
