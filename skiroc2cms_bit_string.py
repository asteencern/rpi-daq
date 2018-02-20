import bitarray as ba
import ctypes

# Documentation on the bit string format can be found at
# https://cms-docdb.cern.ch/cgi-bin/DocDB/ShowDocument?docid=13121

class bit_string:
    list_base=[ 0xDA,0xA0,0xF9,0x32,0xE0,0xC1,0x2E,0x10,0x98,0xB0,
                0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x1F,0xFF,
                0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
                0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
                0xFF,0xFF,0xE9,0xD7,0xAE,0xBA,0x80,0x25 ]
    bits=ba.bitarray(384)
    def __init__(self):
        self.bits.setall(0)
        for i in range(48):
            for j in range(8):
                self.bits[j+i*8]=((self.list_base[i]>>(7-j))&1)

    def enable_channel_for_injection(self,channel):
        if channel<0 or channel>=64:
            print "\n\n!!!!!!!!!!!!!!!!Impossible to select channel ",channel," for charge injection -> must choose 0 <= channel id < 64!!!!!!!!!!!!!!!!\n\n"
        else:
            print("Enable charge injection in channel ",channel)
            channelIndex=channel+237
            self.bits[383-channelIndex]=1

    def set_channels_for_charge_injection(self,channels):
        for c in channels:
            self.enable_channel_for_injection(c)

    def mask_channel(self,channel):
        if channel<0 or channel>=64:
            print "\n\n!!!!!!!!!!!!!!!!Impossible to mask channel ",channel," -> must choose 0 <= channel id < 64!!!!!!!!!!!!!!!!\n\n"
        else:
            print("Disable PreAmp in channel : ",channel)
            channelIndex=channel+173
            self.bits[383-channelIndex]=0
        
    def set_channels_to_mask(self,channels):
        for c in channels:
            self.mask_channel(c)
            
    def disable_trigger_tot(self,channel):
        if channel<0 or channel>=64:
            print "\n\n!!!!!!!!!!!!!!!!Impossible to disable trigger tot in channel ",channel," -> must choose 0 <= channel id < 64!!!!!!!!!!!!!!!!\n\n"
        else:
            print("Disable Trigger TOT in channel : ",channel)
            channelIndex=channel+109
            self.bits[383-channelIndex]=0
        
    def set_channels_to_disable_trigger_tot(self,channels):
        for c in channels:
            self.disable_trigger_tot(c)
            
    def disable_trigger_toa(self,channel):
        if channel<0 or channel>=64:
            print "\n\n!!!!!!!!!!!!!!!!Impossible to disable trigger toa in channel ",channel," -> must choose 0 <= channel id < 64!!!!!!!!!!!!!!!!\n\n"
        else:
            print("Disable Trigger TOA in channel : ",channel)
            channelIndex=channel+45
            self.bits[383-channelIndex]=0
        
    def set_channels_to_disable_trigger_toa(self,channels):
        for c in channels:
            self.disable_trigger_toa(c)

    def get_384_unsigned_char_p(self):
        c_uchar_p = (ctypes.c_ubyte*384)()
        for i in range(0,384):
            c_uchar_p[i]=self.bits[i]
        return c_uchar_p
            
    def get_48_unsigned_char_p(self):
        c_uchar_p = (ctypes.c_ubyte*48)()
        for i in range(0,48):
            c_uchar_p[i]=0
            for j in range(0,8):
                c_uchar_p[i]=c_uchar_p[i]|(self.bits[i*8+j]<<(7-j))
        return c_uchar_p
            
    def set_preamp_feedback_capacitance(self,capa):
        capa=capa&0x3f
        for i in range(0,6):
            bit=(capa>>i)&1
            self.bits[381-6+i]=bit

    def set_tot_dac_threshold(self,thr):
        thr=thr&0x3ff
        for i in range(0,10):
            bit=(thr>>i)&1
            self.bits[61+i]=bit
            
    def Print(self):
        print(self.bits)
