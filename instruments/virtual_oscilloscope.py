# Simple virtual oscilloscope class
# Default time unit: 1 s
# Default frequency unit = 1 Hz
# Default voltage unit: V
# By pfjarschel, 2021

# Imports
import os, time
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
from PyQt6 import uic, QtCore
from PyQt6.QtCore import QTimer, QDir
from PyQt6.QtWidgets import QFileDialog
from instruments.virtual_socketinstrument import VirtualSocketInstrument

# File paths
main_path = os.path.dirname(os.path.realpath(__file__))
thisfile = os.path.basename(__file__)

# Load ui file
FormUI, WindowUI = uic.loadUiType(f"{main_path}/virtual_oscilloscope.ui")

# Communications class
class VirtualOscilloscopeComms(VirtualSocketInstrument):
    def __init__(self, dev, verbose=False):
        super().__init__(verbose)
        self.dev = dev
        self.c_chan = 1

        # Commands dictionaries
        self.comms_horiz = {}
        self.comms_trig = {}
        self.comms_acq = {}
        self.comms_c0 = {}
        self.comms_c1 = {}
        self.comms_c2 = {}
        self.comms_c3 = {}
        self.comms_c4 = {}
        
        # Instrument functions
        # Root commands
        self.comms_root["run?"] = self.get_run
        self.comms_root["run"] = self.run
        self.comms_root["stop"] = self.stop
        
        # Horizontal Commands
        self.comms_horiz["scale?"] = self.get_hscale
        self.comms_horiz["scale"] = self.set_hscale
        self.comms_horiz["offset?"] = self.get_hoffset
        self.comms_horiz["offset"] = self.set_hoffset
        self.comms_horiz["data?"] = self.get_hdata
        self.comms_dicts["horiz"] = self.comms_horiz
        
        # Trigger Commands
        self.comms_trig["mode?"] = self.trigger_mode
        self.comms_trig["free"] = self.trigger_free
        self.comms_trig["auto"] = self.trigger_auto
        self.comms_dicts["trig"] = self.comms_trig
        
        # Acquisition Commands
        self.comms_acq["points?"] = self.get_points
        self.comms_acq["points"] = self.set_points
        self.comms_acq["avgs?"] = self.get_avgs
        self.comms_acq["avgs"] = self.set_avgs
        self.comms_acq["hold?"] = self.get_hold
        self.comms_acq["hold"] = self.set_hold
        self.comms_acq["holdn?"] = self.get_holdn
        self.comms_acq["holdn"] = self.set_holdn
        self.comms_dicts["acq"] = self.comms_acq

        # Channel Commands
        self.comms_c1["enable?"] = self.get_c1_enable
        self.comms_c1["enable"] = self.set_c1_enable
        self.comms_c1["asx?"] = self.get_c1_asx
        self.comms_c1["asx"] = self.set_c1_asx
        self.comms_c1["scale?"] = self.get_c1_scale
        self.comms_c1["scale"] = self.set_c1_scale
        self.comms_c1["offset?"] = self.get_c1_offset
        self.comms_c1["offset"] = self.set_c1_offset
        self.comms_c1["data?"] = self.get_c1_data
        self.comms_dicts["c1"] = self.comms_c1
        
        self.comms_c2["enable?"] = self.get_c2_enable
        self.comms_c2["enable"] = self.set_c2_enable
        self.comms_c2["asx?"] = self.get_c2_asx
        self.comms_c2["asx"] = self.set_c2_asx
        self.comms_c2["scale?"] = self.get_c2_scale
        self.comms_c2["scale"] = self.set_c2_scale
        self.comms_c2["offset?"] = self.get_c2_offset
        self.comms_c2["offset"] = self.set_c2_offset
        self.comms_c2["data?"] = self.get_c2_data
        self.comms_dicts["c2"] = self.comms_c2
        
        self.comms_c3["enable?"] = self.get_c3_enable
        self.comms_c3["enable"] = self.set_c3_enable
        self.comms_c3["asx?"] = self.get_c3_asx
        self.comms_c3["asx"] = self.set_c3_asx
        self.comms_c3["scale?"] = self.get_c3_scale
        self.comms_c3["scale"] = self.set_c3_scale
        self.comms_c3["offset?"] = self.get_c3_offset
        self.comms_c3["offset"] = self.set_c3_offset
        self.comms_c3["data?"] = self.get_c3_data
        self.comms_dicts["c3"] = self.comms_c3
        
        self.comms_c4["enable?"] = self.get_c4_enable
        self.comms_c4["enable"] = self.set_c4_enable
        self.comms_c4["asx?"] = self.get_c4_asx
        self.comms_c4["asx"] = self.set_c4_asx
        self.comms_c4["scale?"] = self.get_c4_scale
        self.comms_c4["scale"] = self.set_c4_scale
        self.comms_c4["offset?"] = self.get_c4_offset
        self.comms_c4["offset"] = self.set_c4_offset
        self.comms_c4["data?"] = self.get_c4_data
        self.comms_dicts["c4"] = self.comms_c4
        
    def GET_IDN(self, args):
        return "PFJ Systems Inc., Virtual Oscilloscope VOSC1, S/N P92348"
    
    def get_run(self, args):
        return f"{int(self.dev.running)}"
    
    def run(self, args):
        self.dev.runAcquisition()
    
    def stop(self, args):
        self.dev.stopAcquisition()
    
    def get_hscale(self, args):
        return f"{self.dev.timediv}"
    
    def set_hscale(self, args):
        try:
            if args:
                val = np.abs(float(args[0]))
                valog = np.log10(val)
                val_sci = np.ceil(valog) - 1
                val_num = 10**(valog - np.ceil(valog) + 1)
                hvalue = 0
                if val_num >= 0.5 and val_num < 3.5:
                    hvalue = 1
                if val_num >= 3.5 and val_num < 7.5:
                    hvalue = 2
                if val_num >= 7.5:
                    hvalue = 0
                    val_sci += 1
                
                dialval = (val_sci + 12)*3 + hvalue
                if dialval < 0:
                    dialval = 0
                if dialval > 39:
                    dialval = 39
                self.dev.hscaleDial.setValue(int(dialval))
        except:
            pass
        
    def get_hoffset(self, args):
        return f"{self.dev.hoffsetSpin.value()}"
    
    def set_hoffset(self, args):
        try:
            if args:
                val = float(args[0])
                if val < -100:
                    val = -100.0
                if val > 100:
                    val = 100.0
                self.dev.hoffsetSpin.setValue(val)
        except:
            pass
                
    def get_hdata(self, args):
        ret_string = ""
        for val in self.dev.x_axis:
            ret_string = f"{ret_string}{val},"
        return ret_string[:-1]
    
    def trigger_mode(self, args):
        if self.dev.triggerfreeRadio.isChecked():
            return "FREE"
        if self.dev.triggerautoRadio.isChecked():
            return "AUTO"
        
    def trigger_free(self, args):
        self.dev.triggerautoRadio.setChecked(False)
        self.dev.triggerfreeRadio.setChecked(True)
    
    def trigger_auto(self, args):
        self.dev.triggerfreeRadio.setChecked(False)
        self.dev.triggerautoRadio.setChecked(True)
            
    def get_points(self, args):
        return f"{self.dev.pointsSpin.value()}"
    
    def set_points(self, args):
        try:
            if args:
                val = int(args[0])
                if val < 100:
                    val = 100
                if val > 10000:
                    val = 10000
                self.dev.pointsSpin.setValue(val)
        except:
            pass
    
    def get_avgs(self, args):
        return f"{self.dev.avgSpin.value()}"
    
    def set_avgs(self, args):
        try:
            if args:
                val = int(args[0])
                if val < 1:
                    val = 1
                if val > 1024:
                    val = 1024
                self.dev.avgSpin.setValue(val)
        except:
            pass
    
    def get_hold(self, args):
        return f"{int(self.dev.holdCheck.isChecked())}"
    
    def set_hold(self, args):
        try:
            if args:
                if (args[0] == "1") or (args[0] == "true") or (args[0] == "on"):
                    self.dev.holdCheck.setChecked(True)
                else:
                    self.dev.holdCheck.setChecked(False)
                self.dev.setAcquisition()
        except:
            pass
    
    def get_holdn(self, args):
        return f"{self.dev.holdSpin.value()}"
    
    def set_holdn(self, args):
        try:
            if args:
                val = int(args[0])
                if val < 2:
                    val = 2
                if val > 1024:
                    val = 1024
                self.dev.hoffsetSpin.setValue(val)
        except:
            pass
        
    def get_channel_enable(self, args):
        returnval = eval(f"int(self.dev.ch{self.c_chan}Check.isChecked())")
        return f"{returnval}"
    
    def set_channel_enable(self, args):
        try:
            if args:
                if (args[0] == "1") or (args[0] == "true") or (args[0] == "on"):
                    eval(f"self.dev.ch{self.c_chan}Check.setChecked(True)")
                else:
                    eval(f"self.dev.ch{self.c_chan}Check.setChecked(False)")
        except:
            pass
    
    def get_channel_asx(self, args):
        returnval = eval(f"int(self.dev.ch{self.c_chan}XCheck.isChecked())")
        return f"{returnval}"
    
    def set_channel_asx(self, args):
        try:
            if args:
                if (args[0] == "1") or (args[0] == "true") or (args[0] == "on"):
                    eval(f"self.dev.ch{self.c_chan}XCheck.setChecked(True)")
                else:
                    eval(f"self.dev.ch{self.c_chan}XCheck.setChecked(False)")
                self.dev.change_xy()
        except:
            pass
    
    def get_channel_scale(self, args):
        returnval = eval(f"float(self.dev.voltdivs[{self.c_chan - 1}])")
        return returnval
    
    def set_channel_scale(self, args):
        try:
            if args:
                val = float(args[0])
                valog = np.log10(val)
                val_sci = np.ceil(valog) - 1
                val_num = 10**(valog - np.ceil(valog) + 1)
                vvalue = 0
                if val_num >= 0.5 and val_num < 3.5:
                    vvalue = 1
                if val_num >= 3.5 and val_num < 7.5:
                    vvalue = 2
                if val_num >= 7.5:
                    vvalue = 0
                    val_sci += 1
                
                dialval = (val_sci + 4)*3 + vvalue
                if dialval < 0:
                    dialval = 0
                if dialval > 15:
                    dialval = 15
                eval(f"self.dev.ch{self.c_chan}scaleDial.setValue(int(dialval))")
        except:
            pass
    
    def get_channel_offset(self, args):
        returnval = eval(f"float(self.dev.ch{self.c_chan}offsSpin.value())")
        return f"{returnval}"
    
    def set_channel_offset(self, args):
        try:
            if args:
                val = float(args[0])
                if val < -100.0:
                    val = 100.0
                if val > 100.0:
                    val = 100.0
                eval(f"self.dev.ch{self.c_chan}offsSpin.setValue({val})")
        except:
            pass
    
    def get_channel_data(self, args):
        array = eval(f"self.dev.y_axis[{self.c_chan - 1}]")
        ret_string = ""
        for val in array:
            ret_string = f"{ret_string}{val},"
        return ret_string[:-1]
    
    def get_c1_enable(self, args):
        self.c_chan = 1
        return self.get_channel_enable(args)
    def set_c1_enable(self, args):
        self.c_chan = 1
        self.set_channel_enable(args)
    def get_c1_asx(self, args):
        self.c_chan = 1
        return self.get_channel_asx(args)
    def set_c1_asx(self, args):
        self.c_chan = 1
        self.set_channel_asx(args)
    def get_c1_scale(self, args):
        self.c_chan = 1
        return self.get_channel_scale(args)
    def set_c1_scale(self, args):
        self.c_chan = 1
        self.set_channel_scale(args)
    def get_c1_offset(self, args):
        self.c_chan = 1
        return self.get_channel_offset(args)
    def set_c1_offset(self, args):
        self.c_chan = 1
        self.set_channel_offset(args)
    def get_c1_data(self, args):
        self.c_chan = 1
        return self.get_channel_data(args)
        
    def get_c2_enable(self, args):
        self.c_chan = 2
        return self.get_channel_enable(args)
    def set_c2_enable(self, args):
        self.c_chan = 2
        self.set_channel_enable(args)
    def get_c2_asx(self, args):
        self.c_chan = 2
        return self.get_channel_asx(args)
    def set_c2_asx(self, args):
        self.c_chan = 2
        self.set_channel_asx(args)
    def get_c2_scale(self, args):
        self.c_chan = 2
        return self.get_channel_scale(args)
    def set_c2_scale(self, args):
        self.c_chan = 2
        self.set_channel_scale(args)
    def get_c2_offset(self, args):
        self.c_chan = 2
        return self.get_channel_offset(args)
    def set_c2_offset(self, args):
        self.c_chan = 2
        self.set_channel_offset(args)
    def get_c2_data(self, args):
        self.c_chan = 2
        return self.get_channel_data(args)
        
    def get_c3_enable(self, args):
        self.c_chan = 3
        return self.get_channel_enable(args)
    def set_c3_enable(self, args):
        self.c_chan = 3
        self.set_channel_enable(args)
    def get_c3_asx(self, args):
        self.c_chan = 3
        return self.get_channel_asx(args)
    def set_c3_asx(self, args):
        self.c_chan = 3
        self.set_channel_asx(args)
    def get_c3_scale(self, args):
        self.c_chan = 3
        return self.get_channel_scale(args)
    def set_c3_scale(self, args):
        self.c_chan = 3
        self.set_channel_scale(args)
    def get_c3_offset(self, args):
        self.c_chan = 3
        return self.get_channel_offset(args)
    def set_c3_offset(self, args):
        self.c_chan = 3
        self.set_channel_offset(args)
    def get_c3_data(self, args):
        self.c_chan = 3
        return self.get_channel_data(args)
        
    def get_c4_enable(self, args):
        self.c_chan = 4
        return self.get_channel_enable(args)
    def set_c4_enable(self, args):
        self.c_chan = 4
        self.set_channel_enable(args)
    def get_c4_asx(self, args):
        self.c_chan = 4
        return self.get_channel_asx(args)
    def set_c4_asx(self, args):
        self.c_chan = 4
        self.set_channel_asx(args)
    def get_c4_scale(self, args):
        self.c_chan = 4
        return self.get_channel_scale(args)
    def set_c4_scale(self, args):
        self.c_chan = 4
        self.set_channel_scale(args)
    def get_c4_offset(self, args):
        self.c_chan = 4
        return self.get_channel_offset(args)
    def set_c4_offset(self, args):
        self.c_chan = 4
        self.set_channel_offset(args)
    def get_c4_data(self, args):
        self.c_chan = 4
        return self.get_channel_data(args)


