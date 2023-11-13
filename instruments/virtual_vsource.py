# Simple virtual voltage source class
# Default voltage unit:
# By pfjarschel, 2023

import os
import numpy as np
from instruments.virtual_socketinstrument import VirtualSocketInstrument
from PyQt6 import uic

# File paths
main_path = os.path.dirname(os.path.realpath(__file__))
thisfile = os.path.basename(__file__)

# Load ui file
FormUI, WindowUI = uic.loadUiType(f"{main_path}/virtual_vsource.ui")

# Communications class
class VirtualVSourceComms(VirtualSocketInstrument):
    def __init__(self, dev, verbose=False):
        super().__init__(verbose)
        self.dev = dev

        # Instrument functions
        self.comms_root["volt?"] = self.get_volt
        self.comms_root["volt"] = self.set_volt

    def GET_IDN(self, args):
        return "PFJ Systems Inc., Virtual Voltage Source VVS1, S/N V5437"
    
    def get_volt(self, args):
        return f"{self.dev.voltage:.3f}"
    
    def set_volt(self, args):
        try:
            if args:
                val = float(args[0])
                mult = self.dev.voltDial.value()
                fine_mult = self.dev.fineDial.value()
                if (val < -10) or ((val > 10) and (val <= 15)):
                    self.dev.volt15Radio.setChecked(True)
                    mult = int(100*(val/30) + 50)
                    coarse = (mult/100.0)*30.0 - 15.0
                    fine_mult = int(100*(val - coarse))
                if ((val < -5) and (val >= -10)) or ((val > 5) and (val <= 10)):
                    self.dev.volt10Radio.setChecked(True)
                    mult = int(100*(val/20) + 50)
                    coarse = (mult/100.0)*20.0 - 10.0
                    fine_mult = int(100*(val - coarse))
                if (val >= -5) and (val <= 5):
                    self.dev.volt5Radio.setChecked(True)
                    mult = int(100*(val/10) + 50)
                    coarse = (mult/100.0)*10.0 - 5.0
                    fine_mult = int(100*(val - coarse))
                if val > 15:
                    self.dev.volt30Radio.setChecked(True)
                    mult = int(100*(val/30))
                    coarse = (mult/100.0)*30.0
                    fine_mult = int(100*(val - coarse))

                self.dev.voltDial.setValue(mult)
                self.dev.fineDial.setValue(fine_mult)
        except:
            pass


# Main instrument class
class VirtualVSource(FormUI, WindowUI):
    # Main parameters
    voltage = 0.0

    # Input objects
    input_npoints_obj = None

    # Internal parameters
    npoints = 10
    v_noise = 0.003
    impedance = 6.4
    add_noise = True
    
    # Waveform holder
    wf = []

    # Default functions
    def __init__(self, verbose=False):
        super(VirtualVSource, self).__init__()
        
        print("Initializing voltage source")

        self.setupUi(self)
        self.setupOtherUi()
        self.setupActions()
        self.comms = VirtualVSourceComms(self, verbose)

        self.show()

    def __del__(self):
        print("Deleting voltage source object")

    def closeEvent(self, event):
        self.comms.close([])
        event.accept()
    
    # UI functions
    def setupOtherUi(self):
        self.lcdNumber.setSmallDecimalPoint(True)
        self.lcdNumber.setDigitCount(5)
    
    def setupActions(self):
        # Connect UI signals to functions
        self.volt5Radio.clicked.connect(self.setSource)
        self.volt10Radio.clicked.connect(self.setSource)
        self.volt15Radio.clicked.connect(self.setSource)
        self.volt30Radio.clicked.connect(self.setSource)
        self.voltDial.valueChanged.connect(self.setSource)
        self.fineDial.valueChanged.connect(self.setSource)

    # Internal functions    
    # Create full waveform
    def get_waveform(self):
        wf = self.voltage*np.ones([self.npoints])

        # Add some noise
        if self.add_noise:
            noise = np.random.uniform(-self.v_noise/2, self.v_noise/2, size=self.npoints)
            wf = wf + noise
        
        self.wf = wf
    
    def setSource(self):
        coarse = 0.0
        fine = 0.5*self.fineDial.value()/100.0
        vfinal = 0.0
        if self.volt5Radio.isChecked():
            coarse = (self.voltDial.value()/100.0)*10.0 - 5.0
            vfinal = coarse + fine
            if vfinal > 5: vfinal = 5.0
            if vfinal < -5: vfinal = -5.0
        if self.volt10Radio.isChecked():
            coarse = (self.voltDial.value()/100.0)*20.0 - 10.0
            vfinal = coarse + fine
            if vfinal > 10: vfinal = 10.0
            if vfinal < -10: vfinal = -10.0
        if self.volt15Radio.isChecked():
            coarse = (self.voltDial.value()/100.0)*30.0 - 15.0
            vfinal = coarse + fine
            if vfinal > 15: vfinal = 15.0
            if vfinal < -15: vfinal = -15.0
        if self.volt30Radio.isChecked():
            coarse = (self.voltDial.value()/100.0)*30.0
            vfinal = coarse + fine
            if vfinal > 30: vfinal = 30.0
            if vfinal < 0: vfinal = 0.0
        
        self.voltage = vfinal
        self.lcdNumber.display(f"{vfinal:.2f}")

    # I/O functions
    # Start communication server
    def startComms(self, port):
        self.comms.start("127.0.0.1", port)

    # Set inputs: to connect the in functions to other instruments
    def set_inputs(self, npoints_obj):    
        self.input_npoints_obj = npoints_obj

    # Input functions: all parameters and instrument inputs are processed here. These are active (calls the output from other instruments)
    # Number of points of the output
    def input_npoints(self):
        if self.input_npoints_obj:
            npoints = self.input_npoints_obj.output_npoints()
        else:
            npoints = 10
        if npoints != self.npoints:
            self.npoints = npoints

    # Output functions: all instrument outputs are processed here. These are passive (called from other instruments)
    # Output signal: The instrument oputput (a series of voltage points)
    def output_signal(self):
        # Get npoints
        self.input_npoints()
        self.wf = np.zeros([self.npoints])

        # Get data
        self.get_waveform()
        return self.wf