import sys
import time
import xdma_reg_if

MIPI_CORE_CONFIG_REG_OFFSET			= 0x00
MIPI_PROTOCOL_CONFIG_REG_OFFSET		= 0x04
MIPI_CORE_STATUS_REG_OFFSET			= 0x10
MIPI_GLOBAL_INT_ENABLE_REG_OFFSET  	= 0x20
MIPI_INTERRUPT_STATUS_REG_OFFSET	= 0x24
MIPI_INTERRUPT_ENABLE_REG_OFFSET	= 0x28
MIPI_GENERIC_SHORT_PKT_REG_OFFSET	= 0x30
MIPI_CLOCK_LANE_INFO_REG_OFFSET		= 0x3C
MIPI_LANE0_STATUS_REG_OFFSET		= 0x40
MIPI_LANE1_STATUS_REG_OFFSET		= 0x44
MIPI_LANE2_STATUS_REG_OFFSET		= 0x48
MIPI_LANE3_STATUS_REG_OFFSET		= 0x4C
MIPI_VC0_IMAGE_INFO1_REG_OFFSET		= 0x60
MIPI_VC0_IMAGE_INFO2_REG_OFFSET		= 0x64
MIPI_VC1_IMAGE_INFO1_REG_OFFSET		= 0x68
MIPI_VC1_IMAGE_INFO2_REG_OFFSET		= 0x6C
MIPI_VC2_IMAGE_INFO1_REG_OFFSET		= 0x70
MIPI_VC2_IMAGE_INFO2_REG_OFFSET		= 0x74
MIPI_VC3_IMAGE_INFO1_REG_OFFSET		= 0x78
MIPI_VC3_IMAGE_INFO2_REG_OFFSET		= 0x7C

MIPI_DPHY_CONTROL_REG_OFFSET		= 0x00
MIPI_DPHY_IDELAY_TAP_REG_OFFSET		= 0x04
MIPI_DPHY_INIT_TIMER_REG_OFFSET		= 0x08
MIPI_DPHY_HS_TIMEOUT_REG_OFFSET		= 0x10
MIPI_DPHY_ESC_TIMEOUT_REG_OFFSET	= 0x14
MIPI_DPHY_CL_STATUS_REG_OFFSET		= 0x18
MIPI_DPHY_DL0_STATUS_REG_OFFSET		= 0x1C
MIPI_DPHY_DL1_STATUS_REG_OFFSET		= 0x20
MIPI_DPHY_DL2_STATUS_REG_OFFSET		= 0x24
MIPI_DPHY_DL3_STATUS_REG_OFFSET		= 0x28
MIPI_DPHY_HS_SETTLE_REG_OFFSET		= 0x30

IO_MUX_ONE_LANE						= 0x0003
IO_MUX_TWO_LANES					= 0x0007
IO_MUX_FOUR_LANES					= 0x001F
IO_MUX_LANES_MASK					= 0x001F
IO_SENSOR_RESET						= 0x0080

# MIPI_CORE_CONFIG_REG 
CORE_ENABLE_MASK					= 0x00000001
SOFT_RESET_MASK						= 0x00000002

# MIPI_CORE_STATUS_REG 
SOFT_RESET_CORE_DISABLED_MASK		= 0x00000001

# MIPI_DPHY_CONTROL_REG_OFFSET
DPHY_SOFT_RESET_MASK				= 0x00000001
DPHY_ENABLE_MASK					= 0x00000002

