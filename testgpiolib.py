import gpiolib

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

gpio=gpiolib.gpiolib()

res=gpio.set_bus_init()
print(res)
gpio.set_output_pin()
gpio.set_bus_read_mode()
res = gpio.send_command(CMD_RESETPULSE);
print(res)
gpio.set_bus_write_mode()
