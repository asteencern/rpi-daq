#include <bcm2835.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <math.h>
#include <string.h>
#include <time.h>


#define MODE_READ 0
#define MODE_WRITE 1
#define MODE_SET   1      // redundant
#define MODE_CLR 2
#define MODE_INPUT_READ 3

#define PULL_UP 0
#define PULL_DOWN 1
#define NO_PULL 2

#define GPIO_BEGIN 0
#define GPIO_END 1
#define NO_ACTION 2

static unsigned char BusMode;         // global to remember status of gpio lines (IN or OUT)

#define STpin RPI_V2_GPIO_P1_12
#define RWpin RPI_V2_GPIO_P1_11
#define AD0pin RPI_V2_GPIO_P1_07
#define AD1pin RPI_V2_GPIO_P1_13
#define AD2pin RPI_V2_GPIO_P1_15
#define AD3pin RPI_V2_GPIO_P1_29
#define D0pin RPI_V2_GPIO_P1_37
#define D1pin RPI_V2_GPIO_P1_36
#define D2pin RPI_V2_GPIO_P1_22
#define D3pin RPI_V2_GPIO_P1_18
#define D4pin RPI_V2_GPIO_P1_38
#define D5pin RPI_V2_GPIO_P1_40
#define D6pin RPI_V2_GPIO_P1_33
#define D7pin RPI_V2_GPIO_P1_35
#define ACKpin RPI_V2_GPIO_P1_16


/*****************************************************/
/* define commands for Master FPGA */
/*****************************************************/
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
#define DAC_HIGH_WORD    0x42
#define DAC_LOW_WORD     0x0A
#define TRIGGER_DELAY    0x07// 0x00 to 0x07

// Calibration String enabling Test Pulse on Ch. 30
unsigned char prog_string_sign_inj[48] = {
0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
0x40,0x00,0x00,0x00,0x08,0x00,0x00,0x00,0x1F,0xFF,
0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25};

// Calibration String enabling Test Pulse on Ch. 0
//unsigned char prog_string_sign_inj[48] = {
//0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
//0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x3F,0xFF,
//0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
//0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
//0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25};

//Calibration String enabling Test Pulse on Ch. 62 and Ch.46
//unsigned char prog_string_sign_inj[48] = {
//0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
//0x48,0x00,0x08,0x00,0x00,0x00,0x00,0x00,0x1F,0xFF,
//0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
//0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
//0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25};


// No signal injection TOA 270			 
unsigned char prog_string_no_sign[48] = {0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x1F,0xFF,
0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25};
				   			

//Injection config (channel 31):
//0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
//0x40,0x00,0x00,0x00,0x10,0x00,0x00,0x00,0x1F,0xFF,
//0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
//0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
//0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25			
				   				   
#define RAWSIZE 30787
#define nSCA 15

int set_bus_init();
int set_bus_read_mode();
int set_bus_write_mode();
int send_command(unsigned char);
int read_command(void);
int read_usedwl();
int read_usedwh();
int write_local_fifo(unsigned char );
int read_local_fifo();
unsigned char return_string[48];
unsigned char raw[RAWSIZE];
unsigned int ev[4][1924];
unsigned int dati[4][128][nSCA];

int read_raw(){
	int i, t;
	for (i = 0; i < 30785; i = i+1){
		t =read_local_fifo();
		raw[i] = (unsigned char) (t & 255);
	}
}

