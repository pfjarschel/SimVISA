SimVISA: Examples of virtual instrumentation to be used as teaching aid for scientific instrumentation control and automation.

The basic idea is mainly composed of 4 elements: 
- Virtual instruments, with graphical interfaces
- A tiny web server embedded in each virtual instrument, to handle message exchange between application and instrument, and act according to the messages
- A "setup" script, to simulate the actual experiment setup
- A script to control the experiment and automate actions and measurements, using standard PyVISA routines.

Requires PyVisa, PyQt6, Numpy, and Matplotlib.

To run the examples, simply run a setup_xxx.py file, and create a script just like you would in a real lab! Or, run one of the example scripts.

VISA commands documentation will be provided in the near future.
This readme will be updated in the near future to include more details.