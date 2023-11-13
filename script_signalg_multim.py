import pyvisa as visa
import numpy as np
import time
import matplotlib.pyplot as plt

rm = visa.ResourceManager()
mult_str = "TCPIP0::127.0.0.1::51234::SOCKET"
sg_str = "TCPIP0::127.0.0.1::51235::SOCKET"

mult = rm.open_resource(mult_str)
mult.read_termination = "\n"
print(mult.query("*IDN?"))

sg = rm.open_resource(sg_str)
sg.read_termination = "\n"
print(sg.query("*IDN?"))

sg.write("freq:freq 0.2")
sg.write("freq:cvar 100")
sg.write("freq:cper 2.0")
sg.write("freq:chrp 0")
sg.write("amp:amp 10.0")
sg.write("out 1")
sg.write("amp:offs 0.0")
sg.write("wave:wave saw")
sg.write("wave:dc 10")
sg.write("wave:phas 90.0")

pts = 100000
times = np.zeros(pts)
volts = np.zeros(pts)

t0 = time.time()
for i in range(pts):
    times[i] = time.time() - t0
    volts[i] = mult.query("meas:volt?")
    # time.sleep(0.011)

plt.plot(times, volts)
plt.show()

sg.write("amp:offs 0")
sg.write("out 0")
sg.close()
mult.close()