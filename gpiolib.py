import libbcm2835._bcm2835 as bcm
import os

class gpiolib :
    MODE_READ=0
    MODE_WRITE=1
    MODE_SET=1      # redundant
    MODE_CLR=2
    MODE_INPUT_READ=3
    PULL_UP=0
    PULL_DOWN=1
    NO_PULL=2
    GPIO_BEGIN=0
    GPIO_END=1
    NO_ACTION=2
    
    STpin=bcm.RPI_V2_GPIO_P1_12
    RWpin=bcm.RPI_V2_GPIO_P1_11
    AD0pin=bcm.RPI_V2_GPIO_P1_07
    AD1pin=bcm.RPI_V2_GPIO_P1_13
    AD2pin=bcm.RPI_V2_GPIO_P1_15
    AD3pin=bcm.RPI_V2_GPIO_P1_29
    D0pin=bcm.RPI_V2_GPIO_P1_37
    D1pin=bcm.RPI_V2_GPIO_P1_36
    D2pin=bcm.RPI_V2_GPIO_P1_22
    D3pin=bcm.RPI_V2_GPIO_P1_18
    D4pin=bcm.RPI_V2_GPIO_P1_38
    D5pin=bcm.RPI_V2_GPIO_P1_40
    D6pin=bcm.RPI_V2_GPIO_P1_33
    D7pin=bcm.RPI_V2_GPIO_P1_35
    ACKpin=bcm.RPI_V2_GPIO_P1_16

    #probably useless to kepp all of them here
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

    BusMode=""
    def __init__(self) :
        bcm.bcm2835_init()
        self.BusMode=""

    ###################### LOW LEVEL ROUTINES ######################
    def set_bus_init(self):
        bcm.bcm2835_gpio_fsel(self.STpin,  bcm.BCM2835_GPIO_FSEL_OUTP)     # set pin direction
        bcm.bcm2835_gpio_fsel(self.RWpin,  bcm.BCM2835_GPIO_FSEL_OUTP)     # set pin direction
        bcm.bcm2835_gpio_fsel(self.ACKpin, bcm.BCM2835_GPIO_FSEL_INPT)     # set pin direction
        bcm.bcm2835_gpio_fsel(self.D7pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D6pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D5pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D4pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D3pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D2pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D1pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D0pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.AD0pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.AD1pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.AD2pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.AD3pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        self.BusMode = self.MODE_READ                    # start in Read mode
        lev = bcm.bcm2835_gpio_lev( self.ACKpin )	  # check that ACK is HIGH
        if lev == bcm.HIGH:
            return 0
        else:
          return -1

    def set_output_pin(self):
        bcm.bcm2835_gpio_fsel(self.RWpin, bcm.BCM2835_GPIO_FSEL_OUTP)
          

    def set_bus_read_mode(self):
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_fsel(self.D7pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D6pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D5pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D4pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D3pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D2pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D1pin, bcm.BCM2835_GPIO_FSEL_INPT)
        bcm.bcm2835_gpio_fsel(self.D0pin, bcm.BCM2835_GPIO_FSEL_INPT)
        self.BusMode = self.MODE_READ
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is HIGH
        if lev == bcm.HIGH:
            return 0
        else:
            return -1

    def set_bus_write_mode(self):
        bcm.bcm2835_gpio_write(self.RWpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_fsel(self.D7pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.D6pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.D5pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.D4pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.D3pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.D2pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.D1pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        bcm.bcm2835_gpio_fsel(self.D0pin, bcm.BCM2835_GPIO_FSEL_OUTP)
        self.BusMode = self.MODE_WRITE
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is HIGH
        if lev == bcm.HIGH:
            return 0
        else:
            return -1


    def send_command(self,cmd):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_READ:
            self.set_bus_write_mode()
        bcm.bcm2835_gpio_write(self.D0pin, (cmd       &1))
        bcm.bcm2835_gpio_write(self.D1pin, ((cmd >> 1)&1))
        bcm.bcm2835_gpio_write(self.D2pin, ((cmd >> 2)&1))
        bcm.bcm2835_gpio_write(self.D3pin, ((cmd >> 3)&1))
        bcm.bcm2835_gpio_write(self.D4pin, ((cmd >> 4)&1))
        bcm.bcm2835_gpio_write(self.D5pin, ((cmd >> 5)&1))
        bcm.bcm2835_gpio_write(self.D6pin, ((cmd >> 6)&1))
        bcm.bcm2835_gpio_write(self.D7pin, ((cmd >> 7)&1))
        bcm.bcm2835_gpio_write(self.RWpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
            print("\n Send Cmd, No ACK = 0")
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
            print("\n Send Cmd, No ACK = 1")
        if NoAck==True:
            return -1
        else:
            return 0

    def fixed_acquisition(self):
        cmd = CMD_SETSTARTACQ | 1
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.HIGH)
        if self.BusMode == self.MODE_READ:
            self.set_bus_write_mode()
        bcm.bcm2835_gpio_write(self.D0pin, (cmd       &1))
        bcm.bcm2835_gpio_write(self.D1pin, ((cmd >> 1)&1))
        bcm.bcm2835_gpio_write(self.D2pin, ((cmd >> 2)&1))
        bcm.bcm2835_gpio_write(self.D3pin, ((cmd >> 3)&1))
        bcm.bcm2835_gpio_write(self.D4pin, ((cmd >> 4)&1))
        bcm.bcm2835_gpio_write(self.D5pin, ((cmd >> 5)&1))
        bcm.bcm2835_gpio_write(self.D6pin, ((cmd >> 6)&1))
        bcm.bcm2835_gpio_write(self.D7pin, ((cmd >> 7)&1))
        bcm.bcm2835_gpio_write(self.RWpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
            print("\n Send Cmd, No ACK = 0")
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
            print("\n Send Cmd, No ACK = 1")
        if NoAck==True:
            return -1
        else:
            return 0

    def set_dac_high_word(self,val):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_READ:
            self.set_bus_write_mode()
        bcm.bcm2835_gpio_write(self.D0pin, (val       &1))
        bcm.bcm2835_gpio_write(self.D1pin, ((val >> 1)&1))
        bcm.bcm2835_gpio_write(self.D2pin, ((val >> 2)&1))
        bcm.bcm2835_gpio_write(self.D3pin, ((val >> 3)&1))
        bcm.bcm2835_gpio_write(self.D4pin, ((val >> 4)&1))
        bcm.bcm2835_gpio_write(self.D5pin, ((val >> 5)&1))
        bcm.bcm2835_gpio_write(self.D6pin, ((val >> 6)&1))
        bcm.bcm2835_gpio_write(self.D7pin, ((val >> 7)&1))
        bcm.bcm2835_gpio_write(self.RWpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin )    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin )    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
        if NoAck==True:
            return -1
        else:
            return 0


    def set_dac_low_word(self,val):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_READ:
            self.set_bus_write_mode()
        bcm.bcm2835_gpio_write(self.D0pin, (val       &1))
        bcm.bcm2835_gpio_write(self.D1pin, ((val >> 1)&1))
        bcm.bcm2835_gpio_write(self.D2pin, ((val >> 2)&1))
        bcm.bcm2835_gpio_write(self.D3pin, ((val >> 3)&1))
        bcm.bcm2835_gpio_write(self.D4pin, ((val >> 4)&1))
        bcm.bcm2835_gpio_write(self.D5pin, ((val >> 5)&1))
        bcm.bcm2835_gpio_write(self.D6pin, ((val >> 6)&1))
        bcm.bcm2835_gpio_write(self.D7pin, ((val >> 7)&1))
        bcm.bcm2835_gpio_write(self.RWpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin )    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
        if NoAck==True:
            return -1
        else:
            return 0

    def set_trigger_delay(self,val):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_READ:
           self.set_bus_write_mode()
        bcm.bcm2835_gpio_write(self.D0pin, (val       &1))
        bcm.bcm2835_gpio_write(self.D1pin, ((val >> 1)&1))
        bcm.bcm2835_gpio_write(self.D2pin, ((val >> 2)&1))
        bcm.bcm2835_gpio_write(self.D3pin, ((val >> 3)&1))
        bcm.bcm2835_gpio_write(self.D4pin, ((val >> 4)&1))
        bcm.bcm2835_gpio_write(self.D5pin, ((val >> 5)&1))
        bcm.bcm2835_gpio_write(self.D6pin, ((val >> 6)&1))
        bcm.bcm2835_gpio_write(self.D7pin, ((val >> 7)&1))
        bcm.bcm2835_gpio_write(self.RWpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
        if NoAck==True:
            return -1
        else:
            return 0


    def read_command(self):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_WRITE:
           self.set_bus_read_mode()
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
            print("\n Send Cmd, No ACK = 0")
        r = 0
        l = bcm.bcm2835_gpio_lev(self.D0pin)
        r = r | l
        l = bcm.bcm2835_gpio_lev(self.D1pin)
        r = r | (l << 1)
        l = bcm.bcm2835_gpio_lev(self.D2pin)
        r = r | (l << 2)
        l = bcm.bcm2835_gpio_lev(self.D3pin)
        r = r | (l << 3)
        l = bcm.bcm2835_gpio_lev(self.D4pin)
        r = r | (l << 4)
        l = bcm.bcm2835_gpio_lev(self.D5pin)
        r = r | (l << 5)
        l = bcm.bcm2835_gpio_lev(self.D6pin)
        r = r | (l << 6)
        l = bcm.bcm2835_gpio_lev(self.D7pin)
        r = r | (l << 7)

        result = int(r)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
            print("\n Send Cmd, No ACK = 1")
        if NoAck==True:
            return -1
        else:
            return result

    # Read used word counter on Max10 FIFO, low part
    def  read_usedwl(self):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_WRITE:
           self.set_bus_read_mode()
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
            print("\n Send Cmd, No ACK = 0")
        r = 0
        l = bcm.bcm2835_gpio_lev(self.D0pin)
        r = r | l
        l = bcm.bcm2835_gpio_lev(self.D1pin)
        r = r | (l << 1)
        l = bcm.bcm2835_gpio_lev(self.D2pin)
        r = r | (l << 2)
        l = bcm.bcm2835_gpio_lev(self.D3pin)
        r = r | (l << 3)
        l = bcm.bcm2835_gpio_lev(self.D4pin)
        r = r | (l << 4)
        l = bcm.bcm2835_gpio_lev(self.D5pin)
        r = r | (l << 5)
        l = bcm.bcm2835_gpio_lev(self.D6pin)
        r = r | (l << 6)
        l = bcm.bcm2835_gpio_lev(self.D7pin)
        r = r | (l << 7)
        result = int(r)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
            print("\n Send Cmd, No ACK = 1")
        if NoAck==True:
            return -1
        else:
            return result

    # Read used word counter on Max10 FIFO, high part
    def read_usedwh(self):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_WRITE:
           self.set_bus_read_mode()
        bcm.bcm2835_gpio_write(self.RWpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
            print("\n Send Cmd, No ACK = 0")
        r = 0
        l = bcm.bcm2835_gpio_lev(self.D0pin)
        r = r | l
        l = bcm.bcm2835_gpio_lev(self.D1pin)
        r = r | (l << 1)
        l = bcm.bcm2835_gpio_lev(self.D2pin)
        r = r | (l << 2)
        l = bcm.bcm2835_gpio_lev(self.D3pin)
        r = r | (l << 3)
        l = bcm.bcm2835_gpio_lev(self.D4pin)
        r = r | (l << 4)
        l = bcm.bcm2835_gpio_lev(self.D5pin)
        r = r | (l << 5)
        l = bcm.bcm2835_gpio_lev(self.D6pin)
        r = r | (l << 6)
        l = bcm.bcm2835_gpio_lev(self.D7pin)
        r = r | (l << 7)
        result = int(r)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
            print("\n Send Cmd, No ACK = 1")
        if NoAck==True:
            return -1
        else:
            return result



    # Write into the local FIFO
    def write_local_fifo(self,val):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_READ:
            self.set_bus_write_mode()
        bcm.bcm2835_gpio_write(self.D0pin, ( val    &1))
        bcm.bcm2835_gpio_write(self.D1pin, ((val >> 1)&1))
        bcm.bcm2835_gpio_write(self.D2pin, ((val >> 2)&1))
        bcm.bcm2835_gpio_write(self.D3pin, ((val >> 3)&1))
        bcm.bcm2835_gpio_write(self.D4pin, ((val >> 4)&1))
        bcm.bcm2835_gpio_write(self.D5pin, ((val >> 5)&1))
        bcm.bcm2835_gpio_write(self.D6pin, ((val >> 6)&1))
        bcm.bcm2835_gpio_write(self.D7pin, ((val >> 7)&1))
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
            print("\n Send Cmd, No ACK = 0")
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)

        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
            print("\n Send Cmd, No ACK = 1")
        if NoAck==True:
            return -1
        else:
            return 0

    # Read from the local FIFO
    def read_local_fifo(self):
        NoAck = False
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.LOW)
        if self.BusMode == self.MODE_WRITE:
            self.set_bus_read_mode()
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
            print("\n Send Cmd, No ACK = 0")
        r = 0
        l = bcm.bcm2835_gpio_lev(self.D0pin)
        r = r | l
        l = bcm.bcm2835_gpio_lev(self.D1pin)
        r = r | (l << 1)
        l = bcm.bcm2835_gpio_lev(self.D2pin)
        r = r | (l << 2)
        l = bcm.bcm2835_gpio_lev(self.D3pin)
        r = r | (l << 3)
        l = bcm.bcm2835_gpio_lev(self.D4pin)
        r = r | (l << 4)
        l = bcm.bcm2835_gpio_lev(self.D5pin)
        r = r | (l << 5)
        l = bcm.bcm2835_gpio_lev(self.D6pin)
        r = r | (l << 6)
        l = bcm.bcm2835_gpio_lev(self.D7pin)
        r = r | (l << 7)
        result = int(r)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
            print("\n Send Cmd, No ACK = 1")
        if NoAck==True:
            return -1
        else:
            return result


    # converts the programming sequence of 48 bytes into 384 single bytes where the LSB is 
    # the bit to be programmed
    def ConvertProgrStrBytetoBit(self,thebytes):
        bits=[]
        for i in range(0,48):
            byte=thebytes[i]
            for j in range(0,8):
                bits.append(1&(byte >>(7-j)))
        return bits


    def ConvertProgrStrBittoByte(self,bits):
        thebytes=[]
        for i in range(0,48):
            b = 0;
            for j in range(0,8):
                b = b | (bits[i*8+j] << (7 - j))
            thebytes.append(b)
        return thebytes
    

    # program the 48 bytes configuration string into the SK2 3 bits at a time
    # for all 4 chips on Hexaboard
    # and return pointer to previous configuration string, assumes pointing to bit sequence
    def prog384(self,newBits):
        returnBits=[]
        for chip in range(0,4):
            returnBits=[]
            for i in range(0,128):    #128=384/3
                bit=i*3
                bit2 = newBits[bit + 0]
                bit1 = newBits[bit + 1]
                bit0 = newBits[bit + 2]
                bits = (bit2 << 2) | (bit1 << 1) | bit0
                cmd = self.CMD_WRPRBITS | bits
                self.send_command(cmd)
                dout = self.read_command()
                bits = dout & 7
                bit2 = (bits >> 2) & 1
                bit1 = (bits >> 1) & 1
                bit0 = bits & 1
                returnBits.append(bit2)
                returnBits.append(bit1)
                returnBits.append(bit0)
        return returnBits

    def progandverify384(self,inputBits):
        outputBits=self.prog384(inputBits)
        outputBits=self.prog384(inputBits) #why do we need to do it twice
        return outputBits



    def progandverify48(self,inputBytes):
        inputBits=self.ConvertProgrStrBytetoBit(inputBytes)
        outputBits=self.prog384(inputBits)
        outputBits=self.prog384(inputBits)
        outputBytes=self.ConvertProgrStrBittoByte(outputBits)
        return outputBytes


    def calib_gen(self):
        bcm.bcm2835_gpio_write(self.AD0pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD1pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD2pin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.AD3pin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.RWpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        bcm.bcm2835_gpio_write(self.STpin, bcm.LOW)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.LOW
        if lev == bcm.HIGH:
            NoAck = True
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        bcm.bcm2835_gpio_write(self.STpin, bcm.HIGH)
        lev = bcm.bcm2835_gpio_lev( self.ACKpin	)    # check that ACK is bcm.HIGH
        if lev == bcm.LOW:
            NoAck = True
        if NoAck==True:
            return -1
        else:
            return 0
