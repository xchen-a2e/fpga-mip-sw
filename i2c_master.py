#!/usr/bin/env python3
import time
import sys

# Opencore IIC parameters 
PRER_LO_OFFSET = (int(0x0) << 2) 
PRER_HI_OFFSET = (int(0x1) << 2) 
CTR_OFFSET     = (int(0x2) << 2) 
RXR_OFFSET     = (int(0x3) << 2) 
TXR_OFFSET     = (int(0x3) << 2) 
CR_OFFSET      = (int(0x4) << 2)
SR_OFFSET      = (int(0x4) << 2) 
GPO_OFFSET     = (int(0x8) << 2)

IIC_CORE_EN_MASK     = 0x80
IIC_CORE_IRQ_EN_MASK = 0x40

IACK_MASK            = 0x01
START_AND_WRITE_MASK = 0x90
WRITE_AND_STOP_MASK  = 0x50
TX_WRITE_MASK        = 0x10
RX_ACK_MASK          = 0x20
RX_NACK_MASK         = 0x28
STOP_BIT_MASK        = 0x40

IIC_TIP_MASK         = 0x02
ICC_BUSY_MASK        = 0x40

REPEATED_START_OPTIONS = 2
XIIC_STOP_OPTIONS      = 1
XIIC_SEND_DATA         = 0

RD      = 1         
WR      = 0         