# Main instrument class
class VirtualOscilloscope(FormUI, WindowUI):

    # Main parameters
    npoints = 1000
    display_points = npoints
    timediv = 100e-9
    timeoffs = 0.0
    voltdivs = np.array([0.5, 0.5, 0.5, 0.5])
    voltscales = voltdivs*10
    voffsets = np.array([0.0, 0.0, 0.0, 0.0])
    channels = [True, False, False, False]
    averages = 1
    hold = False
    holdn = 2
    
    # Input objects
    input_objs = [None, None, None, None]  

    # Internal parameters
    busy = False
    running = False
    loop_timer = None
    mastervscale = [-5.0, 5.0]
    sampletime = timediv*10
    x_axis = np.linspace(timeoffs, timeoffs + sampletime, npoints)
    y_axis = np.zeros([4, npoints])
    avg_buffer = np.zeros([4, 2, npoints])
    hold_buffer = np.zeros([4, 2, npoints])
    avg_counter = 0
    hold_counter = 0
    xymode = False
    xy_x = 1    
    
    # Default functions
    def __init__(self, verbose = False):
        super(VirtualOscilloscope, self).__init__()

        print("Initializing oscilloscope")

        self.setupUi(self)
        self.setupOtherUi()
        self.setupActions()
        self.comms = VirtualOscilloscopeComms(self, verbose)
        
        self.show()
        
    def __del__(self):
        print("Deleting oscilloscope object")
        
    def closeEvent(self, event):
        self.loop_timer.stop()
        self.comms.close([])
        event.accept()
        

    # UI functions
    def setupOtherUi(self):
        self.setup_graph()
        self.channelsChecks = [self.ch1Check, self.ch2Check, self.ch3Check, self.ch4Check]
        self.xyChecks = [self.ch1XCheck, self.ch2XCheck, self.ch3XCheck, self.ch4XCheck]

    def setupActions(self):
        # Connect UI signals to functions
        self.startBut.clicked.connect(self.runAcquisition)
        self.stopBut.clicked.connect(self.stopAcquisition)
        self.saveBut.clicked.connect(self.saveData)
        self.holdCheck.clicked.connect(self.setAcquisition)
        self.ch1XCheck.clicked.connect(self.change_xy)
        self.ch2XCheck.clicked.connect(self.change_xy)
        self.ch3XCheck.clicked.connect(self.change_xy)
        self.ch4XCheck.clicked.connect(self.change_xy)
        self.hoffsetSpin.valueChanged.connect(self.setScales)
        self.pointsSpin.valueChanged.connect(self.setAcquisition)
        self.avgSpin.valueChanged.connect(self.setAcquisition)
        self.holdSpin.valueChanged.connect(self.setAcquisition)
        self.ch1offsSpin.valueChanged.connect(self.setScales)
        self.ch2offsSpin.valueChanged.connect(self.setScales)
        self.ch3offsSpin.valueChanged.connect(self.setScales)
        self.ch4offsSpin.valueChanged.connect(self.setScales)
        self.hscaleDial.valueChanged.connect(self.syncDialsSpins)
        self.hoffsetDial.valueChanged.connect(self.syncDialsSpins)
        self.ch1scaleDial.valueChanged.connect(self.syncDialsSpins)
        self.ch2scaleDial.valueChanged.connect(self.syncDialsSpins)
        self.ch3scaleDial.valueChanged.connect(self.syncDialsSpins)
        self.ch4scaleDial.valueChanged.connect(self.syncDialsSpins)
        self.ch1offsDial.valueChanged.connect(self.syncDialsSpins)
        self.ch2offsDial.valueChanged.connect(self.syncDialsSpins)
        self.ch3offsDial.valueChanged.connect(self.syncDialsSpins)
        self.ch4offsDial.valueChanged.connect(self.syncDialsSpins)
        
        # Timers
        self.loop_timer = QTimer()
        self.loop_timer.timeout.connect(self.measLoop)
        self.loop_timer.setInterval(10)
        self.loop_timer.start()
        
    def setup_graph(self):
        self.figure = plt.figure()
        self.graph = FigureCanvas(self.figure)
        self.graphToolbar = NavigationToolbar(self.graph, self)
        self.graphToolbar.locLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.graphHolder.addWidget(self.graphToolbar)
        self.graphHolder.addWidget(self.graph)
        self.graph_ax = self.figure.add_subplot()
        self.graph_lines = [None, None, None, None]
        (self.graph_lines[0],) = self.graph_ax.plot([],[], 'o', markersize=1)
        (self.graph_lines[1],) = self.graph_ax.plot([],[], 'o', markersize=1)
        (self.graph_lines[2],) = self.graph_ax.plot([],[], 'o', markersize=1)
        (self.graph_lines[3],) = self.graph_ax.plot([],[], 'o', markersize=1)
        for line in self.graph_lines:
            line.set_visible(False)
        self.graph_ax.set_xlim([self.timeoffs, self.timediv*10 + self.timeoffs])
        self.graph_ax.set_ylim([self.mastervscale[0], self.mastervscale[1]])
        self.graph_ax.xaxis.set_ticks(np.linspace(self.timeoffs, self.timediv*10 + self.timeoffs, 11), labels=["","","","","","","","","","",""])
        self.graph_ax.yaxis.set_ticks(np.linspace(self.mastervscale[0], self.mastervscale[1], 11), labels=["","","","","","","","","","",""])
        self.graph_ax.xaxis.set_minor_locator(AutoMinorLocator())
        self.graph_ax.yaxis.set_minor_locator(AutoMinorLocator())
        self.graph_ax.set_xlabel("Time (Div)")
        self.graph_ax.set_ylabel("Voltage (Div)")
        self.graph_ax.grid(True, which='minor', color='gainsboro')
        self.graph_ax.grid(True, which='major', color='gray')
        self.graph.draw()

    # Enable/disable vertical numbers in graph
    def change_vdivs(self):
        if self.showvdivCheck.isChecked():
            self.graph_ax.set_yticklabels(np.linspace(-5, 5, 11))
        else:
            self.graph_ax.set_yticklabels([])

        # self.graphHolder.removeWidget(self.graphToolbar)
        # self.graphToolbar = NavigationToolbar(self.graph, self)
        # self.graphToolbar.locLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        # self.graphHolder.addWidget(self.graphToolbar)

    # Change XY mode
    def change_xy(self):
        ch = int(self.sender().objectName()[2])
        enable = self.sender().isChecked()
        self.ch1XCheck.setChecked(False)
        self.ch2XCheck.setChecked(False)
        self.ch3XCheck.setChecked(False)
        self.ch4XCheck.setChecked(False)
        self.sender().setChecked(enable)
        self.xymode = enable
        self.xy_x = ch
        if enable:
            self.channelsChecks[ch - 1].setChecked(True)

        self.setAcquisition()

    # Start/stop Acquisition
    def runAcquisition(self):
        if not self.running:
            self.running = True
            # self.loop_timer.start()

    def stopAcquisition(self):
        if self.running:
            self.running = False
            # self.loop_timer.stop()

    # Set acquisition stuff
    def setAcquisition(self):
        was_running = False
        if self.running:
            self.stopAcquisition()
            was_running = True

        # self.npoints = self.pointsSpin.value()
        self.display_points = self.pointsSpin.value()
        self.x_axis = np.linspace(self.timeoffs, self.timeoffs + self.sampletime, self.npoints)
        self.y_axis = np.zeros([4, self.npoints])
        self.avg_buffer = np.zeros([4, self.avgSpin.value(), self.npoints])
        self.hold_buffer = np.zeros([4, self.holdSpin.value(), self.npoints])
        self.avg_counter = 0
        self.hold_counter = 0

        # Get rid of empty average buffer
        for i in range(0, 4):
            data = self.input_channels(i)
            self.avg_buffer[i] = np.tile(data, (self.avgSpin.value(), 1))
        
        if was_running:
            self.runAcquisition()
            
    # Set oscilloscope scales
    def setScales(self):
        # Horizontal
        self.timeoffs = 0.01*self.hoffsetSpin.value()*self.sampletime
        
        # Vertical
        self.voffsets[0] = self.ch1offsSpin.value()                             
        self.voffsets[1] = self.ch2offsSpin.value()
        self.voffsets[2] = self.ch3offsSpin.value()
        self.voffsets[3] = self.ch4offsSpin.value()
        
        # Adjust dials positions
        self.hoffsetDial.setValue(int(self.hoffsetSpin.value()*100.0))
        self.ch1offsDial.setValue(int(self.ch1offsSpin.value()*1000.0))
        self.ch2offsDial.setValue(int(self.ch2offsSpin.value()*1000.0))
        self.ch3offsDial.setValue(int(self.ch3offsSpin.value()*1000.0))
        self.ch4offsDial.setValue(int(self.ch4offsSpin.value()*1000.0))
    
    # Sync spin boxes values to dials and sliders values
    def syncDialsSpins(self):
        # Horizontal
        horiz_list = [1e-12, 2e-12, 5e-12]
        hmultiplier = 10**(np.floor(self.hscaleDial.value()/3))
        hvalue = horiz_list[int(self.hscaleDial.value() % 3)]
        self.timediv = hvalue*hmultiplier
        self.sampletime = 10*self.timediv
        self.hscaleInd.setText(f"{self.float2SI(self.timediv)}s")
        self.hoffsetSpin.setValue(self.hoffsetDial.value()/100.0)
        
        # Vertical
        vert_list = [1e-4, 2e-4, 5e-4]
        
        # CH1
        vmultiplier = 10**(np.floor(self.ch1scaleDial.value()/3))
        vvalue = vert_list[int(self.ch1scaleDial.value() % 3)]
        vdiv = vvalue*vmultiplier
        self.ch1scaleInd.setText(f"{self.float2SI(vdiv)}V")
        self.ch1offsSpin.setValue(self.ch1offsDial.value()/1000.0)
        self.voltdivs[0] = vdiv
        
        # CH2
        multiplier = 10**(np.floor(self.ch2scaleDial.value()/3))
        value = vert_list[int(self.ch2scaleDial.value() % 3)]
        vdiv = value*multiplier
        self.ch2scaleInd.setText(f"{self.float2SI(vdiv)}V")
        self.ch2offsSpin.setValue(self.ch2offsDial.value()/1000.0)
        self.voltdivs[1] = vdiv
        
        # CH3
        multiplier = 10**(np.floor(self.ch3scaleDial.value()/3))
        value = vert_list[int(self.ch3scaleDial.value() % 3)]
        vdiv = value*multiplier
        self.ch3scaleInd.setText(f"{self.float2SI(vdiv)}V")
        self.ch3offsSpin.setValue(self.ch3offsDial.value()/1000.0)
        self.voltdivs[2] = vdiv
        
        # CH4
        multiplier = 10**(np.floor(self.ch4scaleDial.value()/3))
        value = vert_list[int(self.ch4scaleDial.value() % 3)]
        vdiv = value*multiplier
        self.ch4scaleInd.setText(f"{self.float2SI(vdiv)}V")
        self.ch4offsSpin.setValue(self.ch4offsDial.value()/1000.0)
        self.voltdivs[3] = vdiv
        
        self.voltscales = self.voltdivs*10


    # Internal functions
    # Helper to convert scientific notation to readable number with appropriate unit
    def float2SI(self, number):
        units = {  0:' ',
           1:'K',  2:'M',  3:'G',  4:'T',  5:'P',  6:'E',  7:'Z',  8:'Y',  9:'R',  10:'Q',
          -1:'m', -2:'u', -3:'n', -4:'p', -5:'f', -6:'a', -7:'z', -8:'y', -9:'r', -10:'q'
        }
         
        mantissa,exponent = f"{number:e}".split("e")
        unitRange         = int(exponent)//3                        
        unit              = units.get(unitRange,None)
        unitValue         = float(mantissa)*10**(int(exponent)%3)
        return f"{unitValue:.0f} {unit}" if unit else f"{number:.5e}"
    
    # Acquisition loop
    def measLoop(self):
        if not self.busy and self.running:
            # Set soft lock
            self.busy = True
            
            # Create arrays
            self.x_axis = np.linspace(self.timeoffs, self.timeoffs + self.sampletime, self.npoints)  
            show_x_axis = np.linspace(self.timeoffs, self.timeoffs + self.sampletime, self.display_points)
            show_data = np.zeros((4, self.display_points))
            if self.holdCheck.isChecked():
                self.x_axis = np.tile(self.x_axis, self.hold_counter + 1)
                self.y_axis = np.zeros([4, self.display_points*(self.hold_counter + 1)])
            
            # Sweep channels
            for i in range(0, len(self.input_objs)):
                if self.channelsChecks[i].isChecked() and self.input_objs[i]:
                    # Adjust phase to simulate trigger (and time offset)
                    if self.triggerautoRadio.isChecked():
                        freq = self.input_objs[i].freq
                        argument = 2*np.pi*freq*self.timeoffs
                        self.input_objs[i].t0 = argument
                    else:
                        self.input_objs[i].t0 = np.random.uniform(0.0, 2*np.pi)
                        
                    # Get data
                    new_data = self.input_channels(i)

                    # If hold is enabled, hold data
                    if self.holdCheck.isChecked():
                        self.hold_buffer[i] = np.concatenate(([new_data], self.hold_buffer[i][0:-1]))
                        self.y_axis[i] = np.concatenate(self.hold_buffer[i][0:self.hold_counter + 1])
                    # If not, perform averaging
                    elif self.avgSpin.value() > 1:
                        self.avg_buffer[i] = np.concatenate(([new_data], self.avg_buffer[i][0:-1]))
                        self.y_axis[i] = self.avg_buffer[i][0:self.avg_counter + 1].mean(axis=0)
                    else:
                        self.y_axis[i] = new_data

                    # Resample data
                    show_data_interp = interp1d(self.x_axis, self.y_axis[i], kind='cubic')
                    show_data[i] = show_data_interp(show_x_axis)

                    # Update plot
                    self.graph_lines[i].set_ydata((show_data[i] + self.voffsets[i])/self.voltdivs[i])
                    self.graph_lines[i].set_xdata(show_x_axis)
                    self.graph_lines[i].set_visible(True)
                else:
                    self.graph_lines[i].set_visible(False)

            self.graph_ax.set_xlim([self.timeoffs, self.timediv*10 + self.timeoffs])
            self.graph_ax.set_ylim([self.mastervscale[0], self.mastervscale[1]])
            self.graph_ax.xaxis.set_ticks(np.linspace(self.timeoffs, self.timediv*10 + self.timeoffs, 11))
            self.graph_ax.yaxis.set_ticks(np.linspace(self.mastervscale[0], self.mastervscale[1], 11))
            self.graph_ax.set_xlabel("Time (s)")
            self.graph_ax.set_ylabel("Voltage (Div)")

            # After getting all data, change plots to XY mode if enabled
            ch = self.xy_x - 1
            if self.xymode and self.channelsChecks[ch].isChecked() and self.input_objs[ch]:
                for i in range(0, len(self.input_objs)):
                    if self.channelsChecks[i].isChecked() and self.input_objs[i] and i != ch:
                        new_x = (show_data[ch] + self.voffsets[ch])/self.voltdivs[ch]
                        self.graph_lines[i].set_xdata(new_x)
                        self.graph_lines[i].set_visible(True)
                        self.graph_ax.set_xlim([self.mastervscale[0], self.mastervscale[1]])
                        self.graph_ax.xaxis.set_ticks(np.linspace(self.mastervscale[0], self.mastervscale[1], 11), labels=["","","","","","","","","","",""])
                    elif self.channelsChecks[i].isChecked() and self.input_objs[i] and i == ch:
                        self.graph_lines[i].set_visible(False)
                
                self.graph_ax.set_xlabel(f"CH{ch + 1} Voltage (Div)")
                self.graph_ax.set_ylabel("Voltage (Div)")
            
            self.graph.draw()
            self.graph.flush_events()

            # Update counters
            if self.holdCheck.isChecked():
                self.hold_counter += 1
                if self.hold_counter >= self.holdSpin.value():
                    self.hold_counter = self.holdSpin.value() - 1
            elif self.avgSpin.value() > 1:
                self.avg_counter += 1
                if self.avg_counter >= self.avgSpin.value():
                    self.avg_counter = self.avgSpin.value() - 1
            
            # Release soft lock
            self.busy = False

    # Save data
    def saveData(self):
        was_running = False
        if self.running:
            self.stopAcquisition()
            was_running = True
        
        file = QFileDialog.getSaveFileName(self, "Save file", QDir.homePath() , "Text files (*.txt)")
        filename = file[0]
        if filename != "":
            if filename[-4:] != ".txt" and filename[-4:] != ".TXT":
                filename = filename + ".txt"   

            with open(filename, "w") as file:
                file.write("Time(s)\t")
                for j in range(0, len(self.input_objs)):
                    if self.channelsChecks[j].isChecked():
                        file.write(f"CH{j + 1}(V)\t")
                file.write("\n")

                for i in range(len(self.y_axis[0])):
                    file.write(f"{self.x_axis[i]}\t")
                    for j in range(0, len(self.input_objs)):
                        if self.channelsChecks[j].isChecked():
                            file.write(f"{self.y_axis[j][i]}")
                            if j < len(self.input_objs) - 1:
                                file.write("\t")
                    file.write("\n")
                file.close()

        if was_running:
            self.runAcquisition()


    # I/O functions
    # Set inputs: to connect the in functions to other instruments
    def startComms(self, port):
        self.comms.start("127.0.0.1", port)
        
    def set_inputs(self, ch1=None, ch2=None, ch3=None, ch4=None):    
        self.input_objs = [ch1, ch2, ch3, ch4]

    # Input functions: all parameters and instrument inputs are processed here. These are active (calls the output from other instruments)
    # Total time of the output wave
    def input_channels(self, channel):
        if self.input_objs[channel] and self.channelsChecks[channel].isChecked():
            data = self.input_objs[channel].output_signal()
        else:
            data = np.zeros([self.npoints])
        return data

    # Output functions: all instrument outputs are processed here. These are passive (called from other instruments)
    # Output sample time 
    def output_sampletime(self):
        return self.sampletime*1

    # Output npoints
    def output_npoints(self):
        return self.npoints*1