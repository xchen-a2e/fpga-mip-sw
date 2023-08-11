import xdma_reg_if
import i2c_master
import time
import sensor

io_device = xdma_reg_if.xdma_reg_if()
if(sensor.SetupCamera(io_device, sensor.sensor_list)):
    print("Initalize sensor success")