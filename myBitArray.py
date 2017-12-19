import bitarray as ba
import ctypes

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
        print("Enable charge injection in channel ",channel)
        channelIndex=channel+237
        self.bits[383-channelIndex]=1

    def set_channels_for_charge_injection(self,channels):
        for c in channels:
            self.enable_channel_for_injection(c)

    def mask_channel(self,channel):
        print("Disable PreAmp in channel : ",channel)
        channelIndex=channel+173
        self.bits[383-channelIndex]=0
        
    def set_channels_to_mask(self,channels):
        for c in channels:
            self.mask_channel(c)
            
    def disable_trigger_tot(self,channel):
        print("Disable Trigger TOT in channel : ",channel)
        channelIndex=channel+109
        self.bits[383-channelIndex]=0
        
    def set_channels_to_disable_trigger_tot(self,channels):
        for c in channels:
            self.disable_trigger_tot(c)
            
    def disable_trigger_toa(self,channel):
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
            temp=ba.bitarray()
            for j in range(0,8):
                #temp.append(self.bits[i*8+j])
                c_uchar_p[i]=c_uchar_p[i]|(self.bits[i*8+j]<<(7-j))
            #print( i,hex(c_uchar_p[i]),bin(c_uchar_p[i])[2:],temp )
        return c_uchar_p
            
    def Print(self):
        print(self.bits)


the_bit_string=bit_string()

the_bit_string.Print()

# the_bits_c_uchar_p=the_bit_string.get_384_unsigned_char_p()
# print( [hex(the_bits_c_uchar_p[i]) for i in range(384)] )
the_bits_c_uchar_p=the_bit_string.get_48_unsigned_char_p()
print( [hex(the_bits_c_uchar_p[i]) for i in range(48)] )
#print([the_bit_string.bits.tobytes()[i] for i in range(0,48)])


channelToInject=[0,10,20,30,40,50,60]
the_bit_string.set_channels_for_charge_injection(channelToInject)
the_bit_string.Print()
channelToMask=[1,11,21,31,41,51,61]
the_bit_string.set_channels_to_mask(channelToMask)
the_bit_string.Print()
channelTOTDisable=[2,12,22,32,42,52,62]
the_bit_string.set_channels_to_disable_trigger_tot(channelTOTDisable)
the_bit_string.Print()
channelTOADisable=[3,13,23,33,43,53,63]
the_bit_string.set_channels_to_disable_trigger_toa(channelTOADisable)
the_bit_string.Print()

the_bits_c_uchar_p=the_bit_string.get_48_unsigned_char_p()
print( [hex(the_bits_c_uchar_p[i]) for i in range(48)] )
#print([the_bit_string.bits.tobytes()[i] for i in range(0,48)])


