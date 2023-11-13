# Simple virtual signal generator class
# Default time unit: 1 s
# Default frequency unit = 1 Hz
# Default voltage unit: V
# By pfjarschel, 2021

# Imports
import os, time
import numpy as np
from instruments.virtual_socketinstrument import VirtualSocketInstrument
from PyQt6 import uic

# File paths
main_path = os.path.dirname(os.path.realpath(__file__))
thisfile = os.path.basename(__file__)

# Load ui file
FormUI, WindowUI = uic.loadUiType(f"{main_path}/virtual_signal_gen.ui")

# Communications class
class VirtualSignalGenComms(VirtualSocketInstrument):
    def __init__(self, dev, verbose=False):
        super().__init__(verbose)
        self.dev = dev

        # Commands dictionaries
        self.comms_freq = {}
        self.comms_amp = {}
        self.comms_wave = {}

        # Instrument functions
        # Root commands
        self.comms_root["out?"] = self.get_output
        self.comms_root["out"] = self.set_output

        # Frequency commands
        self.comms_freq["freq?"] = self.get_freq
        self.comms_freq["freq"] = self.set_freq
        self.comms_freq["chrp?"] = self.get_chirp
        self.comms_freq["chrp"] = self.set_chirp
        self.comms_freq["cvar?"] = self.get_chirp_var
        self.comms_freq["cvar"] = self.set_chirp_var
        self.comms_freq["cper?"] = self.get_chirp_per
        self.comms_freq["cper"] = self.set_chirp_per
        self.comms_dicts["freq"] = self.comms_freq

        # Amplitude commands
        self.comms_amp["offs?"] = self.get_offs
        self.comms_amp["offs"] = self.set_offs
        self.comms_amp["amp?"] = self.get_amp
        self.comms_amp["amp"] = self.set_amp
        self.comms_dicts["amp"] = self.comms_amp

        # Wave commands
        self.comms_wave["wave?"] = self.get_wave
        self.comms_wave["wave"] = self.set_wave
        self.comms_wave["dc?"] = self.get_dc
        self.comms_wave["dc"] = self.set_dc
        self.comms_wave["phas?"] = self.get_phase
        self.comms_wave["phas"] = self.set_phase
        self.comms_dicts["wave"] = self.comms_wave

    def GET_IDN(self, args):
        return "PFJ Systems Inc., Virtual Signal Generator SG1, S/N M9874235"
    
    # Root functions
    def get_output(self, args):
        return f"{int(self.dev.output_enabled)}"
    
    def set_output(self, args):
        if args:
            if (args[0] == "1") or (args[0] == "true") or (args[0] == "on"):
                self.dev.output_enabled = True
                self.dev.onoffBut.setText("Output is ON")
            if (args[0] == "0") or (args[0] == "false") or (args[0] == "off"):
                self.dev.output_enabled = False
                self.dev.onoffBut.setText("Output is OFF")

    # Freq functions
    def get_freq(self, args):
        return f"{self.dev.freq}"
    
    def set_freq(self, args):
        try:
            if args:
                val = float(args[0])
                mult = self.dev.fmultSpin.value()
                if val <= 10.0:
                    mult = val/1.0
                    self.dev.f1hzCheck.setChecked(True)
                if (val > 10.0) and (val <= 1e3):
                    mult = val/100.0
                    self.dev.f100hzCheck.setChecked(True)
                if (val > 1e3) and (val <= 100e3):
                    mult = val/10e3
                    self.dev.f10khzCheck.setChecked(True)
                if (val > 100e3) and (val <= 10e6):
                    mult = val/1e6
                    self.dev.f1mhzCheck.setChecked(True)
                if (val > 10e6) and (val <= 1e9):
                    mult = val/100e6
                    self.dev.f100mhzCheck.setChecked(True)
                if val > 1e9:
                    mult = val/1e9
                    self.dev.f1ghzCheck.setChecked(True)
                self.dev.fmultSpin.setValue(mult)
        except:
            pass

    def get_chirp(self, args):
        return f"{int(self.dev.chirpCheck.isChecked())}"
    
    def set_chirp(self, args):
        if args:
            if (args[0] == "1") or (args[0] == "true") or (args[0] == "on"):
                self.dev.chirpCheck.setChecked(True)
            if (args[0] == "0") or (args[0] == "false") or (args[0] == "off"):
                self.dev.chirpCheck.setChecked(False)

    def get_chirp_var(self, args):
        return f"{self.dev.chirpvarSpin.value()}"
    
    def set_chirp_var(self, args):
        try:
            if args:
                val = float(args[0])
                self.dev.chirpvarSpin.setValue(val)
        except:
            pass

    def get_chirp_per(self, args):
        return f"{self.dev.chirptSpin.value()}"
    
    def set_chirp_per(self, args):
        try:
            if args:
                val = float(args[0])
                self.dev.chirptSpin.setValue(val)
        except:
            pass
    
    # Amp Functions
    def get_amp(self, args):
        return f"{self.dev.amplitude}"
    
    def set_amp(self, args):
        try:
            if args:
                val = float(args[0])
                mult = self.dev.amultSpin.value()
                if val <= 10e-3:
                    mult = val/1e-3
                    self.dev.a1mvCheck.setChecked(True)
                if (val > 10e-3) and (val <= 100e-3):
                    mult = val/10e-3
                    self.dev.a10mvCheck.setChecked(True)
                if (val > 100e-3) and (val <= 1.0):
                    mult = val/100e-3
                    self.dev.a100mvCheck.setChecked(True)
                if (val > 1.0) and (val <= 10.0):
                    mult = val/1.0
                    self.dev.a1vCheck.setChecked(True)
                if val > 10.0:
                    mult = val/10.0
                    self.dev.a10vCheck.setChecked(True)
                self.dev.amultSpin.setValue(mult)
        except:
            pass

    def get_offs(self, args):
        return f"{self.dev.offset}"
    
    def set_offs(self, args):
        try:
            if args:
                val = float(args[0])
                self.dev.offsetSpin.setValue(val)
        except:
            pass

    # Wave functions
    def get_wave(self, args):
        wave = "none"
        if self.dev.sineCheck.isChecked():
            wave = "sine"
        if self.dev.triangleCheck.isChecked():
            wave = "triangle"
        if self.dev.squareCheck.isChecked():
            wave = "square"
        if self.dev.sawCheck.isChecked():
            wave = "saw"
        if self.dev.rsawCheck.isChecked():
            wave = "rsaw"
        if self.dev.pulseCheck.isChecked():
            wave = "pulse"
        return wave
    
    def set_wave(self, args):
        if args:
            wave = args[0]
            if wave == "sine":
                self.dev.sineCheck.setChecked(True)
                self.dev.setParameters()
            if wave == "triangle":
                self.dev.triangleCheck.setChecked(True)
                self.dev.setParameters()
            if wave == "square":
                self.dev.squareCheck.setChecked(True)
                self.dev.setParameters()
            if wave == "saw":
                self.dev.sawCheck.setChecked(True)
                self.dev.setParameters()
            if wave == "rsaw":
                self.dev.rsawCheck.setChecked(True)
                self.dev.setParameters()
            if wave == "pulse":
                self.dev.pulseCheck.setChecked(True)
                self.dev.setParameters()
    
    def get_dc(self, args):
        return f"{self.dev.dutycycle*100.0}"
    
    def set_dc(self, args):
        try:
            if args:
                dc = float(args[0])
                self.dev.dutySpin.setValue(dc)
        except:
            pass

    def get_phase(self, args):
        return f"{self.dev.phase*180.0/np.pi}"
    
    def set_phase(self, args):
        try:
            if args:
                phase = float(args[0])
                self.dev.phaseSpin.setValue(phase)
        except:
            pass
        
