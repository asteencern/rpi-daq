#include <bcm2835.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>

static unsigned char BusMode;         // global to remember status of gpio lines (IN or OUT)
#define MODE_READ 0
#define MODE_WRITE 1

#define  STpin RPI_V2_GPIO_P1_12
#define  RWpin RPI_V2_GPIO_P1_11
#define AD0pin RPI_V2_GPIO_P1_07
#define AD1pin RPI_V2_GPIO_P1_13
#define AD2pin RPI_V2_GPIO_P1_15
#define AD3pin RPI_V2_GPIO_P1_29
#define  D0pin RPI_V2_GPIO_P1_37
#define  D1pin RPI_V2_GPIO_P1_36
#define  D2pin RPI_V2_GPIO_P1_22
#define  D3pin RPI_V2_GPIO_P1_18
#define  D4pin RPI_V2_GPIO_P1_38
#define  D5pin RPI_V2_GPIO_P1_40
#define  D6pin RPI_V2_GPIO_P1_33
#define  D7pin RPI_V2_GPIO_P1_35
#define ACKpin RPI_V2_GPIO_P1_16

#include "data_addr_luts.h"

/* define commands for Master */

#define CMD_IDLE         0x80
#define CMD_RESETPULSE   0x88
#define CMD_WRPRBITS     0x90
#define CMDH_WRPRBITS    0x12 
#define CMD_SETSTARTACQ  0x98
#define CMD_STARTCONPUL  0xA0
#define CMD_STARTROPUL   0xA8
#define CMD_SETSELECT    0xB0
#define CMD_RSTBPULSE    0xD8
#define CMD_READSTATUS   0xC0
#define CMDH_READSTATUS  0x18
#define CMD_LOOPBRFIFO   0xF0
#define CMDH_LOOPBRFIFO  0x1E
#define CMD_LOOPBACK     0xF8
#define CMDH_LOOPBACK    0x1F

static uint32_t *BCM2835_GPIO_LEV_ADDR; 

