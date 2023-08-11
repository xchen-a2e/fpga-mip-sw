#!/usr/bin/env python3
import subprocess
from subprocess import Popen, PIPE

# linux device
xdma_tool = "./reg_rw"
linux_device = "/dev/xdma0_user"

class xdma_reg_if:
    def __init__(self):
        self.run_state = 'RUNNING'
        self.run_process = []

    def run_cmd(self, cmd):
        self.run_process = subprocess.Popen(cmd, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.run_state = 'RUNNING'
        return self.run_process

    def poll_status(self):
        if self.run_state == 'RUNNING':
            if self.run_process.poll() is not None:
                self.run_state = 'COMPLETE'
        return self.run_state

    def run_subprocess(self, cmd):
        output = []
        err = []
        if self.run_state == 'RUNNING':
            sub_p = self.run_cmd(cmd)
            while self.poll_status() != 'COMPLETE':
                sub_p.wait()
            output, err = self.run_process.communicate()
        self.run_state = 'RUNNING'

        return output
    
    @staticmethod    
    def io_read(io_device, offset):
        ret_val = []
        val = []
        cmd = '{} {} {} w'.format(xdma_tool, linux_device, str(offset))
        print("Read command: {}".format(cmd))
        ret_val = io_device.run_subprocess(cmd)
        val = ret_val.split()[len(ret_val.split())-1]
        
        return int(val[2:].decode('ascii'), base=16)

    @staticmethod        
    def io_write(io_device, offset, data):
        cmd = '{} {} {} w {}'.format(xdma_tool, linux_device, str(offset), str(data))
        print("Write command: {}".format(cmd))
        print("Wrtie {} to address {}".format(data, offset))
        io_device.run_subprocess(cmd)
