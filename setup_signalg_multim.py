from instruments.virtual_signal_gen import VirtualSignalGenerator
from instruments.virtual_multimeter import VirtualMultimeter
import sys
from PyQt6.QtWidgets import QApplication


# Construct application
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create instruments
    mult = VirtualMultimeter()
    sg = VirtualSignalGenerator()
    
    # Connect parameters and instruments 
    # The multimeter gets the signal generator output
    mult.set_inputs(sg)
    
    # The signal generator gets the sample time and npoints when needed
    sg.set_inputs(sampletime_obj=mult, npoints_obj=mult)

    # Start communications
    mult.startComms(port=51234)
    sg.startComms(port=51235)

    # Run application
    app.exec()

    # Exit when done
    sys.exit()