class iic_master_driver:
    def __init__(self, io_device, bus_address, base_address, system_frequency, scl_frequency, logger=None, Debug=False):
        self.sAddr = bus_address
        self.sys_freq = system_frequency
        self.scl_freq = scl_frequency
        # initialize device
        self.io_device = io_device
        self.debug = Debug
        self.PRER_LO = hex(base_address + PRER_LO_OFFSET)
        self.PRER_HI = hex(base_address + PRER_HI_OFFSET)
        self.CTR     = hex(base_address + CTR_OFFSET)    
        self.RXR     = hex(base_address + RXR_OFFSET)    
        self.TXR     = hex(base_address + TXR_OFFSET)    
        self.CR      = hex(base_address + CR_OFFSET)    
        self.SR      = hex(base_address + SR_OFFSET)     
        self.GPO_REG = hex(base_address + GPO_OFFSET)    

    def setupIIC(self, high_bit, low_bit):
        data = 0
        self.io_device.io_write(self.io_device, self.PRER_HI, hex(high_bit))
        self.io_device.io_write(self.io_device, self.PRER_LO, hex(low_bit))
        data = self.io_device.io_read(self.io_device, self.PRER_HI)
        if(data != high_bit):
            print('Error: IIC prescale high bit register {} data does not match set value {}'.format(high_bit, data))
            sys.exit()
        data = self.io_device.io_read(self.io_device, self.PRER_LO)
        if(data != low_bit):
            print('Error: IIC prescale low bit register {} data does not match set value {}'.format(low_bit, data))
            sys.exit()

    def iic_getgpo(self):
        data = 0
        data = self.io_device.io_read(self.io_device, self.GPO_REG)
        return data

    def iic_setgpo(self, val):
        data = val & 0xff
        self.io_device.io_write(self.io_device, self.GPO_REG, data)

    def iic_init(self):
        ctrl = 0
        prescale = 0
        prescale_hi = 0
        prescale_lo = 0
        print("Info: Disable IIC device")
        ctrl = self.io_device.io_read(self.io_device, self.CTR)
        ctrl &= ~(IIC_CORE_EN_MASK | IIC_CORE_IRQ_EN_MASK)
        if(self.Debug):
            print('Info: write {} to address {}'.format(hex(ctrl), self.CTR))
        self.io_device.io_write(self.io_device, self.CTR, hex(ctrl))
        #calculate scl frequency count
        prescale = int((self.sys_freq / (5* self.scl_freq)) -1)
        prescale_hi = (prescale >> 8) & 0xff
        prescale_lo = prescale & 0xff
        if(self.Debug):
            print("Info: Setup IIC SLC clock")
        self.setupIIC(prescale_hi, prescale_lo)
        # init device
        if(self.Debug):
              print("Info: Enable IIC device")
        self.io_device.io_write(self.io_device, self.CR, hex(IACK_MASK))
        self.io_device.io_write(self.io_device, self.CTR, (hex(ctrl | IIC_CORE_EN_MASK)))

    def checkTIP(self):
        data = 0
        ts = 0
        timeout = 1/100000  # 1 ms timescale
        time.sleep(200000/(1000000))
        ts = time.time()/1000000
        print("{} us Info: check read/write ack".format(ts))
        while(1):
            data = self.io_device.io_read(self.io_device, self.SR)
            if(self.Debug):
                print("{} us Info: SR register {}".format((time.time()/1000000), hex(data)))
            if((int(data) & IIC_TIP_MASK) == 0):
                break
            if((time.time()/1000000 )> (ts + timeout)):
                sys.exit("{} us Error: timout reached".format(time.time()/1000000))
        print("{} us Info: tip==0".format(time.time()/1000000))

    def send_data(self,data,options):
        if((options == REPEATED_START_OPTIONS) or (options == XIIC_SEND_DATA)):
            self.io_device.io_write(self.io_device, self.TXR, hex(data))
            self.io_device.io_write(self.io_device, self.CR, hex(TX_WRITE_MASK))
            if(options == XIIC_SEND_DATA):
                print("{} us Info: send byte {}".format((time.time()/1000000), hex(data)))
            else:
                print("{} us Info: send last byte {} and repeated start".format((time.time()/1000000), hex(data)))
        elif(options == XIIC_STOP_OPTIONS):
            self.io_device.io_write(self.io_device, self.TXR, hex(data))
            self.io_device.io_write(self.io_device, self.CR, hex(WRITE_AND_STOP_MASK))
            print("{} us Info: send last byte {} and stop".format((time.time()/1000000), hex(data)))
        else:
            sys.exit("Error: invalid cmd")

        self.checkTIP()

    def iic_send(self, data, databyte_count, address, addressbyte_count, options):
        total_byte_count = 0
        command = []
        send_data = 0
        total_byte_count = databyte_count + addressbyte_count
        #append address
        for num_addr in address:
            command.append(num_addr)
        #append data
        if(databyte_count != 0):
            if(databyte_count > 1):
                for num_data in data:
                    command.append(num_data)
            else:
                command.append(data)
        localAddr = hex((int(self.sAddr) << 1) | WR)
        print("{} us Info: generate start, write cmd {} (slave address+ write)".format((time.time()/1000000), localAddr))
        self.io_device.io_write(self.io_device, self.TXR, localAddr)
        self.io_device.io_write(self.io_device, self.CR, hex(START_AND_WRITE_MASK))
        self.checkTIP()
        for ii in range(total_byte_count):
            send_data = command[ii]
            if(ii == (total_byte_count-1)):
                self.send_data(send_data, options)
                time.sleep(1/(10000000)) 
            else:
                self.send_data(send_data, XIIC_SEND_DATA)

    def recv_data(self, numbytes):
        data = 0
        while(numbytes > 0):
            if(numbytes== 1):
                self.io_device.io_write(self.io_device, self.CR, hex(STOP_BIT_MASK | RX_NACK_MASK))
                if(self.Debug):
                    print("{} us Info: read + nack".format((time.time()/1000000)))
            else:
                self.io_device.io_write(self.io_device, self.CR, hex(RX_ACK_MASK))
                if(self.Debug):
                    print("{} us Info: read + ack".format((time.time()/1000000)))
            self.checkTIP()
            data = self.io_device.io_read(self.io_device, self.RXR)
            print("{} us Info: received {} from read address".format((time.time()/1000000), hex(data)))
            numbytes = numbytes - 1
            
        return data
	
    def iic_recv(self, numbytes):
        localAddr = 0
        data = []
        localAddr = hex((int(self.sAddr) << 1) | RD)
        print("{} us Info: generate start, write cmd {} (slave address+ read)".format((time.time()/1000000), localAddr))
        self.io_device.io_write(self.io_device, self.TXR, localAddr)
        self.io_device.io_write(self.io_device, self.CR, hex(START_AND_WRITE_MASK))
        self.checkTIP()
        data.append(self.recv_data(numbytes))

        return data
    
    def iic_read_A16D8(self, addr):
        data = []
        address = []	
        address.append((addr >> 8) & 0xff)
        address.append(addr & 0xff)
        self.iic_init()
        self.iic_send(0, 0, address, 2, REPEATED_START_OPTIONS)
        data = self.iic_recv(1)
        
        return data[0]
    
    def iic_write_A16D8(self, addr, data):
        address = []
        self.iic_init()
        address.append((addr >> 8) & 0xff)
        address.append(addr & 0xff)
        data &= 0xff
        self.iic_send(data, 1, address, 2, XIIC_STOP_OPTIONS)