////////////////////////////// LOW LEVEL ROUTINES //////////////////////////////
extern "C" int set_bus_init()
{
  if(!bcm2835_init()){
    printf("problem in gpiolib.c method set_but_init(): bcm2835_init() failed -> exit code");
    exit(1);
  }

  BCM2835_GPIO_LEV_ADDR = bcm2835_regbase(BCM2835_REGBASE_GPIO) + BCM2835_GPLEV0/4;
  
  bcm2835_gpio_fsel(STpin,  BCM2835_GPIO_FSEL_OUTP);     // set pin direction
  bcm2835_gpio_fsel(RWpin,  BCM2835_GPIO_FSEL_OUTP);     // set pin direction
  bcm2835_gpio_fsel(ACKpin, BCM2835_GPIO_FSEL_INPT);     // set pin direction

  bcm2835_gpio_fsel(D7pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D6pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D5pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D4pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D3pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D2pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D1pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D0pin, BCM2835_GPIO_FSEL_INPT);

  bcm2835_gpio_fsel(AD0pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(AD1pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(AD2pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(AD3pin, BCM2835_GPIO_FSEL_OUTP);

  bcm2835_gpio_set_multi(ADDR_SET_LUT(0));
  bcm2835_gpio_clr_multi(ADDR_CLR_LUT(0));

  BusMode = MODE_READ;                                // start in Read mode

  if(bcm2835_gpio_lev(ACKpin) == HIGH) {
    return(0);
  }
  else {
    return(-1);
  }
}

extern "C" int set_bus_read_mode()
{
  bcm2835_gpio_write(RWpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  
  bcm2835_gpio_fsel(D7pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D6pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D5pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D4pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D3pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D2pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D1pin, BCM2835_GPIO_FSEL_INPT);
  bcm2835_gpio_fsel(D0pin, BCM2835_GPIO_FSEL_INPT);

  BusMode = MODE_READ;

  if(bcm2835_gpio_lev(ACKpin) == HIGH) {
    return(0);
  }
  else {
    return(-1);
  }
}

extern "C" int set_bus_write_mode()
{
  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, HIGH);
  
  bcm2835_gpio_fsel(D7pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(D6pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(D5pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(D4pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(D3pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(D2pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(D1pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(D0pin, BCM2835_GPIO_FSEL_OUTP);
  
  BusMode = MODE_WRITE;

  if(bcm2835_gpio_lev(ACKpin) == HIGH) {
    return(0);
  }
  else {
    return(-1);
  }
}

extern "C" int send_command(unsigned char c)
{
  bool NoAck;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_set_multi(ADDR_SET_LUT(0));
  bcm2835_gpio_clr_multi(ADDR_CLR_LUT(0));

  if(BusMode == MODE_READ)
    set_bus_write_mode();

  bcm2835_gpio_set_multi(DATA_SET_LUT(c));
  bcm2835_gpio_clr_multi(DATA_CLR_LUT(c));

  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
    printf("\n Send Cmd, No ACK = 0");
  }
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(RWpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
    printf("\n Send Cmd, No ACK = 1");
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int fixed_acquisition(void)
{
  bool NoAck;
  char c;
  c = CMD_SETSTARTACQ | 1;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, HIGH);

  if(BusMode == MODE_READ)
    set_bus_write_mode();

  bcm2835_gpio_write(D0pin, (c       &1));
  bcm2835_gpio_write(D1pin, ((c >> 1)&1));
  bcm2835_gpio_write(D2pin, ((c >> 2)&1));
  bcm2835_gpio_write(D3pin, ((c >> 3)&1));
  bcm2835_gpio_write(D4pin, ((c >> 4)&1));
  bcm2835_gpio_write(D5pin, ((c >> 5)&1));
  bcm2835_gpio_write(D6pin, ((c >> 6)&1));
  bcm2835_gpio_write(D7pin, ((c >> 7)&1));

  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
    printf("\n Send Cmd, No ACK = 0");
  }
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(RWpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
    printf("\n Send Cmd, No ACK = 1");
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int set_dac_high_word(unsigned char c)
{
  bool NoAck;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, LOW);
  bcm2835_gpio_write(AD1pin, HIGH);
  bcm2835_gpio_write(AD2pin, HIGH);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_READ)
    set_bus_write_mode();

  bcm2835_gpio_write(D0pin, (c       &1));
  bcm2835_gpio_write(D1pin, ((c >> 1)&1));
  bcm2835_gpio_write(D2pin, ((c >> 2)&1));
  bcm2835_gpio_write(D3pin, ((c >> 3)&1));
  bcm2835_gpio_write(D4pin, ((c >> 4)&1));
  bcm2835_gpio_write(D5pin, ((c >> 5)&1));
  bcm2835_gpio_write(D6pin, ((c >> 6)&1));
  bcm2835_gpio_write(D7pin, ((c >> 7)&1));

  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(RWpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int set_dac_low_word(unsigned char c)
{
  bool NoAck;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, HIGH);
  bcm2835_gpio_write(AD2pin, HIGH);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_READ)
    set_bus_write_mode();

  bcm2835_gpio_write(D0pin, (c       &1));
  bcm2835_gpio_write(D1pin, ((c >> 1)&1));
  bcm2835_gpio_write(D2pin, ((c >> 2)&1));
  bcm2835_gpio_write(D3pin, ((c >> 3)&1));
  bcm2835_gpio_write(D4pin, ((c >> 4)&1));
  bcm2835_gpio_write(D5pin, ((c >> 5)&1));
  bcm2835_gpio_write(D6pin, ((c >> 6)&1));
  bcm2835_gpio_write(D7pin, ((c >> 7)&1));

  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(RWpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int set_trigger_delay(unsigned char c)
{
  bool NoAck;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, HIGH);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_READ)
    set_bus_write_mode();

  bcm2835_gpio_write(D0pin, (c       &1));
  bcm2835_gpio_write(D1pin, ((c >> 1)&1));
  bcm2835_gpio_write(D2pin, ((c >> 2)&1));
  bcm2835_gpio_write(D3pin, ((c >> 3)&1));
  bcm2835_gpio_write(D4pin, ((c >> 4)&1));
  bcm2835_gpio_write(D5pin, ((c >> 5)&1));
  bcm2835_gpio_write(D6pin, ((c >> 6)&1));
  bcm2835_gpio_write(D7pin, ((c >> 7)&1));

  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(RWpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int read_command(void)
{
  bool NoAck;
  unsigned char l;
  unsigned char r;
  int result;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, LOW);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_WRITE)
    set_bus_read_mode();

  bcm2835_gpio_write(RWpin, HIGH);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
    printf("\n Read Cmd, No ACK = 0");
  }

  r = 0;
  l = bcm2835_gpio_lev(D0pin);
  r = r | l;
  l = bcm2835_gpio_lev(D1pin);
  r = r | (l << 1);
  l = bcm2835_gpio_lev(D2pin);
  r = r | (l << 2);
  l = bcm2835_gpio_lev(D3pin);
  r = r | (l << 3);
  l = bcm2835_gpio_lev(D4pin);
  r = r | (l << 4);
  l = bcm2835_gpio_lev(D5pin);
  r = r | (l << 5);
  l = bcm2835_gpio_lev(D6pin);
  r = r | (l << 6);
  l = bcm2835_gpio_lev(D7pin);
  r = r | (l << 7);

  result = (int) r;
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
    printf("\n Read Cmd, No ACK = 1");
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(result);
  }
}

// Read used word counter on Max10 FIFO, low part
extern "C" int read_usedwl(){
  bool NoAck;
  unsigned char l;
  unsigned char r;
  int result;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, LOW);
  bcm2835_gpio_write(AD1pin, HIGH);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_WRITE)
    set_bus_read_mode();

  bcm2835_gpio_write(RWpin, HIGH);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }
  r = 0;
  l = bcm2835_gpio_lev(D0pin);
  r = r | l;
  l = bcm2835_gpio_lev(D1pin);
  r = r | (l << 1);
  l = bcm2835_gpio_lev(D2pin);
  r = r | (l << 2);
  l = bcm2835_gpio_lev(D3pin);
  r = r | (l << 3);
  l = bcm2835_gpio_lev(D4pin);
  r = r | (l << 4);
  l = bcm2835_gpio_lev(D5pin);
  r = r | (l << 5);
  l = bcm2835_gpio_lev(D6pin);
  r = r | (l << 6);
  l = bcm2835_gpio_lev(D7pin);
  r = r | (l << 7);

  result = (int) r;
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(result);
  }
}

// Read used word counter on Max10 FIFO, high part
extern "C" int read_usedwh(){
  bool NoAck;
  unsigned char l;
  unsigned char r;
  int result;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, HIGH);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_WRITE)
    set_bus_read_mode();

  bcm2835_gpio_write(RWpin, HIGH);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }

  r = 0;
  l = bcm2835_gpio_lev(D0pin);
  r = r | l;
  l = bcm2835_gpio_lev(D1pin);
  r = r | (l << 1);
  l = bcm2835_gpio_lev(D2pin);
  r = r | (l << 2);
  l = bcm2835_gpio_lev(D3pin);
  r = r | (l << 3);
  l = bcm2835_gpio_lev(D4pin);
  r = r | (l << 4);
  l = bcm2835_gpio_lev(D5pin);
  r = r | (l << 5);
  l = bcm2835_gpio_lev(D6pin);
  r = r | (l << 6);
  l = bcm2835_gpio_lev(D7pin);
  r = r | (l << 7);

  result = (int) r;
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(result);
  }
}