int decode_raw(){
    int i, j, k, m;
    unsigned char x;
	unsigned int t;
	unsigned int bith, bit11, bit10, bit9, bit8, bit7, bit6, bit5, bit4, bit3, bit2, bit1, bit0;
	for(i = 0; i < 1924; i = i+1){
		for(k = 0; k < 4; k = k + 1){
			ev[k][i] = 0;
		}
   	}
    for(i = 0; i < 1924; i = i+1){
        for (j=0; j < 16; j = j+1){
            x = raw[1 + i*16 + j];
            x = x & 15;
            for (k = 0; k < 4; k = k + 1){
            	ev[k][i] = ev[k][i] | (unsigned int) (((x >> (3 - k) ) & 1) << (15 - j));
            }
        }
   	}
  
/*****************************************************/
/*    Gray to binary conversion                      */
/*****************************************************/
   	for(k = 0; k < 4 ; k = k +1 ){
   		for(i = 0; i < 128*nSCA; i = i + 1){
   			bith = ev[k][i] & 0x8000;
   			t = ev[k][i] & 0x7fff;
   			bit11 = (t >> 11) & 1;
        	bit10 = bit11 ^ ((t >>10) &1);
        	bit9 = bit10 ^ ((t >>9) &1);
        	bit8 = bit9 ^ ((t >>8) &1);
        	bit7 = bit8 ^ ((t >>7) &1);
        	bit6 = bit7 ^ ((t >>6) &1);
        	bit5 = bit6 ^ ((t >>5) &1);
        	bit4 = bit5 ^ ((t >>4) &1);
        	bit3 = bit4 ^ ((t >>3) &1);
        	bit2 = bit3 ^ ((t >>2) &1);
        	bit1 = bit2 ^ ((t >>1) &1);
        	bit0 = bit1 ^ ((t >>0) &1);
        	ev[k][i] =  bith | ((bit11 << 11) + (bit10 << 10) + (bit9 << 9) + (bit8 << 8) + (bit7 << 7) + (bit6 << 6) + (bit5 << 5) + (bit4 << 4) + (bit3  << 3) + (bit2 << 2) + (bit1  << 1) + bit0);
        }
    }
}

int format_channels(){
    int chip, hit, ch;
    for(chip =0; chip < 4; chip = chip +1 ){
        for(ch = 0; ch < 128; ch = ch +1 ){
            for(hit = 0 ; hit <nSCA ; hit = hit +1){
                dati[chip][ch][hit] = ev[chip][hit*128+ch] & 0x0FFF;
            }
        }
    }
    return(0);
}
    
