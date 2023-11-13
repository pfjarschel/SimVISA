from instruments.virtual_signal_gen import VirtualSignalGenerator
from instruments.virtual_rc import VirtualRC
from instruments.virtual_oscilloscope import VirtualOscilloscope
import sys
from PyQt6.QtWidgets import QApplication


# Construct application
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create instruments
    sg = VirtualSignalGenerator()
    rc = VirtualRC()
    osc = VirtualOscilloscope()
    
    # Connect parameters and instruments 
    # The oscilloscope gets the function generator and the circuit outputs
    osc.set_inputs(sg, rc)

    # The circuit gets the signal generator output and the sample time and npoints when needed
    rc.set_inputs(mainin_obj=sg, sampletime_obj=osc, npoints_obj=osc)
    
    # The signal generator gets the sample time and npoints when needed
    sg.set_inputs(sampletime_obj=rc, npoints_obj=rc)

    # Start communications
    osc.startComms(port=51234)
    sg.startComms(port=51235)
    rc.startComms(port=51236)

    # Run application
    app.exec()

    # Exit when done
    sys.exit()