// Write into the local FIFO
extern "C" int write_local_fifo_old(unsigned char c){
  bool NoAck;
  unsigned char l;
  unsigned char r;
  NoAck = false;
  unsigned char lev;

  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_READ)
    set_bus_write_mode();

  bcm2835_gpio_write(D0pin, ( c    &1));
  bcm2835_gpio_write(D1pin, ((c >> 1)&1));
  bcm2835_gpio_write(D2pin, ((c >> 2)&1));
  bcm2835_gpio_write(D3pin, ((c >> 3)&1));
  bcm2835_gpio_write(D4pin, ((c >> 4)&1));
  bcm2835_gpio_write(D5pin, ((c >> 5)&1));
  bcm2835_gpio_write(D6pin, ((c >> 6)&1));
  bcm2835_gpio_write(D7pin, ((c >> 7)&1));

  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }

  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

// Read from the local FIFO
extern "C" int read_local_fifo_old(){
  bool NoAck;
  unsigned char l;
  unsigned char r;
  int result;
  unsigned char lev;
  NoAck = false;

  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, LOW);

  if(BusMode == MODE_WRITE)
    set_bus_read_mode();

  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }

  r = 0;
  l = bcm2835_gpio_lev(D0pin);
  r = r | l;
  l = bcm2835_gpio_lev(D1pin);
  r = r | (l << 1);
  l = bcm2835_gpio_lev(D2pin);
  r = r | (l << 2);
  l = bcm2835_gpio_lev(D3pin);
  r = r | (l << 3);
  l = bcm2835_gpio_lev(D4pin);
  r = r | (l << 4);
  l = bcm2835_gpio_lev(D5pin);
  r = r | (l << 5);
  l = bcm2835_gpio_lev(D6pin);
  r = r | (l << 6);
  l = bcm2835_gpio_lev(D7pin);
  r = r | (l << 7);

  result = (int) r;
  
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }

  return(result);
}


