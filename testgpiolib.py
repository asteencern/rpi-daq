import gpiolib
from optparse import OptionParser
from time import sleep

parser = OptionParser()

parser.add_option("-r", "--saveRawData",dest="saveRawData",
                  help="save raw data",default=True)

parser.add_option("-m", "--moduleNumber", dest="moduleNumber",type="int",
                  help="moduleNumber", default=63)

parser.add_option("-n", "--nEvent", dest="nEvent",type="int",
                  help="number of event",default=100)

parser.add_option("-e", "--externalChargeInjection", dest="externalChargeInjection",
                  help="set to use external injection",default=False)


parser.add_option("-c", "--channelIds", dest="channelIds",
                  help="channel Ids for charge injection", default=[36])

parser.add_option("-i", "--acquisitionType", dest="acquisitionType",choices=["standard","sweep","fixed"],
                  help="method for injection", default="standard")


(options, args) = parser.parse_args()

print(options)

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

prog_string_no_sign = [ 0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
                        0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x1F,0xFF,
                        0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
                        0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
                        0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25 ]

gpio=gpiolib.gpiolib()

#Initialize RPI
res=gpio.set_bus_init()
print(res)

gpio.set_output_pin()
res = gpio.send_command(CMD_RESETPULSE);
print(res)

# gpio.set_bus_read_mode()
# gpio.set_bus_write_mode()


# empty local fifo by forcing extra reads, ignore results
for i in range(0,1):
    res = gpio.read_local_fifo()

res = gpio.set_trigger_delay(TRIGGER_DELAY);

res = gpio.send_command(CMD_RSTBPULSE);
res = gpio.send_command(CMD_SETSELECT | 1);
print("\n\n####################################################\n")
print("Save Raw Data: %s\nExternal Pulse Injection: %s\nFixed Acquisition type: %s\n\n", options.saveRawData, options.externalChargeInjection, options.acquisitionType);
print("####################################################\n");
if options.externalChargeInjection!=True:
    #fprintf(fout,"Configuration used for SK2\n");
    #for i in range(0,48)
    #fprintf(fout,"%02x ",prog_string_no_sign[i]);

    #fprintf(fout,"\nConfiguration read from SK2\n");
    print("\nConfiguration read from SK2\n");	
    outputBytes=gpio.progandverify48(prog_string_no_sign); 
    print([hex(outputBytes[i]) for i in range(0,48)])
    #fprintf(fout,"\n");}
else:
    print(fout,"\nConfiguration read from SK2\n");	
    outputBytes=gpio.progandverify48(prog_string_no_sign); 
    print([hex(outputBytes[i]) for i in range(0,48)])
    # for(i = 0; i < 48; i = i + 1){
    #         prog_string_base[i]=prog_string_no_sign[i];
    #   }	
    #   add_channel(ch,prog_string_base);
      
    #     fprintf(fout,"Configuration used for SK2\n");
    #     for(i = 0; i < 48; i = i + 1){
    #       //fprintf(fout,"%02x ",prog_string_sign_inj[i]);
    #       fprintf(fout,"%02x ",prog_string_base[i]);
    #     }
    #     fprintf(fout,"\nConfiguration read from SK2\n");	
    #     //progandverify48(prog_string_sign_inj, return_string);
    #     progandverify48(prog_string_base, return_string); 
    #     for(i = 0; i < 48; i = i + 1){
    #       fprintf(fout,"%02x ",return_string[i]);
    #     }
    #     fprintf(fout,"\n");
    # }
      
res = gpio.send_command(CMD_SETSELECT);	
sleep(0.01);
print("\nFinished Configuration\n");
