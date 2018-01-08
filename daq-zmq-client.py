import sys
import zmq,time
import bitarray

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
    socket = context.socket(zmq.REQ)
    print("Send request to server")
    socket.connect("tcp://localhost:5555")


    conf=yaml_config()
    daq_options=conf.yaml_opt['daq_options']

    cmd="READ_CONFIG default-config.yaml"
    print cmd    
    socket.send(cmd)
    the_config=socket.recv()
    print("Returned config:\n%s"%the_config)

            
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
    print("\t write bits string in output file")
    byteArray = bytearray(outputBitString)
    outputFile.write(byteArray)
    
    for i in range(0,daq_options['nEvent']):
        cmd="PROCESS_EVENT"
        socket.send(cmd)
        str_data=socket.recv()
        data=str_data.split()
        print "Size of the data = "+str(len(data))+" bytes"
        message=""
        for i in range(0,50):
            message=message+" "+data[i]
            message=message+"\t"+data[len(data)-1]
            print message


    socket.close()
    context.term()