// Write into the local FIFO
extern "C" int write_local_fifo(unsigned char c){
  bool NoAck = false;

  bcm2835_gpio_set_multi(ADDR_SET_LUT(1));
  bcm2835_gpio_clr_multi(ADDR_CLR_LUT(1));

  if(BusMode == MODE_READ)
    set_bus_write_mode();

  bcm2835_gpio_set_multi(DATA_SET_LUT(c));
  bcm2835_gpio_clr_multi(DATA_CLR_LUT(c));

  bcm2835_gpio_write(STpin, LOW);
  //bcm2835_gpio_write(STpin, LOW);
  if(bcm2835_gpio_lev(ACKpin) == HIGH) {
    NoAck = true;
  }

  bcm2835_gpio_write(STpin, HIGH);
  //bcm2835_gpio_write(STpin, HIGH);
  if(bcm2835_gpio_lev(ACKpin) == LOW) {
    NoAck = true;
  }

  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}


// Read from the local FIFO
extern "C" int read_local_fifo(){
  bool NoAck = false;

  bcm2835_gpio_set_multi(ADDR_SET_LUT(1));
  bcm2835_gpio_clr_multi(ADDR_CLR_LUT(1));

  if(BusMode == MODE_WRITE)
    set_bus_read_mode();

  //bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  if(bcm2835_gpio_lev(ACKpin) == HIGH) {
    NoAck = true;
  }
  
  uint32_t val = bcm2835_peri_read( BCM2835_GPIO_LEV_ADDR );
  unsigned char v =
    (val>>D7pin & 0x1) << 7 |
    (val>>D6pin & 0x1) << 6 |
    (val>>D5pin & 0x1) << 5 |
    (val>>D4pin & 0x1) << 4 |
    (val>>D3pin & 0x1) << 3 |
    (val>>D2pin & 0x1) << 2 |
    (val>>D1pin & 0x1) << 1 |
    (val>>D0pin & 0x1) << 0;


  
  bcm2835_gpio_write(STpin, HIGH);
  //bcm2835_gpio_write(STpin, HIGH);

  /* lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH */
  /* if(lev == LOW) { */
  /*   NoAck = true; */
  /* } */

  return(v);
}


// converts the programming sequence of 48 bytes into 384 single bytes where the LSB is 
// the bit to be programmed
extern "C" void ConvertProgrStrBytetoBit(unsigned char * bytes, unsigned char * bits)
{
  int i, j;
  unsigned char b;
  for (i = 0; i < 48; i = i + 1){
    b = *(bytes + sizeof(unsigned char) * i);
    for(j = 0; j < 8; j = j + 1){
      *(bits + sizeof(unsigned char) * j + sizeof(unsigned char) * i * 8) = 1 & (b >> (7-j));	
    }	
  }
}