def MipiConfigLanes(io_device, BaseAddr, Lanes):
    ControlValue = 0
    Data = 0
    ControlValue = xdma_reg_if.xdma_reg_if.io_read(io_device, BaseAddr)

    ControlValue &= ~(int(IO_MUX_LANES_MASK))
    print("INFO: CSI Base = 0x{}".format(hex(BaseAddr)))
    print("INFO: Setting IO MUX value, {} lanes".format(Lanes))
    
    if(Lanes == 1):
        ControlValue |= int(IO_MUX_ONE_LANE)
    elif(Lanes == 2):
        ControlValue |= int(IO_MUX_TWO_LANES)
    elif(Lanes == 4):
        ControlValue |= int(IO_MUX_FOUR_LANES)
    else:
        sys.exit("Error: Invalid number of lanes {}".format(Lanes))
        
    xdma_reg_if.xdma_reg_if.io_write(io_device, BaseAddr, ControlValue)
    Data = xdma_reg_if.xdma_reg_if.io_read(io_device, BaseAddr + int(MIPI_CORE_CONFIG_REG_OFFSET))
    
    if((Data & 0x3) == 0x01): 
        print("INFO: not in reset + enabled; continue this is the state we want to validate")
    elif((Data & 0x3) == 0x00): 
        print("INFO: not in reset + not enabled set enable and continue")
        Data = 0x01
        xdma_reg_if.xdma_reg_if.io_write(io_device,BaseAddr+int(MIPI_CORE_CONFIG_REG_OFFSET), Data)
    elif((Data&0x3) == 0x02): 
        print("INFO: in reset + not enabled take out of reset and enable to start from a known state")
        Data = 0x01
        xdma_reg_if.xdma_reg_if.io_write(io_device,BaseAddr+int(MIPI_CORE_CONFIG_REG_OFFSET), Data)
    else:
        print("INFO: in reset + enabled take out of reset to start from a known state")
        Data = 0x01
        xdma_reg_if.xdma_reg_if.io_write(io_device, BaseAddr+int(MIPI_CORE_CONFIG_REG_OFFSET), Data)
    
    print("INFO: Wait for the core clears the Soft reset/Core enable")
    Data = 0
    timeout = 100
    while((Data & int(SOFT_RESET_CORE_DISABLED_MASK)) & (timeout != 0)):
        Data = xdma_reg_if.xdma_reg_if.io_read(io_device, BaseAddr + int(MIPI_CORE_STATUS_REG_OFFSET))
        time.sleep(0.1)
        timeout = timeout -1

    if(timeout == 0):
        sys.exit("Error: MIPI soft reset clear timeout!! Status = 0x{}".format(hex(Data)))

    Data = xdma_reg_if.xdma_reg_if.io_read(io_device, BaseAddr + int(MIPI_PROTOCOL_CONFIG_REG_OFFSET))
    print("INFO: MIPI_PROTOCOL_CONFIG_REG_OFFSET = 0x{}".format(hex(Data)))
    
    print("INFO: Set the Soft reset of the core")
    Data = xdma_reg_if.xdma_reg_if.io_read(io_device, BaseAddr + int(MIPI_CORE_CONFIG_REG_OFFSET))
    print("INFO: MIPI_CORE_CONFIG_REG_OFFSET = 0x{}".format(hex(Data)))
    Data |= 0x3
    xdma_reg_if.xdma_reg_if.io_write(io_device, BaseAddr+int(MIPI_CORE_CONFIG_REG_OFFSET), Data)

    print("INFO: Wait for the core clears the Soft reset/Core enable")
    Data = 0
    timeout = 100
    while((Data & int(SOFT_RESET_CORE_DISABLED_MASK)) & (timeout != 0)):
        Data = xdma_reg_if.xdma_reg_if.io_read(io_device,BaseAddr + int(MIPI_CORE_STATUS_REG_OFFSET))
        time.sleep(0.1)
        timeout = timeout -1

    if(timeout == 0):
        sys.exit("MIPI soft reset clear timeout!! Status = 0x{}".format(hex(Data)))

    print("INFO: Change the active lanes configuration")
    Data = ((Lanes - 1) & 0x03)
    print("Data = 0x{}".format(hex(Data)))
    xdma_reg_if.xdma_reg_if.io_write(io_device,BaseAddr+int(MIPI_PROTOCOL_CONFIG_REG_OFFSET), Data)

    print("INFO: Clear the Soft reset of the core")
    Data = 0x01
    xdma_reg_if.xdma_reg_if.io_write(io_device,BaseAddr+int(MIPI_CORE_CONFIG_REG_OFFSET), Data)

    print("INFO: Wait for the core clears the Soft reset/Core enable")
    Data = 0
    timeout = 100
    while((Data & int(SOFT_RESET_CORE_DISABLED_MASK)) & (timeout != 0)):
        Data = xdma_reg_if.xdma_reg_if.io_read(io_device,BaseAddr + int(MIPI_CORE_STATUS_REG_OFFSET))
        time.sleep(0.1)
        timeout = timeout -1

    if(timeout == 0):
        sys.exit("Error: MIPI soft reset clear timeout!! Status = 0x{}".format(hex(Data)))

    Data = xdma_reg_if.xdma_reg_if.io_read(io_device,BaseAddr + int(MIPI_PROTOCOL_CONFIG_REG_OFFSET))
    print("MIPI_PROTOCOL_CONFIG_REG_OFFSET = 0x{}".format(hex(Data)))

    return True    

def MipiVerifyStatus(io_device, CsiBaseAddr, DphyBaseAddr, Lanes):
    DPHY_ERROR = 0
    CSI_ERROR = 0
    Data = 0
    for ii in range(Lanes):
        Data = xdma_reg_if.xdma_reg_if.io_read(io_device, DphyBaseAddr + int(MIPI_DPHY_DL0_STATUS_REG_OFFSET)+ (ii << 2))
        print("Lane {} DPHY PKT_CNT {}".format(ii, Data))
        if((Data & 0xFFFF0000) == 0):
            DPHY_ERROR = 1

    Data = xdma_reg_if.xdma_reg_if.io_read(io_device,CsiBaseAddr + int(MIPI_INTERRUPT_STATUS_REG_OFFSET))
    if((Data & 0x80000000) == 0):
        CSI_ERROR = 1
        print("CSI FRAME not received! 0x{}".format(hex(Data)))
    
    if((CSI_ERROR == 1) or (DPHY_ERROR == 1)):
        sys.exit("MIPI-CSI Error, exiting MIPI configuration")
