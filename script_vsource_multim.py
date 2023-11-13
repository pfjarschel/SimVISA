import pyvisa as visa
import numpy as np
import time
import matplotlib.pyplot as plt

rm = visa.ResourceManager()
mult_str = "TCPIP0::127.0.0.1::51234::SOCKET"
vs_str = "TCPIP0::127.0.0.1::51235::SOCKET"

mult = rm.open_resource(mult_str)
mult.read_termination = "\n"
print(mult.query("*IDN?"))

vs = rm.open_resource(vs_str)
vs.read_termination = "\n"
print(vs.query("*IDN?"))

print(vs.query("volt?"))
vs.write("volt 18.472")
time.sleep(0.1)
print(vs.query("volt?"))
print(mult.query("meas:volt?"))
vs.write("volt -12.123")
time.sleep(0.1)

pts = 10
times = np.zeros(pts)
volts = np.zeros(pts)

t0 = time.time()
for i in range(pts):
    times[i] = time.time() - t0
    vs.write(f"volt {np.random.randint(-1000,1000)/100.0}")
    volts[i] = mult.query("meas:volt?")
    time.sleep(1.1)

plt.plot(times, volts)
plt.show()

vs.close()
mult.close()