// converts the programming sequence of 48*4 bytes into 1536 single bytes where the LSB is 
// the bit to be programmed
extern "C" void ConvertProgrStrBytetoBit_4chips(unsigned char * bytes, unsigned char * bits)
{
  int i, j;
  unsigned char b;
  for (i = 0; i < 192; i = i + 1){
    b = *(bytes + sizeof(unsigned char) * i);
    for(j = 0; j < 8; j = j + 1){
      *(bits + sizeof(unsigned char) * j + sizeof(unsigned char) * i * 8) = 1 & (b >> (7-j));	
    }	
  }
}

extern "C" void ConvertProgrStrBittoByte(unsigned char * bits, unsigned char * bytes)
{
  int i, j;
  unsigned char b;
  for (i = 0; i < 48; i = i + 1){
    b = 0;
    for(j = 0; j < 8; j = j + 1){
      b = b | ( *(bits + sizeof(unsigned char) * i*8 + sizeof(unsigned char) * j) << (7 - j));			
    }
    *(bytes + sizeof(unsigned char) * i) = b;	
  }
}

// Converts a string of bits in a string of bytes (4 chips)
extern "C" void ConvertProgrStrBittoByte_4chips(unsigned char * bits, unsigned char * bytes)
{
	int i, j;
	unsigned char b;
	for (i = 0; i < 192; i = i + 1){
		b = 0;
		for(j = 0; j < 8; j = j + 1){
			b = b | ( *(bits + sizeof(unsigned char) * i*8 + sizeof(unsigned char) * j) << (7 - j));			
		}
		*(bytes + sizeof(unsigned char) * i) = b;	
	}
}

// program the 48 bytes configuration string into the SK2 3 bits at a time
// for all 4 chips on Hexaboard
// and return pointer to previous configuration string, assumes pointing to bit sequence
extern "C" int prog384(unsigned char * pNew, unsigned char * pPrevious)
{
  int chip, bit, j, byte_index, bit_index;
  unsigned char bit2, bit1, bit0, bits, cmd;
  unsigned char dout;
  for(chip = 0; chip < 4; chip=chip+1){
    for(bit = 0; bit < 384; bit = bit + 3){
      bit2 = *(pNew + sizeof(unsigned char) * bit + 0);
      bit1 = *(pNew + sizeof(unsigned char) * bit + 1);
      bit0 = *(pNew + sizeof(unsigned char) * bit + 2);
      bits = (bit2 << 2) | (bit1 << 1) | bit0;
      cmd = CMD_WRPRBITS | bits;
      send_command(cmd);
      dout = read_command();
      bits = dout & 7;
      bit2 = (bits >> 2) & 1;
      bit1 = (bits >> 1) & 1;
      bit0 = bits & 1;
      *(pPrevious + sizeof(unsigned char) * bit + 0) = bit2;
      *(pPrevious + sizeof(unsigned char) * bit + 1) = bit1;
      *(pPrevious + sizeof(unsigned char) * bit + 2) = bit0;
    }
  }
  return(0);
}

// program the 192 bytes configuration string into the SK2 3 bits at a time
// and return pointer to previous configuration string, assumes pointing to bit sequence
extern "C" int prog384_4chips(unsigned char * pNew, unsigned char * pPrevious)
{
  int chip, bit, j, byte_index, bit_index;
  unsigned char bit2, bit1, bit0, bits, cmd;
  unsigned char dout;
  for(bit = 0; bit < 1536; bit = bit + 3){
    bit2 = *(pNew + sizeof(unsigned char) * bit + 0);
    bit1 = *(pNew + sizeof(unsigned char) * bit + 1);
    bit0 = *(pNew + sizeof(unsigned char) * bit + 2);
    bits = (bit2 << 2) | (bit1 << 1) | bit0;
    cmd = CMD_WRPRBITS | bits;
    send_command(cmd);
    dout = read_command();
    bits = dout & 7;
    bit2 = (bits >> 2) & 1;
    bit1 = (bits >> 1) & 1;
    bit0 = bits & 1;
    *(pPrevious + sizeof(unsigned char) * bit + 0) = bit2;
    *(pPrevious + sizeof(unsigned char) * bit + 1) = bit1;
    *(pPrevious + sizeof(unsigned char) * bit + 2) = bit0;
  }
  return(0);
}