int main()
{
int res;
int ch, sample, chip;
int i, k, n;
int maxevents = 10;
int dac_ctrl = 0;
int dac_fs = 1920;
struct tm *info;
char buffer[80];
char fname [160];
char dirname[] = "./Data/";	
char pulse_inj[128], pulse_sweep[128], acquisition_type[128];
char instr [1024];
long delay1, delay2, delay3, delay4, delay5, delay6; 
FILE *flog;
FILE *fraw;
FILE *fout;
FILE *finject; 

time_t rawtime;
bool saveraw;

//added by RSLU 23.11.2017
char moduleNumber[10];
 
delay1 = 100;
delay2 = 0;
delay3 = 3000;
delay4 = 100;
delay5 = 0;

/***********************************************************************/
printf("Module Number ? ");
scanf ("%s",moduleNumber);

printf("How many events ? ");
scanf ("%d",&maxevents);
printf("\nSave raw data ? [Y/N] ");
scanf ("%s",instr);
saveraw = false;
if(instr[0] == 'y' | instr[0] == 'Y')
	saveraw = true;

printf("\nExternal Pulse Injection? [Y/N] ");
scanf("%s", pulse_inj);
if(pulse_inj[0] != 'Y' & pulse_inj[0] != 'y' & pulse_inj[0] != 'N' & pulse_inj[0] != 'n'){
	printf("\nInvalid Selection.");	
	exit(0);
}

if(pulse_inj[0] == 'N' | pulse_inj[0] == 'n'){
	printf("\nUse fixed Acquisition Window? [Y/N] ");
	scanf("%s", acquisition_type);
	if(acquisition_type[0] != 'Y' & acquisition_type[0] != 'N' & acquisition_type[0] != 'y' & acquisition_type[0] != 'n'){
		printf("\nInvalid Selection.");	
		exit(0);
	}
}
	
if(pulse_inj[0] == 'Y' | pulse_inj[0] == 'y'){
	acquisition_type[0] = 'n';
	printf("\nSweep Pulse Amplitude? [Y/N] ");
	scanf("%s", pulse_sweep);
	if(pulse_sweep[0] != 'Y' & pulse_sweep[0] != 'N' & pulse_sweep[0] != 'y' & pulse_sweep[0] != 'n'){
		printf("\nInvalid Selection.");	
		exit(0);
	}
}	
else{
	pulse_sweep[0] = 'n';}
/***********************************************************************/

/* Make up a file name for data */
	time(&rawtime);
	info = localtime(&rawtime);
	strftime(buffer,80,"RUN_%d%m%y_%H%M", info);
	//modified by RSLU 23.11.2017
	strcpy(fname, dirname);
	strcat(fname, "Module_");
	strcat(fname, moduleNumber);
	strcat(fname, "_");
	strcat(fname, buffer);
	strcat(fname,".txt");
	printf("Filename will be %s\n",fname);

	//strcpy(fname, dirname);
	//strcat(fname, buffer);
	//strcat(fname,".txt");
	//printf("Filename will be %s\n",fname);

	fout = fopen(fname, "w");
	fprintf(fout,"Total number of events: %d, External Pulse: %s, Fixed Length Acquisition: %s, delays: %li %li %li %li %li ",maxevents, pulse_inj, acquisition_type, delay1, delay2, delay3, delay4, delay5);
	fprintf(fout,"\n%s\n####################################################\n",buffer);
	
    /*	optional save raw data */
	//modified by RSLU 23.11.2017
	strcpy(fname, dirname);
	strcat(fname, "Module_");
	strcat(fname, moduleNumber);
	strcat(fname, "_");
	strcat(fname, buffer);
	strcat(fname,".raw.txt");
	printf("Filename will be %s\n",fname);

	//strcpy(fname, dirname);
	//strcat(fname, buffer);
	//strcat(fname,".raw.txt");
	//printf("Raw filename will be %s\n",fname);

	if(saveraw){
	  flog = fopen("runinfo.log","w");
	  fprintf(flog,fname);
	  fclose (flog);
	  fraw = fopen(fname, "w");
	  //Open a pulse txt if inject mode is selected
	  if(pulse_inj[0] == 'Y' | pulse_inj[0] == 'y'){
	    strcpy(fname, dirname);
	    strcat(fname, "Module_");
	    strcat(fname, moduleNumber);
	    strcat(fname, "_");
	    strcat(fname, buffer);
	    strcat(fname,"_Inj.txt");
	    finject = fopen(fname,"w");
	    printf("Injection information will be stored: %s\n",fname);	    
	  }}

/*  Initialize RPI */
	if (!bcm2835_init())
        return 1;
    set_bus_init();
    // Set the pin to be an output
    bcm2835_gpio_fsel(RWpin, BCM2835_GPIO_FSEL_OUTP);

/* empty local fifo by forcing extra reads, ignore results */
    i = 0;
    for(i=0; i < 33000; i = i+1){
    	res = read_local_fifo();	
    }
   	res = set_trigger_delay(TRIGGER_DELAY);
   	
/*****************************************************/
/*             set configuration                     */
/*****************************************************/

    res = send_command(CMD_RSTBPULSE);
    res = send_command(CMD_SETSELECT | 1);
    printf("\n\n####################################################\n");
    printf("Save Raw Data: %s\nExternal Pulse Injection: %s\nFixed Acquisition Window: %s\nAmplitude Sweep of Injected Signal: %s\n", instr, pulse_inj, acquisition_type,pulse_sweep);
    printf("####################################################\n");
    if(pulse_inj[0] == 'N' | pulse_inj[0] == 'n'){
    fprintf(fout,"Configuration used for SK2\n");
		for(i = 0; i < 48; i = i + 1){
			fprintf(fout,"%x ",prog_string_no_sign[i]);
		}
    fprintf(fout,"\nConfiguration read from SK2\n");	
    progandverify48(prog_string_no_sign, return_string); 
		for(i = 0; i < 48; i = i + 1){
			fprintf(fout,"%x ",return_string[i]);
		}
    fprintf(fout,"\n");}
    else{
	fprintf(fout,"Configuration used for SK2\n");
	fprintf(finject,"Configuration used for SK2\n");
		for(i = 0; i < 48; i = i + 1){
			fprintf(fout,"%x ",prog_string_sign_inj[i]);
			fprintf(finject,"%x ",prog_string_sign_inj[i]);
		}
        fprintf(fout,"\nConfiguration read from SK2\n");
	fprintf(finject,"\nConfiguration read from SK2\n");
	progandverify48(prog_string_sign_inj, return_string); 
		for(i = 0; i < 48; i = i + 1){
			fprintf(fout,"%x ",return_string[i]);
			fprintf(finject,"%x ",return_string[i]);
		}
    fprintf(fout,"\n");
    fprintf(finject,"\n");
    fprintf(finject,"evt\tdac_ctrl( -1 means fixed )\n");    
    }
      
    res = send_command(CMD_SETSELECT);	
    usleep(10000);
    printf("\nFinished Configuration\n");
	
/*****************************************************/
/*                  do the work                     */
/*****************************************************/
    printf("\nStart events acquisition\n");
    n = 0;
    
    for(i = 0; i < maxevents; i = i +1){
		if(pulse_sweep[0] == 'Y' | pulse_sweep[0] == 'y'){ 
		          dac_ctrl = dac_ctrl + dac_fs/maxevents;
			  res = set_dac_high_word((dac_ctrl & 0xFF0)>>4);
			  res = set_dac_low_word(dac_ctrl & 0x00F);

			  //record injection information here
			  fprintf(finject,"%d\t",i);
			  fprintf(finject,"%d\n",dac_ctrl);
		}
		else{
   		          res = set_dac_high_word(DAC_HIGH_WORD);
			  res = set_dac_low_word(DAC_LOW_WORD);

			  //record injection information here
			  fprintf(finject,"%d\t",i);
			  fprintf(finject,"%d\n",-1);
		    }

	res = send_command(CMD_RESETPULSE);
	usleep(delay1);
    	if(acquisition_type[0] == 'Y' | acquisition_type[0] == 'y')
			res = fixed_acquisition();
		else {	
			res = send_command(CMD_SETSTARTACQ | 1);
			usleep(delay2);
			if(pulse_inj[0] == 'N' | pulse_inj[0] == 'n') 
				res = send_command(CMD_SETSTARTACQ);  /* <<<+++   THIS IS THE TRIGGER */
			else	
			calib_gen();
		}
		res = send_command(CMD_STARTCONPUL);
    	usleep(delay3);
    	res = send_command(CMD_STARTROPUL);
    	usleep(delay4);
    	res = read_raw();
    	if(saveraw)
    		fwrite(raw, 1, sizeof(raw), fraw);

	/*****************************************************/
	/*         convert raw to readable data             */
	/*****************************************************/
		res = decode_raw();
	/*****************************************************/
	/* do some verification that data look OK on one chip*/
	/*****************************************************/
		chip= 1;
		for(k = 0; k < 1664; k = k + 1){
			if((ev[chip][k] & 0x8000 ) == 0){
				printf("Wrong MSB at %d %x \n",k,ev[chip][k]);
			}
			if((ev[chip][k] & 0x7E00 ) != 0x0000 & (pulse_inj[0] == 'N' | pulse_inj[0] == 'n') ){
				printf("Noisy Channel at %d %d %x\n", i, k,ev[chip][k] );
			}
			}
		if(ev[chip][1923] != 0xc099){
			printf("Wrong Trailer is %x \n",ev[chip][1923]);
		}

	/*****************************************************/
	/*           final convert to readable stuff         */
	/*****************************************************/
		res = format_channels();
		if(i % 10 == 0){
			printf("\r%d", i);
			fflush(stdout);
		}
			
	/*****************************************************/
	/*             write event to data file              */
	/*****************************************************/
		for(chip = 0; chip < 4; chip = chip + 1){
			fprintf(fout, "Event %d Chip %d RollMask %x \n",i, chip, ev[chip][1920]);
			for(ch =0; ch < 128; ch = ch +1){
				for (sample=0; sample < nSCA; sample = sample +1){
					fprintf(fout, "%d  ", dati[chip][ch][sample]);
				}
				fprintf(fout, "\n");
			}	
		}
		usleep(delay5);
		}
		fclose(fout);
		if(saveraw)
			fclose(fraw);
		if(pulse_inj[0] == 'Y' | pulse_inj[0] == 'y')
		        fclose(finject);
		return(0);     
	}
