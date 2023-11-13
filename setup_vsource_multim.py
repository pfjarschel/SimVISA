from instruments.virtual_vsource import VirtualVSource
from instruments.virtual_multimeter import VirtualMultimeter
import sys
from PyQt6.QtWidgets import QApplication


# Construct application
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create instruments
    mult = VirtualMultimeter()
    vs = VirtualVSource()
    
    # Connect parameters and instruments 
    # The multimeter gets the source output directly
    mult.set_inputs(vs)
    
    # The source gets the npoints when needed
    vs.set_inputs(npoints_obj=mult)

    # Start communications
    mult.startComms(port=51234)
    vs.startComms(port=51235)

    # Run application
    app.exec()

    # Exit when done
    sys.exit()