/*
extern "C" int progandverify384(unsigned char * pNew, unsigned char * pPrevious)
{
  prog384(pNew, pPrevious);
  prog384(pNew, pPrevious);
  return(0);
}
*/


extern "C" int progandverify48(unsigned char * pConfBytes, unsigned char * pPrevious)
{
  unsigned char *pNewConfBits ;  
  unsigned char *pOldConfBits ;
  pNewConfBits = (unsigned char *) malloc(sizeof(unsigned char) * 384);
  pOldConfBits = (unsigned char *) malloc(sizeof(unsigned char) * 384);
  ConvertProgrStrBytetoBit( pConfBytes, pNewConfBits);
  prog384(pNewConfBits, pOldConfBits);
  prog384(pNewConfBits, pOldConfBits);
  ConvertProgrStrBittoByte(pOldConfBits, pPrevious);
  free(pNewConfBits);
  free(pOldConfBits);
  return(0);
}

extern "C" int progandverify48_4chips(unsigned char * pConfBytes, unsigned char * pPrevious)
{
  unsigned char *pNewConfBits ;  
  unsigned char *pOldConfBits ;
  pNewConfBits = (unsigned char *) malloc(sizeof(unsigned char) * 384 * 4);
  pOldConfBits = (unsigned char *) malloc(sizeof(unsigned char) * 384 * 4);
  ConvertProgrStrBytetoBit_4chips( pConfBytes, pNewConfBits);
  prog384_4chips(pNewConfBits, pOldConfBits);
  prog384_4chips(pNewConfBits, pOldConfBits);
  ConvertProgrStrBittoByte_4chips(pOldConfBits, pPrevious);
  free(pNewConfBits);
  free(pOldConfBits);
  return(0);
}

extern "C" int read_configuration_string(unsigned char * pConfBytes, unsigned char * pPrevious)
{
  unsigned char *pNewConfBits ;  
  unsigned char *pOldConfBits ;
  pNewConfBits = (unsigned char *) malloc(sizeof(unsigned char) * 384 * 4);
  pOldConfBits = (unsigned char *) malloc(sizeof(unsigned char) * 384 * 4);
  ConvertProgrStrBytetoBit_4chips( pConfBytes, pNewConfBits);
  prog384_4chips(pNewConfBits, pOldConfBits);
  ConvertProgrStrBittoByte_4chips(pOldConfBits, pPrevious);
  free(pNewConfBits);
  free(pOldConfBits);
  return(0);
}

extern "C" int calib_gen(){
  bool NoAck;
  unsigned char lev;
  bcm2835_gpio_write(AD0pin, LOW);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, HIGH);
  
  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
  }
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
  bcm2835_gpio_write(RWpin, HIGH);
  
}

extern "C" int instrumental_trigger(){
  bool NoAck;
  unsigned char lev;
  bcm2835_gpio_write(AD0pin, LOW);
  bcm2835_gpio_write(AD1pin, HIGH);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, HIGH);

  bcm2835_gpio_write(RWpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    NoAck = true;
    printf("\n Calibration Pulse Gen, ST = 0, NO ACK -> 0 transition\n");
  }
  bcm2835_gpio_write(STpin, HIGH);
  bcm2835_gpio_write(STpin, HIGH);
  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is HIGH
  if(lev == LOW) {
    NoAck = true;
    printf("\n Calibration Pulse Gen, ST = 1, NO ACK -> 1 transition\n");
  }
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
  bcm2835_gpio_write(RWpin, HIGH);
  
}
