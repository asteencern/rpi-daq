#include <bcm2835.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>

static bool BusMode;         // global to remember status of gpio lines (IN or OUT)
#define MODE_READ  HIGH
#define MODE_WRITE LOW


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

#define  STpin RPI_V2_GPIO_P1_12
#define ACKpin RPI_V2_GPIO_P1_16
#define  RWpin RPI_V2_GPIO_P1_11


/* define command packets sent to Hexaboard */
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

/* Bus addresses to the master */
#define ADDR_COMMAND        0x0
#define ADDR_FIFO           0x1
#define ADDR_FIFO_USED_LOW  0x2
#define ADDR_FIFO_USED_HIGH 0x3
#define ADDR_FIFO_FULLADDR_FIFO_FULL      0x4
#define ADDR_TRIG_DELAY     0x5
#define ADDR_DAC_HIGH       0x6
#define ADDR_DAC_LOW        0x7
#define ADDR_CALIB_PULSE    0x8
#define ADDR_FIXED_ACQ      0x9
#define ADDR_INSTR_TRIGGER  0xa

#include "data_addr_utils.h"

////////////////////////////// LOW LEVEL ROUTINES //////////////////////////////

inline int check_ack(){
  if(bcm2835_gpio_lev(ACKpin) == HIGH) {
    return(0);
  }
  else {
    return(-1);
  }
}

