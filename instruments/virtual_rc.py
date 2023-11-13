# Simple virtual RC circuit class
# Default resistance unit: Ohms
# Default capacitance unit: µF
# By pfjarschel, 2023

import os
import time
import numpy as np
from scipy.integrate import odeint
from scipy.fft import fft, ifft, fftfreq
from scipy.signal import windows
from PyQt6 import uic
from PyQt6.QtGui import QPixmap
from instruments.virtual_socketinstrument import VirtualSocketInstrument

# File paths
main_path = os.path.dirname(os.path.realpath(__file__))
thisfile = os.path.basename(__file__)

# Load ui file
FormUI, WindowUI = uic.loadUiType(f"{main_path}/virtual_rc.ui")

# Misc Functions
# FFT
def do_fft(wls, data, window=False, beta=0.0):
    yf = []
    n = len(data)
    if window:
        w = windows.kaiser(n, beta)
        yf = fft(data*w)
    else:
        yf = fft(data)

    delta = wls[1] - wls[0]
    xf = fftfreq(n, delta)

    return xf[:n//2], (2.0/n)*np.abs(yf[:n//2]), xf, yf

def do_ifft(f_raw, yf_raw, cut_l, cut_h, slope=90.0):
    yf_raw[((np.abs(f_raw) > cut_h) | (np.abs(f_raw) < cut_l))] = yf_raw[((np.abs(f_raw) > cut_h) | (np.abs(f_raw) < cut_l))]*(np.abs(f_raw[((np.abs(f_raw) > cut_h) | (np.abs(f_raw) < cut_l))])/cut_h)**(-slope/10)
    y = np.real(ifft(yf_raw))

    if min(y) < 0:
        y = y - min(y)

    return np.real(y)

def fft_filter(x_data, y_data, l_pass, h_pass=0.0, slope=90.0):
    # Do fft
    x_fft, y_fft, f_raw, yf_raw = do_fft(x_data, y_data)

    # Do ifft to remove undesired interference
    return do_ifft(f_raw, yf_raw, h_pass, l_pass, slope)
    

# Communications class
class VirtualRCComms(VirtualSocketInstrument):
    def __init__(self, dev, verbose=False):
        super().__init__(verbose)
        self.dev = dev

        # Commands dictionaries
        # Instrument functions
        # Root commands
        self.comms_root["out?"] = self.get_output
        self.comms_root["out"] = self.set_output
        self.comms_root["c?"] = self.get_c
        self.comms_root["c"] = self.set_c
        self.comms_root["r?"] = self.get_r
        self.comms_root["r"] = self.set_r
        
    def GET_IDN(self, args):
        return "PFJ Systems Inc., Virtual RC Circuit VRC1, S/N R0934567"
    
    def get_output(self, args):
        if self.dev.outCRadio.isChecked():
            return "C"
        if self.dev.outRRadio.isChecked():
            return "R"
    
    def set_output(self, args):
        if args:
            if (args[0] == "r"):
                self.dev.outCRadio.setChecked(False)
                self.dev.outRRadio.setChecked(True)
            if (args[0] == "c"):
                self.dev.outCRadio.setChecked(True)
                self.dev.outRRadio.setChecked(False)
            self.dev.setMeasurement()
                
                
    def get_c(self, args):
        return f"{self.dev.cSpin.value()}"
    
    def set_c(self, args):
        try:
            if args:
                val = float(args[0])
                self.dev.cSpin.setValue(val)
        except:
            pass
    
    def get_r(self, args):
        return f"{self.dev.rSpin.value()}"
    
    def set_r(self, args):
        try:
            if args:
                val = float(args[0])
                self.dev.rSpin.setValue(val)
        except:
            pass


# Main instrument class
class VirtualRC(FormUI, WindowUI):
    # Input objects
    main_input = None
    sampletime_obj = None
    npoints_obj = None

    # Internal parameters
    sampletime = 0.1
    npoints = 10
    impedance = 1.0
    freq = 1000.0

    measR = False
    measC = True

    # Waveform holder
    wf = np.zeros(npoints)
    data = np.zeros(npoints)
    t_array = np.zeros(npoints)

    # Default functions
    def __init__(self, verbose=False):
        super(VirtualRC, self).__init__()
        
        print("Initializing RC circuit")

        self.setupUi(self)
        self.setupOtherUi()
        self.setupActions()
        self.comms = VirtualRCComms(self, verbose)

        self.show()

    def __del__(self):
        print("Deleting RC circuit object")

    def closeEvent(self, event):
        self.comms.close([])
        event.accept()

    # Other functions
    def interp_value(self, ref_val, ref_array, val_array):
        ref_idx = np.abs(ref_array - ref_val).argmin()
        ref_idx_r = ref_idx + 1
        ref_idx_l = ref_idx - 1
        if ref_idx_r >= len(ref_array):
            # Linear interpolation
            li_a = (val_array[ref_idx] - val_array[ref_idx_l])/(ref_array[ref_idx] - ref_array[ref_idx_l])
            val = val_array[ref_idx_l] + li_a*(ref_val - ref_array[ref_idx_l])
        elif ref_idx_l < 0:
            # Linear interpolation
            li_a = (val_array[ref_idx_r] - val_array[ref_idx])/(ref_array[ref_idx_r] - ref_array[ref_idx])
            val = val_array[ref_idx] + li_a*(ref_val - ref_array[ref_idx])
        else:
            try:
                # Quadratic interpolation
                qi_x1 = ref_array[ref_idx_l]
                qi_x2 = ref_array[ref_idx]
                qi_x3 = ref_array[ref_idx_r]
                qi_y1 = val_array[ref_idx_l]
                qi_y2 = val_array[ref_idx]
                qi_y3 = val_array[ref_idx_r]
                qi_A = np.array([[1, qi_x1, qi_x1**2],[1, qi_x2, qi_x2**2],[1, qi_x3, qi_x3**2]])
                qi_B = np.array([qi_y1, qi_y2, qi_y3])
                coefs = np.linalg.solve(qi_A, qi_B)
                val = coefs[0] + coefs[1]*ref_val + coefs[2]*(ref_val**2)
            except:
                # Linear interpolation
                li_a = (val_array[ref_idx_r] - val_array[ref_idx])/(ref_array[ref_idx_r] - ref_array[ref_idx])
                val = val_array[ref_idx] + li_a*(ref_val - ref_array[ref_idx])
        return val

    def model(self, vc, t):
        r = self.rSpin.value()
        c = 1e-6*self.cSpin.value()
        rc = r*c
        
        t_idx = np.abs(self.t_array - t).argmin()
        v_t = self.data[t_idx]
        
        return ((v_t - vc)/rc)

    
    # UI functions
    def setupOtherUi(self):
        self.imgLabel.setPixmap(QPixmap(f"{main_path}/rc.png"))
    
    def setupActions(self):
        # Connect UI signals to functions
        self.outRRadio.clicked.connect(self.setMeasurement)
        self.outCRadio.clicked.connect(self.setMeasurement)
        self.rSpin.valueChanged.connect(self.setCircuit)
        self.cSpin.valueChanged.connect(self.setCircuit)

    def setMeasurement(self):
        self.measR = self.outRRadio.isChecked()
        self.measC = self.outCRadio.isChecked()

    def setCircuit(self):
        pass

    # Circuit functions
    def get_waveform(self, data):
        self.t_array = np.linspace(0.0, self.sampletime, len(data))
        r = self.rSpin.value()
        c = 1e-6*self.cSpin.value()
        
        if np.any(data):
            data = fft_filter(self.t_array, data, 8*(1/(2*np.pi*r*c)), slope=30.0)
            vc_0 = 0.0
            vc_sol = odeint(self.model, vc_0, self.t_array)[:,0]
        else:
            vc_sol = np.zeros(len(data))

        v_array_c = vc_sol
        v_array_r = data - v_array_c

        if self.measR:
            return_array = v_array_r
        elif self.measC:
            return_array = v_array_c
        
        self.wf = return_array

    # I/O functions
    # Start communication server
    def startComms(self, port):
        self.comms.start("127.0.0.1", port)

    # Set inputs: to connect the in functions to other instruments
    def set_inputs(self, mainin_obj, sampletime_obj, npoints_obj):    
        self.sampletime_obj = sampletime_obj
        self.npoints_obj = npoints_obj
        self.main_input = mainin_obj

    # Input functions: all parameters and instrument inputs are processed here. These are active (calls the output from other instruments)
    # Total time of the output wave
    def input_sampletime(self):
        if self.sampletime_obj:
            sampletime = self.sampletime_obj.output_sampletime()
        else:
            sampletime = 2.0/self.freq
            self.t0 = 0.0
            self.tref = 0.0
        if self.sampletime != sampletime:
            self.sampletime = sampletime

    # Number of points of the output wave
    def input_npoints(self):
        if self.npoints_obj:
            npoints = self.npoints_obj.output_npoints()
        else:
            npoints = 1000
        if npoints != self.npoints:
            self.npoints = npoints
    
    def input_channel(self):
        if self.main_input:
            self.freq = self.main_input.freq
            self.main_input.add_noise = False
            data = self.main_input.output_signal()
        else:
            data = np.zeros([self.npoints])

        return data

    # Output functions: all instrument outputs are processed here. These are passive (called from other instruments)
    # Output sample time 
    def output_sampletime(self):
        self.input_sampletime()
        return self.sampletime

    # Output npoints
    def output_npoints(self):
        self.input_npoints()
        return self.npoints
    
    # Output signal: The instrument output (a time-dependent signal)   
    def output_signal(self):
        # Get sampletime and npoints
        self.input_sampletime()
        self.input_npoints()

        self.wf = np.zeros([self.npoints])

        # Get data
        self.data = self.input_channel()
        self.get_waveform(self.data)

        return self.wf