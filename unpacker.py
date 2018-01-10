class unpacker:
    compressedRawData=True
    sk2cms_data=[]
    rollMask=0

    def __init__(self,compressedRawData=True):
        self.compressedRawData=compressedRawData
        self.sk2cms_data=[[[0 for sca in range(15)] for ch in range(128)] for sk in range(4)]
        
    def grayToBinary(self,gray):
        binary = gray & (1 << 11)
        binary |= (gray ^ (binary >> 1)) & (1 << 10)
        binary |= (gray ^ (binary >> 1)) & (1 << 9)
        binary |= (gray ^ (binary >> 1)) & (1 << 8)
        binary |= (gray ^ (binary >> 1)) & (1 << 7)
        binary |= (gray ^ (binary >> 1)) & (1 << 6)
        binary |= (gray ^ (binary >> 1)) & (1 << 5)
        binary |= (gray ^ (binary >> 1)) & (1 << 4)
        binary |= (gray ^ (binary >> 1)) & (1 << 3)
        binary |= (gray ^ (binary >> 1)) & (1 << 2)
        binary |= (gray ^ (binary >> 1)) & (1 << 1)
        binary |= (gray ^ (binary >> 1)) & (1 << 0)
        return binary;
        
        
    def unpack(self,rawdata):
        #decode raw data :
        ev=[ [0 for i in range(1924)] for sk in range(4) ]
        if self.compressedRawData==False:
            for i in range(1924):
                for j in range(16):
                    x = rawdata[i*16 + j]
                    x = x&0xf
                    for sk in range(4):
                        ev[sk][i] = ev[sk][i] | (((x >> (3-sk) ) & 1) << (15 - j))

        else:
            for i in range(1924):
                for j in range(8):
                    x = rawdata[i*8 + j]
                    y = (x >> 4) & 0xf
                    x = x & 0xf
                    for sk in range(4):
                        ev[sk][i] = ev[sk][i] | (((x >> (3 - sk) ) & 1) << (14 - j*2))
                        ev[sk][i] = ev[sk][i] | (((y >> (3 - sk) ) & 1) << (15 - j*2))

        for sk in range(4):
            for i in range(128*15):
                ev[sk][i] = self.grayToBinary(ev[sk][i] & 0x0FFF)
            
        self.rollMask=ev[sk][1920]            
        self.sk2cms_data=[[[0 for sca in range(15)] for ch in range(128)] for sk in range(4)]
        for sk in range(4):
            for ch in range(128):
                for sca in range(0,15):
                    self.sk2cms_data[sk][ch][sca] = ev[sk][sca*128+ch]

    def showData(self,eventID):
        for sk in range(4):
            print "Event = "+str(eventID)+"\t Chip = "+str(sk)+"\t RollMask = "+hex(self.rollMask)
            for ch in range(128):
                stream=""
                for sca in range(15):
                    stream=stream+" "+str(self.sk2cms_data[sk][ch][sca])
                print stream