extern "C" int8_t set_bus_init()
{
  if(!bcm2835_init()){
    printf("problem in gpiolib.c method set_bus_init(): bcm2835_init() failed -> exit code");
    exit(1);
  }
  
  uint32_t *GPIO_BASE = bcm2835_regbase(BCM2835_REGBASE_GPIO);
  GPIO_FSEL1_ADDR = GPIO_BASE + BCM2835_GPFSEL1/4;
  GPIO_FSEL2_ADDR = GPIO_BASE + BCM2835_GPFSEL2/4;
  GPIO_LEV_ADDR   = GPIO_BASE + BCM2835_GPLEV0/4;
  
  // Set direction of handshake pins
  bcm2835_gpio_fsel(STpin,  BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(RWpin,  BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(ACKpin, BCM2835_GPIO_FSEL_INPT);

  // Set direction of address bus pins
  bcm2835_gpio_fsel(AD0pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(AD1pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(AD2pin, BCM2835_GPIO_FSEL_OUTP);
  bcm2835_gpio_fsel(AD3pin, BCM2835_GPIO_FSEL_OUTP);
  
  // Set direction of data bus pins
  bcm2835_peri_set_bits(GPIO_FSEL1_ADDR, DATA_FSEL1_INPT, DATA_FSEL1_MASK);
  bcm2835_peri_set_bits(GPIO_FSEL2_ADDR, DATA_FSEL2_INPT, DATA_FSEL2_MASK);
  
  // Initialize address bus value
  write_address(ADDR_COMMAND);
  CurAddr = ADDR_COMMAND;

  // Set RW to READ
  bcm2835_gpio_write(RWpin, MODE_READ);
  BusMode = MODE_READ;

  // Set STrobe to high (values are latched on HIGH->LOW)
  bcm2835_gpio_write(STpin, HIGH);

  return check_ack();
}

inline void set_bus_mode(uint8_t mode)
{
  if(BusMode == mode) return;
  
  bcm2835_gpio_write(RWpin, mode);
  if(mode == MODE_WRITE){
    bcm2835_peri_set_bits(GPIO_FSEL1_ADDR, DATA_FSEL1_OUTP, DATA_FSEL1_MASK);
    bcm2835_peri_set_bits(GPIO_FSEL2_ADDR, DATA_FSEL2_OUTP, DATA_FSEL2_MASK);
  }else{
    bcm2835_peri_set_bits(GPIO_FSEL1_ADDR, DATA_FSEL1_INPT, DATA_FSEL1_MASK);
    bcm2835_peri_set_bits(GPIO_FSEL2_ADDR, DATA_FSEL2_INPT, DATA_FSEL2_MASK);
  }
  BusMode = mode;

  return;
}


#define ST_LOW_ACK_CHECK_NC() \
  bcm2835_gpio_write(STpin, LOW); \
  while(bcm2835_gpio_lev(ACKpin) == HIGH) { \
  }

#define ST_LOW_ACK_CHECK() \
  bcm2835_gpio_write(STpin, LOW); \
  while(bcm2835_gpio_lev(ACKpin) == HIGH) { \
    NoAck = true; \
  }

#define ST_HIGH_ACK_CHECK() \
  bcm2835_gpio_write(STpin, HIGH)


extern "C" int8_t send_command(uint8_t c)
{
  bool NoAck = false;
  
  write_address(ADDR_COMMAND);
  set_bus_mode(MODE_WRITE);
  write_data(c);
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();
  
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" uint8_t read_command(void)
{
  bool NoAck = false;

  write_address(ADDR_COMMAND);
  set_bus_mode(MODE_READ);
  ST_LOW_ACK_CHECK();
  uint32_t val = bcm2835_peri_read(GPIO_LEV_ADDR);
  uint8_t v = DEMANGLE_DATA(val); 
  ST_HIGH_ACK_CHECK();
  
  if(NoAck){
    return(-1);
  }
  else {
    return(v);
  }
}

extern "C" int fixed_acquisition(void)
{
  bool NoAck = false;
  uint8_t c = CMD_SETSTARTACQ | 1;

  write_address(ADDR_FIXED_ACQ);
  set_bus_mode(MODE_WRITE);
  write_data(c);
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();
  
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int set_dac_high_word(uint8_t c)
{
  bool NoAck = false;

  write_address(ADDR_DAC_HIGH);
  set_bus_mode(MODE_WRITE);
  write_data(c);
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();

  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int set_dac_low_word(uint8_t c)
{
  bool NoAck = false;

  write_address(ADDR_DAC_LOW);
  set_bus_mode(MODE_WRITE);
  write_data(c);
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();

  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int set_dac_word(uint16_t c){
  // Format of input c in terms of output
  // [----|hhhh|hhhh|llll]
  return
    set_dac_high_word( (c>>4) & 0x0ff ) +
    set_dac_low_word (    c   & 0x00f );
}

extern "C" int set_trigger_delay(uint8_t c)
{
  bool NoAck = false;

  write_address(ADDR_TRIG_DELAY);
  set_bus_mode(MODE_WRITE);
  write_data(c);
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();

  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

// Read used word counter on Max10 FIFO, low part
extern "C" uint8_t read_usedwl(){
  bool NoAck = false;

  write_address(ADDR_FIFO_USED_LOW);
  set_bus_mode(MODE_READ);
  ST_LOW_ACK_CHECK();
  uint32_t val = bcm2835_peri_read(GPIO_LEV_ADDR);
  uint8_t v = DEMANGLE_DATA(val); 
  ST_HIGH_ACK_CHECK();
  
  if(NoAck){
    return(-1);
  }
  else {
    return(v);
  }
}

// Read used word counter on Max10 FIFO, high part
extern "C" uint8_t read_usedwh(){
  bool NoAck = false;

  write_address(ADDR_FIFO_USED_HIGH);
  set_bus_mode(MODE_READ);
  ST_LOW_ACK_CHECK();
  uint32_t val = bcm2835_peri_read(GPIO_LEV_ADDR);
  uint8_t v = DEMANGLE_DATA(val); 
  ST_LOW_ACK_CHECK();
  
  if(NoAck){
    return(-1);
  }
  else {
    return(v);
  }
}

extern "C" uint16_t read_usedw(){
  return (read_usedwh() << 8) | read_usedwl();
}

// Read if there are any words on the FIFO (0xff=empty, 0xfc=used)
extern "C" uint8_t read_fifo_status(){
  bool NoAck = false;

  write_address(ADDR_FIFO_FULLADDR_FIFO_FULL);
  set_bus_mode(MODE_READ);
  ST_LOW_ACK_CHECK();
  uint32_t val = bcm2835_peri_read(GPIO_LEV_ADDR);
  uint8_t v = DEMANGLE_DATA(val); 
  ST_HIGH_ACK_CHECK();
  
  if(NoAck){
    return(-1);
  }
  else {
    return(v);
  }
}

// Write into the local FIFO
extern "C" int write_local_fifo(uint8_t c){
  bool NoAck = false;

  write_address(ADDR_FIFO);
  set_bus_mode(MODE_WRITE);
  write_data(c);
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();

  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}


// Read from the local FIFO
extern "C" uint_fast8_t read_local_fifo(){

  write_address(ADDR_FIFO);
  set_bus_mode(MODE_READ);
  ST_LOW_ACK_CHECK_NC();
  uint32_t val = bcm2835_peri_read(GPIO_LEV_ADDR);
  uint8_t v = DEMANGLE_DATA(val); 
  ST_HIGH_ACK_CHECK();

  return(v);
}

// Write into the HB FIFO; only 3 bits can fit
extern "C" int test_remote_fifo(uint8_t c){
  uint8_t val = CMD_LOOPBRFIFO | (c & 0x07);
  send_command( val );
  uint8_t ret = read_command();
  if(val != ret){
    printf("Mismatching readback in %s: 0x%02x sent, 0x%02x received\n", __FUNCTION__, val, ret);
  }
  return ret & 0x7;
}

// Write into the HB loopback register; only 3 bits can fit
extern "C" int test_remote_loopback(uint8_t c){
  uint8_t val = CMD_LOOPBACK | (c & 0x07);
  send_command( val );
  uint8_t ret = read_command();
  if(val != ret){
    printf("Mismatching readback in %s: 0x%02x sent, 0x%02x received\n", __FUNCTION__, val, ret);
  }
  return ret & 0x7;
}


extern "C" int calib_gen(){
  bool NoAck = false;
  
  write_address(ADDR_CALIB_PULSE);
  set_bus_mode(MODE_WRITE);
  // No data to write
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();

  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

extern "C" int instrumental_trigger(){
  bool NoAck = false;

  write_address(ADDR_INSTR_TRIGGER);
  set_bus_mode(MODE_WRITE);
  // No data to write
  ST_LOW_ACK_CHECK();
  ST_HIGH_ACK_CHECK();
  
  if(NoAck){
    return(-1);
  }
  else {
    return(0);
  }
}

// converts the programming sequence of 48 bytes into 384 single bytes where the LSB is 
// the bit to be programmed
extern "C" void ConvertProgrStrBytetoBit(uint8_t * bytes, uint8_t * bits)
{
  uint8_t i, j;
  uint8_t b;
  for (i = 0; i < 48; i = i + 1){
    b = *(bytes + sizeof(uint8_t) * i);
    for(j = 0; j < 8; j = j + 1){
      *(bits + sizeof(uint8_t) * j + sizeof(uint8_t) * i * 8) = 1 & (b >> (7-j));	
    }	
  }
}


// converts the programming sequence of 48*4 bytes into 1536 single bytes where the LSB is 
// the bit to be programmed
extern "C" void ConvertProgrStrBytetoBit_4chips(uint8_t * bytes, uint8_t * bits)
{
  uint8_t i, j;
  uint8_t b;
  for (i = 0; i < 192; i = i + 1){
    b = *(bytes + sizeof(uint8_t) * i);
    for(j = 0; j < 8; j = j + 1){
      *(bits + sizeof(uint8_t) * j + sizeof(uint8_t) * i * 8) = 1 & (b >> (7-j));	
    }	
  }
}

extern "C" void ConvertProgrStrBittoByte(uint8_t * bits, uint8_t * bytes)
{
  uint8_t i, j;
  uint8_t b;
  for (i = 0; i < 48; i = i + 1){
    b = 0;
    for(j = 0; j < 8; j = j + 1){
      b = b | ( *(bits + sizeof(uint8_t) * i*8 + sizeof(uint8_t) * j) << (7 - j));			
    }
    *(bytes + sizeof(uint8_t) * i) = b;	
  }
}

// Converts a string of bits in a string of bytes (4 chips)
extern "C" void ConvertProgrStrBittoByte_4chips(uint8_t * bits, uint8_t * bytes)
{
  uint8_t i, j;
  uint8_t b;
  for (i = 0; i < 192; i = i + 1){
    b = 0;
    for(j = 0; j < 8; j = j + 1){
      b = b | ( *(bits + sizeof(uint8_t) * i*8 + sizeof(uint8_t) * j) << (7 - j));			
    }
    *(bytes + sizeof(uint8_t) * i) = b;	
  }
}

// program the 48 bytes configuration string into the SK2 3 bits at a time
// for all 4 chips on Hexaboard
// and return pointer to previous configuration string, assumes pointing to bit sequence
extern "C" int prog384(uint8_t * pNew, uint8_t * pPrevious)
{
  uint8_t chip;
  uint16_t bit;
  uint8_t bit2, bit1, bit0, bits, cmd;
  uint8_t dout;
  for(chip = 0; chip < 4; chip=chip+1){
    for(bit = 0; bit < 384; bit = bit + 3){
      bit2 = *(pNew + sizeof(uint8_t) * bit + 0);
      bit1 = *(pNew + sizeof(uint8_t) * bit + 1);
      bit0 = *(pNew + sizeof(uint8_t) * bit + 2);
      bits = (bit2 << 2) | (bit1 << 1) | bit0;
      cmd = CMD_WRPRBITS | bits;
      send_command(cmd);
      dout = read_command();
      bits = dout & 7;
      bit2 = (bits >> 2) & 1;
      bit1 = (bits >> 1) & 1;
      bit0 = bits & 1;
      *(pPrevious + sizeof(uint8_t) * bit + 0) = bit2;
      *(pPrevious + sizeof(uint8_t) * bit + 1) = bit1;
      *(pPrevious + sizeof(uint8_t) * bit + 2) = bit0;
    }
  }
  return(0);
}

// program the 192 bytes configuration string into the SK2 3 bits at a time
// and return pointer to previous configuration string, assumes pointing to bit sequence
extern "C" int prog384_4chips(uint8_t * pNew, uint8_t * pPrevious)
{
  uint16_t bit;
  uint8_t bit2, bit1, bit0, bits, cmd;
  uint8_t dout;
  for(bit = 0; bit < 1536; bit = bit + 3){
    bit2 = *(pNew + sizeof(uint8_t) * bit + 0);
    bit1 = *(pNew + sizeof(uint8_t) * bit + 1);
    bit0 = *(pNew + sizeof(uint8_t) * bit + 2);
    bits = (bit2 << 2) | (bit1 << 1) | bit0;
    cmd = CMD_WRPRBITS | bits;
    send_command(cmd);
    dout = read_command();
    bits = dout & 7;
    bit2 = (bits >> 2) & 1;
    bit1 = (bits >> 1) & 1;
    bit0 = bits & 1;
    *(pPrevious + sizeof(uint8_t) * bit + 0) = bit2;
    *(pPrevious + sizeof(uint8_t) * bit + 1) = bit1;
    *(pPrevious + sizeof(uint8_t) * bit + 2) = bit0;
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


extern "C" int progandverify48(uint8_t * pConfBytes, uint8_t * pPrevious)
{
  uint8_t *pNewConfBits ;  
  uint8_t *pOldConfBits ;
  pNewConfBits = (uint8_t *) malloc(sizeof(uint8_t) * 384);
  pOldConfBits = (uint8_t *) malloc(sizeof(uint8_t) * 384);
  ConvertProgrStrBytetoBit( pConfBytes, pNewConfBits);
  prog384(pNewConfBits, pOldConfBits);
  prog384(pNewConfBits, pOldConfBits);
  ConvertProgrStrBittoByte(pOldConfBits, pPrevious);
  free(pNewConfBits);
  free(pOldConfBits);
  return(0);
}

extern "C" int progandverify48_4chips(uint8_t * pConfBytes, uint8_t * pPrevious)
{
  uint8_t *pNewConfBits ;  
  uint8_t *pOldConfBits ;
  pNewConfBits = (uint8_t *) malloc(sizeof(uint8_t) * 384 * 4);
  pOldConfBits = (uint8_t *) malloc(sizeof(uint8_t) * 384 * 4);
  ConvertProgrStrBytetoBit_4chips( pConfBytes, pNewConfBits);
  prog384_4chips(pNewConfBits, pOldConfBits);
  prog384_4chips(pNewConfBits, pOldConfBits);
  ConvertProgrStrBittoByte_4chips(pOldConfBits, pPrevious);
  free(pNewConfBits);
  free(pOldConfBits);
  return(0);
}

extern "C" int read_configuration_string(uint8_t * pConfBytes, uint8_t * pPrevious)
{
  uint8_t *pNewConfBits ;  
  uint8_t *pOldConfBits ;
  pNewConfBits = (uint8_t *) malloc(sizeof(uint8_t) * 384 * 4);
  pOldConfBits = (uint8_t *) malloc(sizeof(uint8_t) * 384 * 4);
  ConvertProgrStrBytetoBit_4chips( pConfBytes, pNewConfBits);
  prog384_4chips(pNewConfBits, pOldConfBits);
  ConvertProgrStrBittoByte_4chips(pOldConfBits, pPrevious);
  free(pNewConfBits);
  free(pOldConfBits);
  return(0);
}


/***************************************
ALL THE LEGACY CODE BELOW CAN BE DELETED
****************************************/
inline void set_bus_read_mode()
{
  bcm2835_gpio_write(RWpin, MODE_READ);
  bcm2835_peri_set_bits(GPIO_FSEL1_ADDR, DATA_FSEL1_INPT, DATA_FSEL1_MASK);
  bcm2835_peri_set_bits(GPIO_FSEL2_ADDR, DATA_FSEL2_INPT, DATA_FSEL2_MASK);
  BusMode = MODE_READ;
  
  return;
}

inline void set_bus_write_mode()
{
  bcm2835_gpio_write(RWpin, MODE_WRITE);
  bcm2835_peri_set_bits(GPIO_FSEL1_ADDR, DATA_FSEL1_OUTP, DATA_FSEL1_MASK);
  bcm2835_peri_set_bits(GPIO_FSEL2_ADDR, DATA_FSEL2_OUTP, DATA_FSEL2_MASK);
  BusMode = MODE_WRITE;

  return;
}

// Write into the local FIFO
extern "C" int write_local_fifo_old(uint8_t c){
  bool NoAck;
  //unsigned char l;
  //unsigned char r;
  NoAck = false;
  unsigned char lev;

  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, LOW);
  CurAddr = 0x1;

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
  //bool NoAck = false;
  unsigned char l;
  unsigned char r;
  int result;
  unsigned char lev;
 
  bcm2835_gpio_write(AD0pin, HIGH);
  bcm2835_gpio_write(AD1pin, LOW);
  bcm2835_gpio_write(AD2pin, LOW);
  bcm2835_gpio_write(AD3pin, LOW);
  CurAddr = 1;

  if(BusMode == MODE_WRITE)
    set_bus_read_mode();

  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);
  bcm2835_gpio_write(STpin, LOW);

  lev = bcm2835_gpio_lev(	ACKpin	);	                // check that ACK is LOW
  if(lev == HIGH) {
    //NoAck = true;
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
    //NoAck = true;
  }

  return(result);
}