# Main instrument class
class VirtualSignalGenerator(FormUI, WindowUI):

    # Wave types
    SINE = 0
    TRIANGLE = 1
    SQUARE = 2
    SAW = 3
    RSAW = 4
    PULSE = 5
    
    # Main parameters
    freq = 1e6
    amplitude = 1.0
    dutycycle = 0.5
    wave = SINE
    offset = 0.0
    sampletime = 2e-6
    npoints = 1000

    # Input objects
    input_sampletime_obj = None
    input_npoints_obj = None

    # Independent limits
    max_freq = 10e9
    min_freq= 0.1
    max_amplitude = 1e2
    min_amplitude = 1e-3
    max_offset = 1e2
    min_offset = -1e2

    # Internal parameters
    risetime = 0.4*(1/max_freq)
    falltime = risetime
    noiselevel = 5*min_amplitude
    jitter = 20e-12
    phase = 0.0
    output_enabled = False
    timemult = 1.0
    impedance = 50.0
    add_noise = True

    # Dependent limits
    min_pulsewidth = risetime + falltime
    max_pulsewidth = (1/freq) - min_pulsewidth
    max_dutycycle = max_pulsewidth/(1/freq)
    min_dutycycle = min_pulsewidth/(1/freq)

    # Waveform holder
    wf = []
    
    # Default functions
    def __init__(self, verbose=False):
        super(VirtualSignalGenerator, self).__init__()
        
        print("Initializing signal generator")
        self.t0 = time.time()  # Will be the phase of the output wave
        self.tref = time.time()  # Initial time for chirp calc
        self.refresh_params()  # Recalculate some parameters

        self.setupUi(self)
        self.setupOtherUi()
        self.setupActions()
        self.comms = VirtualSignalGenComms(self, verbose)

        self.show()

    def __del__(self):
        print("Deleting signal generator object")

    def closeEvent(self, event):
        self.comms.close([])
        event.accept()

    # UI functions
    def setupOtherUi(self):
        # No need for this class, but is standard on my scripts (see oscilloscope for an example)
        pass  
    
    def setupActions(self):
        # Connect UI signals to functions
        self.onoffBut.clicked.connect(self.toggleOutput)
        self.f1hzCheck.clicked.connect(self.setParameters)
        self.f100hzCheck.clicked.connect(self.setParameters)
        self.f10khzCheck.clicked.connect(self.setParameters)
        self.f1mhzCheck.clicked.connect(self.setParameters)
        self.f100mhzCheck.clicked.connect(self.setParameters)
        self.f1ghzCheck.clicked.connect(self.setParameters)
        self.a1mvCheck.clicked.connect(self.setParameters)
        self.a10mvCheck.clicked.connect(self.setParameters)
        self.a100mvCheck.clicked.connect(self.setParameters)
        self.a1vCheck.clicked.connect(self.setParameters)
        self.a10vCheck.clicked.connect(self.setParameters)
        self.sineCheck.clicked.connect(self.setParameters)
        self.triangleCheck.clicked.connect(self.setParameters)
        self.squareCheck.clicked.connect(self.setParameters)
        self.sawCheck.clicked.connect(self.setParameters)
        self.rsawCheck.clicked.connect(self.setParameters)
        self.pulseCheck.clicked.connect(self.setParameters)
        self.fmultSpin.valueChanged.connect(self.setParameters)
        self.amultSpin.valueChanged.connect(self.setParameters)
        self.offsetSpin.valueChanged.connect(self.setParameters)
        self.dutySpin.valueChanged.connect(self.setParameters)
        self.phaseSpin.valueChanged.connect(self.setParameters)
        self.fmultDial.valueChanged.connect(self.syncDialsSpins)
        self.amultDial.valueChanged.connect(self.syncDialsSpins)
        self.offsetSlider.valueChanged.connect(self.syncDialsSpins)
        self.dutySlider.valueChanged.connect(self.syncDialsSpins)
        self.phaseSlider.valueChanged.connect(self.syncDialsSpins)


    def toggleOutput(self):
        if self.output_enabled:
            self.output_enabled = False
            self.onoffBut.setText("Output is OFF")
        else:
            self.output_enabled = True
            self.onoffBut.setText("Output is ON")

    def syncDialsSpins(self):
        # Sync spin boxes values to dials and sliders values
        self.fmultSpin.setValue(self.fmultDial.value()/1000.0)
        self.amultSpin.setValue(self.amultDial.value()/1000.0)
        self.offsetSpin.setValue(self.offsetSlider.value()/1000.0)
        self.dutySpin.setValue(self.dutySlider.value()/100.0)
        self.phaseSpin.setValue(self.phaseSlider.value()/100.0)

    def setParameters(self):
        # Set Frequency
        frange = 1.0
        if self.f1hzCheck.isChecked():
            frange = 1.0
        elif self.f100hzCheck.isChecked():
            frange = 100.0
        elif self.f10khzCheck.isChecked():
            frange = 10000.0
        elif self.f1mhzCheck.isChecked():
            frange = 1e6
        elif self.f100mhzCheck.isChecked():
            frange = 100e6
        elif self.f1ghzCheck.isChecked():
            frange = 1e9
        freq = frange*self.fmultSpin.value()
        self.freq = max(min(self.max_freq, freq), self.min_freq)

        # Set Amplitude
        arange = 1.0
        if self.a1mvCheck.isChecked():
            arange = 1e-3
        elif self.a10mvCheck.isChecked():
            arange = 10e-3
        elif self.a100mvCheck.isChecked():
            arange = 0.1
        elif self.a1vCheck.isChecked():
            arange = 1.0
        elif self.a10vCheck.isChecked():
            arange = 10.0
        amplitude = arange*self.amultSpin.value()
        offset = self.offsetSpin.value()
        self.amplitude = max(min(self.max_amplitude, amplitude), self.min_amplitude)
        self.offset = max(min(self.max_offset, offset), self.min_offset)

        # Set wave
        if self.sineCheck.isChecked():
            self.wave = self.SINE
        elif self.triangleCheck.isChecked():
            self.wave = self.TRIANGLE
        elif self.squareCheck.isChecked():
            self.wave = self.SQUARE
        elif self.sawCheck.isChecked():
            self.wave = self.SAW
        elif self.rsawCheck.isChecked():
            self.wave = self.RSAW
        elif self.pulseCheck.isChecked():
            self.wave = self.PULSE

        # Recalculate some stuff
        self.refresh_params()

        # Set limited duty cycle
        dutycycle = self.dutySpin.value()/100.0
        self.dutycycle = max(min(self.max_dutycycle, dutycycle), self.min_dutycycle)
        self.dutySpin.setValue(self.dutycycle*100.0)

        # Set phase
        self.phase = self.phaseSpin.value()*np.pi/180.0

        # Adjust dials/sliders positions and limited values
        self.fmultDial.setValue(int(self.fmultSpin.value()*1000.0))
        self.amultDial.setValue(int(self.amultSpin.value()*1000.0))
        self.offsetSlider.setValue(int(self.offsetSpin.value()*1000.0))
        self.dutySlider.setValue(int(self.dutySpin.value()*100.0))
        self.phaseSlider.setValue(int(self.phaseSpin.value()*100.0))

    # Internal functions    
    # Create full waveform
    def get_waveform(self):
        wf = np.zeros([self.totnpoints])
        phase = self.t0 % (2*np.pi) + self.phase

        # Add some jitter
        jitter = np.random.uniform(-self.jitter/2, self.jitter/2)

        # Chirped frequency
        freq = self.freq
        if self.chirpCheck.isChecked():
            t = time.time() - self.tref
            freq = self.freq*(1 + (self.chirpvarSpin.value()/100.0)*np.sin(2*np.pi*t/self.chirptSpin.value()))

        # Calculate argument
        argument = 2*np.pi*freq*(self.exttimearray + jitter) + phase

        if self.output_enabled:
            if self.wave == self.SINE:
                wf = 0.5*self.amplitude*np.sin(argument)
            elif self.wave == self.TRIANGLE:
                wf = 0.3183*self.amplitude*np.arcsin(np.cos(argument))
            elif self.wave == self.SQUARE:
                wf = 0.3183*self.amplitude*(np.arctan(np.sin(argument))
                        + np.arctan(1/np.sin(argument)))
            elif self.wave == self.SAW:
                argument = 1*np.pi*freq*(self.exttimearray + jitter) + phase
                wf = -0.3183*self.amplitude*np.arctan(1/np.tan(argument))
            elif self.wave == self.RSAW:
                argument = 1*np.pi*freq*(self.exttimearray + jitter) + phase
                wf = 0.3183*self.amplitude*np.arctan(1/np.tan(argument))
            elif self.wave == self.PULSE:
                multiplier_array = np.where(argument % (2*np.pi) < self.dutycycle*2*np.pi, 1, 0)
                wf = self.amplitude*(multiplier_array - 0.5)
            
        # Filter (simulate risetime)
        filt_wl = min(max(int(self.risetime/self.delta), 3), self.totnpoints)
        if not (filt_wl % 2): filt_wl -= 1
        w = np.blackman(filt_wl)
        wf = np.convolve(wf, w, 'same')/np.sum(w)
        
        # Get only the numper of points wanted
        wf = wf[self.addpoints:-self.addpoints]

        # Add some noise
        if self.add_noise:
            noise = np.random.uniform(-self.noiselevel/2, self.noiselevel/2, size=self.npoints)
            wf = wf + noise + self.offset
        else:
             wf = wf + self.offset

        self.wf = np.clip(wf, self.min_offset, self.max_offset)
    
    # Recalculate some parameters
    def refresh_params(self):
        self.min_pulsewidth = self.risetime + self.falltime
        self.max_pulsewidth = (1/self.freq) - self.min_pulsewidth
        self.max_dutycycle = self.max_pulsewidth/(1/self.freq)
        self.min_dutycycle = self.min_pulsewidth/(1/self.freq)
        
        self.delta = self.sampletime/self.npoints  # Time step
        
        # Points to add (will be cut off later, increases filter precision)
        self.npoints = int(self.npoints*self.timemult)
        self.addpoints = int(self.npoints*0.1)
        self.totnpoints = self.npoints + 2*self.addpoints

        # Added time due to the added points
        self.sampletime = self.sampletime*self.timemult
        self.addtime = self.delta*self.addpoints
        self.tottime = self.sampletime + self.addtime

        # Time arrays
        self.exttimearray = np.linspace(-self.addtime, self.tottime, self.totnpoints)
        self.timearray = np.linspace(0, self.sampletime, self.npoints)


    # I/O functions
    def startComms(self, port):
        self.comms.start("127.0.0.1", port)

    # Set inputs: to connect the in functions to other instruments
    def set_inputs(self, sampletime_obj, npoints_obj):    
        self.input_sampletime_obj = sampletime_obj
        self.input_npoints_obj = npoints_obj

    # Input functions: all parameters and instrument inputs are processed here. These are active (calls the output from other instruments)
    # Total time of the output wave
    def input_sampletime(self):
        if self.input_sampletime_obj:
            sampletime = self.input_sampletime_obj.output_sampletime()
        else:
            sampletime = 2.0/self.freq
            self.t0 = 0.0
            self.tref = 0.0
        if self.sampletime != sampletime:
            self.sampletime = sampletime

    # Number of points of the output wave
    def input_npoints(self):
        if self.input_npoints_obj:
            npoints = self.input_npoints_obj.output_npoints()
        else:
            npoints = 10000
        if npoints != self.npoints:
            self.npoints = npoints

    # Output functions: all instrument outputs are processed here. These are passive (called from other instruments)
    # Output signal: The instrument oputput (a time-dependent signal)   
    def output_signal(self):
        # Get sampletime and npoints
        self.input_sampletime()
        self.input_npoints()
        self.refresh_params()
        self.wf = np.zeros([self.npoints])

        # Get data
        self.get_waveform()

        return self.wf

    # Output time array: outputs the instrument time array on which the signal is based
    def output_timearray(self):
        return self.timearray

    # Output frequency: outputs the signal frequency
    def output_freq(self):
        return self.freq