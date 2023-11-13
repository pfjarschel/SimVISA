# Simple electrical filter class
# Default time unit: 1 s
# Default frequency unit = 1 Hz
# Default voltage unit: V
# By pfjarschel, 2021

# Imports
import os, time
import numpy as np
import matplotlib.pyplot as plt

# File paths
main_path = os.path.dirname(os.path.realpath(__file__))
thisfile = os.path.basename(__file__)


# Main component class
class Filter():

    # Main parameters
    cutoff = 120e6

    # Input objects
    input_waveform_obj = None
    input_time_obj = None

    
    # Default functions
    def __init__(self):    
        print("Initializing filter")
        self.freq = 100e6
        self.t0 = time.time()  # Will be the phase of the output wave
        self.tref = self.t0

    def __del__(self):
        print("Deleting filter object")


    # I/O functions
    # Set inputs: to connect the in functions to other instruments
    def set_inputs(self, waveform_obj, time_obj, freq_obj):    
        self.input_waveform_obj = waveform_obj
        self.input_time_obj = time_obj
        self.input_freq_obj = freq_obj

    # Input functions: all parameters and instrument inputs are processed here. These are active (calls the output from other instruments)
    # Waveform to filter
    def input_waveform(self):
        wf = self.input_waveform_obj.output_signal()
        return wf

    # Time array of the waveform
    def input_time(self):
        timearray = self.input_time_obj.output_timearray()
        return timearray

    # Wave frequency
    def input_freq(self):
        freq = self.input_time_obj.output_freq()
        return freq

    # Output functions: all instrument outputs are processed here. These are passive (called from other instruments)
    # Output signal: The instrument oputput (a time-dependent signal)   
    def output_signal(self):
        # Get frequency
        self.freq = self.input_freq()

        # Temporarily change generator phase, and time multiplier
        self.input_waveform_obj.input_sampletime()
        self.input_waveform_obj.input_npoints()
        self.input_waveform_obj.refresh_params()
        timemult = 3.0
        self.input_waveform_obj.timemult = timemult
        extra_time_phase = 2*np.pi*self.freq*((timemult - 1)*self.input_waveform_obj.sampletime/2)
        phase = np.arctan(self.freq/self.cutoff) + extra_time_phase
        # print((phase - extra_time_phase)*180/np.pi)
        self.input_waveform_obj.phase -= phase
        self.input_waveform_obj.refresh_params()
        
        # Get waveform, and time array
        wf = self.input_waveform()
        timearray = self.input_time()
        npoints1 = self.input_waveform_obj.npoints

        # Reset generator phase and time multiplier
        self.input_waveform_obj.phase += phase
        self.input_waveform_obj.timemult = 1.0
        self.input_waveform_obj.npoints = int(self.input_waveform_obj.npoints/timemult)
        self.input_waveform_obj.refresh_params()

        # Filter waveform
        timestep = timearray[1] - timearray[0]
        filt_wl = min(max(int((1.15/self.cutoff)/timestep), 3), len(wf))
        if not (filt_wl % 2): filt_wl -= 1
        w = np.blackman(filt_wl)
        wf = np.convolve(wf, w, 'same')/np.sum(w)

        # Take the correct slice from the waveform
        npoints0 = self.input_waveform_obj.npoints
        addedpoints = int((npoints1 - npoints0)/2)
        wf = wf[addedpoints:-addedpoints]
        
        return wf
