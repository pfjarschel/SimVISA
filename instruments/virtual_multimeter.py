# Simple virtual multimeter class
# Default voltage unit: V
# Default current unit: A
# Default resistance unit: Ohms
# By pfjarschel, 2023

import os
import numpy as np
from instruments.virtual_socketinstrument import VirtualSocketInstrument
from PyQt6 import uic
from PyQt6.QtCore import QTimer

# File paths
main_path = os.path.dirname(os.path.realpath(__file__))
thisfile = os.path.basename(__file__)

# Load ui file
FormUI, WindowUI = uic.loadUiType(f"{main_path}/virtual_multimeter.ui")

# Communications class
class VirtualMultimeterComms(VirtualSocketInstrument):
    def __init__(self, dev, verbose=False):
        super().__init__(verbose)
        self.dev = dev

        # Commands dictionaries
        self.comms_meas = {}

        # Instrument functions
        self.comms_meas["volt?"] = self.get_volt
        self.comms_meas["curr?"] = self.get_curr
        self.comms_meas["ohms?"] = self.get_ohms
        self.comms_dicts["meas"] = self.comms_meas

    def GET_IDN(self, args):
        return "PFJ Systems Inc., Virtual Multimeter VM1, S/N T347596"
    
    def get_volt(self, args):
        self.dev.voltRadio.setChecked(True)
        self.dev.measV = True
        self.dev.measA = False
        self.dev.measR = False

        val = self.dev.input_channel()
        return f"{val:.3f}"
    
    def get_curr(self, args):
        self.dev.currRadio.setChecked(True)
        self.dev.measV = False
        self.dev.measA = True
        self.dev.measR = False

        val = self.dev.input_channel()
        return f"{val:.3f}"
    
    def get_ohms(self, args):
        self.dev.ohmsRadio.setChecked(True)
        self.dev.measV = False
        self.dev.measA = False
        self.dev.measR = True

        val = self.dev.input_channel()
        return f"{val:.3f}"

# Main instrument class
class VirtualMultimeter(FormUI, WindowUI):
    # Input objects
    input_obj = None  

    # Internal parameters
    sampletime = 0.1
    int_time = 0.25
    npoints = 10

    v_noise = 0.001
    a_noise = 0.001
    r_noise = 0.5

    measV = True
    measA = False
    measR = False

    # Measurement stuff
    meas_timer = QTimer()
    meas_timer.setInterval(int(int_time*1000))

    # Default functions
    def __init__(self, verbose=False):
        super(VirtualMultimeter, self).__init__()
        
        print("Initializing multimeter")

        self.setupUi(self)
        self.setupOtherUi()
        self.setupActions()
        self.meas_timer.start()
        self.comms = VirtualMultimeterComms(self, verbose)

        self.show()

    def __del__(self):
        print("Deleting multimeter object")

    def closeEvent(self, event):
        self.comms.close([])
        event.accept()
    
    # UI functions
    def setupOtherUi(self):
        self.lcdNumber.setSmallDecimalPoint(True)
        self.lcdNumber.setDigitCount(6)
    
    def setupActions(self):
        # Connect UI signals to functions
        self.voltRadio.clicked.connect(self.setMeasurement)
        self.currRadio.clicked.connect(self.setMeasurement)
        self.ohmsRadio.clicked.connect(self.setMeasurement)

        self.meas_timer.timeout.connect(self.measLoop)

    def setMeasurement(self):
        self.measV = self.voltRadio.isChecked()
        self.measA = self.currRadio.isChecked()
        self.measR = self.ohmsRadio.isChecked()

    # Measurement functions   
    def measLoop(self):
        val = self.input_channel()
        val_str = f"{val:.3f}"
        self.lcdNumber.display(val_str)

    # I/O functions
    # Start communication server
    def startComms(self, port):
        self.comms.start("127.0.0.1", port)

    # Set inputs: to connect the in functions to other instruments
    def set_inputs(self, main=None):    
        self.input_obj = main

    # Input functions: all parameters and instrument inputs are processed here. These are active (calls the output from other instruments)
    def input_channel(self):
        if self.input_obj:
            imp = self.input_obj.impedance
            data = self.input_obj.output_signal()
        else:
            imp = 1e9
            data = np.zeros([self.npoints])
        if self.measV:
            val = np.mean(data) + np.random.random()*self.v_noise - self.v_noise/2.0
        elif self.measA:
            val = np.mean(data)/imp + np.random.random()*self.a_noise - self.a_noise/2.0
        elif self.measR:
            val = imp + np.random.random()*self.r_noise - self.r_noise/2.0

        return val

    # Output functions: all instrument outputs are processed here. These are passive (called from other instruments)
    # Output sample time 
    def output_sampletime(self):
        return self.sampletime

    # Output npoints
    def output_npoints(self):
        return self.npoints